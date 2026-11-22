"""Power Ranger: opening-range breakout, retest, then a confirming close (spec Section 3.5).

Steps (all on completed candles, never a pending order):
  1. Mark the high and low of the first 15 minutes of the session open
     (the Asia open works too: set opening_session to "Asia").
  2. A candle closes outside the range (the breakout).
  3. The next candle retests the broken edge and closes back in the breakout direction.
  4. The next candle closes beyond the retest candle's high (buy) or low (sell).
     The signal fires on that close. This module only reports a signal.

Defaults follow the spec: fixed 40 stop and 120 target (units depend on the
instrument). The older structural stop (retest candle extreme) and the previous
day R1/S1 target are still available: pass sl_mode "structural" and
tp_mode "structural".

What is NOT here, on purpose:
  * The spec's buy-stop / sell-stop entry above the retest high. Project rule:
    no pending orders, entries only on a confirmed candle close (AGENTS.md rule 10).
  * Red / Black Ranger variants (spec marks the rules as a gap).
  * News and "price not trapped in the box" pre-trade checks.
  * Max trades a day: risk and trade-limit rules (Step 4).
"""

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
    # Spec defaults: fixed stop and target. Callers can still choose another mode.
    settings = dict(parameters or {})
    settings.setdefault("sl_mode", "fixed")
    settings.setdefault("tp_mode", "fixed")
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
        parameters=settings,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=40,
        default_target=120,
        default_distance_unit=instrument_default_distance_unit(instrument_spec),
    )


def breakout_killed(
    candles: pd.DataFrame,
    timeframe: str,
    facts: MarketFacts,
    direction: Direction,
    parameters: Optional[Dict[str, object]] = None,
) -> bool:
    """Kill rule (spec 3.5): True if the latest candle closed back inside the range.

    The simulator or trade manager calls this after the trade is open.
    """
    if direction not in (Direction.BUY, Direction.SELL):
        raise ValueError("direction must be Direction.BUY or Direction.SELL.")
    if len(candles) == 0:
        return False
    settings = parameters or {}
    levels = opening_range(
        candles,
        timeframe,
        facts.current_time,
        str(settings.get("opening_session", facts.session.name)),
        int(settings.get("range_minutes", 15)),
    )
    if levels is None:
        return False
    range_high, range_low = levels
    last_close = float(candles.iloc[-1]["close"])
    if direction == Direction.BUY:
        return last_close <= range_high
    return last_close >= range_low