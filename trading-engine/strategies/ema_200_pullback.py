"""Conditional 5-minute 200 EMA pullback with a body-close confirmation (spec Section 3.17).

Entry (on a closed candle, never a pending order): price is above (buy) or below
(sell) the 200 EMA, a candle or the one before it tested the EMA, and the latest
candle closes away from it with a solid body (at least 60% of its range).

Defaults follow the spec as starting values: fixed 50 stop (100 when the caller
passes atr above 4.0) and fixed 50 target. The caller can change them with
fixed_stop and fixed_target, or pick sl_mode / tp_mode "volatility_scaled"
(AGENTS.md rule 11). A structural stop is not offered: the spec gives none.

Known gaps against the spec, left as they are:
  * The pullback is tested against the 200 EMA only, not the Daily Flip or POC.
  * "Clearly above or below" the EMA is not measured; a close on the right side counts.
  * The Daily R1/R2 target option is not built.
  * The 60% body size is fixed in the code.
  * The 200 EMA comes from the facts, and the code does not check it is a 5M EMA.
  * Fewer than two trades a day is a risk rule, not checked here.
"""

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
    settings = dict(parameters or {})  # a copy: the caller's dict is never changed
    
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

    # Spec defaults are fixed pips, but the caller may still choose another mode.
    settings.setdefault("sl_mode", "fixed")
    settings["fixed_stop"] = fixed_stop_val
    settings.setdefault("tp_mode", "fixed")
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