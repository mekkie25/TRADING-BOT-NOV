"""Shared strategy entry, confluence, and configurable exit helpers."""

import math
from dataclasses import asdict
from typing import Dict, Iterable, Optional, Sequence

import pandas as pd

from broker.instrument_specs import DistanceUnit, InstrumentSpec
from engine.models import Direction, Signal
from knowledge.operational_definitions import OperationalDefinitionConfig
from strategies.confluence import ConfluenceReason, count_confluence
from strategies.context import MarketFacts


def default_confluence_reasons(
    candles: pd.DataFrame,
    facts: MarketFacts,
    direction: Direction,
) -> tuple[ConfluenceReason, ...]:
    close = float(candles.iloc[-1]["close"])
    bullish = direction == Direction.BUY
    return (
        ConfluenceReason(
            "200 EMA direction",
            "direction",
            facts.ema_200 is not None
            and ((close >= facts.ema_200) if bullish else (close <= facts.ema_200)),
        ),
        ConfluenceReason(
            "Daily Flip direction",
            "direction",
            facts.daily_flip.level is not None
            and ((close >= facts.daily_flip.level) if bullish else (close <= facts.daily_flip.level)),
        ),
        ConfluenceReason(
            "Previous-day equilibrium location",
            "location",
            facts.previous_day.equilibrium is not None
            and ((close <= facts.previous_day.equilibrium) if bullish else (close >= facts.previous_day.equilibrium)),
        ),
        ConfluenceReason(
            "Asia boundary alignment",
            "level_alignment",
            facts.asia.high is not None
            and facts.asia.low is not None
            and _near_any(
                close,
                (facts.asia.high, facts.asia.low),
                facts.average_candle_size or 0,
            ),
        ),
        ConfluenceReason(
            f"{facts.session.name} session",
            "timing_volume",
            facts.session.is_open_window,
        ),
    )


def instrument_default_distance_unit(instrument_spec: InstrumentSpec) -> DistanceUnit:
    if instrument_spec.pip_size is not None:
        return "pips"
    if instrument_spec.point_size is not None:
        return "points"
    if instrument_spec.tick_size is not None:
        return "ticks"
    return "price"


def opening_range(
    candles: pd.DataFrame,
    timeframe: str,
    current_time,
    session_name: str,
    range_minutes: int,
) -> Optional[tuple[float, float]]:
    from datetime import datetime, time, timedelta, timezone
    from zoneinfo import ZoneInfo

    from data.timeframes import TIMEFRAME_LENGTHS
    from knowledge.strategy_sessions import NEW_YORK, SAST

    if isinstance(range_minutes, bool) or not isinstance(range_minutes, int) or range_minutes <= 0:
        raise ValueError("range_minutes must be a positive integer.")
    normalized_timeframe = timeframe.strip().upper()
    if normalized_timeframe not in TIMEFRAME_LENGTHS:
        raise ValueError(f"Unsupported timeframe: {timeframe}.")
    if current_time.tzinfo is None or current_time.utcoffset() != timedelta(0):
        raise ValueError("current_time must be timezone-aware UTC.")
    if session_name == "London":
        local = current_time.astimezone(SAST)
        zone = SAST
        start_clock = time(8, 0)
    elif session_name == "New York":
        local = current_time.astimezone(NEW_YORK)
        zone = NEW_YORK
        start_clock = time(8, 30)
    elif session_name == "Asia":
        local = current_time.astimezone(SAST)
        zone = SAST
        start_clock = time(1, 0)
    else:
        return None
    start = datetime.combine(local.date(), start_clock, tzinfo=zone).astimezone(timezone.utc)
    end = start + timedelta(minutes=range_minutes)
    if current_time < end:
        return None
    times = pd.to_datetime(candles["time"], utc=True, errors="coerce")
    duration = pd.Timedelta(TIMEFRAME_LENGTHS[normalized_timeframe])
    in_range = (
        (times >= pd.Timestamp(start))
        & (times + duration <= pd.Timestamp(end))
        & (times + duration <= pd.Timestamp(current_time))
    )
    selected = candles.loc[in_range.to_numpy()]
    if selected.empty:
        return None
    return float(selected["high"].max()), float(selected["low"].min())


