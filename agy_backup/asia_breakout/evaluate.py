"""Asia range breakout continuation, including the OI-OI variant."""

from typing import Dict, List, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction, Signal
from knowledge.operational_definitions import level_holds, volume_present
from strategies.base import BarContext
from strategies.common import make_signal
from strategies.context import MarketFacts, build_market_facts


VARIANTS = ("close_and_volume", "retest", "oi_oi")


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "close_and_volume",
) -> Optional[Signal]:
    """Evaluate Asia breakout continuation strategy on completed candles.

    Supports three master-file variants:
    - 'close_and_volume': candle closes outside Asia range with volume present
    - 'retest': candle breaks out, retests the broken boundary and holds as support/resistance
    - 'oi_oi': outside-inside-outside (candle 1 outside, candle 2 inside, candle 3 outside)
    """
    settings = parameters or {}
    selected_variant = str(settings.get("variant", variant))
    if selected_variant not in VARIANTS:
        raise ValueError(f"Unknown Asia breakout variant: {selected_variant}.")

    min_candles = int(settings.get("minimum_candles", 3))
    if len(candles) < min_candles or facts.average_candle_size is None:
        return None

    # Pre-trade filter: Asia session must be complete and levels marked
    if not facts.asia.session_complete or facts.asia.high is None or facts.asia.low is None:
        return None

    # Session filter: London and New York sessions by default, rejects mid-Asia
    allowed_sessions = settings.get("allowed_sessions", ("London", "New York"))
    if allowed_sessions is not None and facts.session.name not in allowed_sessions:
        return None
    if facts.session.name == "Asia":
        return None

    asia_high = float(facts.asia.high)
    asia_low = float(facts.asia.low)
    acs = float(facts.average_candle_size)
    if acs <= 0:
        return None

    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    current_close = float(current["close"])
    prev_close = float(previous["close"])

    # Kill rule: breakout candle closing back inside the Asia range cancels immediately
    if selected_variant == "close_and_volume":
        if asia_low <= current_close <= asia_high:
            return None

    bullish = False
    bearish = False
    structural_stop = 0.0

    if selected_variant == "oi_oi":
        if len(candles) < 3:
            return None
        before_previous = candles.iloc[-3]
        bp_close = float(before_previous["close"])
        bullish = (
            bp_close > asia_high
            and prev_close <= asia_high
            and current_close > asia_high
        )
        bearish = (
            bp_close < asia_low
            and prev_close >= asia_low
            and current_close < asia_low
        )
        structural_stop = (
            float(candles.tail(3)["low"].min())
            if bullish
            else float(candles.tail(3)["high"].max())
        )

    elif selected_variant == "retest":
        # Candle prior closed outside, current retested and holds
        retest_wick_tol = float(settings.get("retest_tolerance_acs", 0.25))
        hold_count = int(settings.get("hold_candles", 1))
        bullish = (
            prev_close > asia_high
            and float(current["low"]) <= asia_high + retest_wick_tol * acs
            and current_close > asia_high
            and level_holds(
                candles.tail(hold_count + 1),
                asia_high,
                "bullish",
                acs,
                hold_candles=hold_count,
                wick_tolerance_acs=retest_wick_tol,
            )
        )
        bearish = (
            prev_close < asia_low
            and float(current["high"]) >= asia_low - retest_wick_tol * acs
            and current_close < asia_low
            and level_holds(
                candles.tail(hold_count + 1),
                asia_low,
                "bearish",
                acs,
                hold_candles=hold_count,
                wick_tolerance_acs=retest_wick_tol,
            )
        )
        structural_stop = (
            float(current["low"]) if bullish else float(current["high"])
        )

    else:  # close_and_volume
        bullish = prev_close <= asia_high and current_close > asia_high
        bearish = prev_close >= asia_low and current_close < asia_low
        structural_stop = (
            float(current["low"]) if bullish else float(current["high"])
        )

    if bullish == bearish:
        return None

    direction = Direction.BUY if bullish else Direction.SELL

    # Volume filter: what counts as "with volume" (Section 11.2)
    require_volume = bool(settings.get("require_volume", True))
    if require_volume:
        vol_multiple = float(settings.get("volume_range_multiple", 1.5))
        vol_body_frac = float(settings.get("volume_body_fraction", 0.6))
        if not volume_present(
            current,
            acs,
            range_multiple=vol_multiple,
            minimum_body_fraction=vol_body_frac,
        ):
            return None

    # Target selection: Daily R1/R2, previous daily high/low, or ADR (Section 3.3)
    target_choice = str(settings.get("target_choice", "pivot_r1_s1")).lower()
    structural_target: Optional[float] = None
    if direction == Direction.BUY:
        if target_choice in ("pivot_r2", "r2"):
            structural_target = facts.previous_day.pivots.get("R2")
        elif target_choice in ("previous_day", "previous_day_high", "pdh"):
            structural_target = facts.previous_day.high
        else:  # default pivot_r1_s1
            structural_target = facts.previous_day.pivots.get("R1")
    else:
        if target_choice in ("pivot_s2", "s2"):
            structural_target = facts.previous_day.pivots.get("S2")
        elif target_choice in ("previous_day", "previous_day_low", "pdl"):
            structural_target = facts.previous_day.low
        else:  # default pivot_r1_s1
            structural_target = facts.previous_day.pivots.get("S1")

    # Default stop pips/points by instrument: Gold 50/100, others 30
    is_gold = instrument_spec.symbol.upper() in ("XAUUSD", "GOLD")
    default_stop_val = float(settings.get("fixed_stop", 50.0 if is_gold else 30.0))
    default_target_val = float(settings.get("fixed_target", 100.0 if is_gold else 60.0))

    return make_signal(
        name="asia_breakout",
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
        default_distance_unit=settings.get(
            "distance_unit",
            "points" if instrument_spec.point_size else "pips",
        ),
    )


class AsiaBreakoutStrategy:
    """Strategy class implementing the Strategy protocol for the simulator."""

    def __init__(
        self,
        timeframe: str = "M5",
        symbols: Optional[List[str]] = None,
        variant: str = "close_and_volume",
        parameters: Optional[Dict[str, object]] = None,
    ) -> None:
        self.name = "asia_breakout"
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
