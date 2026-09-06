"""Signed portfolio risk, local P&L attribution and a static delta hedge."""

from dataclasses import dataclass, replace
from math import fsum

from .models import Market, Position, finite
from .pricing import Greeks, greeks, price


def portfolio_greeks(positions: tuple[Position, ...], market: Market) -> Greeks:
    """Sum signed unit Greeks after contract scaling; zero positions contribute nothing."""
    risks = [(p.units, greeks(p.option, market)) for p in positions if p.units]
    fields = ("price", "delta", "gamma", "vega", "theta", "rho")
    return Greeks(*(fsum(units * getattr(risk, field) for units, risk in risks) for field in fields))


def portfolio_value(positions: tuple[Position, ...], market: Market, elapsed_days: float = 0) -> float:
    """Mark-to-model market value; scenario may reach but not pass a live leg's expiry."""
    finite(elapsed_days, "elapsed days")
    if elapsed_days < 0:
        raise ValueError("Elapsed time cannot be negative")
    total = []
    for position in positions:
        if not position.units:
            continue
        remaining = position.option.expiry - elapsed_days / 365
        if remaining < -1e-12:
            raise ValueError("Scenario passes an option expiry; settlement/reinvestment not modelled")
        total.append(position.units * price(replace(position.option, expiry=max(remaining, 0)), market))
    return fsum(total)


@dataclass(frozen=True)
class Scenario:
    """Absolute shocks: spot fraction, vol percentage points, rate bp and calendar days."""

    spot_return: float = 0.05
    vol_points: float = 3.0
    rate_bp: float = 0.0
    days: float = 1.0

    def __post_init__(self) -> None:
        for name in ("spot_return", "vol_points", "rate_bp", "days"):
            finite(getattr(self, name), name)
        if self.spot_return <= -1 or self.days < 0:
            raise ValueError("Spot shock must exceed -100%; days must be nonnegative")

    def apply(self, market: Market) -> Market:
        """Apply endpoint shocks, validating resulting positive spot and volatility."""
        return replace(
            market,
            spot=market.spot * (1 + self.spot_return),
            volatility=market.volatility + self.vol_points / 100,
            rate=market.rate + self.rate_bp / 10000,
        )


@dataclass(frozen=True)
class Explain:
    """Option mark-to-market P&L and static stock hedge, before dividends and financing."""

    initial_value: float
    final_value: float
    exact_pnl: float
    delta_pnl: float
    gamma_pnl: float
    vega_pnl: float
    theta_pnl: float
    rho_pnl: float
    approximation: float
    residual: float
    hedge_shares: float
    stock_pnl: float
    hedge_cost: float
    hedged_pnl: float
    remaining_delta: float


def explain(
    positions: tuple[Position, ...], market: Market, scenario: Scenario, hedge_cost_bp: float = 1.0
) -> Explain:
    """Compare exact option repricing with delta/gamma/vega/theta/rho Taylor terms.

    Hedge is initiated once at opening delta using fractional stock units. Transaction
    cost is charged once on the stock trade; funding, dividends and unwind are excluded.
    The residual is omitted higher-order/cross effects, not a data-quality exception.
    """
    finite(hedge_cost_bp, "hedge cost")
    if hedge_cost_bp < 0:
        raise ValueError("Hedge execution cost must be nonnegative")
    risk = portfolio_greeks(positions, market)
    endpoint = scenario.apply(market)
    ending = portfolio_value(positions, endpoint, scenario.days)
    ds = endpoint.spot - market.spot
    terms = (
        risk.delta * ds,
        0.5 * risk.gamma * ds**2,
        risk.vega * scenario.vol_points / 100,
        risk.theta * scenario.days / 365,
        risk.rho * scenario.rate_bp / 10000,
    )
    approximation = fsum(terms)
    exact = ending - risk.price
    hedge = -risk.delta
    cost = abs(hedge) * market.spot * hedge_cost_bp / 10000
    return Explain(
        risk.price,
        ending,
        exact,
        *terms,
        approximation,
        exact - approximation,
        hedge,
        hedge * ds,
        cost,
        exact + hedge * ds - cost,
        risk.delta + hedge,
    )
