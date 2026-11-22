"""Section 3.11 Reversal strategy: PDH/PDL sweeps, Session extreme sweeps, and engulfing reclaims."""

from typing import Dict, List, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction, Signal
from knowledge.operational_definitions import close_back_rejection
from strategies.base import BarContext
from strategies.common import instrument_default_distance_unit, make_signal
from strategies.context import MarketFacts, build_market_facts


VARIANTS = ("pdh_pdl", "session_extreme", "engulfing")


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "pdh_pdl",
) -> Optional[Signal]:
    """Evaluate Section 3.11 Reversal strategy on completed candles.

    Supports three variants:
    - 'pdh_pdl': sweep of Previous Day High (PDH) or Previous Day Low (PDL) and close back inside
    - 'session_extreme': sweep of Asia session High or Low and close back inside
    - 'engulfing': sweep of PDH/PDL or Session extreme confirmed by an engulfing reversal candle
    """
    settings = dict(parameters or {})
    selected_variant = str(settings.get("variant", variant))
    if selected_variant not in VARIANTS:
        raise ValueError(f"Unknown reversal variant: {selected_variant}.")

    min_candles = int(settings.get("minimum_candles", 2))
    if len(candles) < min_candles:
        return None

    # Session filter: London and New York sessions by default
    allowed_sessions = settings.get("allowed_sessions", ("London", "New York"))
    if allowed_sessions is not None and facts.session.name not in allowed_sessions:
        return None

    acs = facts.average_candle_size
    if acs is None or acs <= 0:
        return None

    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    c_open = float(current["open"])
    c_high = float(current["high"])
    c_low = float(current["low"])
    c_close = float(current["close"])
    p_open = float(previous["open"])
    p_close = float(previous["close"])

    window_candles = int(settings.get("rejection_window_candles", 2))
    min_sweep = float(settings.get("sweep_minimum_acs", 0.05))
    max_sweep = float(settings.get("sweep_maximum_acs", 2.0))

    level_high: Optional[float] = None
    level_low: Optional[float] = None

    if selected_variant == "pdh_pdl":
        level_high = facts.previous_day.high
        level_low = facts.previous_day.low
    elif selected_variant == "session_extreme":
        level_high = facts.asia.high
        level_low = facts.asia.low
    elif selected_variant == "engulfing":
        extreme_source = str(settings.get("extreme_source", "pdh_pdl")).lower()
        if extreme_source in ("asia", "session"):
            level_high = facts.asia.high
            level_low = facts.asia.low
        else:
            level_high = facts.previous_day.high
            level_low = facts.previous_day.low

    if level_high is None or level_low is None:
        return None

    bullish_sweep = False
    bearish_sweep = False

    if selected_variant in ("pdh_pdl", "session_extreme"):
        bullish_sweep = close_back_rejection(
            candles.tail(window_candles),
            level_low,
            "bullish",
            acs,
            minimum_sweep_acs=min_sweep,
            maximum_sweep_acs=max_sweep,
            window_candles=window_candles,
        )
        bearish_sweep = close_back_rejection(
            candles.tail(window_candles),
            level_high,
            "bearish",
            acs,
            minimum_sweep_acs=min_sweep,
            maximum_sweep_acs=max_sweep,
            window_candles=window_candles,
        )
    elif selected_variant == "engulfing":
        bullish_engulfing = (
            c_close > c_open
            and p_close < p_open
            and c_open <= p_close
            and c_close >= p_open
        )
        bearish_engulfing = (
            c_close < c_open
            and p_close > p_open
            and c_open >= p_close
            and c_close <= p_open
        )
        bullish_sweep = c_low < level_low and c_close > level_low and bullish_engulfing
        bearish_sweep = c_high > level_high and c_close < level_high and bearish_engulfing

    if bullish_sweep == bearish_sweep:
        return None

    direction = Direction.BUY if bullish_sweep else Direction.SELL

    # Structural stop sits beyond the extreme of the setup window
    structural_stop = (
        float(candles.tail(window_candles)["low"].min())
        if direction == Direction.BUY
        else float(candles.tail(window_candles)["high"].max())
    )

    # Target selection: equilibrium (default), opposite_extreme, or pivot
    target_choice = str(settings.get("target_choice", "eq")).lower()
    structural_target: Optional[float] = None
    if direction == Direction.BUY:
        if target_choice in ("opposite", "opposite_extreme"):
            structural_target = level_high
        elif target_choice == "pivot":
            structural_target = facts.previous_day.pivots.get("R1") or facts.previous_day.equilibrium
        else:
            structural_target = facts.previous_day.equilibrium or level_high
    else:
        if target_choice in ("opposite", "opposite_extreme"):
            structural_target = level_low
        elif target_choice == "pivot":
            structural_target = facts.previous_day.pivots.get("S1") or facts.previous_day.equilibrium
        else:
            structural_target = facts.previous_day.equilibrium or level_low

    unit = str(settings.get("distance_unit", instrument_default_distance_unit(instrument_spec)))
    default_stop_val = float(settings.get("fixed_stop", 30.0))
    default_target_val = float(settings.get("fixed_target", 60.0))

    return make_signal(
        name="reversal",
        variant=selected_variant,
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


class ReversalStrategy:
    """Strategy class implementing the Strategy protocol for the simulator."""

    def __init__(
        self,
        timeframe: str = "M5",
        symbols: Optional[List[str]] = None,
        variant: str = "pdh_pdl",
        parameters: Optional[Dict[str, object]] = None,
    ) -> None:
        self.name = "reversal"
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