"""Report the current session and whether it is within a killzone."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from .sessions import (
    TIMEZONE_LONDON,
    TIMEZONE_NY,
    SessionConfig,
    SessionName,
    _is_weekend,
    get_current_session,
)


@dataclass
class TimeStructureConfig:
    session_config: SessionConfig = field(default_factory=SessionConfig)


@dataclass
class TimeWindow:
    name: str
    weight: float
    is_killzone: bool


@dataclass(frozen=True)
class SessionReport:
    observed_at_utc: datetime
    session: SessionName
    is_active: bool
    killzones: List[str]
    london_local_time: datetime
    new_york_local_time: datetime
    summary: str


def report_market_time(
    dt: datetime,
    config: Optional[TimeStructureConfig] = None,
) -> SessionReport:
    """Report the configured session and killzone windows at a UTC time."""
    if dt.tzinfo is None or dt.utcoffset() != timedelta(0):
        raise ValueError("dt must be timezone-aware UTC.")
    if config is None:
        config = TimeStructureConfig()

    session = get_current_session(dt, config.session_config)
    london_local = dt.astimezone(TIMEZONE_LONDON)
    new_york_local = dt.astimezone(TIMEZONE_NY)
    killzones = []
    if not _is_weekend(dt) and config.session_config.enable_killzones:
        if (
            config.session_config.london_killzone_start
            <= london_local.time()
            < config.session_config.london_killzone_end
        ):
            killzones.append("London")
        if (
            config.session_config.ny_killzone_start
            <= new_york_local.time()
            < config.session_config.ny_killzone_end
        ):
            killzones.append("New York")

    if killzones:
        killzone_text = f"within the {', '.join(killzones)} killzone"
    else:
        killzone_text = "outside the configured killzones"
    summary = (
        f"At {dt.isoformat()} UTC, the market is in the {session.name.value} "
        f"session and is {killzone_text}. These configured time windows do "
        "not measure trading volume."
    )
    return SessionReport(
        observed_at_utc=dt,
        session=session.name,
        is_active=session.is_active,
        killzones=killzones,
        london_local_time=london_local,
        new_york_local_time=new_york_local,
        summary=summary,
    )


def get_time_window(
    dt: datetime,
    config: Optional[TimeStructureConfig] = None,
) -> Optional[TimeWindow]:
    """Return session timing information, or None outside sessions and killzones."""
    if config is None:
        config = TimeStructureConfig()

    session = get_current_session(dt, config.session_config)
    if not session.is_active and not session.is_killzone:
        return None

    killzone_status = "killzone" if session.is_killzone else "not killzone"
    return TimeWindow(
        name=f"{session.name.value} session, {killzone_status}",
        weight=1.0,
        is_killzone=session.is_killzone,
    )
