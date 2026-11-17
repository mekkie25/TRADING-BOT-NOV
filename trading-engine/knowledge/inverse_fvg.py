# trading-engine/knowledge/inverse_fvg.py
from knowledge.fair_value_gap import check_fvg

def check_for_ifvg(candle1, candle2, candle3, current_candle):
    """
    Checks if a previously formed FVG has been broken (invalidated) 
    and is now acting as an Inverse FVG.
    """
    
    # 1. First, check if the recent 3 candles created an FVG
    fvg = check_fvg(candle1, candle2, candle3)
    
    if fvg['type'] == "NO_FVG":
        return {"type": "NO_IFVG"}
        
    # 2. Check if the current price has broken through the FVG
    # For a BULLISH FVG to become a BEARISH IFVG, price must close BELOW the gap bottom
    if fvg['type'] == "BULLISH_FVG":
        if current_candle['close'] < fvg['gap_bottom']:
            return {
                "type": "BEARISH_IFVG",
                "gap_top": fvg['gap_top'],
                "gap_bottom": fvg['gap_bottom'],
                "midpoint": fvg['midpoint'],
                "reason": "Bullish FVG broken. Now acts as Bearish Resistance."
            }
            
    # For a BEARISH FVG to become a BULLISH IFVG, price must close ABOVE the gap top
    if fvg['type'] == "BEARISH_FVG":
        if current_candle['close'] > fvg['gap_top']:
            return {
                "type": "BULLISH_IFVG",
                "gap_top": fvg['gap_top'],
                "gap_bottom": fvg['gap_bottom'],
                "midpoint": fvg['midpoint'],
                "reason": "Bearish FVG broken. Now acts as Bullish Support."
            }
            
    return {"type": "NO_IFVG"}