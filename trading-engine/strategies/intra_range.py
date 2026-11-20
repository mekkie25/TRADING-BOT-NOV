"""Large opening-range fade, separate from the ORB breakout strategy."""

from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from strategies.common import instrument_default_distance_unit, make_signal, opening_range
from strategies.context import MarketFacts


def evaluate(
    candles: pd.DataFrame,
    timeframe: str,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
) -> Optional[Signal]:
    if len(candles) < 2:
        return None
    settings = parameters or {}
    range_minutes = int(settings.get("range_minutes", 15))
    levels = opening_range(
        candles,
        timeframe,
        facts.current_time,
        str(settings.get("opening_session", facts.session.name)),
        range_minutes,
    )
    if levels is None:
        return None
    range_high, range_low = levels
    unit = str(settings.get("range_size_unit", instrument_default_distance_unit(instrument_spec)))
    threshold = instrument_spec.price_distance(
        float(settings.get("minimum_range_size", 100.0)),
        unit,  # type: ignore[arg-type]
    )
    if range_high - range_low < threshold:
        return None
    previous = candles.iloc[-2]
    current = candles.iloc[-1]
    if previous["close"] > range_high and range_low < current["close"] < range_high:
        direction = Direction.SELL
        rejected = current["high"] >= range_high and current["close"] < range_high
        stop = float(current["high"])
        target = range_low
    elif previous["close"] < range_low and range_low < current["close"] < range_high:
        direction = Direction.BUY
        rejected = current["low"] <= range_low and current["close"] > range_low
        stop = float(current["low"])
        target = range_high
    else:
        return None
    if not rejected:
        return None
    return make_signal(
        name="intra_range",
        variant="range_fade",
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=parameters,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=40,
        default_target=100,
        default_distance_unit=unit,  # type: ignore[arg-type]
    )
