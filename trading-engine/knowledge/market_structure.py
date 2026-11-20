"""Report confirmed swing points and a descriptive market-structure state."""

import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

class TrendState(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGING = "RANGING"

class SwingType(Enum):
    HIGH = "HIGH"
    LOW = "LOW"

class BreakType(Enum):
    BOS = "BOS"       # Break of Structure (continuation)
    CHOCH = "CHOCH"   # Change of Character (reversal)
    NONE = "NONE"

class BreakDirection(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"

@dataclass
class MarketStructureConfig:
    # Number of candles required on the left and right to confirm a swing
    swing_lookback_left: int = 2
    swing_lookback_right: int = 2
    
    # Does a break require a close, or is a wick enough?
    require_close_for_break: bool = True

@dataclass
class SwingPoint:
    type: SwingType
    price: float
    occurred_at: pd.Timestamp    # The timestamp of the actual high/low candle
    confirmed_at: pd.Timestamp   # The timestamp when the right-side lookback completed
    label: str = ""              # HH, HL, LH, LL (populated dynamically)

@dataclass
class BreakEvent:
    type: BreakType
    direction: BreakDirection
    broken_swing: SwingPoint
    break_time: pd.Timestamp
    break_price: float

# ==========================================
# 2. CORE SWING DETECTION
# ==========================================

def _find_swings(df: pd.DataFrame, config: MarketStructureConfig) -> List[SwingPoint]:
    """
    Identifies raw swing highs and lows. 
    A swing is only confirmed AFTER 'swing_lookback_right' candles have closed.
    """
    swings = []
    left = config.swing_lookback_left
    right = config.swing_lookback_right
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    times = df["time"].array
    
    # We iterate through the dataframe, leaving enough room on both sides
    for i in range(left, len(df) - right):
        current_high = highs[i]
        current_low = lows[i]
        
        # Check for Swing High
        is_high = True
        for j in range(1, left + 1):
            if highs[i - j] >= current_high: is_high = False; break
        if is_high:
            for j in range(1, right + 1):
                if highs[i + j] >= current_high: is_high = False; break
                
        if is_high:
            swings.append(SwingPoint(
                type=SwingType.HIGH,
                price=float(current_high),
                occurred_at=times[i],
                confirmed_at=times[i + right]
            ))
            continue # Move to next candle

        # Check for Swing Low
        is_low = True
        for j in range(1, left + 1):
            if lows[i - j] <= current_low: is_low = False; break
        if is_low:
            for j in range(1, right + 1):
                if lows[i + j] <= current_low: is_low = False; break
                
        if is_low:
            swings.append(SwingPoint(
                type=SwingType.LOW,
                price=float(current_low),
                occurred_at=times[i],
                confirmed_at=times[i + right]
            ))

    # Sort chronologically by occurrence
    swings.sort(key=lambda x: x.occurred_at)
    return swings

def _label_swings(swings: List[SwingPoint]) -> List[SwingPoint]:
    """Labels swings as HH, HL, LH, LL based on the previous swing of the same type."""
    last_high = None
    last_low = None
    
    for swing in swings:
        if swing.type == SwingType.HIGH:
            if last_high is not None:
                swing.label = "HH" if swing.price > last_high.price else "LH"
            last_high = swing
        else:
            if last_low is not None:
                swing.label = "HL" if swing.price > last_low.price else "LL"
            last_low = swing
    return swings

# ==========================================
# 3. BREAK DETECTION (BOS / CHoCH)
# ==========================================

def _find_last_break(df: pd.DataFrame, swings: List[SwingPoint], config: MarketStructureConfig) -> BreakEvent:
    """
    Scans for the most recent break of a swing high or swing low.
    """
    if not swings:
        return BreakEvent(BreakType.NONE, BreakDirection.BULLISH, None, None, None)

    times = df["time"].array
    closes = df["close"].to_numpy()
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()

    # Iterate from the end of the dataframe backwards to find the most recent break
    for i in range(len(df) - 1, -1, -1):
        candle_time = times[i]
        
        # We only care about candles that happened AFTER the swing was confirmed
        # (To prevent look-ahead bias)
        valid_swings = [s for s in swings if s.confirmed_at < candle_time]
        
        if not valid_swings:
            continue

        last_high = next((s for s in reversed(valid_swings) if s.type == SwingType.HIGH), None)
        last_low = next((s for s in reversed(valid_swings) if s.type == SwingType.LOW), None)

        # Check Bullish Break (Breaking a High)
        if last_high:
            if config.require_close_for_break:
                broke = closes[i] > last_high.price
            else:
                broke = highs[i] > last_high.price
                
            if broke:
                # Determine if it's a BOS (continuation) or CHoCH (reversal)
                # If the last swing before the high was a HL, breaking the high is a BOS.
                # If the last swing was a LH, breaking it might be a CHoCH.
                # For simplicity, if we are currently BEARISH and break a high, it's a CHoCH.
                current_trend = _determine_trend_state(valid_swings)
                break_type = BreakType.BOS if current_trend == TrendState.BULLISH else BreakType.CHOCH
                break_price = closes[i] if config.require_close_for_break else highs[i]
                return BreakEvent(
                    break_type,
                    BreakDirection.BULLISH,
                    last_high,
                    candle_time,
                    float(break_price),
                )

        # Check Bearish Break (Breaking a Low)
        if last_low:
            if config.require_close_for_break:
                broke = closes[i] < last_low.price
            else:
                broke = lows[i] < last_low.price
                
            if broke:
                current_trend = _determine_trend_state(valid_swings)
                break_type = BreakType.BOS if current_trend == TrendState.BEARISH else BreakType.CHOCH
                break_price = closes[i] if config.require_close_for_break else lows[i]
                return BreakEvent(
                    break_type,
                    BreakDirection.BEARISH,
                    last_low,
                    candle_time,
                    float(break_price),
                )

    return BreakEvent(BreakType.NONE, BreakDirection.BULLISH, None, None, None)

def _determine_trend_state(swings: List[SwingPoint]) -> TrendState:
    """Helper to determine trend based on the last few labeled swings."""
    if len(swings) < 2:
        return TrendState.RANGING
        
    last_high = next((s for s in reversed(swings) if s.type == SwingType.HIGH), None)
    last_low = next((s for s in reversed(swings) if s.type == SwingType.LOW), None)
    
    if not last_high or not last_low:
        return TrendState.RANGING

    if last_high.label == "HH" and last_low.label == "HL":
        return TrendState.BULLISH
    elif last_high.label == "LH" and last_low.label == "LL":
        return TrendState.BEARISH
    else:
        return TrendState.RANGING

# ==========================================
# 4. PUBLIC API
# ==========================================

def get_market_structure(df: pd.DataFrame, config: MarketStructureConfig = MarketStructureConfig()) -> TrendState:
    swings = _find_swings(df, config)
    labeled_swings = _label_swings(swings)
    return _determine_trend_state(labeled_swings)

def get_last_swing_high(df: pd.DataFrame, config: MarketStructureConfig = MarketStructureConfig()) -> Optional[SwingPoint]:
    swings = _find_swings(df, config)
    return next((s for s in reversed(swings) if s.type == SwingType.HIGH), None)

def get_last_swing_low(df: pd.DataFrame, config: MarketStructureConfig = MarketStructureConfig()) -> Optional[SwingPoint]:
    swings = _find_swings(df, config)
    return next((s for s in reversed(swings) if s.type == SwingType.LOW), None)

def get_last_break(df: pd.DataFrame, config: MarketStructureConfig = MarketStructureConfig()) -> BreakEvent:
    swings = _find_swings(df, config)
    labeled_swings = _label_swings(swings)
    return _find_last_break(df, labeled_swings, config)

def analyze(df: pd.DataFrame, config: MarketStructureConfig = MarketStructureConfig()) -> Dict[str, Any]:
    """
    Main entry point. Returns full context of the market structure.
    """
    if df.empty:
        return {"error": "Empty DataFrame"}

    swings = _find_swings(df, config)
    labeled_swings = _label_swings(swings)
    trend = _determine_trend_state(labeled_swings)
    last_break = _find_last_break(df, labeled_swings, config)
    last_swing_high = next(
        (s for s in reversed(labeled_swings) if s.type == SwingType.HIGH),
        None,
    )
    last_swing_low = next(
        (s for s in reversed(labeled_swings) if s.type == SwingType.LOW),
        None,
    )
    summary = f"Market structure is {trend.value.lower()}."
    if last_swing_high is not None:
        summary += (
            f" Latest confirmed swing high is {last_swing_high.price} "
            f"(formed at {last_swing_high.occurred_at}, "
            f"confirmed at {last_swing_high.confirmed_at})."
        )
    if last_swing_low is not None:
        summary += (
            f" Latest confirmed swing low is {last_swing_low.price} "
            f"(formed at {last_swing_low.occurred_at}, "
            f"confirmed at {last_swing_low.confirmed_at})."
        )
    if last_break.type != BreakType.NONE:
        summary += (
            f" Latest reported break is {last_break.direction.value.lower()} "
            f"{last_break.type.value} at {last_break.break_price} "
            f"at {last_break.break_time}."
        )
    
    return {
        "trend": trend,
        "last_break": last_break,
        "last_swing_high": last_swing_high,
        "last_swing_low": last_swing_low,
        "summary": summary,
        "all_swings": labeled_swings
    }