"""Previous-day high/low sweep-and-reclaim reversal."""

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
    if len(candles) < 1:
        return None
    current = candles.iloc[-1]
    if (
        facts.previous_day.low is not None
        and current["low"] < facts.previous_day.low
        and current["close"] > facts.previous_day.low
    ):
        direction = Direction.BUY
        stop = float(current["low"])
        target = facts.previous_day.equilibrium
    elif (
        facts.previous_day.high is not None
        and current["high"] > facts.previous_day.high
        and current["close"] < facts.previous_day.high
    ):
        direction = Direction.SELL
        stop = float(current["high"])
        target = facts.previous_day.equilibrium
    else:
        return None
    return make_signal(
        name="pdh_pdl_reversal",
        variant="sweep_reclaim",
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
    )
