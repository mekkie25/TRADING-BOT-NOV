"""Experimental ORB reversal requiring a completed value-area profile."""

from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from strategies.common import instrument_default_distance_unit, make_signal
from strategies.context import MarketFacts


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
) -> Optional[Signal]:
    profile = facts.volume_profile
    if profile.poc is None or profile.vah is None or profile.val is None:
        return None
    current = candles.iloc[-1]
    if current["low"] < profile.val and current["close"] > profile.val:
        direction = Direction.BUY
        stop = float(current["low"])
        target = profile.poc
    elif current["high"] > profile.vah and current["close"] < profile.vah:
        direction = Direction.SELL
        stop = float(current["high"])
        target = profile.poc
    else:
        return None
    return make_signal(
        name="orb_value_reversal",
        variant="value_edge_rejection",
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=parameters,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=5,
        default_target=10,
        default_distance_unit=instrument_default_distance_unit(instrument_spec),
        conditional=True,
    )
