"""
Module 2: Market Sessions & Time
Depends on: common.py only.

Purpose: Know which session we are in, when it started, and when the market tends to move most.
"""

import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import List, Optional, Tuple
from enum import Enum

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

# All times below are in the local exchange timezone
TIMEZONE_LONDON = ZoneInfo("Europe/London")
TIMEZONE_NY = ZoneInfo("America/New_York")
TIMEZONE_TOKYO = ZoneInfo("Asia/Tokyo")

UTC = ZoneInfo("UTC")

class SessionName(Enum):
    ASIA = "Asia"
    LONDON = "London"
    NEW_YORK = "New York"
    LONDON_NY_OVERLAP = "London/NY Overlap"
    OFF_SESSION = "Off Session"

@dataclass
class SessionConfig:
    # Standard Sessions (Local exchange times)
    asia_start: time = time(9, 0)    # 09:00 Tokyo
    asia_end: time = time(18, 0)     # 18:00 Tokyo
    
    london_start: time = time(8, 0)  # 08:00 London
    london_end: time = time(16, 30)  # 16:30 London
    
    ny_start: time = time(8, 0)      # 08:00 New York
    ny_end: time = time(17, 0)       # 17:00 New York
    
    # Killzones (Optional windows where volatility is highest)
    enable_killzones: bool = True
    london_killzone_start: time = time(7, 0)  # 07:00 London
    london_killzone_end: time = time(10, 0)   # 10:00 London
    
    ny_killzone_start: time = time(8, 30)     # 08:30 New York
    ny_killzone_end: time = time(11, 0)       # 11:00 New York

