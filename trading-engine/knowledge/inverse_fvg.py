"""IFVG: inverse fair value gap retest (spec Section 3.18).

Setup, using the project's fair value gap and inverse fair value gap reports:
  1. Price sweeps a session level (Asia high or low, previous day high or low).
  2. It displaces, leaving a fair value gap.
  3. A later candle closes through the gap, turning it into an inverse gap
     (IFVG). A bullish gap closed through below becomes resistance (sell side).
     A bearish gap closed through above becomes support (buy side).
  4. Price retests the IFVG. The trade is taken on the CLOSE of the tap candle
     when it rejects the zone (never a pending order).

Assumptions the spec leaves open (it marks the exact gap and "violation"
definition as a GAP):
  * A sell setup needs a swept session LOW before the bullish gap; a buy setup
    needs a swept session HIGH before the bearish gap. Switch the check off with
    require_sweep=False.
  * The order block is not defined, so the stop goes beyond the far edge of the
    IFVG zone or the tap candle extreme, whichever is further.
  * The spec says to enter on the 2-minute chart. This code works on whatever
    candles it is given.

Target (target_choice): "rr" (default, rr_multiple times the risk, 1:2),
"eq" (previous day equilibrium) or "asia_extreme" (the opposite Asia extreme).
Stops and targets default to structural; fixed and volatility-scaled stay
selectable through sl_mode and tp_mode.
"""

import math
from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from knowledge.fair_value_gap import FairValueGap, FVGDirection
from knowledge.inverse_fvg import IFVGStatus, get_active_ifvgs
from strategies.common import instrument_default_distance_unit, make_signal
from strategies.context import MarketFacts

TARGET_CHOICES = ("rr", "eq", "asia_extreme")


def _swept_before(
    candles: pd.DataFrame,
    gap: FairValueGap,
    facts: MarketFacts,
    lookback: int,
) -> bool:
    times = list(candles["time"])
    if gap.creation_time not in times:
        return False
    position = times.index(gap.creation_time)
    window = candles.iloc[max(0, position - 2 - lookback): position + 1]
    if gap.direction == FVGDirection.BULLISH:
        levels = [facts.asia.low, facts.previous_day.low]
        lowest = float(window["low"].min())
        return any(level is not None and lowest < level for level in levels)
    levels = [facts.asia.high, facts.previous_day.high]
    highest = float(window["high"].max())
    return any(level is not None and highest > level for level in levels)


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
) -> Optional[Signal]:
    settings: Dict[str, object] = {"sl_mode": "structural", "tp_mode": "structural"}
    settings.update(parameters or {})

    target_choice = str(settings.get("target_choice", "rr"))
    if target_choice not in TARGET_CHOICES:
        raise ValueError(f"target_choice must be one of {', '.join(TARGET_CHOICES)}.")
    rr_multiple = float(settings.get("rr_multiple", 2.0))
    if not math.isfinite(rr_multiple) or rr_multiple <= 0:
        raise ValueError("rr_multiple must be a positive number.")
    lookback = settings.get("sweep_lookback", 5)
    if isinstance(lookback, bool) or not isinstance(lookback, int) or lookback < 0:
        raise ValueError("sweep_lookback must be zero or a positive whole number.")
    require_sweep = bool(settings.get("require_sweep", True))

    if len(candles) < 3:
        return None
    latest = candles.iloc[-1]
    close = float(latest["close"])

    chosen = None
    for item in get_active_ifvgs(candles):
        if item.status == IFVGStatus.FAILED or item.inverted_at >= latest["time"]:
            continue
        if item.new_direction == FVGDirection.BEARISH:
            tapped = float(latest["high"]) >= item.bottom and close < item.bottom
        else:
            tapped = float(latest["low"]) <= item.top and close > item.top
        if not tapped:
            continue
        if require_sweep and not _swept_before(candles, item.original_fvg, facts, lookback):
            continue
        if chosen is None or item.original_fvg.creation_time > chosen.original_fvg.creation_time:
            chosen = item
    if chosen is None:
        return None

    if chosen.new_direction == FVGDirection.BEARISH:
        direction = Direction.SELL
        stop = max(chosen.top, float(latest["high"]))
        risk = stop - close
        asia_target = facts.asia.low
        rr_target = close - rr_multiple * risk
    else:
        direction = Direction.BUY
        stop = min(chosen.bottom, float(latest["low"]))
        risk = close - stop
        asia_target = facts.asia.high
        rr_target = close + rr_multiple * risk
    if risk <= 0:
        return None

    if target_choice == "rr":
        target = rr_target
    elif target_choice == "eq":
        target = facts.previous_day.equilibrium
    else:
        target = asia_target

    return make_signal(
        name="ifvg",
        variant="ifvg_retest",
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=settings,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=30,
        default_target=60,
        default_distance_unit=instrument_default_distance_unit(instrument_spec),
    )