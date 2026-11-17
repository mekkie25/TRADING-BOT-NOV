"""
Module 9: Liquidity Types
Depends on: liquidity.py, sessions.py, common.py.

Purpose: Tell the different kinds of liquidity apart on a live chart.
"""

import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple

from .liquidity import (
    get_liquidity_pools, LiquidityPool, PoolSide, PoolStatus, LiquidityConfig
)
from .sessions import (
    get_previous_session_high_low, SessionName, SessionConfig
)

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

class LiquidityType(Enum):
    EQUAL_HIGHS_LOWS = "EQUAL_HIGHS_LOWS"           # Clustered equal highs/lows (Module 8 default)
    SWING_HIGHS_LOWS = "SWING_HIGHS_LOWS"           # Single prominent swing
    PREVIOUS_DAY = "PREVIOUS_DAY"                   # PDH / PDL
    PREVIOUS_WEEK = "PREVIOUS_WEEK"                 # PWH / PWL
    PREVIOUS_SESSION = "PREVIOUS_SESSION"           # Asian/London session ranges
    RANGE_HIGHS_LOWS = "RANGE_HIGHS_LOWS"           # Consolidation box highs/lows
    ROUND_NUMBER = "ROUND_NUMBER"                   # Psychological levels (e.g., 1.1000, 2000)

@dataclass
class LiquidityTypeConfig:
    # Significance weights (higher = more important)
    weights: Dict[LiquidityType, float] = None
    
    # Session config for previous session detection
    session_config: SessionConfig = None
    
    # Liquidity config for base pool detection
    liquidity_config: LiquidityConfig = None
    
    # For Round Number detection
    round_number_step: float = 0.0100  # For majors. Change to 50 for Gold, etc.
    round_number_tolerance_pct: float = 0.0015  # 0.15% of price

    def __post_init__(self):
        if self.weights is None:
            self.weights = {
                LiquidityType.PREVIOUS_WEEK: 10.0,
                LiquidityType.PREVIOUS_DAY: 9.0,
                LiquidityType.PREVIOUS_SESSION: 8.0,
                LiquidityType.EQUAL_HIGHS_LOWS: 7.0,
                LiquidityType.RANGE_HIGHS_LOWS: 6.0,
                LiquidityType.ROUND_NUMBER: 5.0,
                LiquidityType.SWING_HIGHS_LOWS: 3.0,
            }
        if self.session_config is None:
            self.session_config = SessionConfig()
        if self.liquidity_config is None:
            self.liquidity_config = LiquidityConfig()

