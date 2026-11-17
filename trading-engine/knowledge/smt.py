"""
Module 10: SMT Divergence (Smart Money Technique)
Depends on: market_structure.py, common.py.

Purpose: Compare two related markets and catch when they disagree.
"""

import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple

from .market_structure import _find_swings, SwingPoint, SwingType, MarketStructureConfig

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

class CorrelationType(Enum):
    POSITIVE = "POSITIVE"   # e.g., EURUSD & GBPUSD
    INVERSE = "INVERSE"     # e.g., EURUSD & DXY

class SMTDirection(Enum):
    BULLISH = "BULLISH"     # Reversal to upside expected
    BEARISH = "BEARISH"     # Reversal to downside expected

@dataclass
class SMTConfig:
    # Maximum allowed time difference between the two swing points (in minutes)
    # to be considered a valid comparison
    max_time_offset_minutes: int = 60
    
    # Number of recent swings to compare
    lookback_swings: int = 5
    
    ms_config: MarketStructureConfig = None

    def __post_init__(self):
        if self.ms_config is None:
            self.ms_config = MarketStructureConfig()

@dataclass
class SMTDivergence:
    direction: SMTDirection
    swing_a: SwingPoint
    swing_b: SwingPoint
    confirmed_at: pd.Timestamp  # When the second swing was confirmed
    symbol_a_label: str
    symbol_b_label: str
    divergence_type: str  # "HH_LH" or "LL_HL"

# ==========================================
# 2. CORE LOGIC
# ==========================================

