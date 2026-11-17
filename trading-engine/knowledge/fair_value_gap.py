# trading-engine/knowledge/fair_value_gap.py

def check_fvg(candle1, candle2, candle3):
    """
    Checks for a Fair Value Gap (FVG) over 3 consecutive candles.
    candle1 = oldest (2 bars ago)
    candle2 = middle (1 bar ago) - The explosive candle
    candle3 = newest (current bar)
    """
    
    # 1. Bullish FVG
    # Rule: The High of candle 1 must be LOWER than the Low of candle 3.
    if candle1['high'] < candle3['low']:
        gap_top = candle3['low']
        gap_bottom = candle1['high']
        gap_size = gap_top - gap_bottom
        
        # Check if the middle candle is actually bullish (it must be green)
        if candle2['close'] > candle2['open']:
            return {
                "type": "BULLISH_FVG",
                "gap_top": gap_top,
                "gap_bottom": gap_bottom,
                "size": gap_size,
                "midpoint": (gap_top + gap_bottom) / 2,
                "candle2_size": candle2['high'] - candle2['low']
            }
        
    # 2. Bearish FVG
    # Rule: The Low of candle 1 must be HIGHER than the High of candle 3.
    if candle1['low'] > candle3['high']:
        gap_top = candle1['low']
        gap_bottom = candle3['high']
        gap_size = gap_top - gap_bottom
        
        # Check if the middle candle is actually bearish (it must be red)
        if candle2['close'] < candle2['open']:
            return {
                "type": "BEARISH_FVG",
                "gap_top": gap_top,
                "gap_bottom": gap_bottom,
                "size": gap_size,
                "midpoint": (gap_top + gap_bottom) / 2,
                "candle2_size": candle2['high'] - candle2['low']
            }
        
    # No FVG found
    return {
        "type": "NO_FVG",
        "gap_top": None,
        "gap_bottom": None,
        "size": 0,
        "midpoint": None,
        "candle2_size": 0
    }

def is_price_in_fvg(current_price, fvg):
    """
    Checks if the current price has pulled back into the FVG zone.
    """
    if fvg['type'] == "NO_FVG":
        return False
        
    return fvg['gap_bottom'] <= current_price <= fvg['gap_top']

def is_fvg_invalidated(current_close, fvg):
    """
    Checks if the price has broken completely through the FVG.
    If a Bullish FVG is broken below the bottom, it is invalid.
    If a Bearish FVG is broken above the top, it is invalid.
    """
    if fvg['type'] == "BULLISH_FVG":
        # If price closes below the bottom of the gap, the bulls failed.
        return current_close < fvg['gap_bottom']
        
    if fvg['type'] == "BEARISH_FVG":
        # If price closes above the top of the gap, the bears failed.
        return current_close > fvg['gap_top']
        
    return True # If there's no FVG, it's technically invalidated