@dataclass
class SessionInfo:
    name: SessionName
    is_active: bool
    is_killzone: bool
    start_time_utc: Optional[datetime]
    end_time_utc: Optional[datetime]

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def _ensure_utc(dt: datetime) -> datetime:
    """Ensures a datetime is timezone-aware and in UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)

def _is_weekend(dt: datetime) -> bool:
    """Forex markets are closed from Friday 22:00 UTC to Sunday 22:00 UTC."""
    # 4 = Friday, 5 = Saturday, 6 = Sunday
    if dt.weekday() == 5: # Saturday
        return True
    if dt.weekday() == 4 and dt.hour >= 22: # Friday late
        return True
    if dt.weekday() == 6 and dt.hour < 22: # Sunday early
        return True
    return False

def _get_local_time(dt_utc: datetime, tz: ZoneInfo) -> datetime:
    """Converts UTC to the local exchange timezone."""
    return dt_utc.astimezone(tz)

# ==========================================
# 3. CORE SESSION LOGIC
# ==========================================

def get_current_session(dt: datetime, config: SessionConfig = SessionConfig()) -> SessionInfo:
    """
    Determines the current session, handling DST automatically.
    """
    dt_utc = _ensure_utc(dt)
    
    if _is_weekend(dt_utc):
        return SessionInfo(SessionName.OFF_SESSION, False, False, None, None)

    # Convert to local times
    london_local = _get_local_time(dt_utc, TIMEZONE_LONDON)
    ny_local = _get_local_time(dt_utc, TIMEZONE_NY)
    tokyo_local = _get_local_time(dt_utc, TIMEZONE_TOKYO)
    
    # Check local times against config (note: simple time check ignores midnight crossing for brevity)
    is_asia = config.asia_start <= tokyo_local.time() < config.asia_end
    is_london = config.london_start <= london_local.time() < config.london_end
    is_ny = config.ny_start <= ny_local.time() < config.ny_end
    
    # Check for overlap
    is_overlap = is_london and is_ny
    
    # Check killzones
    is_kz = False
    if config.enable_killzones:
        is_london_kz = config.london_killzone_start <= london_local.time() < config.london_killzone_end
        is_ny_kz = config.ny_killzone_start <= ny_local.time() < config.ny_killzone_end
        is_kz = is_london_kz or is_ny_kz

    if is_overlap:
        name = SessionName.LONDON_NY_OVERLAP
    elif is_london:
        name = SessionName.LONDON
    elif is_ny:
        name = SessionName.NEW_YORK
    elif is_asia:
        name = SessionName.ASIA
    else:
        name = SessionName.OFF_SESSION

    return SessionInfo(
        name=name,
        is_active=(name != SessionName.OFF_SESSION),
        is_killzone=is_kz,
        start_time_utc=None, # Can be populated if needed
        end_time_utc=None
    )

def _get_session_start_dt(dt_utc: datetime, session_name: SessionName, config: SessionConfig) -> Optional[datetime]:
    """Helper to get the UTC start time of a specific session on a given day."""
    if session_name == SessionName.ASIA:
        tz, t = TIMEZONE_TOKYO, config.asia_start
    elif session_name == SessionName.LONDON:
        tz, t = TIMEZONE_LONDON, config.london_start
    elif session_name == SessionName.NEW_YORK:
        tz, t = TIMEZONE_NY, config.ny_start
    else:
        return None

    # Get the date in the local timezone
    local_date = dt_utc.astimezone(tz).date()
    
    # Combine date and time, localized
    local_dt = datetime.combine(local_date, t).replace(tzinfo=tz)
    
    return local_dt.astimezone(UTC)

def get_session_start(dt: datetime, session_name: Optional[SessionName] = None, config: SessionConfig = SessionConfig()) -> Optional[datetime]:
    """Returns the UTC start time of the current (or specified) session."""
    dt_utc = _ensure_utc(dt)
    
    if session_name is None:
        session_info = get_current_session(dt_utc, config)
        if session_info.name == SessionName.OFF_SESSION:
            return None
        # If overlap, default to London start
        session_name = SessionName.LONDON if session_info.name == SessionName.LONDON_NY_OVERLAP else session_info.name

    return _get_session_start_dt(dt_utc, session_name, config)

def minutes_since_session_start(dt: datetime, config: SessionConfig = SessionConfig()) -> float:
    """Returns how many minutes have passed since the current session started."""
    dt_utc = _ensure_utc(dt)
    start = get_session_start(dt_utc, config=config)
    if start is None:
        return 0.0
    return (dt_utc - start).total_seconds() / 60.0

# ==========================================
# 4. CANDLE FILTERING LOGIC
# ==========================================

def get_session_candles(df: pd.DataFrame, dt: datetime, config: SessionConfig = SessionConfig()) -> pd.DataFrame:
    """
    Filters a DataFrame to return only the candles from the current session start up to 'dt'.
    Assumes 'time' column is UTC datetime.
    """
    dt_utc = _ensure_utc(dt)
    start = get_session_start(dt_utc, config=config)
    
    if start is None:
        return pd.DataFrame() # Empty if off-session
        
    # Filter data
    mask = (df['time'] >= start) & (df['time'] <= dt_utc)
    return df[mask]

def get_session_open_price(df: pd.DataFrame, dt: datetime, config: SessionConfig = SessionConfig()) -> Optional[float]:
    """Gets the open price of the first candle in the current session."""
    session_candles = get_session_candles(df, dt, config)
    if session_candles.empty:
        return None
    return float(session_candles.iloc[0]['open'])

def get_session_high_low_so_far(df: pd.DataFrame, dt: datetime, config: SessionConfig = SessionConfig()) -> Tuple[Optional[float], Optional[float]]:
    """Gets the highest high and lowest low of the session so far."""
    session_candles = get_session_candles(df, dt, config)
    if session_candles.empty:
        return None, None
    
    high = float(session_candles['high'].max())
    low = float(session_candles['low'].min())
    return high, low

def get_previous_session_high_low(df: pd.DataFrame, dt: datetime, session_name: SessionName, config: SessionConfig = SessionConfig()) -> Tuple[Optional[float], Optional[float]]:
    """
    Gets the high and low of the PREVIOUS session of the given type.
    Example: If I ask for LONDON, it finds the London session from yesterday.
    """
    dt_utc = _ensure_utc(dt)
    
    # Get start of current requested session
    current_start = _get_session_start_dt(dt_utc, session_name, config)
    if not current_start:
        return None, None

    # Go back 1 day in local time to find the previous session start
    tz = TIMEZONE_LONDON if session_name in [SessionName.LONDON, SessionName.LONDON_NY_OVERLAP] else TIMEZONE_NY
    local_date = current_start.astimezone(tz).date() - timedelta(days=1)
    
    # Skip weekends (logic simplified for brevity; robust production code would loop back to Friday)
    while local_date.weekday() > 4:
         local_date -= timedelta(days=1)
         
    t = config.london_start if session_name == SessionName.LONDON else config.ny_start
    prev_local_dt = datetime.combine(local_date, t).replace(tzinfo=tz)
    prev_start_utc = prev_local_dt.astimezone(UTC)
    
    # To get the end, we can just look at the next few hours (e.g., 8 hours for London)
    duration = timedelta(hours=8) 
    prev_end_utc = prev_start_utc + duration
    
    # Filter the DataFrame
    mask = (df['time'] >= prev_start_utc) & (df['time'] < prev_end_utc)
    prev_candles = df[mask]
    
    if prev_candles.empty:
        return None, None
        
    return float(prev_candles['high'].max()), float(prev_candles['low'].min())