def make_signal(
    *,
    name: str,
    variant: str,
    direction: Direction,
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
    structural_stop_price: Optional[float] = None,
    structural_target_price: Optional[float] = None,
    extra_reasons: Iterable[ConfluenceReason] = (),
    default_stop: float = 30.0,
    default_target: float = 60.0,
    default_distance_unit: DistanceUnit = "pips",
    conditional: bool = False,
    time_limit_seconds: Optional[int] = None,
) -> Optional[Signal]:
    settings = parameters or {}
    acs = facts.average_candle_size
    if acs is None or not math.isfinite(acs) or acs <= 0:
        return None
    reasons = default_confluence_reasons(candles, facts, direction) + tuple(extra_reasons)
    minimum_count = int(settings.get("minimum_confluence_count", 1 if conditional else 0))
    count_mode = str(settings.get("confluence_count_mode", "groups"))
    report = count_confluence(
        reasons,
        minimum_count=minimum_count,
        count_mode=count_mode,  # type: ignore[arg-type]
    )
    if conditional and report.group_count < 1:
        return None
    if not report.meets_minimum:
        return None

    stop_mode = str(settings.get("sl_mode", "volatility_scaled"))
    target_mode = str(settings.get("tp_mode", "volatility_scaled"))
    stop_multiple = float(settings.get("sl_multiple", 1.5))
    target_multiple = float(settings.get("tp_multiple", 3.0))
    stop_buffer = float(settings.get("structural_buffer_acs", 0.25)) * acs
    stop_distance = None
    target_distance = None
    if stop_mode == "volatility_scaled":
        stop_distance = acs * stop_multiple
    elif stop_mode == "fixed":
        stop_distance = instrument_spec.price_distance(
            float(settings.get("fixed_stop", default_stop)),
            str(settings.get("fixed_stop_unit", default_distance_unit)),  # type: ignore[arg-type]
        )
    elif stop_mode == "structural":
        if structural_stop_price is None:
            return None
        structural_stop_price = (
            structural_stop_price - stop_buffer
            if direction == Direction.BUY
            else structural_stop_price + stop_buffer
        )
        if (direction == Direction.BUY and structural_stop_price >= candles.iloc[-1]["close"]) or (
            direction == Direction.SELL and structural_stop_price <= candles.iloc[-1]["close"]
        ):
            return None
    else:
        raise ValueError(f"Unsupported stop-loss mode: {stop_mode}.")

    if target_mode == "volatility_scaled":
        target_distance = acs * target_multiple
    elif target_mode == "fixed":
        target_distance = instrument_spec.price_distance(
            float(settings.get("fixed_target", default_target)),
            str(settings.get("fixed_target_unit", default_distance_unit)),  # type: ignore[arg-type]
        )
    elif target_mode == "structural":
        if structural_target_price is None:
            return None
        if (direction == Direction.BUY and structural_target_price <= candles.iloc[-1]["close"]) or (
            direction == Direction.SELL and structural_target_price >= candles.iloc[-1]["close"]
        ):
            return None
    else:
        raise ValueError(f"Unsupported take-profit mode: {target_mode}.")

    definitions = asdict(
        OperationalDefinitionConfig(
            average_candle_lookback=int(settings.get("acs_lookback", 20)),
            volume_range_multiple=float(settings.get("volume_range_multiple", 1.5)),
            volume_body_fraction=float(settings.get("volume_body_fraction", 0.6)),
            break_distance_acs=float(settings.get("break_distance_acs", 0.1)),
            hold_candles=int(settings.get("hold_candles", 2)),
            hold_wick_tolerance_acs=float(settings.get("hold_wick_tolerance_acs", 0.25)),
            touch_distance_acs=float(settings.get("touch_distance_acs", 0.25)),
            rejection_wick_fraction=float(settings.get("rejection_wick_fraction", 0.5)),
            sweep_minimum_acs=float(settings.get("sweep_minimum_acs", 0.1)),
            sweep_maximum_acs=float(settings.get("sweep_maximum_acs", 2.0)),
            momentum_range_multiple=float(settings.get("momentum_range_multiple", 1.5)),
        )
    )
    definitions.update(
        {
            "sl_multiple": stop_multiple,
            "tp_multiple": target_multiple,
            "minimum_confluence_count": minimum_count,
            "confluence_count_mode": count_mode,
            "fixed_stop": settings.get("fixed_stop", default_stop),
            "fixed_target": settings.get("fixed_target", default_target),
            "distance_unit": settings.get("fixed_stop_unit", default_distance_unit),
        }
    )
    return Signal(
        direction=direction,
        sl_atr_multiple=stop_multiple,
        tp_atr_multiple=target_multiple,
        max_spread_pips=float(settings.get("max_spread_pips", 2.0)),
        strategy_name=name,
        variant=variant,
        session=facts.session.name,
        sl_mode=stop_mode,
        tp_mode=target_mode,
        time_limit_seconds=time_limit_seconds,
        stop_distance=stop_distance,
        target_distance=target_distance,
        structural_stop_price=structural_stop_price,
        structural_target_price=structural_target_price,
        average_candle_size=acs,
        confluence_reasons=list(report.present_reasons),
        confluence_count=(
            report.group_count if count_mode == "groups" else report.reason_count
        ),
        definition_parameters=definitions,
        poc_source=(
            facts.volume_profile.source
            if facts.volume_profile.candle_count
            else None
        ),
    )


def _near_any(price: float, levels: Sequence[Optional[float]], tolerance: float) -> bool:
    if tolerance <= 0:
        return False
    return any(level is not None and abs(price - level) <= tolerance for level in levels)
