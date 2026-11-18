"""Compare reported market-structure directions across explicit timeframes."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Literal, Optional

import pandas as pd

from data.timeframes import TIMEFRAME_LENGTHS
from .market_structure import (
    MarketStructureConfig,
    SwingPoint,
    TrendState,
    analyze as analyze_market_structure,
)


AlignmentState = Literal["bullish", "bearish", "mixed", "not_assessed"]


@dataclass(frozen=True)
class TimeframeStructure:
    timeframe: str
    latest_candle_time: pd.Timestamp
    trend: TrendState
    last_swing_high: Optional[SwingPoint]
    last_swing_low: Optional[SwingPoint]
    summary: str


@dataclass(frozen=True)
class MultiTimeframeReport:
    as_of: datetime
    structures: List[TimeframeStructure]
    unavailable: Dict[str, str]
    alignment: AlignmentState
    summary: str


def analyze_multi_timeframe_alignment(
    candles_by_timeframe: Dict[str, pd.DataFrame],
    as_of: datetime,
    config: Optional[MarketStructureConfig] = None,
) -> MultiTimeframeReport:
    """Compare bullish, bearish, or ranging structure using only closed candles."""
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise ValueError("as_of must be timezone-aware UTC.")

    active_config = config or MarketStructureConfig()
    structures: List[TimeframeStructure] = []
    unavailable: Dict[str, str] = {}
    seen_timeframes = set()

    for supplied_timeframe, candles in candles_by_timeframe.items():
        timeframe = supplied_timeframe.strip().upper()
        if not timeframe:
            raise ValueError("Timeframe names must not be empty.")
        if timeframe in seen_timeframes:
            raise ValueError(f"Timeframe {timeframe} was supplied more than once.")
        seen_timeframes.add(timeframe)
        if timeframe not in TIMEFRAME_LENGTHS:
            raise ValueError(f"Unsupported timeframe: {supplied_timeframe}.")
        if not isinstance(candles, pd.DataFrame):
            raise ValueError(f"{timeframe} candles must be a DataFrame.")
        if candles.empty:
            unavailable[timeframe] = "No candles were supplied."
            continue

        required_columns = {"time", "high", "low", "close"}
        missing_columns = required_columns.difference(candles.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"{timeframe} candles are missing columns: {missing}.")

        times = candles["time"]
        if not pd.api.types.is_datetime64_any_dtype(times) or times.dt.tz is None:
            raise ValueError(f"{timeframe} candle times must be timezone-aware UTC.")
        if any(timestamp.utcoffset().total_seconds() != 0 for timestamp in times):
            raise ValueError(f"{timeframe} candle times must be in UTC.")
        if not times.is_monotonic_increasing or not times.is_unique:
            raise ValueError(
                f"{timeframe} candle times must be unique and chronological."
            )

        candle_duration = pd.Timedelta(TIMEFRAME_LENGTHS[timeframe])
        closed_candles = candles.loc[times + candle_duration <= pd.Timestamp(as_of)]
        if closed_candles.empty:
            unavailable[timeframe] = (
                f"No {timeframe} candle had closed by {as_of.isoformat()}."
            )
            continue

        structure = analyze_market_structure(closed_candles, active_config)
        trend = structure["trend"]
        latest_candle_time = closed_candles.iloc[-1]["time"]
        structures.append(
            TimeframeStructure(
                timeframe=timeframe,
                latest_candle_time=latest_candle_time,
                trend=trend,
                last_swing_high=structure["last_swing_high"],
                last_swing_low=structure["last_swing_low"],
                summary=(
                    f"{timeframe} structure is {trend.value.lower()} using "
                    f"closed candles through {latest_candle_time}."
                ),
            )
        )

    trends = [structure.trend for structure in structures]
    if len(trends) < 2:
        alignment: AlignmentState = "not_assessed"
        summary = (
            "Multi-timeframe alignment was not assessed: fewer than two "
            "timeframes have completed candle data."
        )
    elif all(trend == TrendState.BULLISH for trend in trends):
        alignment = "bullish"
        summary = (
            f"All {len(trends)} available timeframes report bullish market "
            "structure."
        )
    elif all(trend == TrendState.BEARISH for trend in trends):
        alignment = "bearish"
        summary = (
            f"All {len(trends)} available timeframes report bearish market "
            "structure."
        )
    else:
        alignment = "mixed"
        summary = (
            "The available timeframes do not all report the same direction; "
            "at least one is ranging or differs from another."
        )

    if unavailable:
        summary += " Some supplied timeframes were unavailable."

    return MultiTimeframeReport(
        as_of=as_of,
        structures=structures,
        unavailable=unavailable,
        alignment=alignment,
        summary=summary,
    )
