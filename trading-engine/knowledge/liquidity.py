"""
Module 8: Liquidity
Depends on: market_structure.py, sessions.py, common.py.

Purpose: See where liquidity is resting and why price is drawn to it.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple

from .market_structure import _find_swings, SwingPoint, SwingType, MarketStructureConfig

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

class PoolSide(Enum):
    BUY_SIDE = "BUY_SIDE"   # Resting above highs (Short stop losses / Buy stops)
    SELL_SIDE = "SELL_SIDE" # Resting below lows (Long stop losses / Sell stops)

class PoolStatus(Enum):
    UNTOUCHED = "UNTOUCHED"
    SWEPT = "SWEPT"
    BROKEN = "BROKEN"

class LiquidityEvent(Enum):
    SWEEP = "SWEEP"
    BREAK = "BREAK"
    NONE = "NONE"

@dataclass
class LiquidityConfig:
    # How close must two highs/lows be to be considered "Equal"?
    # Expressed as a fraction of ATR (e.g., 0.10 = within 10% of ATR)
    equality_tolerance_atr: float = 0.10
    atr_period: int = 14
    
    # Must price close back inside the range to count as a sweep?
    sweep_requires_close_back: bool = True
    
    # Require a body close to count as a break?
    break_requires_body_close: bool = True
    
    # Minimum number of swings to form a pool
    min_swings_for_pool: int = 2
    
    ms_config: MarketStructureConfig = None

    def __post_init__(self):
        if self.ms_config is None:
            self.ms_config = MarketStructureConfig()

@dataclass
class LiquidityPool:
    side: PoolSide
    level: float              # The price level of the liquidity
    formed_at: pd.Timestamp   # When the pool was created (last swing time)
    swing_count: int          # How many equal highs/lows formed this
    status: PoolStatus = PoolStatus.UNTOUCHED

@dataclass
class SweepEvent:
    pool: LiquidityPool
    event_type: LiquidityEvent
    event_time: pd.Timestamp
    wick_extreme: float       # How far price pushed beyond the level
    close_price: float

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def _calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(period).mean()

def _cluster_levels(swings: List[SwingPoint], tolerance: float) -> List[Tuple[float, int, pd.Timestamp]]:
    """
    Groups swings that are within 'tolerance' of each other.
    Returns a list of (level, count, last_formed_at).
    """
    if not swings:
        return []
        
    # Sort by price
    sorted_swings = sorted(swings, key=lambda s: s.price)
    clusters = []
    
    current_cluster = [sorted_swings[0]]
    
    for swing in sorted_swings[1:]:
        # If this swing is within tolerance of the current cluster's average
        cluster_avg = sum(s.price for s in current_cluster) / len(current_cluster)
        if abs(swing.price - cluster_avg) <= tolerance:
            current_cluster.append(swing)
        else:
            # Close cluster, start new one
            if len(current_cluster) >= 2:
                # Use the most extreme point as the level (highest for highs, lowest for lows)
                level = max(s.price for s in current_cluster) if current_cluster[0].type == SwingType.HIGH else min(s.price for s in current_cluster)
                last_time = max(s.occurred_at for s in current_cluster)
                clusters.append((level, len(current_cluster), last_time))
            current_cluster = [swing]
            
    # Don't forget the last cluster
    if len(current_cluster) >= 2:
        level = max(s.price for s in current_cluster) if current_cluster[0].type == SwingType.HIGH else min(s.price for s in current_cluster)
        last_time = max(s.occurred_at for s in current_cluster)
        clusters.append((level, len(current_cluster), last_time))
        
    return clusters

# ==========================================
# 3. CORE LOGIC
# ==========================================

def get_liquidity_pools(df: pd.DataFrame, config: LiquidityConfig = LiquidityConfig()) -> List[LiquidityPool]:
    """
    Finds Equal Highs (Buy-Side Liquidity) and Equal Lows (Sell-Side Liquidity).
    """
    if df.empty or len(df) < 10:
        return []

    atr_series = _calculate_atr(df, config.atr_period)
    current_atr = atr_series.iloc[-1]
    if pd.isna(current_atr) or current_atr == 0:
        return []
        
    tolerance = current_atr * config.equality_tolerance_atr
    
    swings = _find_swings(df, config.ms_config)
    swing_highs = [s for s in swings if s.type == SwingType.HIGH]
    swing_lows = [s for s in swings if s.type == SwingType.LOW]
    
    pools = []
    
    # Buy-Side Liquidity (Above Highs)
    high_clusters = _cluster_levels(swing_highs, tolerance)
    for level, count, formed_at in high_clusters:
        if count >= config.min_swings_for_pool:
            pools.append(LiquidityPool(
                side=PoolSide.BUY_SIDE,
                level=level,
                formed_at=formed_at,
                swing_count=count
            ))
            
    # Sell-Side Liquidity (Below Lows)
    low_clusters = _cluster_levels(swing_lows, tolerance)
    for level, count, formed_at in low_clusters:
        if count >= config.min_swings_for_pool:
            pools.append(LiquidityPool(
                side=PoolSide.SELL_SIDE,
                level=level,
                formed_at=formed_at,
                swing_count=count
            ))
            
    # Update Status of each pool based on price action AFTER formation
    for pool in pools:
        post_formed = df[df['time'] > pool.formed_at]
        for _, candle in post_formed.iterrows():
            if pool.status != PoolStatus.UNTOUCHED:
                break # Already resolved
                
            if pool.side == PoolSide.BUY_SIDE:
                # Price traded above the level
                if candle['high'] > pool.level:
                    if config.break_requires_body_close and candle['close'] > pool.level:
                        pool.status = PoolStatus.BROKEN
                    elif not config.break_requires_body_close:
                        pool.status = PoolStatus.BROKEN
                    elif config.sweep_requires_close_back and candle['close'] < pool.level:
                        pool.status = PoolStatus.SWEPT
                        
            elif pool.side == PoolSide.SELL_SIDE:
                # Price traded below the level
                if candle['low'] < pool.level:
                    if config.break_requires_body_close and candle['close'] < pool.level:
                        pool.status = PoolStatus.BROKEN
                    elif not config.break_requires_body_close:
                        pool.status = PoolStatus.BROKEN
                    elif config.sweep_requires_close_back and candle['close'] > pool.level:
                        pool.status = PoolStatus.SWEPT
                        
    return pools

def get_recent_sweeps(df: pd.DataFrame, lookback: int = 50, config: LiquidityConfig = LiquidityConfig()) -> List[SweepEvent]:
    """
    Returns liquidity sweeps that have occurred in the last N candles.
    """
    pools = get_liquidity_pools(df, config)
    sweeps = []
    
    recent_df = df.tail(lookback)
    
    for pool in pools:
        if pool.status != PoolStatus.SWEPT:
            continue
            
        # Find the candle that caused the sweep
        for _, candle in recent_df.iterrows():
            if candle['time'] <= pool.formed_at:
                continue
                
            is_sweep = False
            wick_extreme = 0.0
            
            if pool.side == PoolSide.BUY_SIDE and candle['high'] > pool.level and candle['close'] < pool.level:
                is_sweep = True
                wick_extreme = candle['high']
            elif pool.side == PoolSide.SELL_SIDE and candle['low'] < pool.level and candle['close'] > pool.level:
                is_sweep = True
                wick_extreme = candle['low']
                
            if is_sweep:
                sweeps.append(SweepEvent(
                    pool=pool,
                    event_type=LiquidityEvent.SWEEP,
                    event_time=candle['time'],
                    wick_extreme=float(wick_extreme),
                    close_price=float(candle['close'])
                ))
                break # Move to next pool
                
    sweeps.sort(key=lambda x: x.event_time, reverse=True)
    return sweeps

# ==========================================
# 4. UTILITY FUNCTIONS
# ==========================================

def get_nearest_pool_above(pools: List[LiquidityPool], price: float) -> Optional[LiquidityPool]:
    """Finds the nearest UNTOUCHED Buy-Side pool above current price."""
    valid = [p for p in pools if p.side == PoolSide.BUY_SIDE and p.status == PoolStatus.UNTOUCHED and p.level > price]
    if not valid:
        return None
    return min(valid, key=lambda p: p.level)

def get_nearest_pool_below(pools: List[LiquidityPool], price: float) -> Optional[LiquidityPool]:
    """Finds the nearest UNTOUCHED Sell-Side pool below current price."""
    valid = [p for p in pools if p.side == PoolSide.SELL_SIDE and p.status == PoolStatus.UNTOUCHED and p.level < price]
    if not valid:
        return None
    return max(valid, key=lambda p: p.level)

# ==========================================
# 5. ANALYZE WRAPPER
# ==========================================

def analyze(df: pd.DataFrame, config: LiquidityConfig = LiquidityConfig()) -> Dict[str, Any]:
    """Main entry point for liquidity analysis."""
    if df.empty:
        return {"error": "Empty DataFrame"}
        
    pools = get_liquidity_pools(df, config)
    current_price = float(df.iloc[-1]['close'])
    
    recent_sweeps = get_recent_sweeps(df, lookback=50, config=config)
    
    return {
        "current_price": current_price,
        "total_pools": len(pools),
        "untouched_pools": [p for p in pools if p.status == PoolStatus.UNTOUCHED],
        "swept_pools": [p for p in pools if p.status == PoolStatus.SWEPT],
        "nearest_buy_side": get_nearest_pool_above(pools, current_price),
        "nearest_sell_side": get_nearest_pool_below(pools, current_price),
        "recent_sweeps": recent_sweeps
    }