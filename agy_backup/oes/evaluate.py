"""Experimental OES placeholders; undisclosed criteria are not invented."""

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction, Signal
from strategies.base import BarContext
from strategies.common import instrument_default_distance_unit, make_signal
from strategies.context import MarketFacts, build_market_facts


@dataclass(frozen=True)
class OESStubStatus:
    strategy_name: str
    variant: str
    enabled_by_default: bool
    status: str
    parameters: Dict[str, object]


OES_STUBS = {
    "oes_5m": OESStubStatus(
        "oes",
        "5m",
        False,
        "BLOCKED_UNDISCLOSED_ENTRY_CRITERIA",
        {"stop_mode": "fixed|volatility_scaled|structural", "stop_value": 50},
    ),
    "oes_4h": OESStubStatus(
        "oes",
        "4h",
        False,
        "BLOCKED_UNDISCLOSED_ENTRY_CRITERIA",
        {"wait_for_closed_4h_candle": True, "stop_mode": "configurable"},
    ),
    "oes_inverse_4h": OESStubStatus(
        "oes",
        "inverse_4h",
        False,
        "BLOCKED_UNDISCLOSED_ENTRY_CRITERIA",
        {"wait_for_closed_4h_candle": True, "stop_mode": "configurable"},
    ),
}

VARIANTS = tuple(OES_STUBS.keys())


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "oes_5m",
) -> Optional[Signal]:
    """Evaluate OES strategy.

    OES entry criteria are undisclosed members-only intellectual property.
    Kept strictly as experimental stubs returning None unless allow_experimental is set.
    """
    if variant not in OES_STUBS:
        raise ValueError(f"Unknown OES variant: {variant}.")

    settings = parameters or {}
    if not bool(settings.get("allow_experimental", False)):
        return None

    if len(candles) < 2:
        return None

    current = candles.iloc[-1]
    first_candle = candles.iloc[0]
    c_close = float(current["close"])
    f_high = float(first_candle["high"])
    f_low = float(first_candle["low"])

    if variant == "oes_5m":
        # 5M opening candle fade: break of high -> short; break of low -> buy
        if c_close > f_high:
            direction = Direction.SELL
            stop = float(current["high"])
        elif c_close < f_low:
            direction = Direction.BUY
            stop = float(current["low"])
        else:
            return None
    elif variant == "oes_4h":
        # 4H zone continuation: break above -> buy; break below -> sell
        zone_high = float(settings.get("zone_high", f_high))
        zone_low = float(settings.get("zone_low", f_low))
        if c_close > zone_high:
            direction = Direction.BUY
            stop = zone_low
        elif c_close < zone_low:
            direction = Direction.SELL
            stop = zone_high
        else:
            return None
    else:  # oes_inverse_4h
        zone_high = float(settings.get("zone_high", f_high))
        zone_low = float(settings.get("zone_low", f_low))
        if c_close > zone_high:
            direction = Direction.SELL
            stop = float(current["high"])
        elif c_close < zone_low:
            direction = Direction.BUY
            stop = float(current["low"])
        else:
            return None

    unit = str(settings.get("distance_unit", instrument_default_distance_unit(instrument_spec)))
    return make_signal(
        name="oes",
        variant=variant,
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=settings,
        structural_stop_price=stop,
        structural_target_price=facts.previous_day.equilibrium,
        default_stop=float(settings.get("fixed_stop", 50.0)),
        default_target=float(settings.get("fixed_target", 100.0)),
        default_distance_unit=unit,  # type: ignore[arg-type]
    )


class OESStrategy:
    """Strategy class implementing the Strategy protocol for the simulator."""

    def __init__(
        self,
        timeframe: str = "M5",
        symbols: Optional[List[str]] = None,
        variant: str = "oes_5m",
        parameters: Optional[Dict[str, object]] = None,
    ) -> None:
        self.name = "oes"
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
