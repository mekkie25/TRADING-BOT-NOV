"""Opening-range breakout and Pre-ORB configurations (spec Section 3.4).

The box is the opening range of the chosen session. A candle that closes
outside the box starts the trade (no retest needed). This module only reports
a signal; it never places orders.

What lives here (Section 3.4):
  * Box length variants (30m, 15m, 5m, 2m, Pre-ORB 15m).
  * Breakout close above or below the box, optionally needing two closes.
  * Stop just beyond the opposite box edge (structural stop).
  * Kill rule helper: breakout_killed().
  * Two-bullet rule: the caller says which bullet this is.
  * Optional range cap: a wide box is for the Intra-Range fade (3.10) instead.

What is NOT here, on purpose:
  * SuperTrend stop and trailing exit: the spec leaves the ATR period open
    ([GAP]) and trailing belongs to trade management (Step 5).
  * Max two trades and stop-for-the-day: risk and trade-limit rules (Step 3).
"""

from typing import Dict, Optional, Tuple

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from strategies.common import instrument_default_distance_unit, make_signal, opening_range
from strategies.context import MarketFacts


VARIANTS = {"orb_30m": 30, "orb_15m": 15, "orb_5m": 5, "orb_2m": 2, "pre_orb_15m": 15}


def _check_variant(variant: str) -> None:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown ORB variant: {variant}.")


def _box(
    candles: pd.DataFrame,
    timeframe: str,
    facts: MarketFacts,
    variant: str,
    settings: Dict[str, object],
) -> Optional[Tuple[float, float]]:
    duration = int(settings.get("range_minutes", VARIANTS[variant]))
    return opening_range(
        candles,
        timeframe,
        facts.current_time,
        str(settings.get("opening_session", facts.session.name)),
        duration,
    )


def _whole_number(settings: Dict[str, object], key: str, default: int) -> int:
    value = settings.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{key} must be a whole number of 1 or more.")
    return value


def evaluate(
    candles: pd.DataFrame,
    timeframe: str,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "orb_15m",
) -> Optional[Signal]:
    _check_variant(variant)
    settings = parameters or {}

    # Two-bullet rule (spec 3.4 item 5). The caller tracks the trades.
    bullet_number = _whole_number(settings, "bullet_number", 1)
    first_direction = settings.get("first_trade_direction")
    if bullet_number == 2 and not isinstance(first_direction, Direction):
        raise ValueError(
            "bullet_number 2 needs first_trade_direction (Direction.BUY or Direction.SELL)."
        )
    if bullet_number > 2:
        return None

    confirmation = _whole_number(settings, "confirmation_candles", 1)

    levels = _box(candles, timeframe, facts, variant, settings)
    if levels is None:
        return None
    range_high, range_low = levels

    # Optional range cap. A wide box is the Intra-Range fade (3.10) instead.
    max_range = settings.get("max_range")
    if max_range is not None:
        unit = str(settings.get("max_range_unit", instrument_default_distance_unit(instrument_spec)))
        cap = instrument_spec.price_distance(float(max_range), unit)  # type: ignore[arg-type]
        if (range_high - range_low) >= cap:
            return None

    if len(candles) < confirmation + 1:
        return None
    recent_closes = candles["close"].iloc[-confirmation:]
    close_before = float(candles.iloc[-(confirmation + 1)]["close"])

    if bool((recent_closes > range_high).all()) and close_before <= range_high:
        direction = Direction.BUY
        stop = range_low
        target = None
    elif bool((recent_closes < range_low).all()) and close_before >= range_low:
        direction = Direction.SELL
        stop = range_high
        target = None
    else:
        return None

    # Bullet two is only taken on a breakout to the opposite side.
    if bullet_number == 2 and direction == first_direction:
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


def breakout_killed(
    candles: pd.DataFrame,
    timeframe: str,
    facts: MarketFacts,
    direction: Direction,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "orb_15m",
) -> bool:
    """Kill rule (spec 3.4 item 4): True if the latest candle closed back inside the box.

    The simulator or trade manager calls this after the trade is open.
    """
    _check_variant(variant)
    if direction not in (Direction.BUY, Direction.SELL):
        raise ValueError("direction must be Direction.BUY or Direction.SELL.")
    if len(candles) == 0:
        return False
    levels = _box(candles, timeframe, facts, variant, parameters or {})
    if levels is None:
        return False
    range_high, range_low = levels
    last_close = float(candles.iloc[-1]["close"])
    if direction == Direction.BUY:
        return last_close <= range_high
    return last_close >= range_low