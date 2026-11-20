"""Opening-range breakout (ORB) and Pre-ORB strategy."""

from datetime import timedelta
from typing import Dict, List, Optional

import pandas as pd

from broker.instrument_specs import DistanceUnit, InstrumentSpec, get_instrument_spec
from engine.models import Direction, Signal
from strategies.base import BarContext
from strategies.common import (
    instrument_default_distance_unit,
    make_signal,
    opening_range,
)
from strategies.context import MarketFacts, build_market_facts


VARIANTS = {
    "orb_30m": 30,
    "orb_15m": 15,
    "orb_5m": 5,
    "orb_2m": 2,
    "pre_orb_15m": 15,
}


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "orb_15m",
) -> Optional[Signal]:
    """Evaluate Opening Range Breakout (ORB) trigger on completed candles.

    Supports variants based on range duration:
    - 'orb_30m', 'orb_15m', 'orb_5m', 'orb_2m', 'pre_orb_15m'
    """
    if variant not in VARIANTS:
        raise ValueError(f"Unknown ORB variant: {variant}.")

    if len(candles) < 2:
        return None

    settings = parameters or {}
    duration = int(settings.get("range_minutes", VARIANTS[variant]))
    session_name = str(settings.get("opening_session", facts.session.name))

    levels = opening_range(
        candles,
        timeframe=facts.timeframe,
        current_time=facts.current_time,
        session_name=session_name,
        range_minutes=duration,
    )
    if levels is None:
        return None

    range_high, range_low = levels
    box_range = range_high - range_low
    if box_range <= 0:
        return None

    unit = str(settings.get("range_size_unit", instrument_default_distance_unit(instrument_spec)))
    max_range_units = float(settings.get("maximum_range_units", 100.0))
    # 100-pip range rule: if range >= 100 pips, mentor switches to Intra-Range fade
    if bool(settings.get("skip_if_range_exceeds_max", True)):
        max_dist = instrument_spec.price_distance(max_range_units, unit)  # type: ignore[arg-type]
        if box_range >= max_dist:
            return None

    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    c_close = float(current["close"])
    p_close = float(previous["close"])

    # Breakout condition: candle closes outside box
    if c_close > range_high and p_close <= range_high:
        direction = Direction.BUY
        structural_stop = range_low
        structural_target = facts.previous_day.pivots.get("R1") or (range_high + box_range)
    elif c_close < range_low and p_close >= range_low:
        direction = Direction.SELL
        structural_stop = range_high
        structural_target = facts.previous_day.pivots.get("S1") or (range_low - box_range)
    else:
        return None

    # Optional 200 EMA filter (confirmed in transcript that mentor uses NO 200 EMA by default)
    if bool(settings.get("use_200_ema_filter", False)) and facts.ema_200 is not None:
        if direction == Direction.BUY and c_close < facts.ema_200:
            return None
        if direction == Direction.SELL and c_close > facts.ema_200:
            return None

    # Default stop & target
    default_stop_val = float(settings.get("fixed_stop", 40.0))
    default_target_val = float(settings.get("fixed_target", 120.0))

    return make_signal(
        name="orb",
        variant=variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=settings,
        structural_stop_price=structural_stop,
        structural_target_price=structural_target,
        default_stop=default_stop_val,
        default_target=default_target_val,
        default_distance_unit=unit,  # type: ignore[arg-type]
    )


class OrbStrategy:
    """Strategy class implementing the Strategy protocol for the simulator."""

    def __init__(
        self,
        timeframe: str = "M5",
        symbols: Optional[List[str]] = None,
        variant: str = "orb_15m",
        parameters: Optional[Dict[str, object]] = None,
    ) -> None:
        self.name = "orb"
        self.timeframe = timeframe.upper()
        self.symbols = symbols or ["US30", "NAS100", "EURUSD", "XAUUSD", "DAX"]
        self.variant = variant
        self.parameters = parameters or {}

    def on_bar(self, ctx: BarContext) -> Optional[Signal]:
        spec = get_instrument_spec(ctx.symbol)
        facts = build_market_facts(ctx.df, self.timeframe, ctx.current_time, spec)
        return evaluate(
            candles=ctx.df,
            facts=facts,
            instrument_spec=spec,
            parameters=self.parameters,
            variant=self.variant,
        )
