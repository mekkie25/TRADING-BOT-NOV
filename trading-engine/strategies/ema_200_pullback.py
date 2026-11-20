"""Conditional 5-minute 200 EMA pullback with a body-close confirmation."""

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
    if len(candles) < 2 or facts.ema_200 is None:
        return None
    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    if previous["low"] <= facts.ema_200 <= previous["high"] and current["close"] > current["open"] and current["close"] > facts.ema_200:
        direction = Direction.BUY
        stop, target = float(previous["low"]), facts.previous_day.pivots.get("R1")
    elif previous["low"] <= facts.ema_200 <= previous["high"] and current["close"] < current["open"] and current["close"] < facts.ema_200:
        direction = Direction.SELL
        stop, target = float(previous["high"]), facts.previous_day.pivots.get("S1")
    else:
        return None
    return make_signal(
        name="ema_200_pullback",
        variant="m5_200_ema",
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=parameters,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=50,
        default_target=50,
        default_distance_unit=instrument_default_distance_unit(instrument_spec),
        conditional=True,
    )
