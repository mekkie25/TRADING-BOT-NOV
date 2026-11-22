"""All-time-high breakout/retest and separate rejection-fade variants."""

from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from knowledge.operational_definitions import volume_present
from strategies.common import instrument_default_distance_unit, make_signal
from strategies.context import MarketFacts


VARIANTS = ("breakout", "retest", "weekly_r1_no_volume_fade")


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "breakout",
) -> Optional[Signal]:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown all-time-high variant: {variant}.")
    if len(candles) < 2:
        return None
    settings = parameters or {}
    high_value = settings.get("ath_price")
    if high_value is None:
        high_value = settings.get("all_time_high")
    if high_value is None:
        return None
    level = float(high_value)
    if not pd.notna(level) or level <= 0:
        raise ValueError("ath_price must be a positive finite price.")
    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    if variant == "breakout":
        daily_r3 = settings.get("daily_r3")
        if daily_r3 is None and facts.previous_day and facts.previous_day.pivots:
            daily_r3 = facts.previous_day.pivots.get("R3")
        if (
            daily_r3 is None
            or previous["close"] > level
            or current["close"] <= level
            or current["close"] <= float(daily_r3)
            or current["close"] <= current["open"]
        ):
            return None
        if facts.average_candle_size is None or not volume_present(
            current,
            facts.average_candle_size,
            float(settings.get("volume_range_multiple", 1.5)),
            float(settings.get("volume_body_fraction", 0.6)),
        ):
            return None
        direction = Direction.BUY
    elif variant == "retest":
        if previous["close"] <= level or current["low"] > level or current["close"] <= level:
            return None
        direction = Direction.BUY
    else:
        weekly_r1 = settings.get("weekly_r1")
        if weekly_r1 is None or abs(level - float(weekly_r1)) > float(
            settings.get("weekly_r1_tolerance_price", 0.0)
        ):
            return None
        if facts.average_candle_size is None:
            return None
        if volume_present(current, facts.average_candle_size):
            return None
        if current["high"] <= level or current["close"] >= level:
            return None
        direction = Direction.SELL
    next_target = (
        facts.previous_day.pivots.get("R4")
        if direction == Direction.BUY
        else facts.previous_day.pivots.get("P")
    )
    return make_signal(
        name="all_time_high",
        variant=variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=parameters,
        structural_stop_price=float(current["low"] if direction == Direction.BUY else current["high"]),
        structural_target_price=next_target,
        default_stop=30,
        default_target=50,
        default_distance_unit=instrument_default_distance_unit(instrument_spec),
    )
