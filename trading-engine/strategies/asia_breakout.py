"""Asia range breakout continuation, including the OI-OI variant."""

from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from knowledge.operational_definitions import volume_present
from strategies.common import make_signal
from strategies.context import MarketFacts


VARIANTS = ("close_and_volume", "retest", "oi_oi")


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "close_and_volume",
) -> Optional[Signal]:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown Asia breakout variant: {variant}.")
    if len(candles) < 3 or facts.average_candle_size is None:
        return None
    if not facts.asia.session_complete or facts.asia.high is None or facts.asia.low is None:
        return None
    if facts.session.name == "Asia":
        return None
    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    if variant == "oi_oi":
        before_previous = candles.iloc[-3]
        bullish = (
            before_previous["close"] > facts.asia.high
            and previous["close"] <= facts.asia.high
            and current["close"] > facts.asia.high
        )
        bearish = (
            before_previous["close"] < facts.asia.low
            and previous["close"] >= facts.asia.low
            and current["close"] < facts.asia.low
        )
    elif variant == "retest":
        bullish = (
            previous["close"] > facts.asia.high
            and current["low"] <= facts.asia.high
            and current["close"] > facts.asia.high
        )
        bearish = (
            previous["close"] < facts.asia.low
            and current["high"] >= facts.asia.low
            and current["close"] < facts.asia.low
        )
    else:
        bullish = previous["close"] <= facts.asia.high and current["close"] > facts.asia.high
        bearish = previous["close"] >= facts.asia.low and current["close"] < facts.asia.low
    if bullish == bearish:
        return None

    # Check close-back-inside rejection
    if bool((parameters or {}).get("close_back_rejection", True)):
        if bullish and current["close"] < facts.asia.high:
            return None
        if bearish and current["close"] > facts.asia.low:
            return None

    direction = Direction.BUY if bullish else Direction.SELL
    if not volume_present(
        current,
        facts.average_candle_size,
        float((parameters or {}).get("volume_range_multiple", 1.5)),
        float((parameters or {}).get("volume_body_fraction", 0.6)),
    ):
        return None
    return make_signal(
        name="asia_breakout",
        variant=variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=parameters,
        structural_stop_price=(
            float(current["low"]) if bullish else float(current["high"])
        ),
        structural_target_price=(
            facts.previous_day.pivots.get("R1") if bullish
            else facts.previous_day.pivots.get("S1")
        ),
        default_stop=30,
        default_target=60,
        default_distance_unit="points",
    )
