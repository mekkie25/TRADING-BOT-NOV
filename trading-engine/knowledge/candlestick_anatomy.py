# trading-engine/knowledge/candlestick_anatomy.py

def get_candle_metrics(candle):
    """
    Takes a single candle dictionary/row (with open, high, low, close)
    and returns the exact math.
    """
    open_p = candle['open']
    high = candle['high']
    low = candle['low']
    close = candle['close']

    body_top = max(open_p, close)
    body_bottom = min(open_p, close)
    body_size = body_top - body_bottom
    
    upper_wick = high - body_top
    lower_wick = body_bottom - low
    total_range = high - low

    return {
        "body_size": body_size,
        "upper_wick": upper_wick,
        "lower_wick": lower_wick,
        "total_range": total_range,
        "is_bullish": close > open_p,
        "is_bearish": close < open_p
    }

def check_rejection(candle, wick_multiplier=2.0):
    """
    Checks if a candle is a Pin Bar / Rejection.
    Rule: The wick must be X times larger than the body.
    """
    m = get_candle_metrics(candle)
    
    # Avoid dividing by zero on a perfect doji
    if m['body_size'] == 0:
        return "DOJI"

    # Bullish Rejection (Long lower wick)
    if m['lower_wick'] > (m['body_size'] * wick_multiplier):
        return "BULLISH_REJECTION"
        
    # Bearish Rejection (Long upper wick)
    if m['upper_wick'] > (m['body_size'] * wick_multiplier):
        return "BEARISH_REJECTION"
        
    return "NO_REJECTION"

def check_engulfing(prev_candle, current_candle):
    """
    Checks if the current candle body completely engulfs the previous candle body.
    """
    prev_m = get_candle_metrics(prev_candle)
    curr_m = get_candle_metrics(current_candle)

    # Bullish Engulfing: Previous was red, current is green, and current body covers previous body
    if (not prev_m['is_bullish'] and curr_m['is_bullish'] and
        get_candle_metrics(current_candle)['body_size'] > prev_m['body_size']):
        
        curr_top = max(current_candle['open'], current_candle['close'])
        curr_bottom = min(current_candle['open'], current_candle['close'])
        prev_top = max(prev_candle['open'], prev_candle['close'])
        prev_bottom = min(prev_candle['open'], prev_candle['close'])

        if curr_top >= prev_top and curr_bottom <= prev_bottom:
            return "BULLISH_ENGULFING"

    # Bearish Engulfing: Previous was green, current is red, and current body covers previous body
    if (prev_m['is_bullish'] and not curr_m['is_bullish'] and
        get_candle_metrics(current_candle)['body_size'] > prev_m['body_size']):
        
        curr_top = max(current_candle['open'], current_candle['close'])
        curr_bottom = min(current_candle['open'], current_candle['close'])
        prev_top = max(prev_candle['open'], prev_candle['close'])
        prev_bottom = min(prev_candle['open'], prev_candle['close'])

        if curr_top >= prev_top and curr_bottom <= prev_bottom:
            return "BEARISH_ENGULFING"

    return "NO_ENGULFING"

def check_invalidation(rejection_candle, next_candle, rejection_type):
    """
    Checks if the candle AFTER a rejection completely invalidates the move.
    """
    if rejection_type == "BULLISH_REJECTION":
        # If the next candle closes below the low of the rejection, buyers failed.
        if next_candle['close'] < rejection_candle['low']:
            return "INVALIDATED"
            
    if rejection_type == "BEARISH_REJECTION":
        # If the next candle closes above the high of the rejection, sellers failed.
        if next_candle['close'] > rejection_candle['high']:
            return "INVALIDATED"

    return "VALID"