"""Immutable option and market contracts with explicit units."""

from dataclasses import dataclass
from math import isfinite
from typing import Literal


def finite(value: float, name: str) -> None:
    """Reject nonfinite and boolean numerical inputs."""
    if isinstance(value, bool) or not isfinite(value):
        raise ValueError(f"{name} must be finite")


@dataclass(frozen=True)
class Market:
    """Spot in currency/share; annual r, q and volatility in decimals."""

    spot: float = 100.0
    volatility: float = 0.20
    rate: float = 0.03
    dividend: float = 0.0

    def __post_init__(self) -> None:
        for name in ("spot", "volatility", "rate", "dividend"):
            finite(getattr(self, name), name)
        if self.spot <= 0 or self.volatility <= 0:
            raise ValueError("Positive spot and volatility required")


@dataclass(frozen=True)
class Option:
    """European vanilla contract, expiry in ACT/365 model years; strike in currency/share."""

    strike: float
    expiry: float
    kind: Literal["call", "put"] = "call"

    def __post_init__(self) -> None:
        finite(self.strike, "strike")
        finite(self.expiry, "expiry")
        if self.strike <= 0 or self.expiry < 0 or self.kind not in ("call", "put"):
            raise ValueError("Positive strike, nonnegative expiry and call/put required")


@dataclass(frozen=True)
class Position:
    """Signed integer option contracts and shares/contract multiplier."""

    name: str
    option: Option
    contracts: int
    multiplier: int = 100

    def __post_init__(self) -> None:
        if not self.name or type(self.contracts) is not int or type(self.multiplier) is not int:
            raise ValueError("Named position and integer contracts/multiplier required")
        if self.multiplier <= 0:
            raise ValueError("Multiplier must be positive")

    @property
    def units(self) -> int:
        """Signed option units, already incorporating the contract multiplier."""
        return self.contracts * self.multiplier
