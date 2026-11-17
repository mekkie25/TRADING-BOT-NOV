# trading-engine/knowledge/equilibrium.py

def calculate_equilibrium(swing_high, swing_low):
    """
    Calculates the 50% equilibrium level of a price swing.
    """
    if swing_high <= swing_low:
        return None # Invalid swing
        
    eq_level = (swing_high + swing_low) / 2
    
    return {
        "eq_level": eq_level,
        "range_size": swing_high - swing_low
    }

def check_market_zone(current_price, eq_data):
    """
    Tells the bot if the current price is in a Premium or Discount zone.
    """
    if not eq_data:
        return "UNKNOWN"
        
    eq = eq_data['eq_level']
    
    if current_price > eq:
        return "PREMIUM" # Expensive. Only look for Shorts.
    elif current_price < eq:
        return "DISCOUNT" # Cheap. Only look for Longs.
    else:
        return "EQUILIBRIUM" # Exactly at 50%. Wait for a push.

def get_fib_levels(swing_high, swing_low):
    """
    Calculates the Premium (OTE) and Discount levels.
    Standard SMC uses the 61.8% and 79% for deep pullbacks.
    """
    range_size = swing_high - swing_low
    
    return {
        "eq_50": swing_low + (range_size * 0.50), # 50%
        "premium_618": swing_low + (range_size * 0.618), # 61.8% (High Premium)
        "discount_382": swing_low + (range_size * 0.382), # 38.2% (Deep Discount)
    }