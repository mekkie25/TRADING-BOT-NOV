"""Report what time interval a supplied candle timeframe represents."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from data.timeframes import TIMEFRAME_LENGTHS


@dataclass(frozen=True)
class TimeframeObservation:
    timeframe: str
    duration: timedelta
    candle_open_time: datetime
    candle_close_time: datetime
    summary: str


def describe_timeframe(
    timeframe: str,
    candle_open_time: datetime,
) -> TimeframeObservation:
    """Describe the UTC time window covered by a candle with explicit metadata."""
    normalized_timeframe = timeframe.strip().upper()
    if normalized_timeframe not in TIMEFRAME_LENGTHS:
        supported = ", ".join(TIMEFRAME_LENGTHS)
        raise ValueError(f"Unsupported timeframe; use one of: {supported}.")
    if (
        candle_open_time.tzinfo is None
        or candle_open_time.utcoffset() != timedelta(0)
    ):
        raise ValueError("candle_open_time must be timezone-aware UTC.")

    duration = TIMEFRAME_LENGTHS[normalized_timeframe]
    candle_close_time = candle_open_time + duration
    summary = (
        f"A {normalized_timeframe} candle covers the interval from "
        f"{candle_open_time.isoformat()} up to "
        f"{candle_close_time.isoformat()} UTC; its closing price is available "
        "only when that interval has ended."
    )
    return TimeframeObservation(
        timeframe=normalized_timeframe,
        duration=duration,
        candle_open_time=candle_open_time,
        candle_close_time=candle_close_time,
        summary=summary,
    )
