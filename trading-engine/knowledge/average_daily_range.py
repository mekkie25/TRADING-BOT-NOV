"""Report the average high-to-low range of completed daily candles."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd

from data.timeframes import TIMEFRAME_LENGTHS
from knowledge.average_candle_range import analyze_average_candle_range


@dataclass(frozen=True)
class AverageDailyRangeReport:
    timeframe: str
    requested_candles: int
    sample_count: int
    average_range: Optional[float]
    first_candle_time: Optional[pd.Timestamp]
    last_candle_time: Optional[pd.Timestamp]
    summary: str


def analyze_average_daily_range(
    candles: pd.DataFrame,
    timeframe: str,
    lookback_candles: int,
    as_of: datetime,
) -> AverageDailyRangeReport:
    """Average the latest supplied, completed D1 candle ranges as of a UTC time."""
    if not isinstance(timeframe, str):
        raise ValueError("timeframe must be D1.")
    normalized_timeframe = timeframe.strip().upper()
    if normalized_timeframe not in TIMEFRAME_LENGTHS:
        raise ValueError(f"Unsupported timeframe: {timeframe}.")
    if normalized_timeframe != "D1":
        raise ValueError("Average daily range requires the D1 timeframe.")

    candle_range = analyze_average_candle_range(
        candles,
        normalized_timeframe,
        lookback_candles,
        as_of,
    )
    sample_count = candle_range.sample_count
    average_range = candle_range.average_range
    if average_range is None:
        if candles.empty:
            summary = "No average daily range: no candles were supplied."
        else:
            summary = (
                "No average daily range: no completed D1 candles are "
                f"available as of {as_of.isoformat()}."
            )
    elif sample_count < lookback_candles:
        summary = (
            f"Average daily range is {average_range:g} price units across "
            f"{sample_count} supplied completed D1 candles; only "
            f"{sample_count} of {lookback_candles} requested candles were available."
        )
    else:
        summary = (
            f"Average daily range is {average_range:g} price units across "
            f"{sample_count} supplied completed D1 candles."
        )

    return AverageDailyRangeReport(
        timeframe=normalized_timeframe,
        requested_candles=candle_range.requested_candles,
        sample_count=sample_count,
        average_range=average_range,
        first_candle_time=candle_range.first_candle_time,
        last_candle_time=candle_range.last_candle_time,
        summary=summary,
    )
