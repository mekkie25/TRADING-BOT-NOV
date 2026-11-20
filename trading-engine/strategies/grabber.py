"""Grabber and EQ variants, driven by an Asia-boundary sweep and EQ reaction."""

from typing import Dict, List, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction, Signal
from knowledge.operational_definitions import (
    chop_present,
    close_back_rejection,
    level_holds,
)
from strategies.base import BarContext
from strategies.common import make_signal
from strategies.context import MarketFacts, build_market_facts


VARIANTS = ("standard", "reverse_kick", "eq_confirmation")


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "standard",
) -> Optional[Signal]:
    """Evaluate Grabber strategy trigger on completed candles.

    Supports three master-file variants:
    - 'standard': sweep Asia extreme, close back inside, EQ holds -> enter in sweep bounce direction
    - 'reverse_kick': sweep Asia extreme, close back inside, price at EQ -> enter counter to sweep bounce
    - 'eq_confirmation': confirmation entry waiting for candle closing away from EQ
    """
    if variant not in VARIANTS:
        raise ValueError(f"Unknown Grabber variant: {variant}.")

    settings = parameters or {}
    min_candles = int(settings.get("minimum_candles", 3))
    if len(candles) < min_candles or facts.average_candle_size is None:
        return None

    # Session filter: London and New York by default, configurable
    allowed_sessions = settings.get("allowed_sessions", ("London", "New York"))
    if allowed_sessions is not None and facts.session.name not in allowed_sessions:
        return None

    asia_high = facts.asia.high
    asia_low = facts.asia.low
    if asia_high is None or asia_low is None:
        return None

    # EQ level: taken from facts.previous_day.equilibrium by default; Asia range EQ is an option
    eq_source = str(settings.get("eq_source", "previous_day")).lower()
    if eq_source == "asia":
        equilibrium = (asia_high + asia_low) / 2.0
    else:
        equilibrium = facts.previous_day.equilibrium

    if equilibrium is None:
        return None

    acs = facts.average_candle_size
    if acs <= 0:
        return None

    # Optional chop skip filter
    if bool(settings.get("skip_chop", False)):
        chop_count = int(settings.get("chop_candles", 5))
        if len(candles) >= chop_count and chop_present(candles, acs, candle_count=chop_count):
            return None

    window_candles = int(settings.get("rejection_window_candles", 3))
    min_sweep = float(settings.get("sweep_minimum_acs", 0.1))
    max_sweep = float(settings.get("sweep_maximum_acs", 2.0))

    # Detect sweep and close-back reclaim at Asia boundaries
    direction = (
        Direction.BUY
        if close_back_rejection(
            candles.tail(window_candles),
            asia_low,
            "bullish",
            acs,
            minimum_sweep_acs=min_sweep,
            maximum_sweep_acs=max_sweep,
            window_candles=window_candles,
        )
        else Direction.SELL
        if close_back_rejection(
            candles.tail(window_candles),
            asia_high,
            "bearish",
            acs,
            minimum_sweep_acs=min_sweep,
            maximum_sweep_acs=max_sweep,
            window_candles=window_candles,
        )
        else None
    )
    if direction is None:
        return None

    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    current_close = float(current["close"])
    current_low = float(current["low"])
    current_high = float(current["high"])
    prev_low = float(previous["low"])
    prev_high = float(previous["high"])

    # Kill rule: candle closing back outside the swept extreme
    if direction == Direction.BUY and current_close <= asia_low:
        return None
    if direction == Direction.SELL and current_close >= asia_high:
        return None

    touch_tol = float(settings.get("touch_distance_acs", 0.25)) * acs
    wick_tol = float(settings.get("hold_wick_tolerance_acs", 0.25))
    hold_count = int(settings.get("hold_candles", 1))

    if variant == "standard":
        if direction == Direction.BUY:
            confirmed = (
                current_close > equilibrium
                and (prev_low <= equilibrium + touch_tol or current_low <= equilibrium + touch_tol)
                and level_holds(
                    candles.tail(hold_count + 1),
                    equilibrium,
                    "bullish",
                    acs,
                    hold_candles=hold_count,
                    wick_tolerance_acs=wick_tol,
                )
            )
        else:
            confirmed = (
                current_close < equilibrium
                and (prev_high >= equilibrium - touch_tol or current_high >= equilibrium - touch_tol)
                and level_holds(
                    candles.tail(hold_count + 1),
                    equilibrium,
                    "bearish",
                    acs,
                    hold_candles=hold_count,
                    wick_tolerance_acs=wick_tol,
                )
            )
    elif variant == "reverse_kick":
        direction = Direction.SELL if direction == Direction.BUY else Direction.BUY
        # Price rallied/dropped toward EQ and is on the reverse side of EQ
        if direction == Direction.SELL:
            eq_tested = (prev_high >= equilibrium - touch_tol or current_high >= equilibrium - touch_tol)
            confirmed = eq_tested and (current_close < equilibrium)
        else:
            eq_tested = (prev_low <= equilibrium + touch_tol or current_low <= equilibrium + touch_tol)
            confirmed = eq_tested and (current_close > equilibrium)
    else:
        # eq_confirmation: waiting for confirming candle closing away from previous close
        confirmed = (
            current_close > float(previous["close"])
            if direction == Direction.BUY
            else current_close < float(previous["close"])
        )

    if not confirmed:
        return None

    sweep_extreme = (
        float(candles.tail(window_candles)["low"].min())
        if direction == Direction.BUY
        else float(candles.tail(window_candles)["high"].max())
    )

    # Target selection: default to Asia extreme, with previous daily high/low or pivots selectable
    target_choice = str(settings.get("target_choice", "asia_extreme")).lower()
    if direction == Direction.BUY:
        if target_choice in ("previous_day", "previous_day_extreme", "pdh", "previous_day_high"):
            target = facts.previous_day.high or asia_high
        elif target_choice == "pivot":
            target = facts.previous_day.pivots.get("R1") or asia_high
        else:  # default asia_extreme
            target = (
                asia_high
                if current_close < asia_high
                else (facts.previous_day.high or facts.previous_day.pivots.get("R1"))
            )
    else:
        if target_choice in ("previous_day", "previous_day_extreme", "pdl", "previous_day_low"):
            target = facts.previous_day.low or asia_low
        elif target_choice == "pivot":
            target = facts.previous_day.pivots.get("S1") or asia_low
        else:  # default asia_extreme
            target = (
                asia_low
                if current_close > asia_low
                else (facts.previous_day.low or facts.previous_day.pivots.get("S1"))
            )

    return make_signal(
        name="grabber",
        variant=variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=settings,
        structural_stop_price=sweep_extreme,
        structural_target_price=target,
        default_stop=float(settings.get("fixed_stop", 30.0)),
        default_target=float(settings.get("fixed_target", 60.0)),
        default_distance_unit=settings.get(
            "distance_unit",
            "points" if instrument_spec.point_size else "pips",
        ),
    )


class GrabberStrategy:
    """Strategy class implementing the Strategy protocol for the simulator."""

    def __init__(
        self,
        timeframe: str = "M5",
        symbols: Optional[List[str]] = None,
        variant: str = "standard",
        parameters: Optional[Dict[str, object]] = None,
    ) -> None:
        self.name = "grabber"
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
