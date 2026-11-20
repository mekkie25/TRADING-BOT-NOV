"""Call-based Cracker strategy; direction and levels are caller-supplied."""

from datetime import timedelta
from typing import Dict, List, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction, Signal
from strategies.base import BarContext
from strategies.common import instrument_default_distance_unit, make_signal
from strategies.context import MarketFacts, build_market_facts


VARIANTS = ("call_based", "extended_edition")


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    variant: str = "call_based",
) -> Optional[Signal]:
    """Evaluate Cracker strategy on completed candles.

    The real mentor Cracker requires a daily call ('buy' or 'sell')
    and two caller-supplied price levels (call_levels).
    Jokey banter versions (e.g. 'Teemo Cracker') are excluded.
    """
    settings = parameters or {}
    call = str(settings.get("call_direction", "")).lower()
    levels = settings.get("call_levels")
    if call not in ("buy", "sell") or not isinstance(levels, (list, tuple)) or len(levels) != 2:
        return None

    prices = [float(level) for level in levels]
    if any(not pd.notna(level) or level <= 0 for level in prices):
        raise ValueError("Cracker call levels must be positive finite prices.")

    if len(candles) < 2:
        return None

    if bool(settings.get("level_invalidated_before_open", False)):
        return None

    open_time = settings.get("new_york_open_utc")
    if open_time is not None:
        if not isinstance(open_time, pd.Timestamp):
            open_time = pd.Timestamp(open_time)
        if open_time.tzinfo is None or open_time.utcoffset() != timedelta(0):
            raise ValueError("new_york_open_utc must be timezone-aware UTC.")
        latest_time = pd.Timestamp(facts.current_time)
        if latest_time < open_time or latest_time > open_time + timedelta(minutes=5):
            return None

    current = candles.iloc[-1]
    previous = candles.iloc[-2]
    c_high = float(current["high"])
    c_low = float(current["low"])
    c_close = float(current["close"])
    p_close = float(previous["close"])

    tapped = [level for level in prices if c_high >= level >= c_low]
    if not tapped:
        return None

    trigger_level = min(tapped, key=lambda level: abs(level - float(current["open"])))
    if call == "buy" and c_close > trigger_level and p_close <= trigger_level:
        direction = Direction.BUY
        structural_stop = c_low
        structural_target = facts.previous_day.equilibrium
    elif call == "sell" and c_close < trigger_level and p_close >= trigger_level:
        direction = Direction.SELL
        structural_stop = c_high
        structural_target = facts.previous_day.equilibrium
    else:
        return None

    # Filter: buy call holding under Asia low is a brick wall
    if direction == Direction.BUY and facts.asia.low is not None and c_close < facts.asia.low:
        return None

    # Filter: sell call sitting under EQ requires volume drive confirmed
    if direction == Direction.SELL and facts.previous_day.equilibrium is not None:
        below_eq = c_close < facts.previous_day.equilibrium
        if below_eq and not bool(settings.get("sell_drive_confirmed", False)):
            return None

    # Skip Friday filter option
    if facts.current_time.weekday() == 4 and bool(settings.get("skip_friday", True)):
        return None

    unit = str(settings.get("distance_unit", instrument_default_distance_unit(instrument_spec)))
    default_stop_val = float(settings.get("fixed_stop", 60.0))
    default_target_val = float(settings.get("fixed_target", 60.0))
    is_extended = bool(settings.get("extended_edition", False)) or variant == "extended_edition"

    return make_signal(
        name="cracker",
        variant=variant,
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
        time_limit_seconds=(
            None if is_extended
            else int(settings.get("exit_after_seconds", 90))
        ),
    )


class CrackerStrategy:
    """Strategy class implementing the Strategy protocol for the simulator."""

    def __init__(
        self,
        timeframe: str = "M1",
        symbols: Optional[List[str]] = None,
        variant: str = "call_based",
        parameters: Optional[Dict[str, object]] = None,
    ) -> None:
        self.name = "cracker"
        self.timeframe = timeframe.upper()
        self.symbols = symbols or ["US30", "NAS100", "XAUUSD"]
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
