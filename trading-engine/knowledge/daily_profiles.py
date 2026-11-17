"""
Module 15: Daily Profiles
Depends on: sessions.py, candlesticks.py, market_structure.py, liquidity.py, judas_swing.py, common.py.

Purpose: Recognise the common shapes a day takes, early enough to use them.

NOTE: Course definition was left blank. The profiles implemented here 
(Trend Day, Range Day, Reversal Day, Judas-Then-Trend) are placeholders 
based on standard SMC theory.
"""

import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple

from .sessions import get_current_session, get_session_start, SessionName, SessionConfig
from .liquidity import get_liquidity_pools, PoolStatus, PoolSide, LiquidityConfig
from .market_structure import _find_swings, SwingType, MarketStructureConfig
from .judas_swing import get_judas_swing, JudasState, JudasConfig

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

class ProfileName(Enum):
    TREND_DAY = "TREND_DAY"
    RANGE_DAY = "RANGE_DAY"
    REVERSAL_DAY = "REVERSAL_DAY"
    JUDAS_THEN_TREND = "JUDAS_THEN_TREND"
    TOO_EARLY = "TOO_EARLY"

@dataclass
class ProfilePhase:
    name: str
    completed: bool
    description: str

@dataclass
class ProfileConfig:
    # Minimum day range (in pips) to qualify for trend/range day classification
    min_day_range_pips: float = 30.0
    
    # If day range < this, it's a range day
    range_day_max_pips: float = 50.0
    
    # If close is within this % of high/low, it's a strong trend day
    trend_day_close_proximity_pct: float = 0.20
    
    session_config: SessionConfig = None
    liquidity_config: LiquidityConfig = None
    ms_config: MarketStructureConfig = None
    judas_config: JudasConfig = None

    def __post_init__(self):
        if self.session_config is None: self.session_config = SessionConfig()
        if self.liquidity_config is None: self.liquidity_config = LiquidityConfig()
        if self.ms_config is None: self.ms_config = MarketStructureConfig()
        if self.judas_config is None: self.judas_config = JudasConfig()

@dataclass
class ProfileMatch:
    profile: ProfileName
    confidence: float # 0 to 100
    phases_completed: List[ProfilePhase]
    reasoning: str

@dataclass
class ProfileClassification:
    best_match: Optional[ProfileName]
    confidence: float
    all_matches: List[ProfileMatch]
    is_too_early: bool
    current_time: pd.Timestamp

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def _is_judas_trend(df: pd.DataFrame, config: ProfileConfig) -> Tuple[bool, str]:
    """Checks if a Judas swing has occurred and trend has continued."""
    judas = get_judas_swing(df, config=config.judas_config)
    if judas.state in [JudasState.CONFIRMED_BULLISH, JudasState.CONFIRMED_BEARISH]:
        # Further confirm: has price moved significantly past the fake extreme?
        current_close = df.iloc[-1]['close']
        if judas.state == JudasState.CONFIRMED_BULLISH and current_close > judas.fake_move_extreme:
            return True, f"Bullish Judas confirmed, price pushed above {judas.fake_move_extreme}"
        elif judas.state == JudasState.CONFIRMED_BEARISH and current_close < judas.fake_move_extreme:
            return True, f"Bearish Judas confirmed, price pushed below {judas.fake_move_extreme}"
    return False, ""

def _detect_trend_day(df: pd.DataFrame, config: ProfileConfig) -> Tuple[bool, float, str]:
    """Checks if the day has trended decisively in one direction."""
    day_high = df['high'].max()
    day_low = df['low'].min()
    day_range = day_high - day_low
    
    if day_range < config.min_day_range_pips:
        return False, 0, "Range too small for trend day"
        
    current_close = df.iloc[-1]['close']
    
    # Check if close is at the extreme (strong trend day)
    close_from_high = (day_high - current_close) / day_range
    close_from_low = (current_close - day_low) / day_range
    
    if close_from_high <= config.trend_day_close_proximity_pct:
        conf = min((1 - close_from_high) * 100, 95)
        return True, conf, "Close near daily high - strong bullish trend"
    elif close_from_low <= config.trend_day_close_proximity_pct:
        conf = min((1 - close_from_low) * 100, 95)
        return True, conf, "Close near daily low - strong bearish trend"
        
    return False, 0, "Close not near extremes"

