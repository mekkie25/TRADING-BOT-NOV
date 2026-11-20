"""Report completed Asia-session high and low levels from closed candles."""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Literal, Optional
from zoneinfo import ZoneInfo

import pandas as pd
import numpy as np

from data.timeframes import TIMEFRAME_LENGTHS


AsiaLevelMode = Literal["wick", "body"]
SAST = ZoneInfo("Africa/Johannesburg")


@dataclass(frozen=True)
class AsiaLevelsReport:
    observed_at_utc: datetime
    session_date: str
    high: Optional[float]
    low: Optional[float]
    candle_count: int
    level_mode: AsiaLevelMode
    session_complete: bool
    summary: str


def analyze_asia_levels(
    candles: pd.DataFrame,
    timeframe: str,
    as_of: datetime,
    start: time = time(1, 0),
    end: time = time(6, 0),
    level_mode: AsiaLevelMode = "wick",
) -> AsiaLevelsReport:
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise ValueError("as_of must be timezone-aware UTC.")
    normalized = timeframe.strip().upper()
    if normalized not in TIMEFRAME_LENGTHS:
        raise ValueError(f"Unsupported timeframe: {timeframe}.")
    if level_mode not in ("wick", "body"):
        raise ValueError("level_mode must be 'wick' or 'body'.")
    if end <= start:
        raise ValueError("Asia session end must be later than its start.")
    if not isinstance(candles, pd.DataFrame):
        raise ValueError("candles must be a DataFrame.")
    required = {"time", "open", "high", "low", "close"}
    missing = required.difference(candles.columns)
    if missing:
        raise ValueError(f"Candles are missing columns: {', '.join(sorted(missing))}.")
    if candles.empty:
        return _empty_report(as_of, level_mode, "No Asia-session candles were supplied.")
    times = pd.to_datetime(candles["time"], utc=True, errors="coerce")
    if times.isna().any() or not times.is_monotonic_increasing or times.duplicated().any():
        raise ValueError("Candle times must be valid, unique, and chronological.")
    prices = candles[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce")
    price_values = prices.to_numpy(dtype=float)
    if not np.isfinite(price_values).all() or (price_values <= 0).any():
        raise ValueError("Candle prices must be positive finite numbers.")

    local_as_of = as_of.astimezone(SAST)
    local_start = datetime.combine(local_as_of.date(), start, tzinfo=SAST)
    local_end = datetime.combine(local_as_of.date(), end, tzinfo=SAST)
    start_utc = pd.Timestamp(local_start.astimezone(ZoneInfo("UTC")))
    end_utc = pd.Timestamp(local_end.astimezone(ZoneInfo("UTC")))
    duration = pd.Timedelta(TIMEFRAME_LENGTHS[normalized])
    completed = (times + duration <= pd.Timestamp(as_of)).to_numpy()
    contained = ((times >= start_utc) & (times + duration <= end_utc)).to_numpy()
    selected = candles.loc[completed & contained]
    session_complete = pd.Timestamp(as_of) >= end_utc
    if selected.empty:
        state = "completed" if session_complete else "in progress"
        return _empty_report(
            as_of,
            level_mode,
            f"No completed Asia-session candles are available; the session is {state}.",
            local_as_of.date().isoformat(),
            session_complete,
        )
    selected_prices = selected[["open", "high", "low", "close"]].apply(
        pd.to_numeric,
        errors="raise",
    )
    if level_mode == "wick":
        high = float(selected_prices["high"].max())
        low = float(selected_prices["low"].min())
    else:
        high = float(selected_prices[["open", "close"]].max(axis=1).max())
        low = float(selected_prices[["open", "close"]].min(axis=1).min())
    return AsiaLevelsReport(
        observed_at_utc=as_of,
        session_date=local_as_of.date().isoformat(),
        high=high,
        low=low,
        candle_count=len(selected),
        level_mode=level_mode,
        session_complete=session_complete,
        summary=(
            f"Observed {level_mode}-based Asia high {high:g} and low {low:g} "
            f"from {len(selected)} completed candles; session "
            f"{'is complete' if session_complete else 'is not complete'}."
        ),
    )


def _empty_report(
    as_of: datetime,
    mode: AsiaLevelMode,
    message: str,
    session_date: str = "",
    session_complete: bool = False,
) -> AsiaLevelsReport:
    return AsiaLevelsReport(
        observed_at_utc=as_of,
        session_date=session_date,
        high=None,
        low=None,
        candle_count=0,
        level_mode=mode,
        session_complete=session_complete,
        summary=message,
    )
