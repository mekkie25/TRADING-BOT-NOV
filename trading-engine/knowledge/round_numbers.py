"""Report nearby round-number prices using an explicitly supplied interval."""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal


@dataclass(frozen=True)
class RoundNumberReport:
    symbol: str
    time: datetime
    price: float
    step: float
    lower_level: float
    upper_level: float
    is_exact_level: bool
    distance_to_lower: float
    distance_to_upper: float
    summary: str


def analyze_round_numbers(
    symbol: str,
    time: datetime,
    price: float,
    step: float,
) -> RoundNumberReport:
    """Find the price levels around a quote without assuming an instrument step."""
    if not symbol.strip():
        raise ValueError("symbol must not be empty.")
    if time.tzinfo is None or time.utcoffset() != timedelta(0):
        raise ValueError("time must be timezone-aware UTC.")
    if not math.isfinite(price) or price <= 0:
        raise ValueError("price must be a positive finite number.")
    if not math.isfinite(step) or step <= 0:
        raise ValueError("step must be a positive finite number.")

    decimal_price = Decimal(str(price))
    decimal_step = Decimal(str(step))
    lower = decimal_price // decimal_step * decimal_step
    is_exact_level = decimal_price == lower
    upper = lower if is_exact_level else lower + decimal_step
    lower_level = float(lower)
    upper_level = float(upper)
    distance_to_lower = float(decimal_price - lower)
    distance_to_upper = float(upper - decimal_price)

    if is_exact_level:
        summary = (
            f"{symbol} price is at the configured round-number level "
            f"{lower_level:g} at {time.isoformat()} UTC."
        )
    else:
        summary = (
            f"{symbol} price is between configured round-number levels "
            f"{lower_level:g} and {upper_level:g} at {time.isoformat()} UTC."
        )

    return RoundNumberReport(
        symbol=symbol,
        time=time,
        price=price,
        step=step,
        lower_level=lower_level,
        upper_level=upper_level,
        is_exact_level=is_exact_level,
        distance_to_lower=distance_to_lower,
        distance_to_upper=distance_to_upper,
        summary=summary,
    )
