# trading-engine/knowledge/liquidity.py
import pandas as pd

# ==========================================
# 1. SWING POINT LIQUIDITY (EQUAL HIGHS/LOWS)
# ==========================================
def find_equal_highs(highs, tolerance_pips=2.0):
    if len(highs) < 2: return None
    tolerance = tolerance_pips * 0.0001
    if abs(highs[-1] - highs[-2]) <= tolerance:
        return {"level": max(highs[-1], highs[-2]), "type": "BUY_SIDE_LIQUIDITY"}
    return None

def find_equal_lows(lows, tolerance_pips=2.0):
    if len(lows) < 2: return None
    tolerance = tolerance_pips * 0.0001
    if abs(lows[-1] - lows[-2]) <= tolerance:
        return {"level": min(lows[-1], lows[-2]), "type": "SELL_SIDE_LIQUIDITY"}
    return None

# ==========================================
# 2. PREVIOUS DAY LIQUIDITY (PDH / PDL)
# ==========================================
def get_previous_day_levels(df):
    """
    Finds the Previous Day High (PDH) and Previous Day Low (PDL).
    """
    if 'timestamp' not in df.columns or len(df) < 20:
        return None
        
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    days = df['date'].unique()
    
    if len(days) < 2: return None
        
    previous_day = days[-2]
    prev_day_data = df[df['date'] == previous_day]
    
    if prev_day_data.empty: return None
        
    return {
        "PDH": prev_day_data['high'].max(),
        "PDL": prev_day_data['low'].min()
    }

# ==========================================
# 3. ASIAN RANGE LIQUIDITY
# ==========================================
def get_asian_range(df):
    """
    Calculates the Asian Range High and Low based on SAST time.
    Assumes 'timestamp' is in SAST.
    """
    if 'timestamp' not in df.columns:
        return None
        
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    
    # Asian Session is 02:00 to 11:00 SAST
    asian_bars = df[(df['hour'] >= 2) & (df['hour'] < 11)]
    
    if asian_bars.empty:
        return None
        
    return {
        "asian_high": asian_bars['high'].max(),
        "asian_low": asian_bars['low'].min()
    }

# ==========================================
# 4. SWEEP DETECTORS
# ==========================================
def check_sweep(current_candle, level, direction):
    """
    Checks if a specific level was swept.
    direction: "HIGH" or "LOW"
    """
    if not level: return False
        
    if direction == "HIGH":
        # Wick goes above, close comes back below
        return current_candle['high'] > level and current_candle['close'] < level
        
    if direction == "LOW":
        # Wick goes below, close comes back above
        return current_candle['low'] < level and current_candle['close'] > level
        
    return False