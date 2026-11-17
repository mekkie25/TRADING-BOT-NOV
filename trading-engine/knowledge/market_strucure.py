# trading-engine/knowledge/market_structure.py
import pandas as pd

def find_swings(df, lookback=3):
    """
    Finds Swing Highs and Swing Lows using a fractal method.
    A Swing High must be higher than 'lookback' candles to its left AND right.
    """
    # Create columns to hold the swing points
    df['swing_high'] = None
    df['swing_low'] = None

    for i in range(lookback, len(df) - lookback):
        # Check for Swing High
        is_high = True
        for j in range(1, lookback + 1):
            if df['high'].iloc[i] <= df['high'].iloc[i - j] or df['high'].iloc[i] <= df['high'].iloc[i + j]:
                is_high = False
                break
        if is_high:
            df.at[df.index[i], 'swing_high'] = df['high'].iloc[i]

        # Check for Swing Low
        is_low = True
        for j in range(1, lookback + 1):
            if df['low'].iloc[i] >= df['low'].iloc[i - j] or df['low'].iloc[i] >= df['low'].iloc[i + j]:
                is_low = False
                break
        if is_low:
            df.at[df.index[i], 'swing_low'] = df['low'].iloc[i]

    return df

def determine_market_structure(df, lookback=3):
    """
    Analyzes the swings to return the current market state: 
    BULLISH, BEARISH, RANGING, or CHOPPY.
    Also detects BOS (Break of Structure) and CHoCH (Change of Character).
    """
    df = find_swings(df, lookback)
    
    # Get all swing highs and lows
    swing_highs = df['swing_high'].dropna()
    swing_lows = df['swing_low'].dropna()

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {"state": "UNDEFINED", "event": "NONE", "reason": "Not enough swings"}

    # Get the last 2 swings
    last_high = swing_highs.iloc[-1]
    prev_high = swing_highs.iloc[-2]
    last_low = swing_lows.iloc[-1]
    prev_low = swing_lows.iloc[-2]

    # 1. BULLISH STRUCTURE (Higher Highs, Higher Lows)
    if last_high > prev_high and last_low > prev_low:
        return {
            "state": "BULLISH", 
            "event": "NONE", 
            "reason": "Making Higher Highs and Higher Lows",
            "key_level": last_low # The most recent higher low
        }

    # 2. BEARISH STRUCTURE (Lower Highs, Lower Lows)
    if last_high < prev_high and last_low < prev_low:
        return {
            "state": "BEARISH", 
            "event": "NONE", 
            "reason": "Making Lower Highs and Lower Lows",
            "key_level": last_high # The most recent lower high
        }

    # 3. RANGING (Equal Highs and Lows)
    if abs(last_high - prev_high) < (last_high * 0.0005) and abs(last_low - prev_low) < (last_low * 0.0005):
        return {
            "state": "RANGING", 
            "event": "NONE", 
            "reason": "Equal Highs and Lows",
            "key_level": (last_high + last_low) / 2
        }

    # 4. CHOPPY / INDECISION
    return {"state": "CHOPPY", "event": "NONE", "reason": "Mixed Signals"}

def check_for_choch(df, current_price, lookback=3):
    """
    Checks if the current price has just caused a Change of Character (CHoCH).
    A CHoCH happens when price breaks the most recent Swing Low in a Bullish trend, or Swing High in a Bearish trend.
    """
    df = find_swings(df, lookback)
    swing_highs = df['swing_high'].dropna()
    swing_lows = df['swing_low'].dropna()
    
    current_structure = determine_market_structure(df)
    
    if current_structure['state'] == "BULLISH":
        # If we break below the last Higher Low, it's a CHoCH (Reversal to Bearish)
        if current_price < current_structure['key_level']:
            return "CHoCH_BEARISH"
            
    if current_structure['state'] == "BEARISH":
        # If we break above the last Lower High, it's a CHoCH (Reversal to Bullish)
        if current_price > current_structure['key_level']:
            return "CHoCH_BULLISH"
            
    return "NONE"