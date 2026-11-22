"""Intra-Range: fade of a large opening range (spec Section 3.10), separate from ORB.

Pre-trade: the opening range must be at least minimum_range_size (default 100,
in the instrument's own units). A smaller range is the ORB breakout (3.4) instead.

Entry variants (the signal fires on the close of the last candle, never a pending order):
  * poke_then_reject (default, the spec read literally): one candle breaks out of
    the range but closes back inside; the next candle tests the same edge and is
    rejected (wick rejection, Section 11.4), closing inside the range.
  * range_fade (the older version): one candle closes outside the range and the
    next candle closes back inside after touching the edge.

Target: the other side of the range [spec]. Stop: the spec does NOT state one
([GAP]). The default here is an assumption: just beyond the extreme of the
candles that made the setup. Fixed and volatility-scaled stops and targets stay
selectable with sl_mode and tp_mode (AGENTS.md rule 11). The fixed 40 and 100
numbers are placeholders, not from the spec.

What is NOT here, on purpose:
  * Trade management and trade limits: Step 5 and Step 4.
"""

from typing import Dict, Optional, Tuple

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from knowledge.operational_definitions import wick_rejection
from strategies.common import instrument_default_distance_unit, make_signal, opening_range
from strategies.context import MarketFacts


VARIANTS = ("poke_then_reject", "range_fade")


def _poke_then_reject(
    previous: pd.Series,
    current: pd.Series,
    range_high: float,
    range_low: float,
    settings: Dict[str, object],
) -> Optional[Tuple[Direction, float, float]]:
    """Spec 3.10 read literally: a candle pokes out and closes back inside, the next one rejects the edge."""
    fraction = float(settings.get("rejection_wick_fraction", 0.5))
    previous_back_inside = range_low < previous["close"] < range_high
    current_inside = range_low < current["close"] < range_high
    if (
        previous["high"] > range_high
        and previous_back_inside
        and current_inside
        and wick_rejection(current, range_high, "bearish", fraction)
    ):
        return Direction.SELL, max(float(previous["high"]), float(current["high"])), range_low
    if (
        previous["low"] < range_low
        and previous_back_inside
        and current_inside
        and wick_rejection(current, range_low, "bullish", fraction)
    ):
        return Direction.BUY, min(float(previous["low"]), float(current["low"])), range_high
    return None


def evaluate(
    candles: pd.DataFrame,
    timeframe: str,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "poke_then_reject",
) -> Optional[Signal]:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown Intra-Range variant: {variant}.")
    if len(candles) < 2:
        return None
    # Spec target is the other side of the range; the stop is an assumption (see docstring).
    settings = dict(parameters or {})
    settings.setdefault("sl_mode", "structural")
    settings.setdefault("tp_mode", "structural")
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
    if variant == "poke_then_reject":
        setup = _poke_then_reject(previous, current, range_high, range_low, settings)
        if setup is None:
            return None
        direction, stop, target = setup
        rejected = True
    elif previous["close"] > range_high and range_low < current["close"] < range_high:
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
        variant=variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=settings,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=40,
        default_target=100,
        default_distance_unit=unit,  # type: ignore[arg-type]
    )