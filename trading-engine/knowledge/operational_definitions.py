"""Reusable, configurable candle definitions for strategy evaluation."""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Optional, Sequence

import numpy as np
import pandas as pd

from data.timeframes import TIMEFRAME_LENGTHS


RangeMethod = Literal["range", "true_range"]


@dataclass(frozen=True)
class OperationalDefinitionConfig:
    average_candle_lookback: int = 20
    average_candle_method: RangeMethod = "range"
    time_of_day_days: int = 20
    volume_range_multiple: float = 1.5
    volume_body_fraction: float = 0.6
    volume_drive_candles: int = 1
    chop_candles: int = 5
    chop_range_multiple: float = 0.8
    chop_overlap_fraction: float = 0.5
    break_distance_acs: float = 0.1
    hold_candles: int = 2
    hold_wick_tolerance_acs: float = 0.25
    touch_distance_acs: float = 0.25
    rejection_wick_fraction: float = 0.5
    sweep_minimum_acs: float = 0.1
    sweep_maximum_acs: float = 2.0
    rejection_window_candles: int = 2
    momentum_range_multiple: float = 1.5
    momentum_body_fraction: float = 0.6
    momentum_close_fraction: float = 0.25
    momentum_no_overlap_candles: int = 3
    aligned_levels_acs: float = 0.5


def average_candle_size(
    candles: pd.DataFrame,
    lookback: int = 20,
    method: RangeMethod = "range",
) -> Optional[float]:
    """Return mean high-low range, or true range, over supplied closed candles."""
    _validate_lookback(lookback)
    _validate_ohlc(candles, minimum_rows=1)
    if method not in ("range", "true_range"):
        raise ValueError("method must be 'range' or 'true_range'.")
    sample = candles.tail(lookback)
    high = sample["high"].to_numpy(dtype=float)
    low = sample["low"].to_numpy(dtype=float)
    ranges = high - low
    if method == "true_range":
        close = sample["close"].to_numpy(dtype=float)
        previous_close = candles["close"].shift(1).loc[sample.index].to_numpy(dtype=float)
        ranges = np.maximum.reduce(
            (ranges, np.abs(high - previous_close), np.abs(low - previous_close))
        )
        if len(sample) and sample.index[0] == candles.index[0]:
            ranges[0] = high[0] - low[0]
    return float(np.mean(ranges)) if len(ranges) else None


def average_candle_size_by_time_of_day(
    candles: pd.DataFrame,
    timeframe: str,
    as_of: datetime,
    days: int = 20,
    timezone_name: str = "UTC",
    method: RangeMethod = "range",
) -> Optional[float]:
    """Average prior completed candles matching the as-of candle's local slot."""
    _validate_as_of(as_of)
    _validate_lookback(days)
    duration = _timeframe_duration(timeframe)
    _validate_ohlc(candles, minimum_rows=1)
    times = _validated_times(candles)
    zone = _timezone(timezone_name)
    local_as_of = pd.Timestamp(as_of).tz_convert(zone)
    local_slot = (pd.Timestamp(as_of) - duration).tz_convert(zone)
    slot = (local_slot.hour, local_slot.minute, local_slot.second)
    local_times = times.dt.tz_convert(zone)
    completed = times + duration <= pd.Timestamp(as_of)
    prior_days = local_times.dt.date < local_as_of.date()
    same_slot = (
        (local_times.dt.hour == slot[0])
        & (local_times.dt.minute == slot[1])
        & (local_times.dt.second == slot[2])
    )
    selected = candles.loc[(completed & prior_days & same_slot).to_numpy()]
    if selected.empty:
        return None
    selected = selected.tail(days)
    return average_candle_size(selected, len(selected), method)


def average_body_size(candles: pd.DataFrame, lookback: int = 20) -> Optional[float]:
    _validate_lookback(lookback)
    _validate_ohlc(candles, minimum_rows=1)
    sample = candles.tail(lookback)
    body = (sample["close"] - sample["open"]).abs().to_numpy(dtype=float)
    return float(np.mean(body)) if len(body) else None


