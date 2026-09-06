"""Closed forms, parity, finite-difference Greeks and independent numerical checks."""

from dataclasses import replace
from math import exp

import pytest
from scipy.stats import norm

from derivatives_lab import Market, Option, crr_price, greeks, implied_volatility, price
from derivatives_lab.pricing import normal_cdf, normal_pdf


@pytest.mark.parametrize("x", [-12, -8, -4, -1, 0, 1, 4, 8, 12])
def test_normal_scipy(x):
    assert normal_cdf(x) == pytest.approx(norm.cdf(x), rel=1e-12, abs=1e-35)
    assert normal_pdf(x) == pytest.approx(norm.pdf(x), rel=1e-12, abs=1e-35)


def test_known_values():
    market, call = Market(100, 0.2, 0.05), Option(100, 1)
    assert price(call, market) == pytest.approx(10.4505835721856, abs=1e-11)
    assert price(replace(call, kind="put"), market) == pytest.approx(5.57352602225697, abs=1e-11)
    g = greeks(call, market)
    assert g.delta == pytest.approx(0.636830651175619, abs=1e-12)
    assert g.gamma == pytest.approx(0.0187620173458469, abs=1e-12)
    assert g.vega == pytest.approx(37.5240346916938, abs=1e-11)
    assert g.theta == pytest.approx(-6.4140275464382, abs=1e-11)


@pytest.mark.parametrize("spot", [65, 100, 135])
@pytest.mark.parametrize("rate,q", [(0.03, 0), (-0.01, 0.02), (0.07, 0.04)])
def test_parity_and_bounds(spot, rate, q):
    market, call = Market(spot, 0.3, rate, q), Option(100, 0.5)
    put = replace(call, kind="put")
    c, p = price(call, market), price(put, market)
    assert c - p == pytest.approx(spot * exp(-q * 0.5) - 100 * exp(-rate * 0.5), abs=1e-11)
    assert 0 <= c <= spot * exp(-q * 0.5)
    assert 0 <= p <= 100 * exp(-rate * 0.5)
    cg, pg = greeks(call, market), greeks(put, market)
    assert cg.delta - pg.delta == pytest.approx(exp(-q * 0.5))
    assert cg.gamma == pytest.approx(pg.gamma)
    assert cg.vega == pytest.approx(pg.vega)


@pytest.mark.parametrize("kind", ["call", "put"])
@pytest.mark.parametrize(
    "s,v,r,q,t",
    [
        (100, 0.2, 0.03, 0, 1),
        (90, 0.35, -0.01, 0.02, 0.5),
        (110, 0.18, 0.05, 0.03, 0.1),
        (100, 0.5, 0, 0.08, 7 / 365),
    ],
)
def test_greeks_numerical(kind, s, v, r, q, t):
    m, o = Market(s, v, r, q), Option(100, t, kind)
    g, h, e = greeks(o, m), 0.001, 1e-5
    up, down = price(o, replace(m, spot=s + h)), price(o, replace(m, spot=s - h))
    assert g.delta == pytest.approx((up - down) / (2 * h), rel=1e-6, abs=1e-8)
    assert g.gamma == pytest.approx((up + down - 2 * g.price) / h**2, rel=2e-5, abs=1e-7)
    assert g.vega == pytest.approx(
        (price(o, replace(m, volatility=v + e)) - price(o, replace(m, volatility=v - e))) / (2 * e), rel=1e-6
    )
    assert g.rho == pytest.approx(
        (price(o, replace(m, rate=r + e)) - price(o, replace(m, rate=r - e))) / (2 * e), rel=1e-6
    )
    assert g.theta == pytest.approx(
        (price(replace(o, expiry=t - e), m) - price(replace(o, expiry=t + e), m)) / (2 * e), rel=1e-6
    )
    assert g.vega_point == pytest.approx(g.vega / 100)
    assert g.theta_day == pytest.approx(g.theta / 365)
    assert g.rho_bp == pytest.approx(g.rho / 10000)


@pytest.mark.parametrize("kind", ["call", "put"])
@pytest.mark.parametrize("spot", [80, 100, 120])
def test_crr_independent(kind, spot):
    m, o = Market(spot, 0.25, 0.03, 0.01), Option(100, 0.5, kind)
    assert crr_price(o, m, 1200) == pytest.approx(price(o, m), abs=0.004)


def test_tree_convergence():
    m, o = Market(), Option(100, 1)
    assert abs(crr_price(o, m, 1000) - price(o, m)) < abs(crr_price(o, m, 100) - price(o, m))


@pytest.mark.parametrize("kind", ["call", "put"])
@pytest.mark.parametrize("vol", [0.08, 0.2, 0.65, 1.5])
def test_iv_roundtrip(kind, vol):
    m, o = Market(100, vol, 0.03, 0.01), Option(100, 0.5, kind)
    assert implied_volatility(o, replace(m, volatility=0.3), price(o, m)) == pytest.approx(vol, abs=1e-9)


@pytest.mark.parametrize(
    "kind,spot,payoff", [("call", 120, 20), ("put", 80, 20), ("call", 80, 0), ("put", 120, 0)]
)
def test_expiry(kind, spot, payoff):
    m, o = Market(spot), Option(100, 0, kind)
    assert price(o, m) == crr_price(o, m) == payoff
    with pytest.raises(ValueError):
        greeks(o, m)
    with pytest.raises(ValueError):
        implied_volatility(o, m, 10)


@pytest.mark.parametrize("premium", [-1, 0, 100, 101])
def test_bad_premium(premium):
    with pytest.raises(ValueError):
        implied_volatility(Option(100, 1), Market(), premium)


def test_solver_boundaries():
    o, m = Option(100, 1), Market()
    with pytest.raises(ValueError, match="volatility bracket"):
        implied_volatility(o, m, price(o, replace(m, volatility=6)))
    with pytest.raises(ValueError):
        implied_volatility(o, m, 10, tolerance=0)
    with pytest.raises(RuntimeError):
        implied_volatility(o, m, 10, max_iterations=1)
    with pytest.raises(ValueError):
        crr_price(o, m, 0)
    with pytest.raises(ValueError, match="probability"):
        crr_price(o, Market(volatility=0.000001, rate=0.5), 1)
