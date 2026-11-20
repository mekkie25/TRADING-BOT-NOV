"""Calculate traditional pivot levels from supplied previous-period prices."""

import math
from dataclasses import dataclass
from numbers import Real
from typing import Dict, Literal

from data.timeframes import TIMEFRAME_LENGTHS


PivotPeriod = Literal["daily", "weekly", "monthly", "yearly"]

PIVOT_PERIOD_BY_CHART_TIMEFRAME: Dict[str, PivotPeriod] = {
    "M1": "daily",
    "M5": "daily",
    "M15": "daily",
    "M30": "daily",
    "H1": "daily",
    "H2": "daily",
    "H4": "weekly",
    "D1": "monthly",
    "W1": "yearly",
    "MONTHLY": "yearly",
}


@dataclass(frozen=True)
class PivotPointsReport:
    chart_timeframe: str
    pivot_period: PivotPeriod
    levels: Dict[str, float]
    summary: str


def get_pivot_period(chart_timeframe: str) -> PivotPeriod:
    """Return the requested pivot period for a chart timeframe."""
    if not isinstance(chart_timeframe, str):
        raise ValueError("chart_timeframe must be a supported chart timeframe.")

    normalized_timeframe = chart_timeframe.strip().upper()
    if normalized_timeframe not in PIVOT_PERIOD_BY_CHART_TIMEFRAME:
        supported = ", ".join(
            timeframe
            for timeframe in PIVOT_PERIOD_BY_CHART_TIMEFRAME
            if timeframe in TIMEFRAME_LENGTHS or timeframe == "MONTHLY"
        )
        raise ValueError(
            f"Unsupported chart timeframe; use one of: {supported}."
        )
    return PIVOT_PERIOD_BY_CHART_TIMEFRAME[normalized_timeframe]


def calculate_pivot_points(
    chart_timeframe: str,
    previous_high: float,
    previous_low: float,
    previous_close: float,
) -> PivotPointsReport:
    """Calculate Traditional pivots using supplied completed-period values.

    The caller supplies high, low, and close from the previous completed
    period selected by ``get_pivot_period``. This function does not fetch or
    aggregate candle data.
    """
    pivot_period = get_pivot_period(chart_timeframe)
    normalized_timeframe = chart_timeframe.strip().upper()
    high = _positive_price("previous_high", previous_high)
    low = _positive_price("previous_low", previous_low)
    close = _positive_price("previous_close", previous_close)
    if high < low:
        raise ValueError("previous_high must be greater than or equal to previous_low.")
    if not low <= close <= high:
        raise ValueError("previous_close must be within the previous period range.")

    price_range = high - low
    pivot = (high + low + close) / 3.0
    r1 = 2.0 * pivot - low
    s1 = 2.0 * pivot - high
    r2 = pivot + price_range
    s2 = pivot - price_range
    r3 = high + 2.0 * (pivot - low)
    s3 = low - 2.0 * (high - pivot)
    r4 = r3 + price_range
    s4 = s3 - price_range
    r5 = r4 + price_range
    s5 = s4 - price_range
    levels = {
        "P": pivot,
        "R1": r1,
        "S1": s1,
        "R2": r2,
        "S2": s2,
        "R3": r3,
        "S3": s3,
        "R4": r4,
        "S4": s4,
        "R5": r5,
        "S5": s5,
    }
    if not all(math.isfinite(level) for level in levels.values()):
        raise ValueError("The supplied prices produce non-finite pivot levels.")

    return PivotPointsReport(
        chart_timeframe=normalized_timeframe,
        pivot_period=pivot_period,
        levels=levels,
        summary=(
            f"Traditional {pivot_period} pivot levels were calculated from "
            "the supplied previous completed period high, low, and close. "
            "This calculation does not choose a trade or fetch period data."
        ),
    )


def _positive_price(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite positive number.")
    price = float(value)
    if not math.isfinite(price) or price <= 0:
        raise ValueError(f"{name} must be a finite positive number.")
    return price
