"""OES (spec Sections 3.7 and 3.8). EXPERIMENTAL: the entry criteria are unverified.

OES is a members-only system and the mentor never names its two entry
criteria. The 5-minute version below (spec 3.7 version A) comes from summary
files, not from a mentor's explanation, so it is switched OFF by default. Turn
it on with parameters {"enabled": True}. Nothing here has been backtested.

oes_5m (version A, the opening 5-minute candle fade):
  1. Mark the high and low of the first 5-minute candle after the session open.
  2. The first side to CLOSE beyond that candle is the break.
  3. A later candle closes back inside the box. The signal fires on that close
     and trades the opposite way: a failed break of the high is a sell, a failed
     break of the low is a buy.
The spec says "whichever side breaks first, trade the opposite" and does not say
whether to wait for the failed break. Waiting for the close back inside is an
assumption. There are no pending orders (AGENTS.md rule 10).

Stop and target defaults follow the spec as starting values: fixed 50 stop and
fixed 100 target (1:2). Gold mentors use 52 to 54 for spread: set fixed_stop.
Structural and volatility-scaled modes stay selectable (AGENTS.md rule 11). The
structural stop is beyond the extreme of the failed break, and the structural
target is the previous-day pivot S1 (sell) or R1 (buy), both assumptions.

What is NOT here, on purpose:
  * The 4-hour and inverse 4-hour OES variants: the spec gives no entry for them.
  * Version B (3.8, 4H zone continuation): the spec calls it a partial hint.
  * Version C (the "three boxes"): the spec says it cannot be coded.
  * The cancel rules "volume stalls and candles overlap" and the session window
    length: the spec gives no numbers. Use max_minutes_after_open to cap how late
    the first break may come.
  * Break-even at 80% and trade management.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from knowledge.strategy_sessions import NEW_YORK, SAST, StrategySessionConfig
from strategies.common import instrument_default_distance_unit, make_signal, opening_range
from strategies.context import MarketFacts


@dataclass(frozen=True)
class OESStubStatus:
    strategy_name: str
    variant: str
    enabled_by_default: bool
    status: str
    parameters: Dict[str, object]


OES_STUBS = {
    "oes_5m": OESStubStatus(
        "oes",
        "5m",
        False,
        "EXPERIMENTAL_UNVERIFIED_CRITERIA",
        {"enabled": False, "stop_mode": "fixed|volatility_scaled|structural", "stop_value": 50},
    ),
    "oes_4h": OESStubStatus(
        "oes",
        "4h",
        False,
        "BLOCKED_UNDISCLOSED_ENTRY_CRITERIA",
        {"wait_for_closed_4h_candle": True, "stop_mode": "configurable"},
    ),
    "oes_inverse_4h": OESStubStatus(
        "oes",
        "inverse_4h",
        False,
        "BLOCKED_UNDISCLOSED_ENTRY_CRITERIA",
        {"wait_for_closed_4h_candle": True, "stop_mode": "configurable"},
    ),
}


def _session_start_utc(current_time: datetime, session_name: str) -> Optional[datetime]:
    """Session open in UTC, using the same clocks as strategies.common.opening_range."""
    config = StrategySessionConfig()
    if session_name == "London":
        zone, clock = SAST, config.london_start
    elif session_name == "New York":
        zone, clock = NEW_YORK, config.new_york_open
    elif session_name == "Asia":
        zone, clock = SAST, config.asia_start
    else:
        return None
    local = current_time.astimezone(zone)
    return datetime.combine(local.date(), clock, tzinfo=zone).astimezone(timezone.utc)


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "oes_5m",
) -> Optional[Signal]:
    if variant not in OES_STUBS:
        raise ValueError(f"Unknown OES variant: {variant}.")
    if variant != "oes_5m":
        return None  # the 4-hour variants stay blocked
    settings = dict(parameters or {})
    if not bool(settings.get("enabled", False)):
        return None  # experimental: off unless asked for
    settings.setdefault("sl_mode", "fixed")
    settings.setdefault("tp_mode", "fixed")

    session_name = str(settings.get("opening_session", facts.session.name))
    levels = opening_range(candles, facts.timeframe, facts.current_time, session_name, 5)
    start = _session_start_utc(facts.current_time, session_name)
    if levels is None or start is None:
        return None
    box_high, box_low = levels

    times = pd.to_datetime(candles["time"], utc=True, errors="coerce")
    after = candles.loc[(times >= pd.Timestamp(start + timedelta(minutes=5))).to_numpy()]
    if len(after) < 2:
        return None
    closes = after["close"].astype(float).to_numpy()
    outside = (closes > box_high) | (closes < box_low)
    if not outside.any():
        return None
    first = int(outside.argmax())
    sequence = after.iloc[first:]
    if len(sequence) < 2:
        return None

    window = settings.get("max_minutes_after_open")
    if window is not None:
        first_time = pd.to_datetime(sequence.iloc[0]["time"], utc=True)
        if first_time > pd.Timestamp(start + timedelta(minutes=float(window))):
            return None

    sequence_closes = closes[first:]
    prior, last_close = sequence_closes[:-1], float(sequence_closes[-1])
    previous = facts.previous_day
    pivots = previous.pivots if previous is not None else {}
    if closes[first] > box_high:
        # Failed break of the high: every close since the break stayed above, now back inside.
        if not (bool((prior > box_high).all()) and box_low < last_close < box_high):
            return None
        direction = Direction.SELL
        stop = float(sequence["high"].max())
        target = pivots.get("S1")
    else:
        if not (bool((prior < box_low).all()) and box_low < last_close < box_high):
            return None
        direction = Direction.BUY
        stop = float(sequence["low"].min())
        target = pivots.get("R1")

    return make_signal(
        name="oes",
        variant="oes_5m",
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=settings,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=50,
        default_target=100,
        default_distance_unit=instrument_default_distance_unit(instrument_spec),
    )