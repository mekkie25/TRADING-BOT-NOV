"""Conditional value-area fade and breakout/retest setups."""

from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from strategies.common import instrument_default_distance_unit, make_signal
from strategies.context import MarketFacts


VARIANTS = ("fade", "breakout_retest")


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "fade",
) -> Optional[Signal]:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown value-area variant: {variant}.")
    profile = facts.volume_profile
    if profile.poc is None or profile.vah is None or profile.val is None or len(candles) < 2:
        return None
    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    if profile.val <= current["close"] <= profile.vah and abs(current["close"] - profile.poc) <= (profile.bin_size or 0) / 2:
        return None
    if variant == "fade":
        if current["low"] <= profile.val and current["close"] > profile.val:
            direction, stop, target = Direction.BUY, float(current["low"]), profile.poc
        elif current["high"] >= profile.vah and current["close"] < profile.vah:
            direction, stop, target = Direction.SELL, float(current["high"]), profile.poc
        else:
            return None
    else:
        if previous["close"] > profile.vah and current["low"] <= profile.vah and current["close"] > profile.vah:
            direction, stop, target = Direction.BUY, float(current["low"]), facts.previous_day.pivots.get("R1")
        elif previous["close"] < profile.val and current["high"] >= profile.val and current["close"] < profile.val:
            direction, stop, target = Direction.SELL, float(current["high"]), facts.previous_day.pivots.get("S1")
        else:
            return None
    return make_signal(
        name="value_area",
        variant=variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=parameters,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=30,
        default_target=60,
        default_distance_unit=instrument_default_distance_unit(instrument_spec),
        conditional=True,
    )
