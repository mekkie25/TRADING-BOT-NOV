"""Report geometric trend-line candidates from supplied timeframe candles."""

import math
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

import pandas as pd

from .market_structure import MarketStructureConfig, SwingPoint, SwingType, _find_swings


TrendLineType = Literal["candidate_support", "candidate_resistance"]


@dataclass(frozen=True)
class TrendLine:
    timeframe: str
    type: TrendLineType
    first_swing: SwingPoint
    second_swing: SwingPoint
    current_time: pd.Timestamp
    current_price: float
    line_price: float
    slope_per_day: float
    description: str


@dataclass(frozen=True)
class TrendLineReport:
    lines: List[TrendLine]
    unavailable: Dict[str, str]
    summary: str


def _line_price_at(
    first_swing: SwingPoint,
    second_swing: SwingPoint,
    at_time: pd.Timestamp,
) -> tuple[float, float]:
    elapsed_seconds = (
        second_swing.occurred_at - first_swing.occurred_at
    ).total_seconds()
    if elapsed_seconds <= 0:
        raise ValueError("Trend-line swing times must be strictly increasing.")

    slope_per_second = (second_swing.price - first_swing.price) / elapsed_seconds
    elapsed_to_current = (at_time - first_swing.occurred_at).total_seconds()
    line_price = first_swing.price + slope_per_second * elapsed_to_current
    return line_price, slope_per_second * 86400


def analyze_trend_lines(
    candles_by_timeframe: Dict[str, pd.DataFrame],
    config: Optional[MarketStructureConfig] = None,
) -> TrendLineReport:
    """Report one candidate line per available timeframe and swing type."""
    active_config = config or MarketStructureConfig()
    lines: List[TrendLine] = []
    unavailable: Dict[str, str] = {}

    for timeframe, candles in candles_by_timeframe.items():
        if candles.empty:
            unavailable[timeframe] = "No candles were supplied."
            continue
        if "close" not in candles.columns:
            raise ValueError(f"{timeframe} candles are missing the close column.")
        times = candles["time"]
        if not pd.api.types.is_datetime64_any_dtype(times) or times.dt.tz is None:
            raise ValueError(f"{timeframe} candle times must be timezone-aware UTC.")
        if not times.is_monotonic_increasing:
            raise ValueError(f"{timeframe} candle times must be in chronological order.")
        if any(timestamp.utcoffset().total_seconds() != 0 for timestamp in times):
            raise ValueError(f"{timeframe} candle times must be in UTC.")

        swings = _find_swings(candles, active_config)
        current_time = candles.iloc[-1]["time"]
        current_price = float(candles.iloc[-1]["close"])
        if not math.isfinite(current_price) or current_price <= 0:
            raise ValueError(f"{timeframe} latest close must be a positive finite price.")

        for swing_type, line_type in (
            (SwingType.HIGH, "candidate_resistance"),
            (SwingType.LOW, "candidate_support"),
        ):
            same_type_swings = [swing for swing in swings if swing.type == swing_type]
            label = "resistance" if swing_type == SwingType.HIGH else "support"
            if len(same_type_swings) < 2:
                unavailable[f"{timeframe}.{label}"] = (
                    f"Fewer than two confirmed swing {label} points are available."
                )
                continue

            first_swing, second_swing = same_type_swings[-2:]
            line_price, slope_per_day = _line_price_at(
                first_swing,
                second_swing,
                current_time,
            )
            description = (
                f"{timeframe} candidate {label} line joins swings at "
                f"{first_swing.price} and {second_swing.price}; at "
                f"{current_time} the line is at {line_price}, while the latest "
                f"close is {current_price}."
            )
            lines.append(
                TrendLine(
                    timeframe=timeframe,
                    type=line_type,
                    first_swing=first_swing,
                    second_swing=second_swing,
                    current_time=current_time,
                    current_price=current_price,
                    line_price=line_price,
                    slope_per_day=slope_per_day,
                    description=description,
                )
            )

    if lines:
        summary = (
            f"Found {len(lines)} candidate trend lines across the supplied "
            "timeframes. Each line connects the two latest confirmed swings "
            "of the same type; it is a geometric observation, not a trade signal."
        )
    else:
        summary = "No candidate trend lines could be formed from the supplied data."
    return TrendLineReport(lines=lines, unavailable=unavailable, summary=summary)