@dataclass
class ClassifiedPool:
    pool: LiquidityPool
    liquidity_type: LiquidityType
    significance_score: float  # Combination of weight + pool strength

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def _get_previous_week_hl(df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
    """Gets last week's high and low."""
    df_weekly = df.set_index('time').resample('1W').agg({
        'high': 'max', 'low': 'min'
    }).dropna()
    
    if len(df_weekly) < 2:
        return None, None
        
    prev_week = df_weekly.iloc[-2]
    return float(prev_week['high']), float(prev_week['low'])

def _get_previous_day_hl(df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
    """Gets previous daily candle high and low."""
    df_daily = df.set_index('time').resample('1D').agg({
        'high': 'max', 'low': 'min'
    }).dropna()
    
    if len(df_daily) < 2:
        return None, None
        
    prev_day = df_daily.iloc[-2]
    return float(prev_day['high']), float(prev_day['low'])

def _is_near_round_number(price: float, config: LiquidityTypeConfig) -> bool:
    """Checks if price is close to a psychological round number."""
    remainder = price % config.round_number_step
    distance = min(remainder, config.round_number_step - remainder)
    tolerance = price * config.round_number_tolerance_pct
    return distance <= tolerance

# ==========================================
# 3. CLASSIFICATION LOGIC
# ==========================================

def classify_pool(pool: LiquidityPool, df: pd.DataFrame, config: LiquidityTypeConfig = LiquidityTypeConfig()) -> ClassifiedPool:
    """
    Assigns a type to a pool by checking against known reference levels.
    """
    level = pool.level
    
    # 1. Get reference levels
    pdh, pdl = _get_previous_day_hl(df)
    pwh, pwl = _get_previous_week_hl(df)
    
    # Get previous session levels based on the pool's formation time
    # We'll use the pool's formed_at time to look back
    asia_hl = get_previous_session_high_low(df, pool.formed_at, SessionName.ASIA, config.session_config)
    london_hl = get_previous_session_high_low(df, pool.formed_at, SessionName.LONDON, config.session_config)
    
    # Tolerance for matching reference levels (e.g., 3% of ATR)
    atr = (df['high'].iloc[-1] - df['low'].iloc[-1]) # Quick proxy
    level_tolerance = 0.0015 * level # 0.15% of price
    
    # 2. Check against each type (order matters - most specific first)
    detected_type = LiquidityType.EQUAL_HIGHS_LOWS # Default from Module 8
    
    # Check previous week
    if pwh and abs(level - pwh) <= level_tolerance:
        detected_type = LiquidityType.PREVIOUS_WEEK
    elif pwl and abs(level - pwl) <= level_tolerance:
        detected_type = LiquidityType.PREVIOUS_WEEK
        
    # Check previous day
    elif pdh and abs(level - pdh) <= level_tolerance:
        detected_type = LiquidityType.PREVIOUS_DAY
    elif pdl and abs(level - pdl) <= level_tolerance:
        detected_type = LiquidityType.PREVIOUS_DAY
        
    # Check previous session
    elif asia_hl[0] and abs(level - asia_hl[0]) <= level_tolerance:
        detected_type = LiquidityType.PREVIOUS_SESSION
    elif asia_hl[1] and abs(level - asia_hl[1]) <= level_tolerance:
        detected_type = LiquidityType.PREVIOUS_SESSION
    elif london_hl[0] and abs(level - london_hl[0]) <= level_tolerance:
        detected_type = LiquidityType.PREVIOUS_SESSION
    elif london_hl[1] and abs(level - london_hl[1]) <= level_tolerance:
        detected_type = LiquidityType.PREVIOUS_SESSION
        
    # Check round number
    elif _is_near_round_number(level, config):
        detected_type = LiquidityType.ROUND_NUMBER
        
    # Check if it's a single swing (low swing count)
    elif pool.swing_count <= 1:
        detected_type = LiquidityType.SWING_HIGHS_LOWS
        
    # 3. Calculate final significance score
    base_weight = config.weights.get(detected_type, 1.0)
    # Bonus for more swings (stronger pool)
    swing_bonus = min(pool.swing_count, 5) * 0.5
    significance = base_weight + swing_bonus
    
    return ClassifiedPool(
        pool=pool,
        liquidity_type=detected_type,
        significance_score=significance
    )

# ==========================================
# 4. PUBLIC API
# ==========================================

def get_pools_by_type(df: pd.DataFrame, liq_type: LiquidityType, config: LiquidityTypeConfig = LiquidityTypeConfig()) -> List[ClassifiedPool]:
    """Returns all pools of a specific type."""
    raw_pools = get_liquidity_pools(df, config.liquidity_config)
    classified = [classify_pool(p, df, config) for p in raw_pools]
    return [c for c in classified if c.liquidity_type == liq_type]

def get_most_significant_pool(df: pd.DataFrame, side: PoolSide, config: LiquidityTypeConfig = LiquidityTypeConfig()) -> Optional[ClassifiedPool]:
    """
    Returns the single most important pool in the given direction.
    E.g., 'What is the most significant BUY_SIDE pool above us?'
    """
    raw_pools = get_liquidity_pools(df, config.liquidity_config)
    current_price = float(df.iloc[-1]['close'])
    
    classified = [classify_pool(p, df, config) for p in raw_pools if p.status == PoolStatus.UNTOUCHED]
    
    if side == PoolSide.BUY_SIDE:
        valid = [c for c in classified if c.pool.side == PoolSide.BUY_SIDE and c.pool.level > current_price]
        if not valid: return None
        # Sort by significance first, then by proximity
        return max(valid, key=lambda c: (c.significance_score, -abs(c.pool.level - current_price)))
    else:
        valid = [c for c in classified if c.pool.side == PoolSide.SELL_SIDE and c.pool.level < current_price]
        if not valid: return None
        return max(valid, key=lambda c: (c.significance_score, -abs(c.pool.level - current_price)))

# ==========================================
# 5. ANALYZE WRAPPER
# ==========================================

def analyze(df: pd.DataFrame, config: LiquidityTypeConfig = LiquidityTypeConfig()) -> Dict[str, Any]:
    """Main entry point for typed liquidity analysis."""
    if df.empty:
        return {"error": "Empty DataFrame"}
        
    raw_pools = get_liquidity_pools(df, config.liquidity_config)
    classified_pools = [classify_pool(p, df, config) for p in raw_pools]
    
    current_price = float(df.iloc[-1]['close'])
    
    # Group by type
    by_type = {}
    for cp in classified_pools:
        if cp.liquidity_type not in by_type:
            by_type[cp.liquidity_type] = []
        by_type[cp.liquidity_type].append(cp)
        
    return {
        "current_price": current_price,
        "all_classified": classified_pools,
        "by_type": by_type,
        "most_significant_buy_side": get_most_significant_pool(df, PoolSide.BUY_SIDE, config),
        "most_significant_sell_side": get_most_significant_pool(df, PoolSide.SELL_SIDE, config),
        "counts_by_type": {k.value: len(v) for k, v in by_type.items()}
    }