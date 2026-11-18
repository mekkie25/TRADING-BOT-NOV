"""Report candidate supply and demand zones from confirmed swing candles."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Literal, Optional

import pandas as pd

from .market_structure import MarketStructureConfig
from .multi_timeframe_alignment import analyze_multi_timeframe_alignment
from .support_resistance import analyze_support_resistance


ZoneType = Literal["candidate_supply", "candidate_demand"]


@dataclass(frozen=True)
class SupplyDemandZone:
    type: ZoneType
    low: float
    high: float
    occurred_at: pd.Timestamp
    confirmed_at: pd.Timestamp
    timeframe: str
    swing_label: str


@dataclass(frozen=True)
class SupplyDemandReport:
    as_of: datetime
    timeframe: str
    zones: List[SupplyDemandZone]
    unavailable: Dict[str, str]
    summary: str


def analyze_supply_demand(
    candles: pd.DataFrame,
    timeframe: str,
    as_of: datetime,
    config: Optional[MarketStructureConfig] = None,
) -> SupplyDemandReport:
    """Report each confirmed swing candle's full range as a candidate zone.

    Only candles whose explicitly labeled timeframe window has closed by
    ``as_of`` are used. A swing high candle is labeled candidate supply and a
    swing low candle candidate demand; these are geometric conventions only.
    """
    normalized_timeframe = timeframe.strip().upper()
    structure_report = analyze_multi_timeframe_alignment(
        {normalized_timeframe: candles},
        as_of,
        config,
    )
    timeframe_structure = next(
        (
            structure
            for structure in structure_report.structures
            if structure.timeframe == normalized_timeframe
        ),
        None,
    )

    if timeframe_structure is None:
        unavailable = structure_report.unavailable
        reason = unavailable.get(normalized_timeframe, "No closed candles.")
        return SupplyDemandReport(
            as_of=as_of,
            timeframe=normalized_timeframe,
            zones=[],
            unavailable=unavailable,
            summary=(
                f"No candidate supply or demand zones for "
                f"{normalized_timeframe}: {reason}"
            ),
        )

    closed_candles = candles.loc[
        candles["time"] <= timeframe_structure.latest_candle_time
    ]
    swing_levels = analyze_support_resistance(
        closed_candles,
        config,
    ).levels
    candle_ranges = closed_candles.set_index("time")
    zones: List[SupplyDemandZone] = []

    for level in swing_levels:
        candle = candle_ranges.loc[level.occurred_at]
        if level.type == "candidate_resistance":
            zone_type: ZoneType = "candidate_supply"
        else:
            zone_type = "candidate_demand"

        zones.append(
            SupplyDemandZone(
                type=zone_type,
                low=float(candle["low"]),
                high=float(candle["high"]),
                occurred_at=level.occurred_at,
                confirmed_at=level.confirmed_at,
                timeframe=normalized_timeframe,
                swing_label=level.swing_label,
            )
        )

    supply_count = sum(zone.type == "candidate_supply" for zone in zones)
    demand_count = len(zones) - supply_count
    if zones:
        summary = (
            f"Found {supply_count} candidate supply zones and "
            f"{demand_count} candidate demand zones on {normalized_timeframe}. "
            "Each zone is the full high-to-low range of a confirmed swing "
            "candle; this does not prove resting orders or predict a reaction."
        )
    else:
        summary = (
            f"No confirmed swing-candle ranges were available for candidate "
            f"supply or demand zones on {normalized_timeframe}."
        )

    return SupplyDemandReport(
        as_of=as_of,
        timeframe=normalized_timeframe,
        zones=zones,
        unavailable=structure_report.unavailable,
        summary=summary,
    )
