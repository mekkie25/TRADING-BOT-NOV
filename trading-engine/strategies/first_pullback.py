"""First pullback in a trend with configurable impulse retracement bounds."""

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
    if len(candles) < 3 or facts.ema_200 is None or facts.average_candle_size is None:
        return None
    settings = parameters or {}
    impulse = candles.iloc[-3]
    pullback = candles.iloc[-2]
    current = candles.iloc[-1]
    minimum = float(settings.get("pullback_min_fraction", 0.3))
    maximum = float(settings.get("pullback_max_fraction", 0.6))
    impulse_range = float(impulse["high"] - impulse["low"])
    if impulse_range <= 0 or not 0 <= minimum <= maximum <= 1:
        raise ValueError("Pullback fractions must satisfy 0 <= minimum <= maximum <= 1.")
    if (
        impulse["close"] > impulse["open"]
        and impulse["close"] > facts.ema_200
        and pullback["low"] < impulse["close"]
        and pullback["low"] >= impulse["high"] - impulse_range * maximum
        and pullback["low"] <= impulse["high"] - impulse_range * minimum
        and current["close"] > pullback["high"]
    ):
        direction, stop, target = Direction.BUY, float(pullback["low"]), facts.previous_day.pivots.get("R1")
    elif (
        impulse["close"] < impulse["open"]
        and impulse["close"] < facts.ema_200
        and pullback["high"] > impulse["close"]
        and pullback["high"] <= impulse["low"] + impulse_range * maximum
        and pullback["high"] >= impulse["low"] + impulse_range * minimum
        and current["close"] < pullback["low"]
    ):
        direction, stop, target = Direction.SELL, float(pullback["high"]), facts.previous_day.pivots.get("S1")
    else:
        return None
    return make_signal(
        name="first_pullback",
        variant="trend_pullback",
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