def candle_body_close(candle: pd.Series) -> float:
    """A candle close is its close price; wicks do not alter this value."""
    return _positive_finite("close", candle["close"])


def volume_present(
    candle: pd.Series,
    average_size: float,
    range_multiple: float = 1.5,
    minimum_body_fraction: float = 0.6,
) -> bool:
    _validate_positive(average_size, "average_size")
    _validate_fraction(minimum_body_fraction, "minimum_body_fraction", allow_zero=True)
    _validate_positive(range_multiple, "range_multiple")
    candle_range = _positive_or_zero(candle["high"] - candle["low"], "candle range")
    body = abs(_positive_finite("close", candle["close"]) - _positive_finite("open", candle["open"]))
    return (
        candle_range >= range_multiple * average_size
        and candle_range > 0
        and body / candle_range >= minimum_body_fraction
    )


def drive_of_volume(
    candles: pd.DataFrame,
    average_size: float,
    direction: Literal["bullish", "bearish"],
    consecutive_candles: int = 1,
    range_multiple: float = 1.5,
    minimum_body_fraction: float = 0.6,
) -> bool:
    _validate_lookback(consecutive_candles)
    _validate_ohlc(candles, minimum_rows=consecutive_candles)
    for _, candle in candles.tail(consecutive_candles).iterrows():
        bullish = candle["close"] > candle["open"]
        if bullish != (direction == "bullish"):
            return False
        if not volume_present(
            candle,
            average_size,
            range_multiple,
            minimum_body_fraction,
        ):
            return False
    return True


def chop_present(
    candles: pd.DataFrame,
    average_size: float,
    candle_count: int = 5,
    range_multiple: float = 0.8,
    overlap_fraction: float = 0.5,
) -> bool:
    _validate_lookback(candle_count)
    _validate_ohlc(candles, minimum_rows=candle_count)
    _validate_positive(average_size, "average_size")
    _validate_positive(range_multiple, "range_multiple")
    _validate_fraction(overlap_fraction, "overlap_fraction", allow_zero=True)
    sample = candles.tail(candle_count)
    highs = sample["high"].to_numpy(dtype=float)
    lows = sample["low"].to_numpy(dtype=float)
    ranges = highs - lows
    if not np.all(ranges < range_multiple * average_size):
        return False
    overlaps = []
    for index in range(1, len(sample)):
        overlap = max(0.0, min(highs[index - 1], highs[index]) - max(lows[index - 1], lows[index]))
        denominator = min(ranges[index - 1], ranges[index])
        overlaps.append(overlap / denominator if denominator > 0 else 1.0)
    return bool(overlaps) and all(value >= overlap_fraction for value in overlaps)


def level_holds(
    candles: pd.DataFrame,
    level: float,
    direction: Literal["bullish", "bearish"],
    average_size: float,
    hold_candles: int = 2,
    wick_tolerance_acs: float = 0.25,
    break_distance_acs: float = 0.0,
) -> bool:
    _validate_lookback(hold_candles)
    _validate_level(level)
    _validate_positive(average_size, "average_size")
    _validate_nonnegative(wick_tolerance_acs, "wick_tolerance_acs")
    _validate_nonnegative(break_distance_acs, "break_distance_acs")
    _validate_ohlc(candles, minimum_rows=hold_candles)
    sample = candles.tail(hold_candles)
    tolerance = average_size * wick_tolerance_acs
    distance = average_size * break_distance_acs
    if direction == "bullish":
        return bool(
            (sample["close"] > level + distance).all()
            and (sample["low"] >= level - tolerance).all()
            and (sample["low"] <= level + tolerance).any()
        )
    if direction == "bearish":
        return bool(
            (sample["close"] < level - distance).all()
            and (sample["high"] <= level + tolerance).all()
            and (sample["high"] >= level - tolerance).any()
        )
    raise ValueError("direction must be 'bullish' or 'bearish'.")


