"""
Module 5: Fair Value Gaps (FVG)
Depends on: candlesticks.py, common.py.

Purpose: Spot fair value gaps on any chart and know what they mean.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

class FVGDirection(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"

class FVGStatus(Enum):
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"

class FillCriteria(Enum):
    WICK_TOUCH = "WICK_TOUCH"      # Any touch of the gap invalidates it
    FIFTY_PERCENT = "FIFTY_PERCENT" # Price must reach the midpoint (CE)
    FULL_CLOSE = "FULL_CLOSE"       # Price must close beyond the opposite side of the gap

@dataclass
class FVGConfig:
    # Filter noise: Gap must be at least this size relative to ATR
    min_gap_atr_multiple: float = 0.20
    atr_period: int = 14
    
    # What counts as a "filled" gap?
    fill_criteria: FillCriteria = FillCriteria.FIFTY_PERCENT

@dataclass
class FairValueGap:
    direction: FVGDirection
    top: float
    bottom: float
    midpoint: float
    creation_time: pd.Timestamp
    status: FVGStatus = FVGStatus.OPEN
    
    @property
    def height(self) -> float:
        return self.top - self.bottom

# ==========================================
# 2. CORE LOGIC
# ==========================================

def _calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Helper to calculate ATR for the gap size filter."""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(period).mean()

def get_active_fvgs(df: pd.DataFrame, direction: Optional[FVGDirection] = None, config: FVGConfig = FVGConfig()) -> List[FairValueGap]:
    """
    Scans the dataframe for FVGs and tracks their status up to the current candle.
    """
    if len(df) < 3:
        return []

    # Calculate ATR for the filter
    atr_series = _calculate_atr(df, config.atr_period)
    
    active_fvgs: List[FairValueGap] = []
    
    # We iterate through history to find gaps, then track price action to update status
    for i in range(2, len(df)):
        c1 = df.iloc[i-2]
        c2 = df.iloc[i-1]
        c3 = df.iloc[i]
        
        # 1. Detect NEW gaps at candle 3 close
        current_atr = atr_series.iloc[i]
        
        # Bullish FVG: High of C1 < Low of C3
        if c1['high'] < c3['low']:
            gap_size = c3['low'] - c1['high']
            if not pd.isna(current_atr) and gap_size >= (current_atr * config.min_gap_atr_multiple):
                if direction is None or direction == FVGDirection.BULLISH:
                    active_fvgs.append(FairValueGap(
                        direction=FVGDirection.BULLISH,
                        top=float(c3['low']),
                        bottom=float(c1['high']),
                        midpoint=float((c3['low'] + c1['high']) / 2),
                        creation_time=c3['time'],
                        status=FVGStatus.OPEN
                    ))
        
        # Bearish FVG: Low of C1 > High of C3
        elif c1['low'] > c3['high']:
            gap_size = c1['low'] - c3['high']
            if not pd.isna(current_atr) and gap_size >= (current_atr * config.min_gap_atr_multiple):
                if direction is None or direction == FVGDirection.BEARISH:
                    active_fvgs.append(FairValueGap(
                        direction=FVGDirection.BEARISH,
                        top=float(c1['low']),
                        bottom=float(c3['high']),
                        midpoint=float((c1['low'] + c3['high']) / 2),
                        creation_time=c3['time'],
                        status=FVGStatus.OPEN
                    ))

        # 2. Update status of EXISTING gaps with the current candle (c3)
        # We only check gaps created BEFORE this candle
        for fvg in active_fvgs:
            if fvg.creation_time >= c3['time'] or fvg.status == FVGStatus.FILLED:
                continue
            
            _update_fvg_status(fvg, c3, config.fill_criteria)

    return active_fvgs

def _update_fvg_status(fvg: FairValueGap, candle: pd.Series, criteria: FillCriteria):
    """Updates the status of a gap based on the latest candle."""
    if fvg.direction == FVGDirection.BULLISH:
        # Price coming down into the gap
        if criteria == FillCriteria.WICK_TOUCH:
            if candle['low'] <= fvg.top:
                fvg.status = FVGStatus.FILLED
        elif criteria == FillCriteria.FIFTY_PERCENT:
            if candle['low'] <= fvg.midpoint:
                # If it closed below the bottom, it's dead
                if candle['close'] < fvg.bottom:
                    fvg.status = FVGStatus.FILLED
                else:
                    fvg.status = FVGStatus.PARTIALLY_FILLED
        elif criteria == FillCriteria.FULL_CLOSE:
            if candle['close'] < fvg.bottom:
                fvg.status = FVGStatus.FILLED
            elif candle['low'] < fvg.top:
                fvg.status = FVGStatus.PARTIALLY_FILLED
                
    elif fvg.direction == FVGDirection.BEARISH:
        # Price coming up into the gap
        if criteria == FillCriteria.WICK_TOUCH:
            if candle['high'] >= fvg.bottom:
                fvg.status = FVGStatus.FILLED
        elif criteria == FillCriteria.FIFTY_PERCENT:
            if candle['high'] >= fvg.midpoint:
                if candle['close'] > fvg.top:
                    fvg.status = FVGStatus.FILLED
                else:
                    fvg.status = FVGStatus.PARTIALLY_FILLED
        elif criteria == FillCriteria.FULL_CLOSE:
            if candle['close'] > fvg.top:
                fvg.status = FVGStatus.FILLED
            elif candle['high'] > fvg.bottom:
                fvg.status = FVGStatus.PARTIALLY_FILLED

# ==========================================
# 3. UTILITY FUNCTIONS
# ==========================================

def get_nearest_fvg(fvgs: List[FairValueGap], current_price: float, direction: FVGDirection) -> Optional[FairValueGap]:
    """Finds the closest unfilled FVG in the specified direction."""
    valid_fvgs = [f for f in fvgs if f.direction == direction and f.status != FVGStatus.FILLED]
    
    if not valid_fvgs:
        return None
        
    if direction == FVGDirection.BULLISH:
        # For bullish, we want the gap below current price. Closest = highest bottom
        valid_fvgs = [f for f in valid_fvgs if f.top <= current_price]
        if not valid_fvgs: return None
        return max(valid_fvgs, key=lambda f: f.top)
    else:
        # For bearish, we want the gap above current price. Closest = lowest top
        valid_fvgs = [f for f in valid_fvgs if f.bottom >= current_price]
        if not valid_fvgs: return None
        return min(valid_fvgs, key=lambda f: f.bottom)

def is_price_in_fvg(price: float, fvg: FairValueGap) -> bool:
    """Checks if the current price is inside the gap."""
    return fvg.bottom <= price <= fvg.top

# ==========================================
# 4. ANALYZE WRAPPER
# ==========================================

def analyze(df: pd.DataFrame, config: FVGConfig = FVGConfig()) -> Dict[str, Any]:
    """
    Main entry point. Returns active gaps and their context.
    """
    if df.empty:
        return {"error": "Empty DataFrame"}
        
    all_fvgs = get_active_fvgs(df, config=config)
    active_fvgs = [f for f in all_fvgs if f.status != FVGStatus.FILLED]
    current_price = float(df.iloc[-1]['close'])
    
    return {
        "current_price": current_price,
        "active_bullish_fvgs": [f for f in active_fvgs if f.direction == FVGDirection.BULLISH],
        "active_bearish_fvgs": [f for f in active_fvgs if f.direction == FVGDirection.BEARISH],
        "nearest_bullish": get_nearest_fvg(all_fvgs, current_price, FVGDirection.BULLISH),
        "nearest_bearish": get_nearest_fvg(all_fvgs, current_price, FVGDirection.BEARISH)
    }