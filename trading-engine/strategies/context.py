"""Build market facts from completed OHLC candles for strategy evaluations."""

import math
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Dict, Optional
from zoneinfo import ZoneInfo

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from data.timeframes import TIMEFRAME_LENGTHS
from indicators.exponential_moving_average import (
    analyze_exponential_moving_averages,
)
from knowledge.asia_levels import AsiaLevelsReport, analyze_asia_levels
from knowledge.daily_flip import DailyFlipReport, analyze_daily_flip
from knowledge.operational_definitions import average_candle_size
from knowledge.strategy_sessions import (
    NEW_YORK,
    SAST,
    StrategySession,
    StrategySessionConfig,
    report_strategy_session,
)
from knowledge.volume_profile import (
    ApproximateVolumeProfileProvider,
    VolumeProfileProvider,
    VolumeProfileReport,
)


@dataclass(frozen=True)
class PreviousDayFacts:
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    equilibrium: Optional[float]
    pivots: Dict[str, float]


@dataclass(frozen=True)
class MarketFacts:
    current_time: datetime
    timeframe: str
    session: StrategySession
    average_candle_size: Optional[float]
    asia: AsiaLevelsReport
    previous_day: PreviousDayFacts
    daily_flip: DailyFlipReport
    ema_200: Optional[float]
    volume_profile: VolumeProfileReport


def build_market_facts(
    candles: pd.DataFrame,
    timeframe: str,
    current_time: datetime,
    symbol_spec: InstrumentSpec,
    session_config: Optional[StrategySessionConfig] = None,
    profile_provider: Optional[VolumeProfileProvider] = None,
) -> MarketFacts:
    if current_time.tzinfo is None or current_time.utcoffset() != timedelta(0):
        raise ValueError("current_time must be timezone-aware UTC.")
    normalized_timeframe = timeframe.strip().upper()
    if normalized_timeframe not in TIMEFRAME_LENGTHS:
        raise ValueError(f"Unsupported timeframe: {timeframe}.")
    if not isinstance(candles, pd.DataFrame) or candles.empty:
        raise ValueError("candles must be a non-empty DataFrame.")
    required = {"time", "open", "high", "low", "close"}
    missing = required.difference(candles.columns)
    if missing:
        raise ValueError(f"Candles are missing columns: {', '.join(sorted(missing))}.")
    times = pd.to_datetime(candles["time"], utc=True, errors="coerce")
    if times.isna().any() or not times.is_monotonic_increasing or times.duplicated().any():
        raise ValueError("Candle times must be valid, unique, and chronological.")
    duration = pd.Timedelta(TIMEFRAME_LENGTHS[normalized_timeframe])
    completed = candles.loc[(times + duration <= pd.Timestamp(current_time)).to_numpy()]
    if completed.empty:
        raise ValueError("No completed candles are available at current_time.")

    size = average_candle_size(completed, min(20, len(completed)))
    asia = analyze_asia_levels(completed, normalized_timeframe, current_time)
    previous_day = _previous_day_facts(completed, current_time, normalized_timeframe)
    daily_flip = analyze_daily_flip(completed, current_time)
    ema_report = analyze_exponential_moving_averages(
        completed,
        normalized_timeframe,
        current_time,
    )
    ema_200 = ema_report.values.get(200)
    session = report_strategy_session(current_time, session_config)
    profile = (profile_provider or ApproximateVolumeProfileProvider()).calculate(
        completed,
        normalized_timeframe,
        *_session_window(current_time, session.name),
        current_time,
        size or float(completed["high"].sub(completed["low"]).mean()),
        symbol_spec.tick_size,
    )
    return MarketFacts(
        current_time=current_time,
        timeframe=normalized_timeframe,
        session=session,
        average_candle_size=size,
        asia=asia,
        previous_day=previous_day,
        daily_flip=daily_flip,
        ema_200=ema_200,
        volume_profile=profile,
    )


def _previous_day_facts(
    candles: pd.DataFrame,
    current_time: datetime,
    timeframe: str,
) -> PreviousDayFacts:
    duration = pd.Timedelta(TIMEFRAME_LENGTHS[timeframe])
    times = pd.to_datetime(candles["time"], utc=True, errors="coerce")
    current_day_start = pd.Timestamp(
        datetime.combine(current_time.date(), time.min, tzinfo=timezone.utc)
    )
    previous_day_start = current_day_start - pd.Timedelta(days=1)
    contained = (
        (times >= previous_day_start)
        & (times + duration <= current_day_start)
        & (times + duration <= pd.Timestamp(current_time))
    )
    selected = candles.loc[contained.to_numpy()]
    if selected.empty:
        return PreviousDayFacts(None, None, None, None, {})
    high = float(selected["high"].max())
    low = float(selected["low"].min())
    close = float(selected.iloc[-1]["close"])
    equilibrium = (high + low) / 2.0
    pivot = (high + low + close) / 3.0
    price_range = high - low
    return PreviousDayFacts(
        high=high,
        low=low,
        close=close,
        equilibrium=equilibrium,
        pivots={
            "P": pivot,
            "R1": 2 * pivot - low,
            "S1": 2 * pivot - high,
            "R2": pivot + price_range,
            "S2": pivot - price_range,
            "R3": high + 2 * (pivot - low),
            "S3": low - 2 * (high - pivot),
            "R4": high + 3 * (pivot - low),
        },
    )


def _session_window(
    current_time: datetime,
    session_name: str,
) -> tuple[datetime, datetime]:
    if session_name == "Asia":
        local = current_time.astimezone(SAST)
        return _local_window(local.date(), time(1), time(6), SAST)
    if session_name == "London":
        local = current_time.astimezone(SAST)
        return _local_window(local.date(), time(8), time(10), SAST)
    if session_name == "New York":
        local = current_time.astimezone(NEW_YORK)
        return _local_window(local.date(), time(8, 30), time(9, 30), NEW_YORK)
    return current_time, current_time + timedelta(seconds=1)


def _local_window(
    day,
    start: time,
    end: time,
    timezone_info: ZoneInfo,
) -> tuple[datetime, datetime]:
    return (
        datetime.combine(day, start, tzinfo=timezone_info).astimezone(timezone.utc),
        datetime.combine(day, end, tzinfo=timezone_info).astimezone(timezone.utc),
    )
