"""Report the current UTC day's open as the Daily Flip level."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import math
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class DailyFlipReport:
    day: date
    level: Optional[float]
    source_candle_time: Optional[pd.Timestamp]
    summary: str


def analyze_daily_flip(candles: pd.DataFrame, as_of: datetime) -> DailyFlipReport:
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise ValueError("as_of must be timezone-aware UTC.")
    day_start = datetime.combine(as_of.date(), time.min, tzinfo=timezone.utc)
    if not isinstance(candles, pd.DataFrame):
        raise ValueError("candles must be a DataFrame.")
    if candles.empty:
        return _missing_report(as_of.date(), "No candles were supplied.")
    if not {"time", "open"}.issubset(candles.columns):
        raise ValueError("Candles must include 'time' and 'open' columns.")
    times = pd.to_datetime(candles["time"], utc=True, errors="coerce")
    if times.isna().any() or not times.is_monotonic_increasing or times.duplicated().any():
        raise ValueError("Candle times must be valid, unique, and chronological.")
    observed = candles.loc[(times >= pd.Timestamp(day_start)) & (times <= pd.Timestamp(as_of))]
    if observed.empty:
        return _missing_report(as_of.date(), "No current-day candle was available.")
    opening = pd.to_numeric(observed["open"], errors="coerce")
    open_values = opening.to_numpy(dtype=float, na_value=float("nan"))
    if not all(math.isfinite(value) and value > 0 for value in open_values):
        raise ValueError("Candle opens must be positive finite prices.")
    first = observed.iloc[0]
    level = float(first["open"])
    source_time = pd.Timestamp(first["time"])
    return DailyFlipReport(
        day=as_of.date(),
        level=level,
        source_candle_time=source_time,
        summary=f"Daily Flip is the current UTC day's first observed candle open at {level:g}.",
    )


def _missing_report(day: date, message: str) -> DailyFlipReport:
    return DailyFlipReport(day, None, None, f"No Daily Flip level: {message}")
