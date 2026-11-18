"""Report confirmed swing points as possible support or resistance levels."""

from dataclasses import dataclass
from typing import List, Literal, Optional

import pandas as pd

from .market_structure import (
    MarketStructureConfig,
    SwingType,
    _find_swings,
    _label_swings,
)


LevelType = Literal["candidate_support", "candidate_resistance"]


@dataclass(frozen=True)
class SupportResistanceLevel:
    type: LevelType
    price: float
    occurred_at: pd.Timestamp
    confirmed_at: pd.Timestamp
    swing_label: str


@dataclass(frozen=True)
class SupportResistanceReport:
    levels: List[SupportResistanceLevel]
    summary: str


def analyze_support_resistance(
    df: pd.DataFrame,
    config: Optional[MarketStructureConfig] = None,
) -> SupportResistanceReport:
    """Report confirmed swing highs/lows as candidates, not guaranteed barriers."""
    if df.empty:
        return SupportResistanceReport(
            levels=[],
            summary="No candidate support or resistance levels: there are no candles.",
        )

    active_config = config or MarketStructureConfig()
    swings = _label_swings(_find_swings(df, active_config))
    levels: List[SupportResistanceLevel] = []

    for swing in swings:
        if swing.type == SwingType.HIGH:
            level_type: LevelType = "candidate_resistance"
        else:
            level_type = "candidate_support"

        levels.append(
            SupportResistanceLevel(
                type=level_type,
                price=swing.price,
                occurred_at=swing.occurred_at,
                confirmed_at=swing.confirmed_at,
                swing_label=swing.label,
            )
        )

    support_count = sum(level.type == "candidate_support" for level in levels)
    resistance_count = len(levels) - support_count
    summary = (
        f"Found {support_count} candidate support levels and "
        f"{resistance_count} candidate resistance levels from confirmed swings. "
        "These are possible reaction levels, not guarantees."
    )
    return SupportResistanceReport(levels=levels, summary=summary)
