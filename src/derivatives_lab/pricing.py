"""Black–Scholes–Merton pricing and analytical Greeks, standard library only."""

from dataclasses import dataclass
from math import erfc, exp, log, pi, sqrt

from .models import Market, Option


def normal_cdf(x: float) -> float:
    """Standard normal CDF via erfc for stable negative-tail evaluation."""
    return 0.5 * erfc(-x / sqrt(2))


def normal_pdf(x: float) -> float:
    """Standard normal density."""
    return exp(-x * x / 2) / sqrt(2 * pi)


def _d(option: Option, market: Market) -> tuple[float, float]:
    if option.expiry <= 0:
        raise ValueError("Greeks require positive time to expiry")
    sigma_t = market.volatility * sqrt(option.expiry)
    d1 = (
        log(market.spot / option.strike)
        + (market.rate - market.dividend + 0.5 * market.volatility**2) * option.expiry
    ) / sigma_t
    return d1, d1 - sigma_t


def price(option: Option, market: Market) -> float:
    """Value per option unit; at expiry return intrinsic payoff, not undefined Greeks."""
    sign = 1 if option.kind == "call" else -1
    if option.expiry == 0:
        return max(sign * (market.spot - option.strike), 0.0)
    d1, d2 = _d(option, market)
    discounted_spot = market.spot * exp(-market.dividend * option.expiry)
    discounted_strike = option.strike * exp(-market.rate * option.expiry)
    return max(
        sign * (discounted_spot * normal_cdf(sign * d1) - discounted_strike * normal_cdf(sign * d2)), 0.0
    )


@dataclass(frozen=True)
class Greeks:
    """Per-unit derivatives: vega/rho per 1.0 decimal change; theta per calendar year."""

    price: float
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float

    @property
    def vega_point(self) -> float:
        """Currency per one volatility percentage point, e.g. 20% → 21%."""
        return self.vega * 0.01

    @property
    def theta_day(self) -> float:
        """Currency per elapsed calendar day, using 365 days/year."""
        return self.theta / 365

    @property
    def rho_bp(self) -> float:
        """Currency per +1bp continuously compounded rate change."""
        return self.rho * 0.0001


def greeks(option: Option, market: Market) -> Greeks:
    """Closed-form BSM derivatives with continuous dividend yield."""
    d1, d2 = _d(option, market)
    sign = 1 if option.kind == "call" else -1
    t, s, k = option.expiry, market.spot, option.strike
    dq, dr = exp(-market.dividend * t), exp(-market.rate * t)
    n1, n2, density = normal_cdf(sign * d1), normal_cdf(sign * d2), normal_pdf(d1)
    delta = sign * dq * n1
    gamma = dq * density / (s * market.volatility * sqrt(t))
    vega = s * dq * density * sqrt(t)
    theta = -s * dq * density * market.volatility / (2 * sqrt(t)) + sign * (
        market.dividend * s * dq * n1 - market.rate * k * dr * n2
    )
    rho = sign * k * t * dr * n2
    return Greeks(price(option, market), delta, gamma, vega, theta, rho)
