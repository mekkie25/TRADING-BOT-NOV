"""Report account equity declines from a supplied peak."""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Sequence, Tuple


EquityPoint = Tuple[datetime, float]


@dataclass(frozen=True)
class DrawdownReading:
    peak_equity: float
    equity: float
    amount: float
    percent: Optional[float]
    peak_time: Optional[datetime]
    equity_time: datetime


@dataclass(frozen=True)
class DrawdownReport:
    current: Optional[DrawdownReading]
    maximum_amount: Optional[DrawdownReading]
    maximum_percent: Optional[DrawdownReading]
    summary: str


def analyze_drawdown(
    equity_history: Sequence[EquityPoint],
    opening_equity: Optional[float] = None,
) -> DrawdownReport:
    """Report peak-to-current declines; history must be ordered in UTC."""
    if not equity_history:
        return DrawdownReport(
            current=None,
            maximum_amount=None,
            maximum_percent=None,
            summary="No drawdown reading: no equity history was supplied.",
        )

    if opening_equity is not None and (
        not math.isfinite(opening_equity) or opening_equity <= 0
    ):
        raise ValueError("opening_equity must be a positive finite amount.")

    previous_time: Optional[datetime] = None
    for time, equity in equity_history:
        if time.tzinfo is None or time.utcoffset() != timedelta(0):
            raise ValueError("Every equity timestamp must be timezone-aware UTC.")
        if previous_time is not None and time <= previous_time:
            raise ValueError("Equity timestamps must be strictly increasing.")
        if not math.isfinite(equity):
            raise ValueError("Equity values must be finite.")
        previous_time = time

    first_time, first_equity = equity_history[0]
    peak_equity = opening_equity if opening_equity is not None else first_equity
    peak_time = None if opening_equity is not None else first_time
    current: Optional[DrawdownReading] = None
    maximum_amount: Optional[DrawdownReading] = None
    maximum_percent: Optional[DrawdownReading] = None

    for time, equity in equity_history:
        if equity >= peak_equity:
            peak_equity = equity
            peak_time = time

        amount = max(peak_equity - equity, 0.0)
        percent = amount / peak_equity * 100 if peak_equity > 0 else None
        reading = DrawdownReading(
            peak_equity=peak_equity,
            equity=equity,
            amount=amount,
            percent=percent,
            peak_time=peak_time,
            equity_time=time,
        )
        current = reading

        if maximum_amount is None or reading.amount > maximum_amount.amount:
            maximum_amount = reading
        if (
            reading.percent is not None
            and (
                maximum_percent is None
                or reading.percent > maximum_percent.percent
            )
        ):
            maximum_percent = reading

    assert current is not None
    if current.amount == 0:
        summary = (
            f"Equity is at its supplied peak of {current.peak_equity:g}; "
            "current drawdown is 0."
        )
    elif current.percent is None:
        summary = (
            f"Equity is {current.amount:g} below its supplied peak, "
            "but a percentage cannot be calculated from a non-positive peak."
        )
    else:
        summary = (
            f"Equity is {current.amount:g} ({current.percent:.2f}%) below "
            f"its peak of {current.peak_equity:g}."
        )

    return DrawdownReport(
        current=current,
        maximum_amount=maximum_amount,
        maximum_percent=maximum_percent,
        summary=summary,
    )
