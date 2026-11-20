"""Grabber and EQ variants, driven by an Asia-boundary sweep and EQ reaction."""

from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from knowledge.operational_definitions import close_back_rejection, level_holds
from strategies.common import make_signal
from strategies.context import MarketFacts


VARIANTS = ("standard", "reverse_kick", "eq_confirmation")


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "standard",
) -> Optional[Signal]:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown Grabber variant: {variant}.")
    if len(candles) < 3 or facts.average_candle_size is None:
        return None
    asia_high = facts.asia.high
    asia_low = facts.asia.low
    equilibrium = facts.previous_day.equilibrium
    if asia_high is None or asia_low is None or equilibrium is None:
        return None
    direction = (
        Direction.BUY
        if close_back_rejection(
            candles.tail(3), asia_low, "bullish", facts.average_candle_size
        )
        else Direction.SELL
        if close_back_rejection(
            candles.tail(3), asia_high, "bearish", facts.average_candle_size
        )
        else None
    )
    if direction is None:
        return None
    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    if variant == "standard":
        if direction == Direction.BUY:
            confirmed = (
                current["close"] > equilibrium
                and previous["low"] <= equilibrium
                and level_holds(
                    candles.tail(2), equilibrium, "bullish",
                    facts.average_candle_size, hold_candles=1,
                )
            )
        else:
            confirmed = (
                current["close"] < equilibrium
                and previous["high"] >= equilibrium
                and level_holds(
                    candles.tail(2), equilibrium, "bearish",
                    facts.average_candle_size, hold_candles=1,
                )
            )
    elif variant == "reverse_kick":
        direction = Direction.SELL if direction == Direction.BUY else Direction.BUY
        confirmed = (
            current["close"] < equilibrium
            if direction == Direction.SELL
            else current["close"] > equilibrium
        )
    else:
        confirmed = (
            current["close"] > previous["close"]
            if direction == Direction.BUY
            else current["close"] < previous["close"]
        )
    if not confirmed:
        return None

    sweep_extreme = (
        float(candles.tail(3)["low"].min())
        if direction == Direction.BUY
        else float(candles.tail(3)["high"].max())
    )
    if direction == Direction.BUY:
        target = asia_high if current["close"] < asia_high else facts.previous_day.pivots.get("R1")
    else:
        target = asia_low if current["close"] > asia_low else facts.previous_day.pivots.get("S1")
    return make_signal(
        name="grabber",
        variant=variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=parameters,
        structural_stop_price=sweep_extreme,
        structural_target_price=target,
        default_stop=30,
        default_target=60,
        default_distance_unit="pips",
    )
