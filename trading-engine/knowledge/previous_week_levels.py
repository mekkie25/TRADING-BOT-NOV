"""Report observed high and low prices from the previous UTC calendar week."""

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

import pandas as pd

from data.timeframes import TIMEFRAME_LENGTHS


@dataclass(frozen=True)
class PreviousWeekLevelsReport:
    week_start: date
    week_end: date
    timeframe: str
    observed_high: Optional[float]
    observed_low: Optional[float]
    candle_count: int
    first_candle_time: Optional[pd.Timestamp]
    last_candle_time: Optional[pd.Timestamp]
    summary: str


def analyze_previous_week_levels(
    candles: pd.DataFrame,
    timeframe: str,
    as_of: datetime,
) -> PreviousWeekLevelsReport:
    """Report observed levels from fully contained, completed UTC-week candles."""
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise ValueError("as_of must be timezone-aware UTC.")

    normalized_timeframe = timeframe.strip().upper()
    if normalized_timeframe not in TIMEFRAME_LENGTHS:
        raise ValueError(f"Unsupported timeframe: {timeframe}.")

    current_week_start = datetime.combine(
        as_of.date() - timedelta(days=as_of.weekday()),
        time.min,
        tzinfo=timezone.utc,
    )
    previous_week_start = current_week_start - timedelta(days=7)
    previous_week_end = current_week_start
    week_start = previous_week_start.date()
    week_end = (previous_week_end - timedelta(days=1)).date()

    def missing_report(message: str) -> PreviousWeekLevelsReport:
        return PreviousWeekLevelsReport(
            week_start=week_start,
            week_end=week_end,
            timeframe=normalized_timeframe,
            observed_high=None,
            observed_low=None,
            candle_count=0,
            first_candle_time=None,
            last_candle_time=None,
            summary=message,
        )

    if not isinstance(candles, pd.DataFrame):
        raise ValueError("candles must be a DataFrame.")
    if candles.empty:
        return missing_report(
            f"No observed levels for the UTC week starting {week_start}: "
            "no candles were supplied."
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

    prices = candles[["high", "low"]].apply(pd.to_numeric, errors="coerce")
    values = prices.to_numpy(dtype=float, na_value=float("nan"))
    if not all(math.isfinite(value) for value in values.flat):
        raise ValueError("Candle highs and lows must be finite numbers.")
    if (prices <= 0).any().any() or (prices["high"] < prices["low"]).any():
        raise ValueError("Candle highs and lows must be positive and consistent.")

    duration = pd.Timedelta(TIMEFRAME_LENGTHS[normalized_timeframe])
    window_start = pd.Timestamp(previous_week_start)
    window_end = pd.Timestamp(previous_week_end)
    candle_close_times = times + duration
    in_previous_week = (
        (times >= window_start)
        & (candle_close_times <= window_end)
        & (candle_close_times <= pd.Timestamp(as_of))
    ).to_numpy()
    observed = candles.loc[in_previous_week]
    if observed.empty:
        return missing_report(
            f"No observed levels for the UTC week starting {week_start}: "
            "no fully contained, completed candles were supplied."
        )

    observed_prices = prices.loc[in_previous_week]
    observed_high = float(observed_prices["high"].max())
    observed_low = float(observed_prices["low"].min())
    first_time = observed.iloc[0]["time"]
    last_time = observed.iloc[-1]["time"]
    summary = (
        f"Observed high for the UTC week {week_start} through {week_end} is "
        f"{observed_high:g} and observed low is {observed_low:g}, from "
        f"{len(observed)} supplied candles. These levels reflect available "
        "data and may not include extremes from missing candles."
    )
    return PreviousWeekLevelsReport(
        week_start=week_start,
        week_end=week_end,
        timeframe=normalized_timeframe,
        observed_high=observed_high,
        observed_low=observed_low,
        candle_count=len(observed),
        first_candle_time=first_time,
        last_candle_time=last_time,
        summary=summary,
    )
