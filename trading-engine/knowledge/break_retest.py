"""Report a price-level break and any later touch of that level."""

import math
from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
import pandas as pd


BreakDirection = Literal["bullish", "bearish"]
BreakConfirmation = Literal["close", "wick"]
BreakRetestStatus = Literal[
    "no_data",
    "no_break",
    "waiting_for_retest",
    "retest_observed",
]


@dataclass(frozen=True)
class BreakRetestReport:
    level: float
    direction: BreakDirection
    confirmation: BreakConfirmation
    tolerance: float
    status: BreakRetestStatus
    break_time: Optional[pd.Timestamp]
    break_price: Optional[float]
    retest_time: Optional[pd.Timestamp]
    retest_low: Optional[float]
    retest_high: Optional[float]
    retest_close: Optional[float]
    summary: str


def analyze_break_retest(
    candles: pd.DataFrame,
    level: float,
    direction: BreakDirection,
    confirmation: BreakConfirmation = "close",
    tolerance: float = 0.0,
) -> BreakRetestReport:
    """Find a crossing of a supplied level and a later candle touching it."""
    if not math.isfinite(level) or level <= 0:
        raise ValueError("level must be a positive finite price.")
    if direction not in ("bullish", "bearish"):
        raise ValueError("direction must be 'bullish' or 'bearish'.")
    if confirmation not in ("close", "wick"):
        raise ValueError("confirmation must be 'close' or 'wick'.")
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be a finite non-negative price distance.")
    if not isinstance(candles, pd.DataFrame):
        raise ValueError("candles must be a DataFrame.")

    empty_report = BreakRetestReport(
        level=level,
        direction=direction,
        confirmation=confirmation,
        tolerance=tolerance,
        status="no_data",
        break_time=None,
        break_price=None,
        retest_time=None,
        retest_low=None,
        retest_high=None,
        retest_close=None,
        summary="No break-and-retest reading: no candles were supplied.",
    )
    if candles.empty:
        return empty_report

    required_columns = {"time", "open", "high", "low", "close"}
    missing_columns = required_columns.difference(candles.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Candles are missing columns: {missing}.")

    times = candles["time"]
    if not pd.api.types.is_datetime64_any_dtype(times) or times.dt.tz is None:
        raise ValueError("Candle times must be timezone-aware UTC.")
    if any(timestamp.utcoffset().total_seconds() != 0 for timestamp in times):
        raise ValueError("Candle times must be in UTC.")
    if not times.is_monotonic_increasing or not times.is_unique:
        raise ValueError("Candle times must be unique and chronological.")

    prices = candles[["open", "high", "low", "close"]].apply(
        pd.to_numeric,
        errors="coerce",
    )
    if not np.isfinite(prices.to_numpy(dtype=float)).all():
        raise ValueError("Candle prices must be finite numbers.")
    if (prices <= 0).any().any():
        raise ValueError("Candle prices must be positive.")
    if (
        (prices["high"] < prices["low"])
        | (prices["high"] < prices["open"])
        | (prices["high"] < prices["close"])
        | (prices["low"] > prices["open"])
        | (prices["low"] > prices["close"])
    ).any():
        raise ValueError("Candle OHLC prices are inconsistent.")

    break_index = None
    for index in range(1, len(candles)):
        previous = prices.iloc[index - 1]
        current = prices.iloc[index]
        if direction == "bullish":
            crossed = (
                current["close"] > level and previous["close"] <= level
                if confirmation == "close"
                else current["high"] > level and previous["high"] <= level
            )
            break_price = current["close"] if confirmation == "close" else current["high"]
        else:
            crossed = (
                current["close"] < level and previous["close"] >= level
                if confirmation == "close"
                else current["low"] < level and previous["low"] >= level
            )
            break_price = current["close"] if confirmation == "close" else current["low"]
        if crossed:
            break_index = index
            break

    if break_index is None:
        return BreakRetestReport(
            level=level,
            direction=direction,
            confirmation=confirmation,
            tolerance=tolerance,
            status="no_break",
            break_time=None,
            break_price=None,
            retest_time=None,
            retest_low=None,
            retest_high=None,
            retest_close=None,
            summary=(
                f"No {direction} {confirmation}-confirmed break of "
                f"{level:g} was found in the supplied candles."
            ),
        )

    break_time = times.iloc[break_index]
    break_price = float(
        prices.iloc[break_index]["close"]
        if confirmation == "close"
        else (
            prices.iloc[break_index]["high"]
            if direction == "bullish"
            else prices.iloc[break_index]["low"]
        )
    )

    retest_index = None
    for index in range(break_index + 1, len(candles)):
        candle = prices.iloc[index]
        if candle["low"] <= level + tolerance and candle["high"] >= level - tolerance:
            retest_index = index
            break

    if retest_index is None:
        return BreakRetestReport(
            level=level,
            direction=direction,
            confirmation=confirmation,
            tolerance=tolerance,
            status="waiting_for_retest",
            break_time=break_time,
            break_price=break_price,
            retest_time=None,
            retest_low=None,
            retest_high=None,
            retest_close=None,
            summary=(
                f"A {direction} break of {level:g} was observed at {break_time}; "
                "no later retest touch appears in the supplied candles."
            ),
        )

    retest = prices.iloc[retest_index]
    retest_time = times.iloc[retest_index]
    return BreakRetestReport(
        level=level,
        direction=direction,
        confirmation=confirmation,
        tolerance=tolerance,
        status="retest_observed",
        break_time=break_time,
        break_price=break_price,
        retest_time=retest_time,
        retest_low=float(retest["low"]),
        retest_high=float(retest["high"]),
        retest_close=float(retest["close"]),
        summary=(
            f"A {direction} break of {level:g} was observed at {break_time}; "
            f"a later candle touched the level at {retest_time}. The retest "
            "touch alone does not show that the level held."
        ),
    )
