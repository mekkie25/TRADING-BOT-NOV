"""Asia boundary sweep-and-fade strategy."""

from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from knowledge.operational_definitions import close_back_rejection
from strategies.common import make_signal
from strategies.context import MarketFacts


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
) -> Optional[Signal]:
    if len(candles) < 2 or facts.average_candle_size is None:
        return None
    if facts.session.name not in ("London", "New York"):
        return None
    if facts.asia.high is None or facts.asia.low is None:
        return None
    if facts.asia.high is not None and facts.asia.low is not None:
        if candles.iloc[-1]["close"] > facts.asia.low and candles.iloc[-1]["close"] < facts.asia.high:
            if bool((parameters or {}).get("skip_if_both_extremes_taken", True)):
                high_taken = bool((candles["high"] > facts.asia.high).any())
                low_taken = bool((candles["low"] < facts.asia.low).any())
                if high_taken and low_taken:
                    return None
    if close_back_rejection(
        candles.tail(int((parameters or {}).get("rejection_window_candles", 2))),
        facts.asia.low,
        "bullish",
        facts.average_candle_size,
        minimum_sweep_acs=float((parameters or {}).get("sweep_minimum_acs", 0.1)),
        maximum_sweep_acs=float((parameters or {}).get("sweep_maximum_acs", 2.0)),
        window_candles=int((parameters or {}).get("rejection_window_candles", 2)),
    ):
        return make_signal(
            name="asia_fade",
            variant="sweep_reclaim",
            direction=Direction.BUY,
            candles=candles,
            facts=facts,
            instrument_spec=instrument_spec,
            parameters=parameters,
            structural_stop_price=float(candles.tail(2)["low"].min()),
            structural_target_price=facts.previous_day.equilibrium or facts.asia.high,
            default_stop=30,
            default_target=60,
            default_distance_unit="points",
        )
    if close_back_rejection(
        candles.tail(int((parameters or {}).get("rejection_window_candles", 2))),
        facts.asia.high,
        "bearish",
        facts.average_candle_size,
        minimum_sweep_acs=float((parameters or {}).get("sweep_minimum_acs", 0.1)),
        maximum_sweep_acs=float((parameters or {}).get("sweep_maximum_acs", 2.0)),
        window_candles=int((parameters or {}).get("rejection_window_candles", 2)),
    ):
        return make_signal(
            name="asia_fade",
            variant="sweep_reclaim",
            direction=Direction.SELL,
            candles=candles,
            facts=facts,
            instrument_spec=instrument_spec,
            parameters=parameters,
            structural_stop_price=float(candles.tail(2)["high"].max()),
            structural_target_price=facts.previous_day.equilibrium or facts.asia.low,
            default_stop=30,
            default_target=60,
            default_distance_unit="points",
        )
    return None
