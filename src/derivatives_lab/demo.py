"""Synthetic portfolio presets and a reproducible JSON demo."""

import json
from dataclasses import asdict

from .models import Market, Option, Position
from .portfolio import Scenario, explain

PRESETS = ("Short straddle", "Long call", "Bull call spread", "Long strangle")


def preset(
    name: str = "Short straddle", strike: float = 100, days: int = 90, contracts: int = 50
) -> tuple[Position, ...]:
    """Return standard illustrative structures with no stock or cash-account holdings."""
    if name not in PRESETS or type(contracts) is not int or contracts <= 0 or days <= 0:
        raise ValueError("Valid preset, positive days and positive integer contracts required")
    call = Option(strike, days / 365, "call")
    put = Option(strike, days / 365, "put")
    if name == "Short straddle":
        return (Position("Short ATM call", call, -contracts), Position("Short ATM put", put, -contracts))
    if name == "Long call":
        return (Position("Long call", call, contracts),)
    if name == "Bull call spread":
        return (
            Position("Long lower call", call, contracts),
            Position("Short upper call", Option(strike * 1.1, days / 365), -contracts),
        )
    return (
        Position("Long OTM call", Option(strike * 1.1, days / 365), contracts),
        Position("Long OTM put", Option(strike * 0.9, days / 365, "put"), contracts),
    )


def main() -> None:
    """Print a reproducible synthetic short-straddle shock and static hedge comparison."""
    result = explain(preset(), Market(), Scenario())
    print(
        json.dumps(
            {
                "market": "synthetic",
                "units": "EUR, calendar days, annual decimal rates",
                "scope": "Mark-to-market P&L before financing and dividends",
                "scenario": asdict(Scenario()),
                "result": asdict(result),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
