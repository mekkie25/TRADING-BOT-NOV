"""Report timestamp, OHLC, and unusually large candle issues."""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from data.timeframes import TIMEFRAME_LENGTHS
PRICE_COLUMNS = ("open", "high", "low", "close")
REQUIRED_COLUMNS = ("time", "open", "high", "low", "close")


@dataclass
class DataQualityReport:
    timeframe: str
    candle_count: int
    first_time: Optional[datetime]
    last_time: Optional[datetime]
    missing_columns: List[str]
    invalid_timestamp_count: int
    duplicate_timestamp_count: int
    out_of_order_timestamp_count: int
    invalid_price_row_count: int
    non_positive_price_row_count: int
    invalid_ohlc_row_count: int
    zero_range_candle_count: int
    gap_count: int
    weekend_shaped_gap_count: int
    gap_examples: List[Dict[str, Any]]
    omitted_gap_count: int
    largest_candle_ranges: List[Dict[str, Any]]
    largest_close_changes: List[Dict[str, Any]]

    @property
    def has_errors(self) -> bool:
        return bool(
            self.missing_columns
            or self.invalid_timestamp_count
            or self.duplicate_timestamp_count
            or self.out_of_order_timestamp_count
            or self.invalid_price_row_count
            or self.non_positive_price_row_count
            or self.invalid_ohlc_row_count
        )

    @property
    def status(self) -> str:
        if self.has_errors:
            return "ERROR"
        if self.gap_count or self.zero_range_candle_count:
            return "REVIEW"
        return "PASS"

    @property
    def summary(self) -> str:
        expected = TIMEFRAME_LENGTHS[self.timeframe]
        expected_hours = expected.total_seconds() / 3600
        summary = (
            f"{self.candle_count} {self.timeframe} candles; "
            f"missing columns: {', '.join(self.missing_columns) or 'none'}; "
            f"{self.invalid_timestamp_count} invalid timestamps, "
            f"{self.duplicate_timestamp_count} duplicate timestamps, "
            f"{self.out_of_order_timestamp_count} out-of-order timestamps, "
            f"{self.invalid_price_row_count} invalid-price rows, "
            f"{self.non_positive_price_row_count} non-positive-price rows, "
            f"{self.invalid_ohlc_row_count} malformed OHLC rows, "
            f"{self.zero_range_candle_count} zero-range candles; "
            f"{self.gap_count} intervals longer than {expected_hours:g} hour(s) "
            f"({self.weekend_shaped_gap_count} weekend-shaped)."
        )
        if self.largest_candle_ranges:
            largest_range = self.largest_candle_ranges[0]
            summary += (
                " Largest observed candle range was "
                f"{largest_range['rangePercent']:.3f}% of the previous close at "
                f"{largest_range['time']} (candidate for manual review; no automatic "
                "price-movement threshold is applied)."
            )
        return summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "timeframe": self.timeframe,
            "candleCount": self.candle_count,
            "firstTime": self.first_time.isoformat() if self.first_time else None,
            "lastTime": self.last_time.isoformat() if self.last_time else None,
            "missingColumns": list(self.missing_columns),
            "invalidTimestampCount": self.invalid_timestamp_count,
            "duplicateTimestampCount": self.duplicate_timestamp_count,
            "outOfOrderTimestampCount": self.out_of_order_timestamp_count,
            "invalidPriceRowCount": self.invalid_price_row_count,
            "nonPositivePriceRowCount": self.non_positive_price_row_count,
            "invalidOhlcRowCount": self.invalid_ohlc_row_count,
            "zeroRangeCandleCount": self.zero_range_candle_count,
            "gapCount": self.gap_count,
            "weekendShapedGapCount": self.weekend_shaped_gap_count,
            "gapExamples": list(self.gap_examples),
            "omittedGapCount": self.omitted_gap_count,
            "largestCandleRanges": list(self.largest_candle_ranges),
            "largestCloseChanges": list(self.largest_close_changes),
            "summary": self.summary,
        }


