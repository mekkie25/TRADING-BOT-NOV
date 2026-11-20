"""Opening-range breakout followed by a confirming retest."""

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
    if len(candles) < 3:
        return None
    settings = parameters or {}
    duration = int(settings.get("range_minutes", 15))
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
    breakout = candles.iloc[-3]
    retest = candles.iloc[-2]
    confirmation = candles.iloc[-1]
    if (
        breakout["close"] > range_high
        and retest["low"] <= range_high
        and retest["close"] > range_high
        and confirmation["close"] > retest["high"]
    ):
        direction = Direction.BUY
        stop = float(retest["low"])
        target = facts.previous_day.pivots.get("R1")
    elif (
        breakout["close"] < range_low
        and retest["high"] >= range_low
        and retest["close"] < range_low
        and confirmation["close"] < retest["low"]
    ):
        direction = Direction.SELL
        stop = float(retest["high"])
        target = facts.previous_day.pivots.get("S1")
    else:
        return None
    return make_signal(
        name="power_ranger",
        variant="15m_range_5m_retest",
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
