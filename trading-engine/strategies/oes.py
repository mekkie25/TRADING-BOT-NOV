"""Experimental OES placeholders; undisclosed criteria are not invented."""

from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Signal
from strategies.context import MarketFacts


@dataclass(frozen=True)
class OESStubStatus:
    strategy_name: str
    variant: str
    enabled_by_default: bool
    status: str
    parameters: Dict[str, object]


OES_STUBS = {
    "oes_5m": OESStubStatus(
        "oes",
        "5m",
        False,
        "BLOCKED_UNDISCLOSED_ENTRY_CRITERIA",
        {"stop_mode": "fixed|volatility_scaled|structural", "stop_value": 50},
    ),
    "oes_4h": OESStubStatus(
        "oes",
        "4h",
        False,
        "BLOCKED_UNDISCLOSED_ENTRY_CRITERIA",
        {"wait_for_closed_4h_candle": True, "stop_mode": "configurable"},
    ),
    "oes_inverse_4h": OESStubStatus(
        "oes",
        "inverse_4h",
        False,
        "BLOCKED_UNDISCLOSED_ENTRY_CRITERIA",
        {"wait_for_closed_4h_candle": True, "stop_mode": "configurable"},
    ),
}


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "oes_5m",
) -> Optional[Signal]:
    if variant not in OES_STUBS:
        raise ValueError(f"Unknown OES variant: {variant}.")
    return None
