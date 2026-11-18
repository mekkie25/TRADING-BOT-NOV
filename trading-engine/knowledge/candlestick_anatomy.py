"""
Module 1: Candlestick Anatomy
Depends on: common.py only.

Purpose: Measure candle parts and identify configured candle patterns without choosing a trade.
"""

import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

@dataclass
class CandleConfig:
    """All thresholds are configurable to match specific course rules."""
    doji_body_threshold: float = 0.10 
    marubozu_body_threshold: float = 0.85 
    rejection_wick_to_body_ratio: float = 2.0 
    rejection_wick_to_range_ratio: float = 0.60 
    control_strength_threshold: float = 0.60

class Control(Enum):
    BUYERS = "BUYERS"
    SELLERS = "SELLERS"
    BALANCED = "BALANCED"

class CandleType(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    DOJI = "DOJI"

# ==========================================
# 2. DATA STRUCTURES
# ==========================================

@dataclass
class CandleAnatomy:
    body_size: float
    upper_wick: float
    lower_wick: float
    total_range: float
    body_pct_of_range: float
    direction: CandleType

@dataclass
class ControlReading:
    control: Control
    strength_score: float
    reason: str

# ==========================================
# 3. CORE FUNCTIONS
# ==========================================

def describe_candle(candle: pd.Series, config: CandleConfig = CandleConfig()) -> CandleAnatomy:
    """Calculates the raw anatomy of a single Pandas Series (candle)."""
    total_range = candle['high'] - candle['low']
    
    if total_range == 0:
        return CandleAnatomy(0, 0, 0, 0, 0, CandleType.DOJI)

    body_size = abs(candle['close'] - candle['open'])
    upper_wick = candle['high'] - max(candle['open'], candle['close'])
    lower_wick = min(candle['open'], candle['close']) - candle['low']
    body_pct = body_size / total_range

    if body_pct <= config.doji_body_threshold:
        direction = CandleType.DOJI
    elif candle['close'] > candle['open']:
        direction = CandleType.BULLISH
    else:
        direction = CandleType.BEARISH

    return CandleAnatomy(
        body_size=body_size,
        upper_wick=upper_wick,
        lower_wick=lower_wick,
        total_range=total_range,
        body_pct_of_range=body_pct,
        direction=direction
    )

def get_candle_control(candle: pd.Series, config: CandleConfig = CandleConfig()) -> ControlReading:
    """Determines who was in control and provides a numeric strength score."""
    anat = describe_candle(candle, config)
    
    if anat.total_range == 0:
        return ControlReading(Control.BALANCED, 0.0, "Zero range (flat candle)")

    if anat.direction == CandleType.BULLISH:
        strength = anat.body_pct_of_range
        if strength >= config.control_strength_threshold:
            return ControlReading(Control.BUYERS, strength, f"Bullish body dominates {strength:.0%} of range")
        return ControlReading(Control.BALANCED, strength, "Bullish, but wicks show opposing pressure")

    elif anat.direction == CandleType.BEARISH:
        strength = anat.body_pct_of_range
        if strength >= config.control_strength_threshold:
            return ControlReading(Control.SELLERS, strength, f"Bearish body dominates {strength:.0%} of range")
        return ControlReading(Control.BALANCED, strength, "Bearish, but wicks show opposing pressure")
        
    else:
        return ControlReading(Control.BALANCED, 0.0, "Doji - Indecision / equilibrium")

def is_rejection(candle: pd.Series, side: str, config: CandleConfig = CandleConfig()) -> bool:
    """
    Checks if a candle is a rejection candle.
    side: 'TOP' (bearish rejection) or 'BOTTOM' (bullish rejection)
    """
    anat = describe_candle(candle, config)
    
    if anat.total_range == 0:
        return False

    if side.upper() == 'TOP':
        wick = anat.upper_wick
    elif side.upper() == 'BOTTOM':
        wick = anat.lower_wick
    else:
        raise ValueError("Side must be 'TOP' or 'BOTTOM'")

    wick_to_body = wick / anat.body_size if anat.body_size > 0 else float('inf')
    wick_to_range = wick / anat.total_range

    return (wick_to_body >= config.rejection_wick_to_body_ratio) and (wick_to_range >= config.rejection_wick_to_range_ratio)

# ==========================================
# 4. PATTERN ANALYSIS (DataFrame focused)
# ==========================================

def _is_engulfing(c1: pd.Series, c2: pd.Series, config: CandleConfig) -> str:
    anat1 = describe_candle(c1, config)
    anat2 = describe_candle(c2, config)
    
    if anat2.direction == CandleType.BULLISH and anat1.direction == CandleType.BEARISH:
        if c2['close'] > c1['open'] and c2['open'] < c1['close']:
            return "BULLISH_ENGULFING"
    elif anat2.direction == CandleType.BEARISH and anat1.direction == CandleType.BULLISH:
        if c2['close'] < c1['open'] and c2['open'] > c1['close']:
            return "BEARISH_ENGULFING"
    return "NONE"

def _is_inside_bar(c1: pd.Series, c2: pd.Series) -> bool:
    return (c2['high'] <= c1['high']) and (c2['low'] >= c1['low'])

def _is_outside_bar(c1: pd.Series, c2: pd.Series) -> bool:
    return (c2['high'] > c1['high']) and (c2['low'] < c1['low'])

def analyze(df: pd.DataFrame, config: CandleConfig = CandleConfig(), lookback: int = 3) -> Dict[str, Any]:
    """
    Main entry point. Analyzes the end of a DataFrame.
    Expects candles sorted chronologically (oldest to newest). Multi-candle
    patterns are only checked when enough candles are available.
    """
    if lookback < 1:
        raise ValueError("lookback must be at least one candle")
    if df.empty:
        return {"error": "No candles provided."}

    # Isolate the most recent candles for analysis
    recent = df.tail(lookback)
    
    current = recent.iloc[-1]
    result = {
        "current_anatomy": describe_candle(current, config),
        "current_control": get_candle_control(current, config),
        "is_rejection_top": is_rejection(current, "TOP", config),
        "is_rejection_bottom": is_rejection(current, "BOTTOM", config),
        "patterns": []
    }

    # Single candle patterns
    anat = result["current_anatomy"]
    if anat.direction == CandleType.DOJI:
        result["patterns"].append("DOJI")
    if anat.body_pct_of_range >= config.marubozu_body_threshold:
        result["patterns"].append("MARUBOZU")

    # Two candle patterns
    if len(recent) >= 2:
        prev = recent.iloc[-2]
        engulf = _is_engulfing(prev, current, config)
        if engulf != "NONE":
            result["patterns"].append(engulf)
        if _is_inside_bar(prev, current):
            result["patterns"].append("INSIDE_BAR")
        if _is_outside_bar(prev, current):
            result["patterns"].append("OUTSIDE_BAR")

    # Three candle patterns (Morning/Evening Star logic)
    if len(recent) >= 3:
        c3 = recent.iloc[-3]
        c2 = recent.iloc[-2]
        c1 = recent.iloc[-1]
        anat3 = describe_candle(c3, config)
        anat1 = describe_candle(c1, config)
        
        if (anat3.direction == CandleType.BEARISH and 
            describe_candle(c2, config).direction == CandleType.DOJI and 
            anat1.direction == CandleType.BULLISH and c1['close'] > (c3['open'] + c3['close'])/2):
            result["patterns"].append("MORNING_STAR")
            
        if (anat3.direction == CandleType.BULLISH and 
            describe_candle(c2, config).direction == CandleType.DOJI and 
            anat1.direction == CandleType.BEARISH and c1['close'] < (c3['open'] + c3['close'])/2):
            result["patterns"].append("EVENING_STAR")

    return result