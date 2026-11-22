"""Section 3.13 Value Area strategy: Value-area fade and breakout/retest variants."""

from typing import Dict, List, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction, Signal
from strategies.base import BarContext
from strategies.common import instrument_default_distance_unit, make_signal
from strategies.context import MarketFacts, build_market_facts


VARIANTS = ("fade", "breakout_retest")


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "fade",
) -> Optional[Signal]:
    """Evaluate Section 3.13 Value Area strategy on completed candles.

    Supports two variants:
    - 'fade': price tests VAH/VAL outer boundary and rejects back toward POC / opposite edge
    - 'breakout_retest': price breaks through VAH/VAL, retests the boundary, and continues
    """
    settings = dict(parameters or {})
    selected_variant = str(settings.get("variant", variant))
    if selected_variant not in VARIANTS:
        raise ValueError(f"Unknown value-area variant: {selected_variant}.")

    profile = facts.volume_profile
    if profile.poc is None or profile.vah is None or profile.val is None or len(candles) < 2:
        return None

    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    c_open = float(current["open"])
    c_high = float(current["high"])
    c_low = float(current["low"])
    c_close = float(current["close"])
    p_close = float(previous["close"])

    poc = float(profile.poc)
    vah = float(profile.vah)
    val = float(profile.val)
    bin_size = float(profile.bin_size or 0.0)

    # Filter: if price is already sitting right at the POC magnet, do not enter
    if val <= c_close <= vah and abs(c_close - poc) <= (bin_size / 2.0):
        return None

    direction: Optional[Direction] = None
    structural_stop: float = 0.0
    structural_target: Optional[float] = None
    target_choice = str(settings.get("target_choice", "poc")).lower()

    if selected_variant == "fade":
        # Bullish fade from VAL rejection -> BUY toward POC
        if c_low <= val and c_close > val:
            direction = Direction.BUY
            structural_stop = c_low
            if target_choice in ("opposite", "opposite_edge", "vah"):
                structural_target = vah
            else:  # default to POC
                structural_target = poc

        # Bearish fade from VAH rejection -> SELL toward POC
        elif c_high >= vah and c_close < vah:
            direction = Direction.SELL
            structural_stop = c_high
            if target_choice in ("opposite", "opposite_edge", "val"):
                structural_target = val
            else:  # default to POC
                structural_target = poc

    elif selected_variant == "breakout_retest":
        # Bullish breakout above VAH, retested and held -> BUY toward R1
        if p_close > vah and c_low <= vah and c_close > vah:
            direction = Direction.BUY
            structural_stop = c_low
            if target_choice in ("r2", "pivot_r2"):
                structural_target = facts.previous_day.pivots.get("R2")
            else:
                structural_target = facts.previous_day.pivots.get("R1")

        # Bearish breakout below VAL, retested and held -> SELL toward S1
        elif p_close < val and c_high >= val and c_close < val:
            direction = Direction.SELL
            structural_stop = c_high
            if target_choice in ("s2", "pivot_s2"):
                structural_target = facts.previous_day.pivots.get("S2")
            else:
                structural_target = facts.previous_day.pivots.get("S1")

    if direction is None:
        return None

    unit = str(settings.get("distance_unit", instrument_default_distance_unit(instrument_spec)))
    default_stop_val = float(settings.get("fixed_stop", 30.0))
    default_target_val = float(settings.get("fixed_target", 60.0))

    return make_signal(
        name="value_area",
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
        conditional=bool(settings.get("conditional", False)),
    )


class ValueAreaStrategy:
    """Strategy class implementing the Strategy protocol for the simulator."""

    def __init__(
        self,
        timeframe: str = "M5",
        symbols: Optional[List[str]] = None,
        variant: str = "fade",
        parameters: Optional[Dict[str, object]] = None,
    ) -> None:
        self.name = "value_area"
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