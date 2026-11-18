"""Report equilibrium and price location within a supplied market range."""

import math
import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

from .market_structure import get_last_swing_high, get_last_swing_low, MarketStructureConfig

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

class RangeMode(Enum):
    SWING = "SWING"                 # Latest confirmed swing low to swing high
    EXPLICIT = "EXPLICIT"           # Manual high/low passed in
    PREVIOUS_DAY = "PREVIOUS_DAY"   # Previous daily candle's high/low

class PriceZone(Enum):
    PREMIUM = "PREMIUM"
    DISCOUNT = "DISCOUNT"
    AT_EQUILIBRIUM = "AT_EQUILIBRIUM"

@dataclass
class EquilibriumConfig:
    # Tolerance band around 50% to be considered "At Equilibrium" (e.g., 2% of range)
    equilibrium_tolerance_pct: float = 0.02
    
    # Optional 25% and 75% levels
    enable_quartiles: bool = True
    
    # Config for swing detection
    ms_config: MarketStructureConfig = None

    def __post_init__(self):
        if self.ms_config is None:
            self.ms_config = MarketStructureConfig()

@dataclass
class RangeInfo:
    high: float
    low: float
    equilibrium: float
    quartile_low: Optional[float] = None   # 25% level
    quartile_high: Optional[float] = None  # 75% level
    
    @property
    def range_size(self) -> float:
        return self.high - self.low

@dataclass
class EquilibriumResult:
    range_info: Optional[RangeInfo]
    current_zone: Optional[PriceZone]
    current_price: float
    distance_to_eq_pct: float  # How far from 50% as % of range

# ==========================================
# 2. CORE LOGIC
# ==========================================

def _build_range_info(high: float, low: float, config: EquilibriumConfig) -> RangeInfo:
    """Constructs a RangeInfo object with 50% EQ and optional 25/75 quartiles."""
    if not math.isfinite(high) or not math.isfinite(low):
        raise ValueError("Range high and low must be finite prices.")
    if high <= low:
        raise ValueError(f"Invalid range: High ({high}) must be > Low ({low})")
    
    eq = (high + low) / 2
    range_size = high - low
    
    q_low = low + (range_size * 0.25) if config.enable_quartiles else None
    q_high = low + (range_size * 0.75) if config.enable_quartiles else None
    
    return RangeInfo(
        high=high,
        low=low,
        equilibrium=eq,
        quartile_low=q_low,
        quartile_high=q_high
    )

def get_equilibrium(
    df: pd.DataFrame, 
    range_mode: RangeMode, 
    high: Optional[float] = None, 
    low: Optional[float] = None,
    config: EquilibriumConfig = EquilibriumConfig()
) -> Optional[RangeInfo]:
    """
    Calculates the range and equilibrium level based on the mode.
    """
    if df.empty:
        return None
        
    if range_mode == RangeMode.EXPLICIT:
        if high is None or low is None:
            raise ValueError("High and Low must be provided for EXPLICIT mode")
        return _build_range_info(high, low, config)
        
    elif range_mode == RangeMode.SWING:
        swing_high = get_last_swing_high(df, config.ms_config)
        swing_low = get_last_swing_low(df, config.ms_config)
        
        if not swing_high or not swing_low:
            return None
            
        return _build_range_info(swing_high.price, swing_low.price, config)
        
    elif range_mode == RangeMode.PREVIOUS_DAY:
        # Resample to daily timeframe
        # Ensure 'time' is datetime and set as index for resampling
        df_daily = df.set_index('time').resample('1D').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).dropna()
        
        if len(df_daily) < 2:
            return None
            
        # Get previous day's high/low (index -2 because -1 is today)
        prev_day = df_daily.iloc[-2]
        return _build_range_info(float(prev_day['high']), float(prev_day['low']), config)
        
    return None

def get_price_zone(price: float, range_info: RangeInfo, config: EquilibriumConfig = EquilibriumConfig()) -> PriceZone:
    """Determines if price is in Premium, Discount, or at Equilibrium."""
    if not range_info:
        return PriceZone.AT_EQUILIBRIUM
        
    tolerance = range_info.range_size * config.equilibrium_tolerance_pct
    
    if abs(price - range_info.equilibrium) <= tolerance:
        return PriceZone.AT_EQUILIBRIUM
    elif price > range_info.equilibrium:
        return PriceZone.PREMIUM
    else:
        return PriceZone.DISCOUNT

def has_price_touched_equilibrium(df: pd.DataFrame, range_info: RangeInfo, since_time: pd.Timestamp) -> bool:
    """Checks if price has tested the 50% level since a given time."""
    if not range_info:
        return False
        
    recent_candles = df[df['time'] >= since_time]
    if recent_candles.empty:
        return False
        
    eq = range_info.equilibrium
    # If any candle's low is below EQ AND high is above EQ, it touched it
    touched = ((recent_candles['low'] <= eq) & (recent_candles['high'] >= eq)).any()
    return bool(touched)

# ==========================================
# 3. ANALYZE WRAPPER
# ==========================================

def analyze(df: pd.DataFrame, range_mode: RangeMode = RangeMode.SWING, high: Optional[float] = None, low: Optional[float] = None, config: EquilibriumConfig = EquilibriumConfig()) -> Dict[str, Any]:
    """
    Main entry point for equilibrium analysis.
    """
    if df.empty:
        return {"error": "Empty DataFrame"}
        
    current_price = float(df.iloc[-1]['close'])
    
    range_info = get_equilibrium(df, range_mode, high, low, config)
    if not range_info:
        return {
            "current_price": current_price,
            "zone": None,
            "error": "Could not establish range (insufficient data)"
        }
        
    zone = get_price_zone(current_price, range_info, config)
    distance_pct = (
        abs(current_price - range_info.equilibrium)
        / range_info.range_size
        * 100
    )
    current_time = df.iloc[-1]["time"]
    zone_label = zone.value.lower().replace("_", " ")
    summary = (
        f"At {current_time}, price is {current_price} in the {zone_label} "
        f"part of the range from {range_info.low} to {range_info.high}; "
        f"equilibrium is {range_info.equilibrium}."
    )
    if config.enable_quartiles:
        summary += (
            f" The lower quartile is {range_info.quartile_low} and the upper "
            f"quartile is {range_info.quartile_high}; these are range levels, "
            "not a claim that either is a best trade area."
        )
    
    return {
        "summary": summary,
        "current_price": current_price,
        "current_time": current_time,
        "range_info": range_info,
        "zone": zone,
        "distance_to_eq_pct": distance_pct,
        "is_discount": zone == PriceZone.DISCOUNT,
        "is_premium": zone == PriceZone.PREMIUM,
        "at_or_below_lower_quartile": (
            current_price <= range_info.quartile_low
            if config.enable_quartiles and range_info.quartile_low is not None
            else False
        ),
        "at_or_above_upper_quartile": (
            current_price >= range_info.quartile_high
            if config.enable_quartiles and range_info.quartile_high is not None
            else False
        ),
    }