"""Implied volatility inversion and an independent CRR tree valuation benchmark."""

from dataclasses import replace
from math import exp, sqrt

from .models import Market, Option, finite
from .pricing import price


def implied_volatility(
    option: Option, market: Market, premium: float, tolerance: float = 1e-10, max_iterations: int = 200
) -> float:
    """Invert a European premium over volatility [1e-6, 5.0] with bracketed bisection.

    Strict arbitrage boundaries and the finite search domain can reject a premium.
    Tolerance is absolute volatility width; no implied volatility exists at expiry.
    """
    finite(premium, "premium")
    finite(tolerance, "tolerance")
    if option.expiry <= 0 or tolerance <= 0 or max_iterations < 1:
        raise ValueError("Positive expiry, tolerance and iteration limit required")
    discounted_spot = market.spot * exp(-market.dividend * option.expiry)
    discounted_strike = option.strike * exp(-market.rate * option.expiry)
    if option.kind == "call":
        lower_bound, upper_bound = max(0.0, discounted_spot - discounted_strike), discounted_spot
    else:
        lower_bound, upper_bound = max(0.0, discounted_strike - discounted_spot), discounted_strike
    if not lower_bound < premium < upper_bound:
        raise ValueError("Premium must be strictly inside European no-arbitrage bounds")
    lower, upper = 0.000001, 5.0
    if (
        not price(option, replace(market, volatility=lower))
        <= premium
        <= price(option, replace(market, volatility=upper))
    ):
        raise ValueError("Premium lies outside the supported volatility bracket")
    for _ in range(max_iterations):
        middle = (lower + upper) / 2
        if upper - lower <= tolerance:
            return middle
        if price(option, replace(market, volatility=middle)) < premium:
            lower = middle
        else:
            upper = middle
    raise RuntimeError("Implied volatility did not converge")


def crr_price(option: Option, market: Market, steps: int = 500) -> float:
    """European Cox–Ross–Rubinstein tree, O(n²) time / O(n) memory; benchmark only.

    Reject invalid risk-neutral probabilities instead of silently clamping them.
    This implementation shares inputs, but not normal-CDF pricing logic, with BSM.
    """
    if type(steps) is not int or not 1 <= steps <= 3000:
        raise ValueError("steps must be an integer from 1 to 3000")
    if option.expiry == 0:
        return price(option, market)
    dt = option.expiry / steps
    up = exp(market.volatility * sqrt(dt))
    down = 1 / up
    probability = (exp((market.rate - market.dividend) * dt) - down) / (up - down)
    if not 0 <= probability <= 1:
        raise ValueError("Invalid tree probability; increase steps or adjust market inputs")
    sign = 1 if option.kind == "call" else -1
    values = [
        max(sign * (market.spot * up**j * down ** (steps - j) - option.strike), 0.0) for j in range(steps + 1)
    ]
    discount = exp(-market.rate * dt)
    for level in range(steps, 0, -1):
        for node in range(level):
            values[node] = discount * (probability * values[node + 1] + (1 - probability) * values[node])
    return values[0]
