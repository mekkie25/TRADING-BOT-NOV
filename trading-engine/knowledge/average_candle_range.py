"""Report the average high-to-low range for an explicit candle timeframe."""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from data.timeframes import TIMEFRAME_LENGTHS


@dataclass(frozen=True)
class AverageCandleRangeReport:
    timeframe: str
    requested_candles: int
    sample_count: int
    average_range: Optional[float]
    first_candle_time: Optional[pd.Timestamp]
    last_candle_time: Optional[pd.Timestamp]
    summary: str


def analyze_average_candle_range(
    candles: pd.DataFrame,
    timeframe: str,
    lookback_candles: int,
    as_of: datetime,
) -> AverageCandleRangeReport:
    """Average supplied candle ranges whose timeframe windows have completed."""
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise ValueError("as_of must be timezone-aware UTC.")
    if (
        isinstance(lookback_candles, bool)
        or not isinstance(lookback_candles, int)
        or lookback_candles <= 0
    ):
        raise ValueError("lookback_candles must be a positive whole number.")
    if not isinstance(timeframe, str):
        raise ValueError("timeframe must be a supported candle timeframe.")

    normalized_timeframe = timeframe.strip().upper()
    if normalized_timeframe not in TIMEFRAME_LENGTHS:
        raise ValueError(f"Unsupported timeframe: {timeframe}.")

    def missing_report(message: str) -> AverageCandleRangeReport:
        return AverageCandleRangeReport(
            timeframe=normalized_timeframe,
            requested_candles=lookback_candles,
            sample_count=0,
            average_range=None,
            first_candle_time=None,
            last_candle_time=None,
            summary=message,
        )

    if not isinstance(candles, pd.DataFrame):
        raise ValueError("candles must be a DataFrame.")
    if candles.empty:
        return missing_report(
            f"No average {normalized_timeframe} candle range: no candles were supplied."
        )

    required_columns = {"time", "high", "low"}
    missing_columns = required_columns.difference(candles.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Candles are missing columns: {missing}.")

    times = candles["time"]
    if (
        not pd.api.types.is_datetime64_any_dtype(times)
        or times.dt.tz is None
        or times.isna().any()
    ):
        raise ValueError("Candle times must be valid, timezone-aware UTC values.")
    if any(timestamp.utcoffset() != timedelta(0) for timestamp in times):
        raise ValueError("Candle times must be in UTC.")
    if not times.is_monotonic_increasing or not times.is_unique:
        raise ValueError("Candle times must be unique and chronological.")

    duration = pd.Timedelta(TIMEFRAME_LENGTHS[normalized_timeframe])
    completed_mask = (times + duration) <= pd.Timestamp(as_of)
    completed = candles.loc[completed_mask.to_numpy()]
    if completed.empty:
        return missing_report(
            f"No average {normalized_timeframe} candle range: no completed "
            f"candles are available as of {as_of.isoformat()}."
        )

    sample = completed.tail(lookback_candles)
    prices = sample[["high", "low"]].apply(pd.to_numeric, errors="coerce")
    values = prices.to_numpy(dtype=float, na_value=float("nan"))
    if not all(math.isfinite(value) for value in values.flat):
        raise ValueError("Candle highs and lows must be finite numbers.")
    if (prices <= 0).any().any() or (prices["high"] < prices["low"]).any():
        raise ValueError("Candle highs and lows must be positive and consistent.")

    ranges = prices["high"] - prices["low"]
    sample_count = len(sample)
    average_range = math.fsum(ranges.tolist()) / sample_count
    first_time = sample.iloc[0]["time"]
    last_time = sample.iloc[-1]["time"]

    if sample_count < lookback_candles:
        summary = (
            f"Average {normalized_timeframe} candle range is "
            f"{average_range:g} price units across {sample_count} supplied "
            f"completed candles; only {sample_count} of {lookback_candles} "
            "requested candles were available."
        )
    else:
        summary = (
            f"Average {normalized_timeframe} candle range is "
            f"{average_range:g} price units across {sample_count} supplied "
            "completed candles."
        )

    return AverageCandleRangeReport(
        timeframe=normalized_timeframe,
        requested_candles=lookback_candles,
        sample_count=sample_count,
        average_range=average_range,
        first_candle_time=first_time,
        last_candle_time=last_time,
        summary=summary,
    )
