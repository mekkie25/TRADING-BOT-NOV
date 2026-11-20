"""Shared result types for strategy trigger evaluations."""

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple

import pandas as pd

from engine.models import Direction


StrategyStatus = Literal["TRIGGERED", "NOT_TRIGGERED", "BLOCKED"]
CheckStatus = Literal["PASS", "FAIL", "UNKNOWN"]


@dataclass(frozen=True)
class StrategyCheck:
    name: str
    status: CheckStatus
    reason: str


@dataclass(frozen=True)
class StrategyEvaluation:
    strategy_name: str
    variant: str
    status: StrategyStatus
    direction: Optional[Direction]
    trigger_time: Optional[pd.Timestamp]
    entry_reference_price: Optional[float]
    stop_loss_price: Optional[float]
    take_profit_prices: Tuple[float, ...]
    checks: Tuple[StrategyCheck, ...]
    summary: str
    confluence_reasons: Tuple[str, ...] = ()
    confluence_count: int = 0
    average_candle_size: Optional[float] = None
    poc_source: Optional[str] = None
    definition_parameters: Dict[str, object] = None
    sl_mode: str = "volatility_scaled"
    tp_mode: str = "volatility_scaled"

    @property
    def triggered(self) -> bool:
        return self.status == "TRIGGERED"
