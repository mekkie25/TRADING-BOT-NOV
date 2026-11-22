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
    settings = parameters or {}
    
    if len(candles) < 2 or facts.ema_200 is None:
        return None
        
    ema_200 = float(facts.ema_200)
    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    
    c_open = float(current["open"])
    c_close = float(current["close"])
    c_high = float(current["high"])
    c_low = float(current["low"])
    
    # 1. Solid body check (Audit fix)
    c_range = c_high - c_low
    if c_range <= 0:
        return None
    c_body = abs(c_close - c_open)
    if (c_body / c_range) < 0.6:  # Must be a solid body (>60% of range)
        return None

    direction: Optional[Direction] = None

    # 2. Proper Pullback Logic (Audit fix)
    if c_close > ema_200 and c_close > c_open:
        tested_ema = previous["low"] <= ema_200 or current["low"] <= ema_200
        if tested_ema:
            direction = Direction.BUY
            
    elif c_close < ema_200 and c_close < c_open:
        tested_ema = previous["high"] >= ema_200 or current["high"] >= ema_200
        if tested_ema:
            direction = Direction.SELL

    if direction is None:
        return None

    # 3. Tunable Stops and Targets (Spec 3.17 + Audit fix)
    # Default is 50 pips. If ATR > 4.0, stop is 100 pips.
    fixed_stop_val = 50.0
    atr_value = float(settings.get("atr", 0.0))
    if atr_value > 4.0:
        fixed_stop_val = 100.0

    fixed_stop_val = float(settings.get("fixed_stop", fixed_stop_val))
    fixed_target_val = float(settings.get("fixed_target", 50.0))

    # Force the engine to use fixed pip mode instead of the default ATR scaled mode
    settings["sl_mode"] = "fixed"
    settings["fixed_stop"] = fixed_stop_val
    settings["tp_mode"] = "fixed"
    settings["fixed_target"] = fixed_target_val

    return make_signal(
        name="ema_200_pullback",
        variant="m5_200_ema",
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=settings,
        structural_stop_price=None, 
        structural_target_price=None,
        default_stop=fixed_stop_val,
        default_target=fixed_target_val,
        default_distance_unit=instrument_default_distance_unit(instrument_spec),
        conditional=True,
    )