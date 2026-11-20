"""Session-low/high sweep followed by an engulfing reversal candle."""

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
    if len(candles) < 2 or facts.asia.high is None or facts.asia.low is None:
        return None
    previous = candles.iloc[-2]
    current = candles.iloc[-1]
    bullish_engulfing = (
        current["close"] > current["open"]
        and previous["close"] < previous["open"]
        and current["open"] <= previous["close"]
        and current["close"] >= previous["open"]
    )
    bearish_engulfing = (
        current["close"] < current["open"]
        and previous["close"] > previous["open"]
        and current["open"] >= previous["close"]
        and current["close"] <= previous["open"]
    )
    if current["low"] < facts.asia.low and current["close"] > facts.asia.low and bullish_engulfing:
        direction = Direction.BUY
        stop = float(current["low"])
        target = facts.previous_day.equilibrium or facts.asia.high
    elif current["high"] > facts.asia.high and current["close"] < facts.asia.high and bearish_engulfing:
        direction = Direction.SELL
        stop = float(current["high"])
        target = facts.previous_day.equilibrium or facts.asia.low
    else:
        return None
    return make_signal(
        name="session_low_reversal",
        variant="sweep_engulfing",
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