def _align_dataframes(df_a: pd.DataFrame, df_b: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ensures both DataFrames have the same time range.
    Trims the longer one to match the shorter one.
    """
    if df_a.empty or df_b.empty:
        return df_a, df_b
        
    start = max(df_a['time'].min(), df_b['time'].min())
    end = min(df_a['time'].max(), df_b['time'].max())
    
    df_a_aligned = df_a[(df_a['time'] >= start) & (df_a['time'] <= end)].reset_index(drop=True)
    df_b_aligned = df_b[(df_b['time'] >= start) & (df_b['time'] <= end)].reset_index(drop=True)
    
    return df_a_aligned, df_b_aligned

def _flip_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Flips prices for inverse correlation comparison (e.g., DXY)."""
    df_flipped = df.copy()
    # To flip: open becomes high-ish, close becomes low-ish.
    # The easiest way to compare inverse is to multiply all prices by -1
    # so a "high" on the inverse becomes a "low" on the primary.
    for col in ['open', 'high', 'low', 'close']:
        df_flipped[col] = -df_flipped[col]
    # After flipping, the new high = -old_low, new low = -old_high
    df_flipped['high'] = -df['low']
    df_flipped['low'] = -df['high']
    return df_flipped

def _find_smt_divergence(
    swings_a: List[SwingPoint], 
    swings_b: List[SwingPoint],
    config: SMTConfig
) -> Optional[SMTDivergence]:
    """
    Compares the last N swing highs/lows between two markets.
    """
    # Get recent swing highs and lows
    highs_a = [s for s in swings_a if s.type == SwingType.HIGH][-config.lookback_swings:]
    lows_a = [s for s in swings_a if s.type == SwingType.LOW][-config.lookback_swings:]
    highs_b = [s for s in swings_b if s.type == SwingType.HIGH][-config.lookback_swings:]
    lows_b = [s for s in swings_b if s.type == SwingType.LOW][-config.lookback_swings:]

    # Check Bearish SMT (at Highs)
    # Look for a swing high in A that made a Higher High, but the corresponding one in B made a Lower High
    for i in range(len(highs_a) - 1, 0, -1):
        sa_curr = highs_a[i]
        sa_prev = highs_a[i-1]
        
        # Find matching swing in B (closest in time)
        sb_match = next((s for s in reversed(highs_b) if abs((s.occurred_at - sa_curr.occurred_at).total_seconds()) <= config.max_time_offset_minutes * 60), None)
        sb_prev = next((s for s in reversed(highs_b) if abs((s.occurred_at - sa_prev.occurred_at).total_seconds()) <= config.max_time_offset_minutes * 60), None)
        
        if sb_match and sb_prev:
            a_higher_high = sa_curr.price > sa_prev.price
            b_lower_high = sb_match.price < sb_prev.price
            
            if a_higher_high and b_lower_high:
                # We have a bearish divergence! 
                # Confirm when B's swing was confirmed (the lagging one)
                return SMTDivergence(
                    direction=SMTDirection.BEARISH,
                    swing_a=sa_curr,
                    swing_b=sb_match,
                    confirmed_at=max(sa_curr.confirmed_at, sb_match.confirmed_at),
                    symbol_a_label="A",
                    symbol_b_label="B",
                    divergence_type="HH_LH"
                )

    # Check Bullish SMT (at Lows)
    # Look for a swing low in A that made a Lower Low, but the one in B made a Higher Low
    for i in range(len(lows_a) - 1, 0, -1):
        sa_curr = lows_a[i]
        sa_prev = lows_a[i-1]
        
        sb_match = next((s for s in reversed(lows_b) if abs((s.occurred_at - sa_curr.occurred_at).total_seconds()) <= config.max_time_offset_minutes * 60), None)
        sb_prev = next((s for s in reversed(lows_b) if abs((s.occurred_at - sa_prev.occurred_at).total_seconds()) <= config.max_time_offset_minutes * 60), None)
        
        if sb_match and sb_prev:
            a_lower_low = sa_curr.price < sa_prev.price
            b_higher_low = sb_match.price > sb_prev.price
            
            if a_lower_low and b_higher_low:
                return SMTDivergence(
                    direction=SMTDirection.BULLISH,
                    swing_a=sa_curr,
                    swing_b=sb_match,
                    confirmed_at=max(sa_curr.confirmed_at, sb_match.confirmed_at),
                    symbol_a_label="A",
                    symbol_b_label="B",
                    divergence_type="LL_HL"
                )

    return None

# ==========================================
# 3. PUBLIC API
# ==========================================

def get_smt_divergence(
    df_a: pd.DataFrame, 
    df_b: pd.DataFrame, 
    correlation: CorrelationType = CorrelationType.POSITIVE,
    config: SMTConfig = SMTConfig()
) -> Optional[SMTDivergence]:
    """
    Finds the most recent SMT divergence between two symbols.
    """
    # 1. Align data
    df_a_aligned, df_b_aligned = _align_dataframes(df_a, df_b)
    if df_a_aligned.empty or df_b_aligned.empty:
        return None
        
    # 2. Handle inverse correlation
    if correlation == CorrelationType.INVERSE:
        df_b_aligned = _flip_prices(df_b_aligned)
        
    # 3. Find swings
    swings_a = _find_swings(df_a_aligned, config.ms_config)
    swings_b = _find_swings(df_b_aligned, config.ms_config)
    
    if not swings_a or not swings_b:
        return None
        
    # 4. Find divergence
    return _find_smt_divergence(swings_a, swings_b, config)

def get_recent_divergences(
    df_a: pd.DataFrame, 
    df_b: pd.DataFrame, 
    correlation: CorrelationType = CorrelationType.POSITIVE,
    lookback_candles: int = 200,
    config: SMTConfig = SMTConfig()
) -> List[SMTDivergence]:
    """Finds all divergences in the recent lookback window."""
    # This is a simpler approach: check divergence at every confirmed swing
    divergences = []
    df_a_aligned, df_b_aligned = _align_dataframes(df_a, df_b)
    
    if df_a_aligned.empty or df_b_aligned.empty:
        return []
        
    if correlation == CorrelationType.INVERSE:
        df_b_aligned = _flip_prices(df_b_aligned)
        
    swings_a = _find_swings(df_a_aligned, config.ms_config)
    
    # For each swing confirmed within the lookback, check divergence
    cutoff_time = df_a_aligned['time'].max() - pd.Timedelta(hours=lookback_candles) # Approximate
    
    for confirmed_swing in [s for s in swings_a if s.confirmed_at > cutoff_time]:
        # Truncate dataframes to only include data up to when the swing was confirmed
        df_a_trunc = df_a_aligned[df_a_aligned['time'] <= confirmed_swing.confirmed_at]
        df_b_trunc = df_b_aligned[df_b_aligned['time'] <= confirmed_swing.confirmed_at]
        
        div = get_smt_divergence(df_a_trunc, df_b_trunc, correlation, config)
        if div and div.confirmed_at == confirmed_swing.confirmed_at:
             divergences.append(div)
             
    return divergences

# ==========================================
# 4. ANALYZE WRAPPER
# ==========================================

def analyze(
    df_a: pd.DataFrame, 
    df_b: pd.DataFrame, 
    correlation: CorrelationType = CorrelationType.POSITIVE,
    config: SMTConfig = SMTConfig()
) -> Dict[str, Any]:
    """Main entry point for SMT analysis."""
    if df_a.empty or df_b.empty:
        return {"error": "One or both DataFrames are empty"}
        
    divergence = get_smt_divergence(df_a, df_b, correlation, config)
    
    return {
        "has_divergence": divergence is not None,
        "divergence": divergence,
        "correlation_used": correlation.value
    }