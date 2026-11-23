"""Builds higher timeframe candles from stored 1-minute candles.

Candle times are always the OPEN time of the candle, in UTC.

Bucket rules:
  * M5, M15, M30, H1: aligned to the UTC clock.
  * H4, D1, W1, MN1: aligned to the trading-day rollover at 17:00 New York time
    (daylight saving aware). This is the usual daily candle of forex, gold and
    index brokers. A 17:00 start means:
      - D1 runs 17:00 to 17:00 New York time,
      - H4 candles start at 17:00, 21:00, 01:00, 05:00, 09:00 and 13:00 New York time,
      - W1 starts on Sunday 17:00 New York time,
      - MN1 starts at the rollover that begins the month's first trading day.
    Your broker's own daily candle may differ a little, so compare before trusting
    daily levels.

Only the final candle can be unfinished. By default it is dropped unless the
data already covers its full period (complete_only=True).

Volume is the sum of the 1-minute tick volumes.
"""

from typing import Dict, Iterable, Optional

import numpy as np
import pandas as pd

NEW_YORK = "America/New_York"
# 17:00 New York + 7 hours = midnight, so the "trading day" becomes a plain calendar day.
ROLLOVER_SHIFT = pd.Timedelta(hours=7)

COLUMNS = ["time", "open", "high", "low", "close", "volume"]
FIXED_FREQUENCIES = {"M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h"}
ROLLOVER_TIMEFRAMES = ("H4", "D1", "W1", "MN1")
TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1")


def _prepare(m1: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in COLUMNS if column not in m1.columns]
    if missing:
        raise ValueError(f"1-minute candles are missing columns: {missing}.")
    frame = m1[COLUMNS].copy()
    frame["time"] = pd.to_datetime(frame["time"], utc=True)
    return frame.sort_values("time").reset_index(drop=True)


def _ny_wall_clock(times: pd.Series) -> pd.Series:
    """New York wall-clock time without a time zone, moved so the trading day starts at midnight."""
    return times.dt.tz_convert(NEW_YORK).dt.tz_localize(None) + ROLLOVER_SHIFT


def _wall_to_utc(wall: pd.Series) -> pd.Series:
    """Turn shifted New York wall-clock bucket starts back into UTC times."""
    unshifted = wall - ROLLOVER_SHIFT
    # In the one repeated hour of the autumn clock change the first occurrence is used.
    ambiguous = np.ones(len(unshifted), dtype=bool)
    return unshifted.dt.tz_localize(
        NEW_YORK, ambiguous=ambiguous, nonexistent="shift_forward"
    ).dt.tz_convert("UTC")


def _bucket_starts(times: pd.Series, timeframe: str) -> pd.Series:
    if timeframe in FIXED_FREQUENCIES:
        return times.dt.floor(FIXED_FREQUENCIES[timeframe])
    shifted = _ny_wall_clock(times)
    if timeframe == "H4":
        wall = shifted.dt.floor("4h")
    elif timeframe == "D1":
        wall = shifted.dt.normalize()
    elif timeframe == "W1":
        wall = shifted.dt.normalize() - pd.to_timedelta(shifted.dt.dayofweek, unit="D")
    else:  # MN1
        wall = shifted.dt.normalize() - pd.to_timedelta(shifted.dt.day - 1, unit="D")
    return _wall_to_utc(wall)


def _bucket_end(start_utc: pd.Timestamp, timeframe: str) -> pd.Timestamp:
    """When the candle that opens at start_utc is over."""
    if timeframe in FIXED_FREQUENCIES:
        return start_utc + pd.Timedelta(FIXED_FREQUENCIES[timeframe])
    shifted = start_utc.tz_convert(NEW_YORK).tz_localize(None) + ROLLOVER_SHIFT
    if timeframe == "H4":
        end = shifted + pd.Timedelta(hours=4)
    elif timeframe == "D1":
        end = shifted + pd.Timedelta(days=1)
    elif timeframe == "W1":
        end = shifted + pd.Timedelta(days=7)
    else:  # MN1
        end = shifted + pd.offsets.MonthBegin(1)
    end = end - ROLLOVER_SHIFT
    return end.tz_localize(NEW_YORK, ambiguous=True, nonexistent="shift_forward").tz_convert("UTC")


def build(
    m1: pd.DataFrame,
    timeframe: str,
    as_of: Optional[pd.Timestamp] = None,
    complete_only: bool = True,
) -> pd.DataFrame:
    """Candles for one timeframe, built from 1-minute candles.

    as_of is the moment the data is known up to. It defaults to one minute after
    the last 1-minute candle. Pass the current time when working with live data.
    """
    timeframe = timeframe.upper()
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"Unknown timeframe {timeframe}. Use one of {TIMEFRAMES}.")
    frame = _prepare(m1)
    if timeframe == "M1" or frame.empty:
        return frame

    frame["bucket"] = _bucket_starts(frame["time"], timeframe)
    frame = frame.dropna(subset=["bucket"])
    built = (
        frame.groupby("bucket", sort=True)
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        .reset_index()
        .rename(columns={"bucket": "time"})
    )

    if complete_only and not built.empty:
        if as_of is None:
            reference = frame["time"].iloc[-1] + pd.Timedelta(minutes=1)
        else:
            reference = pd.Timestamp(as_of)
            reference = reference.tz_localize("UTC") if reference.tzinfo is None else reference.tz_convert("UTC")
        if _bucket_end(built["time"].iloc[-1], timeframe) > reference:
            built = built.iloc[:-1]
    return built[COLUMNS].reset_index(drop=True)


def build_all(
    m1: pd.DataFrame,
    timeframes: Iterable[str] = TIMEFRAMES[1:],
    as_of: Optional[pd.Timestamp] = None,
    complete_only: bool = True,
) -> Dict[str, pd.DataFrame]:
    """Several timeframes at once, as a dictionary keyed by timeframe name."""
    return {tf.upper(): build(m1, tf, as_of=as_of, complete_only=complete_only) for tf in timeframes}