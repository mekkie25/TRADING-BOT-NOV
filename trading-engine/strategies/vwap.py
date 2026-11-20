"""Conditional VWAP rejection and break/retest variants."""

from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from indicators.anchored_vwap import calculate_anchored_vwap
from strategies.common import instrument_default_distance_unit, make_signal
from strategies.context import MarketFacts


VARIANTS = ("mean_reversion", "break_and_retest")


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "break_and_retest",
) -> Optional[Signal]:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown VWAP variant: {variant}.")
    volume_column = next(
        (name for name in ("tick_volume", "volume") if name in candles.columns),
        None,
    )
    if volume_column is None or len(candles) < 3:
        return None
    volumes = pd.to_numeric(candles[volume_column], errors="coerce")
    prices = (candles["high"] + candles["low"] + candles["close"]) / 3.0
    if volumes.isna().any() or (volumes < 0).any() or volumes.sum() <= 0:
        return None
    anchor_index = int((parameters or {}).get("anchor_index", 0))
    if anchor_index < 0 or anchor_index >= len(candles):
        raise ValueError("anchor_index is outside the supplied candle history.")
    vwap = calculate_anchored_vwap(
        prices.iloc[anchor_index:].tolist(),
        volumes.iloc[anchor_index:].tolist(),
    )
    previous = candles.iloc[-2]
    current = candles.iloc[-1]
    if variant == "mean_reversion":
        if current["low"] <= vwap and current["close"] > vwap:
            direction, stop, target = Direction.BUY, float(current["low"]), vwap
        elif current["high"] >= vwap and current["close"] < vwap:
            direction, stop, target = Direction.SELL, float(current["high"]), vwap
        else:
            return None
    else:
        if previous["close"] > vwap and current["low"] <= vwap and current["close"] > vwap:
            direction, stop = Direction.BUY, float(current["low"])
            target = facts.previous_day.pivots.get("R1")
        elif previous["close"] < vwap and current["high"] >= vwap and current["close"] < vwap:
            direction, stop = Direction.SELL, float(current["high"])
            target = facts.previous_day.pivots.get("S1")
        else:
            return None
    return make_signal(
        name="vwap",
        variant=variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=parameters,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=47,
        default_target=47,
        default_distance_unit=instrument_default_distance_unit(instrument_spec),
        conditional=True,
    )
