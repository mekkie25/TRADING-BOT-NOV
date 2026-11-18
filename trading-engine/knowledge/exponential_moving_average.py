"""Report the 20, 50, 100, and 200-period EMAs from completed candles."""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

import pandas as pd

from data.timeframes import TIMEFRAME_LENGTHS


EMA_PERIODS = (20, 50, 100, 200)


@dataclass(frozen=True)
class ExponentialMovingAverageReport:
    timeframe: str
    as_of: datetime
    candle_count: int
    first_candle_time: Optional[pd.Timestamp]
    latest_candle_time: Optional[pd.Timestamp]
    values: Dict[int, float]
    summary: str


def analyze_exponential_moving_averages(
    candles: pd.DataFrame,
    timeframe: str,
    as_of: datetime,
) -> ExponentialMovingAverageReport:
    """Calculate the latest EMA values using only completed close prices.

    Each EMA is seeded with the first supplied completed close, matching the
    recursive EMA convention. Values can differ from TradingView when its chart
    has more historical candles than the supplied data.
    """
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise ValueError("as_of must be timezone-aware UTC.")
    if not isinstance(timeframe, str):
        raise ValueError("timeframe must be a supported candle timeframe.")

    normalized_timeframe = timeframe.strip().upper()
    if normalized_timeframe not in TIMEFRAME_LENGTHS:
        raise ValueError(f"Unsupported timeframe: {timeframe}.")
    if not isinstance(candles, pd.DataFrame):
        raise ValueError("candles must be a DataFrame.")

    if candles.empty:
        return _missing_report(
            normalized_timeframe,
            as_of,
            f"No completed {normalized_timeframe} candles were supplied.",
        )

    required_columns = {"time", "close"}
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
    completed = candles.loc[
        (times + duration <= pd.Timestamp(as_of)).to_numpy()
    ]
    if completed.empty:
        return _missing_report(
            normalized_timeframe,
            as_of,
            f"No completed {normalized_timeframe} candles were available "
            f"as of {as_of.isoformat()}.",
        )

    close_prices = pd.to_numeric(completed["close"], errors="coerce")
    price_values = close_prices.to_numpy(dtype=float, na_value=float("nan"))
    if not all(math.isfinite(value) for value in price_values):
        raise ValueError("Candle closes must be finite numbers.")
    if (close_prices <= 0).any():
        raise ValueError("Candle closes must be positive.")

    values = {
        period: _calculate_ema(price_values, period)
        for period in EMA_PERIODS
    }
    first_candle_time = completed.iloc[0]["time"]
    latest_candle_time = completed.iloc[-1]["time"]
    candle_count = len(completed)
    summary = (
        f"Reported EMA 20, 50, 100, and 200 for {normalized_timeframe} "
        f"close prices across {candle_count} supplied completed candles, "
        f"through {latest_candle_time}. Results depend on the supplied history "
        "and are indicator values, not trade signals."
    )

    return ExponentialMovingAverageReport(
        timeframe=normalized_timeframe,
        as_of=as_of,
        candle_count=candle_count,
        first_candle_time=first_candle_time,
        latest_candle_time=latest_candle_time,
        values=values,
        summary=summary,
    )


def _calculate_ema(prices, period: int) -> float:
    alpha = 2.0 / (period + 1)
    ema = float(prices[0])
    for price in prices[1:]:
        ema = alpha * float(price) + (1.0 - alpha) * ema
    return ema


def _missing_report(
    timeframe: str,
    as_of: datetime,
    summary: str,
) -> ExponentialMovingAverageReport:
    return ExponentialMovingAverageReport(
        timeframe=timeframe,
        as_of=as_of,
        candle_count=0,
        first_candle_time=None,
        latest_candle_time=None,
        values={},
        summary=summary,
    )