def _detect_range_day(df: pd.DataFrame, config: ProfileConfig) -> Tuple[bool, float, str]:
    """Checks if the day has stayed within a tight range."""
    day_high = df['high'].max()
    day_low = df['low'].min()
    day_range = day_high - day_low
    
    if day_range < config.range_day_max_pips:
        # Confidence is higher the tighter the range is
        conf = max(50, 100 - (day_range / config.range_day_max_pips) * 50)
        return True, conf, f"Range of {day_range:.1f} pips is very tight"
        
    return False, 0, "Range too wide for range day"

def _detect_reversal_day(df: pd.DataFrame, config: ProfileConfig) -> Tuple[bool, float, str]:
    """Checks if price swept one side and reversed strongly."""
    pools = get_liquidity_pools(df, config.liquidity_config)
    swept = [p for p in pools if p.status == PoolStatus.SWEPT]
    
    if not swept:
        return False, 0, "No liquidity sweeps detected"
        
    # If we swept lows and now we're at the highs, it's a bullish reversal
    current_close = df.iloc[-1]['close']
    day_high = df['high'].max()
    day_low = df['low'].min()
    day_range = day_high - day_low
    
    if day_range == 0: return False, 0, "No range"
    
    swept_lows = any(p.side == PoolSide.SELL_SIDE for p in swept)
    swept_highs = any(p.side == PoolSide.BUY_SIDE for p in swept)
    
    # Reversal up
    if swept_lows:
        reversal_dist = (current_close - day_low) / day_range
        if reversal_dist > 0.6: # Price moved 60% off the low
            return True, reversal_dist * 100, "Swept lows and reversed strongly to the upside"
            
    # Reversal down
    if swept_highs:
        reversal_dist = (day_high - current_close) / day_range
        if reversal_dist > 0.6:
            return True, reversal_dist * 100, "Swept highs and reversed strongly to the downside"
            
    return False, 0, "No confirmed reversal"

# ==========================================
# 3. CLASSIFICATION LOGIC
# ==========================================

def describe() -> str:
    return (
        "Daily Profiles: Recognises the common shapes a day takes. "
        "NOTE: Course definition was blank. Using placeholder profiles: "
        "Trend Day (close near extreme), Range Day (tight range), "
        "Reversal Day (sweep then reverse), Judas-Then-Trend (fake move then real move)."
    )