def inspect_candle_data(
    df: pd.DataFrame,
    timeframe: str,
    max_examples: int = 10,
) -> DataQualityReport:
    """Return data issues and review candidates without changing the candles."""
    normalized_timeframe = timeframe.upper()
    if normalized_timeframe not in TIMEFRAME_LENGTHS:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    if not isinstance(max_examples, int) or max_examples < 0:
        raise ValueError("max_examples must be a non-negative integer")
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Candle data must be a pandas DataFrame")

    source = df.copy()
    if "time" not in source.columns and "timestamp" in source.columns:
        source = source.rename(columns={"timestamp": "time"})
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in source.columns
    ]

    if "time" in source.columns:
        times = pd.to_datetime(
            source["time"],
            format="mixed",
            utc=True,
            errors="coerce",
        )
    else:
        times = pd.Series(pd.NaT, index=source.index, dtype="datetime64[ns, UTC]")
    valid_times = times.dropna()
    invalid_timestamp_count = int(times.isna().sum())
    duplicate_timestamp_count = int(valid_times.duplicated().sum())
    out_of_order_timestamp_count = int(
        (times.diff().dropna() < pd.Timedelta(0)).sum()
    )

    sorted_times = valid_times.sort_values().reset_index(drop=True)
    expected_interval = pd.Timedelta(TIMEFRAME_LENGTHS[normalized_timeframe])
    gaps: List[Dict[str, Any]] = []
    weekend_shaped_gap_count = 0
    for index in range(1, len(sorted_times)):
        previous_time = sorted_times.iloc[index - 1]
        next_time = sorted_times.iloc[index]
        duration = next_time - previous_time
        if duration <= expected_interval:
            continue

        weekend_shaped = previous_time.weekday() == 4 and next_time.weekday() == 6
        if weekend_shaped:
            weekend_shaped_gap_count += 1
        gaps.append(
            {
                "previousTime": previous_time.isoformat(),
                "nextTime": next_time.isoformat(),
                "gapHours": duration.total_seconds() / 3600,
                "category": "weekend-shaped" if weekend_shaped else "other",
            }
        )

    numeric_prices = pd.DataFrame(index=source.index)
    for column in PRICE_COLUMNS:
        if column in source.columns:
            numeric_prices[column] = pd.to_numeric(source[column], errors="coerce")
        else:
            numeric_prices[column] = np.nan

    price_values = numeric_prices.to_numpy(dtype=float)
    finite_rows = np.isfinite(price_values).all(axis=1)
    invalid_price_row_count = int((~finite_rows).sum())
    finite_price_values = np.isfinite(price_values)
    non_positive_rows = ((price_values <= 0) & finite_price_values).any(axis=1)
    non_positive_price_row_count = int(non_positive_rows.sum())

    valid_price_rows = numeric_prices.loc[finite_rows]
    invalid_ohlc = (
        (valid_price_rows["high"] < valid_price_rows["low"])
        | (valid_price_rows["high"] < valid_price_rows["open"])
        | (valid_price_rows["high"] < valid_price_rows["close"])
        | (valid_price_rows["low"] > valid_price_rows["open"])
        | (valid_price_rows["low"] > valid_price_rows["close"])
    )
    invalid_ohlc_row_count = int(invalid_ohlc.sum())
    zero_range_candle_count = int(
        (
            finite_rows
            & (numeric_prices["high"].to_numpy() == numeric_prices["low"].to_numpy())
        ).sum()
    )

    largest_candle_ranges: List[Dict[str, Any]] = []
    largest_close_changes: List[Dict[str, Any]] = []
    if not source.empty and not missing_columns:
        valid_candles = source.copy()
        valid_candles["time"] = times
        for column in PRICE_COLUMNS:
            valid_candles[column] = numeric_prices[column]
        valid_candles = valid_candles.loc[
            times.notna().to_numpy() & finite_rows
        ].sort_values("time").reset_index(drop=True)
        valid_candles = valid_candles.loc[
            (valid_candles[list(PRICE_COLUMNS)] > 0).all(axis=1)
            & (
                (valid_candles["high"] >= valid_candles["low"])
                & (valid_candles["high"] >= valid_candles["open"])
                & (valid_candles["high"] >= valid_candles["close"])
                & (valid_candles["low"] <= valid_candles["open"])
                & (valid_candles["low"] <= valid_candles["close"])
            )
        ].reset_index(drop=True)

        previous_close = valid_candles["close"].shift(1)
        range_percent = (
            (valid_candles["high"] - valid_candles["low"]) / previous_close.abs() * 100
        )
        close_change_percent = (
            (valid_candles["close"] / previous_close - 1).abs() * 100
        )

        range_indices = range_percent.nlargest(max_examples).index
        for index in range_indices:
            if index == 0 or not math.isfinite(float(range_percent.iloc[index])):
                continue
            largest_candle_ranges.append(
                {
                    "time": valid_candles.iloc[index]["time"].isoformat(),
                    "rangePercent": float(range_percent.iloc[index]),
                    "previousClose": float(previous_close.iloc[index]),
                    "high": float(valid_candles.iloc[index]["high"]),
                    "low": float(valid_candles.iloc[index]["low"]),
                }
            )

        change_indices = close_change_percent.nlargest(max_examples).index
        for index in change_indices:
            if index == 0 or not math.isfinite(float(close_change_percent.iloc[index])):
                continue
            largest_close_changes.append(
                {
                    "previousTime": valid_candles.iloc[index - 1]["time"].isoformat(),
                    "time": valid_candles.iloc[index]["time"].isoformat(),
                    "changePercent": float(close_change_percent.iloc[index]),
                    "previousClose": float(previous_close.iloc[index]),
                    "close": float(valid_candles.iloc[index]["close"]),
                }
            )

    sorted_times_values = sorted_times.tolist()
    return DataQualityReport(
        timeframe=normalized_timeframe,
        candle_count=len(source),
        first_time=sorted_times_values[0].to_pydatetime() if sorted_times_values else None,
        last_time=sorted_times_values[-1].to_pydatetime() if sorted_times_values else None,
        missing_columns=missing_columns,
        invalid_timestamp_count=invalid_timestamp_count,
        duplicate_timestamp_count=duplicate_timestamp_count,
        out_of_order_timestamp_count=out_of_order_timestamp_count,
        invalid_price_row_count=invalid_price_row_count,
        non_positive_price_row_count=non_positive_price_row_count,
        invalid_ohlc_row_count=invalid_ohlc_row_count,
        zero_range_candle_count=zero_range_candle_count,
        gap_count=len(gaps),
        weekend_shaped_gap_count=weekend_shaped_gap_count,
        gap_examples=gaps[:max_examples],
        omitted_gap_count=max(0, len(gaps) - max_examples),
        largest_candle_ranges=largest_candle_ranges,
        largest_close_changes=largest_close_changes,
    )
