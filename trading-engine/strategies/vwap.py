"""Section 3.14 VWAP strategy: Mean-reversion fade and break-and-retest variants."""

from typing import Dict, List, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction, Signal
from indicators.anchored_vwap import calculate_anchored_vwap
from strategies.base import BarContext
from strategies.common import instrument_default_distance_unit, make_signal
from strategies.context import MarketFacts, build_market_facts


VARIANTS = ("mean_reversion", "break_and_retest")


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "break_and_retest",
) -> Optional[Signal]:
    """Evaluate Section 3.14 VWAP strategy on completed candles.

    Supports two variants:
    - 'break_and_retest': candle breaks through VWAP, then retests and holds
    - 'mean_reversion': candle rejects away from extended levels back toward VWAP,
                        or rejects off VWAP
    """
    settings = dict(parameters or {})
    selected_variant = str(settings.get("variant", variant))
    if selected_variant not in VARIANTS:
        raise ValueError(f"Unknown VWAP variant: {selected_variant}.")

    if len(candles) < 3:
        return None

    volume_column = next(
        (name for name in ("tick_volume", "volume") if name in candles.columns),
        None,
    )
    if volume_column is None:
        return None

    volumes = pd.to_numeric(candles[volume_column], errors="coerce")
    prices = (candles["high"] + candles["low"] + candles["close"]) / 3.0
    if volumes.isna().any() or (volumes < 0).any() or volumes.sum() <= 0:
        return None

    anchor_index = int(settings.get("anchor_index", 0))
    if anchor_index < 0 or anchor_index >= len(candles):
        raise ValueError("anchor_index is outside the supplied candle history.")

    vwap = calculate_anchored_vwap(
        prices.iloc[anchor_index:].tolist(),
        volumes.iloc[anchor_index:].tolist(),
    )

    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    c_open = float(current["open"])
    c_high = float(current["high"])
    c_low = float(current["low"])
    c_close = float(current["close"])
    p_close = float(previous["close"])

    direction: Optional[Direction] = None
    stop: float = 0.0
    target: Optional[float] = None
    target_choice = str(settings.get("target_choice", "default")).lower()

    if selected_variant == "break_and_retest":
        # Bullish retest: previously closed above VWAP, current tested VWAP from above and held
        if p_close > vwap and c_low <= vwap and c_close > vwap:
            direction = Direction.BUY
            stop = c_low
            if target_choice in ("r2", "pivot_r2"):
                target = facts.previous_day.pivots.get("R2")
            else:
                target = facts.previous_day.pivots.get("R1")

        # Bearish retest: previously closed below VWAP, current tested VWAP from below and held
        elif p_close < vwap and c_high >= vwap and c_close < vwap:
            direction = Direction.SELL
            stop = c_high
            if target_choice in ("s2", "pivot_s2"):
                target = facts.previous_day.pivots.get("S2")
            else:
                target = facts.previous_day.pivots.get("S1")

    elif selected_variant == "mean_reversion":
        # Bullish mean-reversion toward VWAP from below
        if c_low < vwap and c_close < vwap and c_close > c_open:
            direction = Direction.BUY
            stop = c_low
            target = vwap

        # Bearish mean-reversion toward VWAP from above
        elif c_high > vwap and c_close > vwap and c_close < c_open:
            direction = Direction.SELL
            stop = c_high
            target = vwap

        # VWAP rejection bounce away from VWAP
        elif c_low <= vwap and c_close > vwap:
            direction = Direction.BUY
            stop = c_low
            target = facts.previous_day.pivots.get("R1")
        elif c_high >= vwap and c_close < vwap:
            direction = Direction.SELL
            stop = c_high
            target = facts.previous_day.pivots.get("S1")

    if direction is None:
        return None

    unit = str(settings.get("distance_unit", instrument_default_distance_unit(instrument_spec)))
    default_stop_val = float(settings.get("fixed_stop", 47.0))
    default_target_val = float(settings.get("fixed_target", 47.0))

    return make_signal(
        name="vwap",
        variant=selected_variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=settings,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=default_stop_val,
        default_target=default_target_val,
        default_distance_unit=unit,  # type: ignore[arg-type]
        conditional=bool(settings.get("conditional", True)),
    )


class VwapStrategy:
    """Strategy class implementing the Strategy protocol for the simulator."""

    def __init__(
        self,
        timeframe: str = "M5",
        symbols: Optional[List[str]] = None,
        variant: str = "break_and_retest",
        parameters: Optional[Dict[str, object]] = None,
    ) -> None:
        self.name = "vwap"
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