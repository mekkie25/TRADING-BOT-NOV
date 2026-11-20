"""Opening-range breakout and Pre-ORB configurations."""

from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from strategies.common import instrument_default_distance_unit, make_signal, opening_range
from strategies.context import MarketFacts


VARIANTS = {"orb_30m": 30, "orb_15m": 15, "orb_5m": 5, "orb_2m": 2, "pre_orb_15m": 15}


def evaluate(
    candles: pd.DataFrame,
    timeframe: str,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "orb_15m",
) -> Optional[Signal]:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown ORB variant: {variant}.")
    settings = parameters or {}
    duration = int(settings.get("range_minutes", VARIANTS[variant]))
    levels = opening_range(
        candles,
        timeframe,
        facts.current_time,
        str(settings.get("opening_session", facts.session.name)),
        duration,
    )
    if levels is None:
        return None
    range_high, range_low = levels
    current = candles.iloc[-1]
    previous = candles.iloc[-2] if len(candles) > 1 else current
    if current["close"] > range_high and previous["close"] <= range_high:
        direction = Direction.BUY
        stop = range_low
        target = None
    elif current["close"] < range_low and previous["close"] >= range_low:
        direction = Direction.SELL
        stop = range_high
        target = None
    else:
        return None
    return make_signal(
        name="orb",
        variant=variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=parameters,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=40,
        default_target=120,
        default_distance_unit=instrument_default_distance_unit(instrument_spec),
    )