def wick_rejection(
    candle: pd.Series,
    level: float,
    direction: Literal["bullish", "bearish"],
    minimum_wick_fraction: float = 0.5,
) -> bool:
    _validate_level(level)
    _validate_fraction(minimum_wick_fraction, "minimum_wick_fraction")
    high = _positive_finite("high", candle["high"])
    low = _positive_finite("low", candle["low"])
    open_price = _positive_finite("open", candle["open"])
    close = _positive_finite("close", candle["close"])
    total_range = high - low
    if total_range <= 0:
        return False
    if direction == "bullish":
        wick = min(open_price, close) - low
        return low <= level and close > level and wick / total_range >= minimum_wick_fraction
    if direction == "bearish":
        wick = high - max(open_price, close)
        return high >= level and close < level and wick / total_range >= minimum_wick_fraction
    raise ValueError("direction must be 'bullish' or 'bearish'.")


def close_back_rejection(
    candles: pd.DataFrame,
    level: float,
    direction: Literal["bullish", "bearish"],
    average_size: float,
    minimum_sweep_acs: float = 0.1,
    maximum_sweep_acs: float = 2.0,
    window_candles: int = 2,
) -> bool:
    _validate_lookback(window_candles)
    _validate_ohlc(candles, minimum_rows=1)
    _validate_level(level)
    _validate_positive(average_size, "average_size")
    _validate_nonnegative(minimum_sweep_acs, "minimum_sweep_acs")
    _validate_positive(maximum_sweep_acs, "maximum_sweep_acs")
    if maximum_sweep_acs < minimum_sweep_acs:
        raise ValueError("maximum_sweep_acs must be at least minimum_sweep_acs.")
    for _, candle in candles.tail(window_candles).iterrows():
        if direction == "bullish":
            depth = level - candle["low"]
            if (
                candle["low"] < level
                and minimum_sweep_acs * average_size <= depth <= maximum_sweep_acs * average_size
                and candle["close"] > level
            ):
                return True
        elif direction == "bearish":
            depth = candle["high"] - level
            if (
                candle["high"] > level
                and minimum_sweep_acs * average_size <= depth <= maximum_sweep_acs * average_size
                and candle["close"] < level
            ):
                return True
        else:
            raise ValueError("direction must be 'bullish' or 'bearish'.")
    return False


def momentum_break(
    candles: pd.DataFrame,
    level: float,
    direction: Literal["bullish", "bearish"],
    average_size: float,
    range_multiple: float = 1.5,
    minimum_body_fraction: float = 0.6,
    close_outer_fraction: float = 0.25,
) -> bool:
    _validate_ohlc(candles, minimum_rows=1)
    _validate_level(level)
    _validate_positive(average_size, "average_size")
    _validate_positive(range_multiple, "range_multiple")
    _validate_fraction(minimum_body_fraction, "minimum_body_fraction", allow_zero=True)
    _validate_fraction(close_outer_fraction, "close_outer_fraction")
    candle = candles.iloc[-1]
    high = float(candle["high"])
    low = float(candle["low"])
    candle_range = high - low
    if candle_range <= 0 or candle_range < range_multiple * average_size:
        return False
    body_fraction = abs(float(candle["close"]) - float(candle["open"])) / candle_range
    if body_fraction < minimum_body_fraction:
        return False
    if direction == "bullish":
        return bool(
            candle["close"] > level
            and (high - candle["close"]) / candle_range <= close_outer_fraction
        )
    if direction == "bearish":
        return bool(
            candle["close"] < level
            and (candle["close"] - low) / candle_range <= close_outer_fraction
        )
    raise ValueError("direction must be 'bullish' or 'bearish'.")


