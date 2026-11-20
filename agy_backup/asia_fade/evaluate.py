"""Asia boundary sweep-and-fade strategy."""

from typing import Dict, List, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction, Signal
from knowledge.operational_definitions import close_back_rejection
from strategies.base import BarContext
from strategies.common import make_signal
from strategies.context import MarketFacts, build_market_facts


VARIANTS = ("sweep_reclaim", "second_candle_confirmation")


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "sweep_reclaim",
) -> Optional[Signal]:
    """Evaluate Asia sweep-and-fade strategy on completed candles.

    Supports two variants:
    - 'sweep_reclaim': enters on the candle closing back inside the Asia boundary
    - 'second_candle_confirmation': waits for a second candle holding/closing in fade direction
    """
    settings = parameters or {}
    selected_variant = str(settings.get("variant", variant))
    if selected_variant not in VARIANTS:
        raise ValueError(f"Unknown Asia Fade variant: {selected_variant}.")

    min_candles = int(settings.get("minimum_candles", 2))
    if len(candles) < min_candles or facts.average_candle_size is None:
        return None

    # Session filter: London and New York sessions by default
    allowed_sessions = settings.get("allowed_sessions", ("London", "New York"))
    if allowed_sessions is not None and facts.session.name not in allowed_sessions:
        return None

    if facts.asia.high is None or facts.asia.low is None:
        return None

    asia_high = float(facts.asia.high)
    asia_low = float(facts.asia.low)
    acs = float(facts.average_candle_size)
    if acs <= 0:
        return None

    # Pre-trade filter: skip if both Asia extremes already taken and price is in the middle
    current_close = float(candles.iloc[-1]["close"])
    if asia_low < current_close < asia_high:
        if bool(settings.get("skip_if_both_extremes_taken", True)):
            high_taken = bool((candles["high"] > asia_high).any())
            low_taken = bool((candles["low"] < asia_low).any())
            if high_taken and low_taken:
                return None

    window_candles = int(settings.get("rejection_window_candles", 2))
    min_sweep = float(settings.get("sweep_minimum_acs", 0.1))
    max_sweep = float(settings.get("sweep_maximum_acs", 2.0))
    require_solid_body = bool(settings.get("require_solid_body", False))
    min_body_fraction = float(settings.get("minimum_body_fraction", 0.5))
    target_choice = str(settings.get("target_choice", "eq")).lower()

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

    # If both swept in window or neither, skip
    if (bullish_sweep and bearish_sweep) or (not bullish_sweep and not bearish_sweep):
        return None

    current = candles.iloc[-1]
    previous = candles.iloc[-2]

    # Optional solid-body filter (NotebookLM variant)
    if require_solid_body:
        c_range = float(current["high"]) - float(current["low"])
        if c_range <= 0:
            return None
        body = abs(float(current["close"]) - float(current["open"]))
        if (body / c_range) < min_body_fraction:
            return None

    direction: Optional[Direction] = None
    structural_stop: float = 0.0
    structural_target: Optional[float] = None

    if bullish_sweep:
        # Bullish fade from Asia Low sweep -> Buy
        if selected_variant == "second_candle_confirmation":
            # Candle prior to current should have swept and current confirms
            if len(candles) < 3:
                return None
            sweep_prior = close_back_rejection(
                candles.iloc[-window_candles - 1 : -1],
                asia_low,
                "bullish",
                acs,
                minimum_sweep_acs=min_sweep,
                maximum_sweep_acs=max_sweep,
                window_candles=window_candles,
            )
            confirmed = sweep_prior and (float(current["close"]) > float(previous["close"])) and (float(current["close"]) > asia_low)
            if not confirmed:
                return None

        direction = Direction.BUY
        structural_stop = float(candles.tail(window_candles)["low"].min())
        if target_choice == "opposite_extreme":
            structural_target = asia_high
        elif target_choice == "pivot":
            structural_target = facts.previous_day.pivots.get("P") or asia_high
        else:  # default eq
            structural_target = facts.previous_day.equilibrium or asia_high

    elif bearish_sweep:
        # Bearish fade from Asia High sweep -> Sell
        if selected_variant == "second_candle_confirmation":
            if len(candles) < 3:
                return None
            sweep_prior = close_back_rejection(
                candles.iloc[-window_candles - 1 : -1],
                asia_high,
                "bearish",
                acs,
                minimum_sweep_acs=min_sweep,
                maximum_sweep_acs=max_sweep,
                window_candles=window_candles,
            )
            confirmed = sweep_prior and (float(current["close"]) < float(previous["close"])) and (float(current["close"]) < asia_high)
            if not confirmed:
                return None

        direction = Direction.SELL
        structural_stop = float(candles.tail(window_candles)["high"].max())
        if target_choice == "opposite_extreme":
            structural_target = asia_low
        elif target_choice == "pivot":
            structural_target = facts.previous_day.pivots.get("P") or asia_low
        else:  # default eq
            structural_target = facts.previous_day.equilibrium or asia_low

    if direction is None:
        return None

    return make_signal(
        name="asia_fade",
        variant=selected_variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=settings,
        structural_stop_price=structural_stop,
        structural_target_price=structural_target,
        default_stop=float(settings.get("fixed_stop", 30.0)),
        default_target=float(settings.get("fixed_target", 60.0)),
        default_distance_unit=settings.get(
            "distance_unit",
            "points" if instrument_spec.point_size else "pips",
        ),
    )


class AsiaFadeStrategy:
    """Strategy class implementing the Strategy protocol for the simulator."""

    def __init__(
        self,
        timeframe: str = "M5",
        symbols: Optional[List[str]] = None,
        variant: str = "sweep_reclaim",
        parameters: Optional[Dict[str, object]] = None,
    ) -> None:
        self.name = "asia_fade"
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
