"""Portfolio scaling, nonlinear risk and delta-hedge accounting scope."""

import json
from dataclasses import replace

import pytest

from derivatives_lab import (
    Market,
    Option,
    Position,
    Scenario,
    explain,
    greeks,
    portfolio_greeks,
    portfolio_value,
)
from derivatives_lab.demo import PRESETS, main, preset


@pytest.mark.parametrize("name", PRESETS)
def test_aggregation(name):
    positions, market = preset(name), Market()
    total = portfolio_greeks(positions, market)
    for field in ("price", "delta", "gamma", "vega", "theta", "rho"):
        assert getattr(total, field) == pytest.approx(
            sum(p.units * getattr(greeks(p.option, market), field) for p in positions)
        )
    assert total.price == pytest.approx(portfolio_value(positions, market))


def test_zero_shock_and_cost():
    result = explain(preset("Long call"), Market(), Scenario(0, 0, 0, 0))
    assert result.exact_pnl == result.approximation == result.residual == 0
    assert result.remaining_delta == 0
    assert result.hedged_pnl == pytest.approx(-result.hedge_cost)
    assert result.hedge_cost == pytest.approx(abs(result.hedge_shares) * 100 / 10000)


def test_short_gamma_survives_hedging():
    positions, market = preset(), Market()
    assert portfolio_greeks(positions, market).gamma < 0
    assert portfolio_greeks(positions, market).vega < 0
    for move in (-0.15, 0.15):
        result = explain(positions, market, Scenario(move, 0, 0, 0), 0)
        assert result.hedged_pnl < 0
        assert result.hedged_pnl == pytest.approx(result.exact_pnl + result.stock_pnl)
        assert result.exact_pnl == pytest.approx(result.approximation + result.residual)


def test_small_shock_approximation():
    positions, market = preset("Long call"), Market()
    small = explain(positions, market, Scenario(0.001, 0, 0, 0))
    large = explain(positions, market, Scenario(0.10, 0, 0, 0))
    assert abs(small.residual) < 0.001
    assert abs(small.residual / small.exact_pnl) < abs(large.residual / large.exact_pnl)


def test_mixed_shock_units():
    positions, market = preset(), Market()
    g, shock = portfolio_greeks(positions, market), Scenario(0.02, 1, 10, 1)
    result = explain(positions, market, shock)
    assert result.delta_pnl == pytest.approx(g.delta * 2)
    assert result.gamma_pnl == pytest.approx(0.5 * g.gamma * 4)
    assert result.vega_pnl == pytest.approx(g.vega_point)
    assert result.theta_pnl == pytest.approx(g.theta_day)
    assert result.rho_pnl == pytest.approx(g.rho_bp * 10)
    assert result.exact_pnl == pytest.approx(portfolio_value(positions, shock.apply(market), 1) - g.price)


def test_expiry_horizon_empty_and_zero_positions():
    positions, market = preset("Long call", days=7, contracts=1), Market(110)
    assert portfolio_value(positions, market, 7) == pytest.approx(1000)
    assert portfolio_value((), market) == 0
    assert portfolio_greeks((), market).delta == 0
    zero = (Position("zero", Option(100, 0), 0),)
    assert portfolio_value(zero, market, 1) == 0
    assert portfolio_greeks(zero, market).price == 0
    with pytest.raises(ValueError):
        portfolio_value(positions, market, 8)
    with pytest.raises(ValueError):
        portfolio_value(positions, market, -1)


@pytest.mark.parametrize(
    "op",
    [
        lambda: Market(0),
        lambda: Market(volatility=0),
        lambda: Market(rate=float("nan")),
        lambda: Market(spot=True),
        lambda: Option(0, 1),
        lambda: Option(100, -1),
        lambda: Option(100, 1, "bad"),
        lambda: Position("", Option(100, 1), 1),
        lambda: Position("x", Option(100, 1), 1.2),
        lambda: Position("x", Option(100, 1), 1, 0),
        lambda: Scenario(spot_return=-1),
        lambda: Scenario(days=-1),
        lambda: Scenario(vol_points=-99).apply(Market()),
        lambda: preset("bad"),
        lambda: preset(contracts=0),
        lambda: explain(preset(), Market(), Scenario(), -1),
    ],
)
def test_bad_inputs(op):
    with pytest.raises(ValueError):
        op()


def test_demo(capsys):
    main()
    data = json.loads(capsys.readouterr().out)
    assert data["market"] == "synthetic"
    assert data["result"]["remaining_delta"] == 0
    assert data["result"]["exact_pnl"] < 0


def test_offset_positions():
    call = Position("long", Option(100, 0.5), 10)
    offset = replace(call, name="short", contracts=-10)
    assert portfolio_greeks((call, offset), Market()).price == 0
    assert explain((call, offset), Market(), Scenario()).exact_pnl == 0
