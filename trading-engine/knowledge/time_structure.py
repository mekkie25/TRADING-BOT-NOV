"""Report the current session and whether it is within a killzone."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .sessions import SessionConfig, get_current_session


@dataclass
class TimeStructureConfig:
    session_config: SessionConfig = field(default_factory=SessionConfig)


@dataclass
class TimeWindow:
    name: str
    weight: float
    is_killzone: bool


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
