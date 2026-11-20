"""Grabber and EQ variants, driven by an Asia-boundary sweep and EQ reaction."""

from typing import Dict, List, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction, Signal
from knowledge.operational_definitions import (
    chop_present,
    close_back_rejection,
    level_holds,
    wick_rejection,
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
    - 'reverse_kick': sweep Asia extreme, close back inside, rejects at EQ -> enter counter to sweep bounce
    - 'eq_confirmation': confirmation entry waiting for a candle closing away from EQ
    """
    if variant not in VARIANTS:
        raise ValueError(f"Unknown Grabber variant: {variant}.")

    settings = parameters or {}
    min_candles = int(settings.get("minimum_candles", 3))
    if len(candles) < min_candles or facts.average_candle_size is None:
        return None

    # Session filter: Grabber is traded during London and New York sessions
    allowed_sessions = settings.get("allowed_sessions", ("London", "New York"))
    if allowed_sessions is not None and facts.session.name not in allowed_sessions:
        return None

    # Required marked levels: Asia high/low and Previous-day EQ
    asia_high = facts.asia.high
    asia_low = facts.asia.low
    equilibrium = facts.previous_day.equilibrium
    if asia_high is None or asia_low is None or equilibrium is None:
        return None

    acs = facts.average_candle_size
    if acs <= 0:
        return None

    # Skip choppy directionless days if chop filter is requested
    if bool(settings.get("skip_chop", False)):
        chop_count = int(settings.get("chop_candles", 5))
        if len(candles) >= chop_count and chop_present(candles, acs, candle_count=chop_count):
            return None

    # Operational definition parameters
    window_candles = int(settings.get("rejection_window_candles", 4))
    min_sweep = float(settings.get("sweep_minimum_acs", 0.1))
    max_sweep = float(settings.get("sweep_maximum_acs", 2.0))
    touch_distance = float(settings.get("touch_distance_acs", 0.25)) * acs
    wick_tol = float(settings.get("hold_wick_tolerance_acs", 0.25))
    hold_count = int(settings.get("hold_candles", 1))

    # Check for Asia sweeps with closed-candle reclaim
    bullish_sweep = close_back_rejection(
        candles.tail(window_candles),
        asia_low,
        "bullish",
        acs,
        minimum_sweep_acs=min_sweep,
        maximum_sweep_acs=max_sweep,
        window_candles=window_candles,
    )
    bearish_sweep = close_back_rejection(
        candles.tail(window_candles),
        asia_high,
        "bearish",
        acs,
        minimum_sweep_acs=min_sweep,
        maximum_sweep_acs=max_sweep,
        window_candles=window_candles,
    )

    # If both extremes swept or neither, skip
    if bullish_sweep and bearish_sweep:
        return None
    if not bullish_sweep and not bearish_sweep:
        return None

    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    current_close = float(current["close"])
    current_low = float(current["low"])
    current_high = float(current["high"])
    prev_low = float(previous["low"])
    prev_high = float(previous["high"])

    # Kill rules: price closing back outside the swept extreme
    if bullish_sweep and current_close <= asia_low:
        return None
    if bearish_sweep and current_close >= asia_high:
        return None

    direction: Optional[Direction] = None
    confirmed = False
    sweep_extreme: float = 0.0
    structural_target: Optional[float] = None

    if bullish_sweep:
        # Initial reaction from Asia low sweep is upward toward EQ
        sweep_extreme = float(candles.tail(window_candles)["low"].min())
        eq_tested = (current_low <= equilibrium + touch_distance) or (prev_low <= equilibrium + touch_distance)

        if not eq_tested:
            return None

        if variant == "standard":
            # EQ holds as support -> Buy toward Asia High
            direction = Direction.BUY
            confirmed = (
                current_close >= equilibrium
                and level_holds(
                    candles.tail(hold_count + 1),
                    equilibrium,
                    "bullish",
                    acs,
                    hold_candles=hold_count,
                    wick_tolerance_acs=wick_tol,
                )
            )
            structural_target = (
                asia_high
                if current_close < asia_high
                else facts.previous_day.pivots.get("R1")
            )

        elif variant == "reverse_kick":
            # Rejects underneath EQ -> Short immediately back toward Asia Low
            direction = Direction.SELL
            # Current close underneath EQ and failed to hold above it
            under_eq = current_close <= equilibrium
            rejection = wick_rejection(current, equilibrium, "bearish", minimum_wick_fraction=0.4) or (
                current_high >= equilibrium - touch_distance and under_eq
            )
            confirmed = under_eq and rejection
            # Structural stop above EQ, target back to Asia low / S1
            sweep_extreme = max(current_high, float(previous["high"]))
            structural_target = (
                asia_low
                if current_close > asia_low
                else facts.previous_day.pivots.get("S1")
            )

        elif variant == "eq_confirmation":
            # Wait for confirming candle closing away from EQ to the upside
            direction = Direction.BUY
            confirmed = (
                current_close > equilibrium
                and current_close > float(previous["close"])
                and current_close > float(current["open"])
            )
            structural_target = (
                asia_high
                if current_close < asia_high
                else facts.previous_day.pivots.get("R1")
            )

    elif bearish_sweep:
        # Initial reaction from Asia high sweep is downward toward EQ
        sweep_extreme = float(candles.tail(window_candles)["high"].max())
        eq_tested = (current_high >= equilibrium - touch_distance) or (prev_high >= equilibrium - touch_distance)

        if not eq_tested:
            return None

        if variant == "standard":
            # EQ holds as resistance -> Sell toward Asia Low
            direction = Direction.SELL
            confirmed = (
                current_close <= equilibrium
                and level_holds(
                    candles.tail(hold_count + 1),
                    equilibrium,
                    "bearish",
                    acs,
                    hold_candles=hold_count,
                    wick_tolerance_acs=wick_tol,
                )
            )
            structural_target = (
                asia_low
                if current_close > asia_low
                else facts.previous_day.pivots.get("S1")
            )

        elif variant == "reverse_kick":
            # Rejects above EQ -> Buy immediately back toward Asia High
            direction = Direction.BUY
            above_eq = current_close >= equilibrium
            rejection = wick_rejection(current, equilibrium, "bullish", minimum_wick_fraction=0.4) or (
                current_low <= equilibrium + touch_distance and above_eq
            )
            confirmed = above_eq and rejection
            sweep_extreme = min(current_low, float(previous["low"]))
            structural_target = (
                asia_high
                if current_close < asia_high
                else facts.previous_day.pivots.get("R1")
            )

        elif variant == "eq_confirmation":
            # Wait for confirming candle closing away from EQ to the downside
            direction = Direction.SELL
            confirmed = (
                current_close < equilibrium
                and current_close < float(previous["close"])
                and current_close < float(current["open"])
            )
            structural_target = (
                asia_low
                if current_close > asia_low
                else facts.previous_day.pivots.get("S1")
            )

    if not confirmed or direction is None:
        return None

    return make_signal(
        name="grabber",
        variant=variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=settings,
        structural_stop_price=sweep_extreme,
        structural_target_price=structural_target,
        default_stop=float(settings.get("fixed_stop", 30.0)),
        default_target=float(settings.get("fixed_target", 60.0)),
        default_distance_unit=settings.get("distance_unit", "points" if instrument_spec.point_size else "pips"),
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