def classify_so_far(df: pd.DataFrame, time: pd.Timestamp, config: ProfileConfig = ProfileConfig()) -> ProfileClassification:
    """
    Classifies the day using ONLY data up to the given 'time'.
    Returns a probability distribution across profiles.
    """
    if df.empty:
        return ProfileClassification(ProfileName.TOO_EARLY, 0, [], True, time)
        
    # 1. No look-ahead: Slice data
    past_data = df[df['time'] <= time].copy()
    if past_data.empty:
        return ProfileClassification(ProfileName.TOO_EARLY, 0, [], True, time)

    # Check if enough time has passed (e.g., past London open)
    session_info = get_current_session(time, config.session_config)
    if session_info.name in [SessionName.ASIA, SessionName.OFF_SESSION]:
        return ProfileClassification(
            best_match=None,
            confidence=0,
            all_matches=[],
            is_too_early=True,
            current_time=time
        )

    # 2. Gather Evidence
    matches = []
    
    # Trend Day Check
    is_trend, conf_trend, reason_trend = _detect_trend_day(past_data, config)
    if is_trend:
        matches.append(ProfileMatch(ProfileName.TREND_DAY, conf_trend, [], reason_trend))
        
    # Range Day Check
    is_range, conf_range, reason_range = _detect_range_day(past_data, config)
    if is_range:
        matches.append(ProfileMatch(ProfileName.RANGE_DAY, conf_range, [], reason_range))
        
    # Reversal Day Check
    is_rev, conf_rev, reason_rev = _detect_reversal_day(past_data, config)
    if is_rev:
        matches.append(ProfileMatch(ProfileName.REVERSAL_DAY, conf_rev, [], reason_rev))
        
    # Judas Then Trend Check
    is_judas, reason_judas = _is_judas_trend(past_data, config)
    if is_judas:
        # Judas is a strong signal, give it high confidence
        matches.append(ProfileMatch(ProfileName.JUDAS_THEN_TREND, 85.0, [], reason_judas))

    if not matches:
        return ProfileClassification(
            best_match=None,
            confidence=0,
            all_matches=[],
            is_too_early=False,
            current_time=time
        )

    # 3. Pick the best match
    best = max(matches, key=lambda m: m.confidence)
    
    return ProfileClassification(
        best_match=best.profile,
        confidence=best.confidence,
        all_matches=sorted(matches, key=lambda m: m.confidence, reverse=True),
        is_too_early=False,
        current_time=time
    )

def classify_completed_day(day_candles: pd.DataFrame, config: ProfileConfig = ProfileConfig()) -> ProfileName:
    """
    Final classification AFTER the day has ended. 
    Used for backtesting statistics only.
    """
    if day_candles.empty:
        return ProfileName.RANGE_DAY
        
    # Use the full day data
    result = classify_so_far(day_candles, day_candles.iloc[-1]['time'], config)
    
    if result.best_match is None:
        return ProfileName.RANGE_DAY # Default fallback
        
    return result.best_match

# ==========================================
# 4. STATISTICS FUNCTION
# ==========================================

def get_profile_statistics(df: pd.DataFrame, config: ProfileConfig = ProfileConfig()) -> Dict[str, Any]:
    """
    Calculates how often each profile occurred historically.
    Uses final labels only.
    """
    if df.empty:
        return {"error": "Empty DataFrame"}
        
    # Group by day
    df_copy = df.copy()
    df_copy['date'] = df_copy['time'].dt.date
    
    daily_profiles = []
    for date, day_df in df_copy.groupby('date'):
        if len(day_df) < 20: # Skip partial days
            continue
        profile = classify_completed_day(day_df, config)
        daily_profiles.append({"date": date, "profile": profile})
        
    if not daily_profiles:
        return {"error": "Insufficient data"}
        
    results_df = pd.DataFrame(daily_profiles)
    total_days = len(results_df)
    
    counts = results_df['profile'].value_counts().to_dict()
    
    stats = {}
    for profile, count in counts.items():
        stats[profile.value if hasattr(profile, 'value') else profile] = {
            "count": count,
            "pct": round(count / total_days * 100, 2),
            "sample_size": total_days
        }
        
    return {
        "total_days_analyzed": total_days,
        "profiles": stats,
        "is_reliable": total_days >= 30
    }

# ==========================================
# 5. ANALYZE WRAPPER
# ==========================================

def analyze(df: pd.DataFrame, time: pd.Timestamp, config: ProfileConfig = ProfileConfig()) -> Dict[str, Any]:
    """Main entry point for real-time profile analysis."""
    result = classify_so_far(df, time, config)
    
    return {
        "definition": describe(),
        "best_match": result.best_match.value if result.best_match else None,
        "confidence": result.confidence,
        "is_too_early": result.is_too_early,
        "all_matches": [
            {
                "profile": m.profile.value,
                "confidence": m.confidence,
                "reasoning": m.reasoning
            } for m in result.all_matches
        ]
    }