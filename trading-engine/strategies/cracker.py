"""Call-based Cracker (spec Section 3.6, version B); direction and levels are caller-supplied.

The daily call (buy or sell) and the two price levels are given by the caller.
After the open, a candle that closes through the first level tapped, in the
call's direction, is the entry. The signal fires on that close; there are no
pending orders (AGENTS.md rule 10). This module only reports a signal.

Defaults follow the spec as starting values: fixed 60 stop and fixed 60 target
(1:1). Use fixed_target 120 for 1:2. The structural stop (the entry candle's
extreme) and the previous-day equilibrium target stay selectable with sl_mode
and tp_mode "structural", and so does the volatility-scaled mode
(AGENTS.md rule 11).

What is NOT here, on purpose:
  * Version A ("Teemo" joke version): the spec says do not use it.
  * Version C (wick) and version D (barrier): the spec's rules for them are unclear.
  * End-of-month, bank-holiday and CPI/NFP skips: the news filter is not built
    and the spec does not say which days count as end of month.
  * Break-even at 80%, the 90-second exit itself, max two trades a day:
    trade management and risk rules. The 90 seconds is passed on as time_limit_seconds.
"""

from datetime import timedelta
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
    # Spec defaults: fixed stop and target. Callers can still choose another mode.
    settings = dict(parameters or {})
    settings.setdefault("sl_mode", "fixed")
    settings.setdefault("tp_mode", "fixed")
    call = str(settings.get("call_direction", "")).lower()
    levels = settings.get("call_levels")
    if call not in ("buy", "sell") or not isinstance(levels, (list, tuple)) or len(levels) != 2:
        return None
    prices = [float(level) for level in levels]
    if any(not pd.notna(level) or level <= 0 for level in prices):
        raise ValueError("Cracker call levels must be positive finite prices.")
    if len(candles) < 2:
        return None
    if bool(settings.get("level_invalidated_before_open", False)):
        return None
    open_time = settings.get("new_york_open_utc")
    if open_time is None:
        return None
    if not isinstance(open_time, pd.Timestamp):
        open_time = pd.Timestamp(open_time)
    if open_time.tzinfo is None or open_time.utcoffset() != timedelta(0):
        raise ValueError("new_york_open_utc must be timezone-aware UTC.")
    latest_time = pd.Timestamp(facts.current_time)
    if latest_time < open_time or latest_time > open_time + timedelta(minutes=5):
        return None
    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    tapped = [
        level for level in prices
        if float(current["high"]) >= level >= float(current["low"])
    ]
    if not tapped:
        return None
    trigger_level = min(tapped, key=lambda level: abs(level - float(current["open"])))
    if call == "buy" and current["close"] > trigger_level and previous["close"] <= trigger_level:
        direction = Direction.BUY
        stop = float(current["low"])
        target = facts.previous_day.equilibrium
    elif call == "sell" and current["close"] < trigger_level and previous["close"] >= trigger_level:
        direction = Direction.SELL
        stop = float(current["high"])
        target = facts.previous_day.equilibrium
    else:
        return None
    if direction == Direction.BUY and facts.asia.low is not None and current["close"] < facts.asia.low:
        return None
    if direction == Direction.SELL and facts.previous_day.equilibrium is not None:
        below_eq = current["close"] < facts.previous_day.equilibrium
        if below_eq and not bool(settings.get("sell_drive_confirmed", False)):
            return None
    if facts.current_time.weekday() == 4 and bool(settings.get("skip_friday", True)):
        return None
    return make_signal(
        name="cracker",
        variant="call_based",
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=settings,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=60,
        default_target=60,
        default_distance_unit=instrument_default_distance_unit(instrument_spec),
        time_limit_seconds=(
            None if bool(settings.get("extended_edition", False))
            else int(settings.get("exit_after_seconds", 90))
        ),
    )