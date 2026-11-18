"""Report weekly market structure and its alignment with daily structure."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Literal, Optional

import pandas as pd

from .market_structure import (
    BreakEvent,
    BreakType,
    MarketStructureConfig,
    TrendState,
    get_last_break,
)
from .multi_timeframe_alignment import (
    AlignmentState,
    analyze_multi_timeframe_alignment,
)


WeeklyBiasState = Literal["bullish", "bearish", "neutral", "unknown"]


@dataclass(frozen=True)
class WeeklyBiasReport:
    as_of: datetime
    weekly_bias: WeeklyBiasState
    weekly_structure: Optional[TrendState]
    daily_structure: Optional[TrendState]
    alignment: AlignmentState
    last_weekly_break: Optional[BreakEvent]
    unavailable: Dict[str, str]
    summary: str


def analyze_weekly_bias(
    weekly_candles: pd.DataFrame,
    daily_candles: pd.DataFrame,
    as_of: datetime,
    config: Optional[MarketStructureConfig] = None,
) -> WeeklyBiasReport:
    """Report weekly structure, the latest confirmed weekly break, and D1 context.

    The supplied frames must contain W1 and D1 candles respectively. Structure
    and break labels use the existing configured market-structure convention.
    """
    structure_report = analyze_multi_timeframe_alignment(
        {"W1": weekly_candles, "D1": daily_candles},
        as_of,
        config,
    )
    structures = {item.timeframe: item for item in structure_report.structures}
    weekly = structures.get("W1")
    daily = structures.get("D1")

    if weekly is None:
        weekly_bias: WeeklyBiasState = "unknown"
        last_weekly_break = None
    else:
        weekly_bias = {
            TrendState.BULLISH: "bullish",
            TrendState.BEARISH: "bearish",
            TrendState.RANGING: "neutral",
        }[weekly.trend]
        closed_weekly_candles = weekly_candles.loc[
            weekly_candles["time"] <= weekly.latest_candle_time
        ]
        reported_break = get_last_break(
            closed_weekly_candles,
            config or MarketStructureConfig(),
        )
        last_weekly_break = (
            reported_break if reported_break.type != BreakType.NONE else None
        )

    weekly_structure = weekly.trend if weekly is not None else None
    daily_structure = daily.trend if daily is not None else None
    summary = _build_summary(
        weekly_bias,
        weekly_structure,
        daily_structure,
        structure_report.alignment,
        structure_report.unavailable,
        last_weekly_break,
    )

    return WeeklyBiasReport(
        as_of=as_of,
        weekly_bias=weekly_bias,
        weekly_structure=weekly_structure,
        daily_structure=daily_structure,
        alignment=structure_report.alignment,
        last_weekly_break=last_weekly_break,
        unavailable=structure_report.unavailable,
        summary=summary,
    )


def _build_summary(
    weekly_bias: WeeklyBiasState,
    weekly_structure: Optional[TrendState],
    daily_structure: Optional[TrendState],
    alignment: AlignmentState,
    unavailable: Dict[str, str],
    last_weekly_break: Optional[BreakEvent],
) -> str:
    if weekly_structure is None:
        weekly_detail = unavailable.get("W1", "No completed W1 candles.")
        summary = f"Weekly bias is unknown: {weekly_detail}"
    else:
        summary = f"Weekly market structure is {weekly_bias}."

    if daily_structure is None:
        daily_detail = unavailable.get("D1", "No completed D1 candles.")
        summary += f" Daily structure was not assessed: {daily_detail}"
    elif alignment in ("bullish", "bearish"):
        summary += (
            f" Daily structure is also {daily_structure.value.lower()}; "
            "weekly and daily structures align."
        )
    elif alignment == "not_assessed":
        summary += (
            f" Daily structure is {daily_structure.value.lower()}; "
            "weekly and daily alignment was not assessed."
        )
    else:
        summary += (
            f" Daily structure is {daily_structure.value.lower()}; "
            "weekly and daily structures do not confirm the same direction."
        )

    if last_weekly_break is not None:
        summary += (
            f" The latest reported weekly break is "
            f"{last_weekly_break.direction.value.lower()} "
            f"{last_weekly_break.type.value} at {last_weekly_break.break_price} "
            f"on {last_weekly_break.break_time}."
        )
    else:
        summary += " No confirmed weekly structure break was reported."

    summary += " This is a market observation, not a trade decision."
    return summary