def sweep_depth(
    candle: pd.Series,
    level: float,
    direction: Literal["bullish", "bearish"],
    average_size: float,
) -> Optional[float]:
    """Return sweep depth in ACS units, or None when the level was not swept."""
    _validate_level(level)
    _validate_positive(average_size, "average_size")
    if direction == "bullish":
        distance = level - float(candle["low"])
    elif direction == "bearish":
        distance = float(candle["high"]) - level
    else:
        raise ValueError("direction must be 'bullish' or 'bearish'.")
    return distance / average_size if distance > 0 else None


def aligned_levels(
    levels: Sequence[float],
    average_size: float,
    maximum_distance_acs: float = 0.5,
) -> bool:
    _validate_positive(average_size, "average_size")
    _validate_nonnegative(maximum_distance_acs, "maximum_distance_acs")
    prices = [_positive_finite("level", level) for level in levels]
    if len(prices) < 2:
        return False
    return max(prices) - min(prices) <= average_size * maximum_distance_acs


def _validate_ohlc(candles: pd.DataFrame, minimum_rows: int) -> None:
    if not isinstance(candles, pd.DataFrame):
        raise ValueError("candles must be a DataFrame.")
    required = {"open", "high", "low", "close"}
    missing = required.difference(candles.columns)
    if missing:
        raise ValueError(f"Candles are missing columns: {', '.join(sorted(missing))}.")
    if len(candles) < minimum_rows:
        raise ValueError(f"At least {minimum_rows} candles are required.")
    prices = candles[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce")
    values = prices.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("OHLC values must be positive finite numbers.")
    if (
        (prices["high"] < prices["low"])
        | (prices["high"] < prices["open"])
        | (prices["high"] < prices["close"])
        | (prices["low"] > prices["open"])
        | (prices["low"] > prices["close"])
    ).any():
        raise ValueError("Candle highs and lows must contain open and close.")


def _validated_times(candles: pd.DataFrame) -> pd.Series:
    if "time" not in candles.columns:
        raise ValueError("Candles must include a 'time' column.")
    times = pd.to_datetime(candles["time"], utc=True, errors="coerce")
    if times.isna().any() or not times.is_monotonic_increasing or times.duplicated().any():
        raise ValueError("Candle times must be valid, unique, and chronological.")
    return times


def _validate_lookback(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("lookback must be a positive integer.")


def _validate_as_of(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("as_of must be timezone-aware UTC.")


def _timeframe_duration(timeframe: str) -> pd.Timedelta:
    normalized = timeframe.strip().upper()
    if normalized not in TIMEFRAME_LENGTHS:
        raise ValueError(f"Unsupported timeframe: {timeframe}.")
    return pd.Timedelta(TIMEFRAME_LENGTHS[normalized])


def _timezone(name: str):
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as error:
        raise ValueError(f"Unknown timezone: {name}.") from error


def _validate_level(value: float) -> None:
    _positive_finite("level", value)


def _validate_positive(value: float, name: str) -> None:
    number = _positive_finite(name, value)
    if number <= 0:
        raise ValueError(f"{name} must be positive.")


def _validate_nonnegative(value: float, name: str) -> None:
    number = _positive_or_zero(value, name)
    if number < 0:
        raise ValueError(f"{name} must not be negative.")


def _validate_fraction(value: float, name: str, allow_zero: bool = False) -> None:
    number = _positive_or_zero(value, name) if allow_zero else _positive_finite(name, value)
    if not 0 <= number <= 1:
        raise ValueError(f"{name} must be between 0 and 1.")


def _positive_finite(name: str, value: float) -> float:
    if isinstance(value, bool) or not math.isfinite(float(value)) or float(value) <= 0:
        raise ValueError(f"{name} must be a positive finite number.")
    return float(value)


def _positive_or_zero(value: float, name: str) -> float:
    if isinstance(value, bool) or not math.isfinite(float(value)) or float(value) < 0:
        raise ValueError(f"{name} must be a finite non-negative number.")
    return float(value)
