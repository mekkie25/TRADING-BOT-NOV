"""
Placeholder for market_conditions.py.
Expand this later with ADX, volatility regimes, etc.
"""
from enum import Enum
import pandas as pd

class MarketCondition(Enum):
    TRENDING = "TRENDING"
    CHOPPY = "CHOPPY"
    CONSOLIDATING = "CONSOLIDATING"
    UNKNOWN = "UNKNOWN"

def get_market_condition(df: pd.DataFrame) -> MarketCondition:
    """Simple placeholder: returns TRENDING if recent close is far from old close."""
    if df.empty or len(df) < 20:
        return MarketCondition.UNKNOWN
    # Simple proxy: if the 20-period range is less than 50% of ATR, call it choppy
    range_20 = df['high'].tail(20).max() - df['low'].tail(20).min()
    atr = (df['high'] - df['low']).tail(20).mean()
    if range_20 < atr * 2:
        return MarketCondition.CHOPPY
    return MarketCondition.TRENDING