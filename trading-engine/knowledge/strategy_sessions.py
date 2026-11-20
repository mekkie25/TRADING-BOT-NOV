"""Configurable strategy sessions with explicit SAST and New York clocks."""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Literal, Optional
from zoneinfo import ZoneInfo


StrategySessionName = Literal["Asia", "London", "New York", "Off Session"]
SAST = ZoneInfo("Africa/Johannesburg")
NEW_YORK = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class StrategySessionConfig:
    asia_start: time = time(1, 0)
    asia_end: time = time(6, 0)
    london_start: time = time(8, 0)
    london_end: time = time(10, 0)
    new_york_open: time = time(8, 30)
    new_york_end: time = time(9, 30)


@dataclass(frozen=True)
class StrategySession:
    name: StrategySessionName
    observed_at_utc: datetime
    local_time: datetime
    is_open_window: bool


def report_strategy_session(
    observed_at: datetime,
    config: Optional[StrategySessionConfig] = None,
) -> StrategySession:
    if observed_at.tzinfo is None or observed_at.utcoffset() != timedelta(0):
        raise ValueError("observed_at must be timezone-aware UTC.")
    settings = config or StrategySessionConfig()
    sast_time = observed_at.astimezone(SAST)
    new_york_time = observed_at.astimezone(NEW_YORK)
    local_clock = sast_time.timetz().replace(tzinfo=None)
    if settings.asia_start <= local_clock < settings.asia_end:
        name: StrategySessionName = "Asia"
        active = True
    elif settings.london_start <= local_clock < settings.london_end:
        name = "London"
        active = True
    elif settings.new_york_open <= new_york_time.time().replace(tzinfo=None) < settings.new_york_end:
        name = "New York"
        active = True
        local_clock = new_york_time.timetz().replace(tzinfo=None)
    else:
        name = "Off Session"
        active = False
    return StrategySession(name, observed_at, sast_time if name != "New York" else new_york_time, active)
