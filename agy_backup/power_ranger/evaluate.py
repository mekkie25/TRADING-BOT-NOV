"""Power Ranger strategy: Opening-range breakout followed by confirming retest."""

from typing import Dict, List, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction, Signal
from strategies.base import BarContext
from strategies.common import (
    instrument_default_distance_unit,
    make_signal,
    opening_range,
)
from strategies.context import MarketFacts, build_market_facts


VARIANTS = ("15m_range_5m_retest",)


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "15m_range_5m_retest",
) -> Optional[Signal]:
    """Evaluate Power Ranger strategy on completed candles.

    1. Mark high and low of first 15 minutes of open (New York or Asia).
    2. Wait for 5M candle breakout outside the range.
    3. Next 5M candle retests the broken boundary and holds in breakout direction.
    4. Enters in the breakout continuation direction.
    """
    if len(candles) < 3:
        return None

    settings = parameters or {}
    duration = int(settings.get("range_minutes", 15))
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
    breakout = candles.iloc[-3]
    retest = candles.iloc[-2]
    confirmation = candles.iloc[-1]

    b_close = float(breakout["close"])
    r_low = float(retest["low"])
    r_high = float(retest["high"])
    r_close = float(retest["close"])
    c_close = float(confirmation["close"])

    if (
        b_close > range_high
        and r_low <= range_high
        and r_close > range_high
        and c_close > float(retest["high"])
    ):
        direction = Direction.BUY
        structural_stop = r_low
        structural_target = facts.previous_day.pivots.get("R1")
    elif (
        b_close < range_low
        and r_high >= range_low
        and r_close < range_low
        and c_close < float(retest["low"])
    ):
        direction = Direction.SELL
        structural_stop = r_high
        structural_target = facts.previous_day.pivots.get("S1")
    else:
        return None

    unit = str(settings.get("distance_unit", instrument_default_distance_unit(instrument_spec)))
    default_stop_val = float(settings.get("fixed_stop", 40.0))
    default_target_val = float(settings.get("fixed_target", 120.0))

    return make_signal(
        name="power_ranger",
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


class PowerRangerStrategy:
    """Strategy class implementing the Strategy protocol for the simulator."""

    def __init__(
        self,
        timeframe: str = "M5",
        symbols: Optional[List[str]] = None,
        variant: str = "15m_range_5m_retest",
        parameters: Optional[Dict[str, object]] = None,
    ) -> None:
        self.name = "power_ranger"
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
