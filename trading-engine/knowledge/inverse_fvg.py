"""Detect and report configured inversions of fair value gaps."""

import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any

from .fair_value_gap import FairValueGap, FVGDirection, FVGStatus, get_active_fvgs, FVGConfig

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

class IFVGStatus(Enum):
    FRESH = "FRESH"         # Just inverted, price hasn't returned yet
    RETESTED = "RETESTED"   # Price has come back to test the new zone
    FAILED = "FAILED"       # Price has broken through the new zone as well

@dataclass
class IFVGConfig:
    fvg_config: FVGConfig = None
    # Do we require a full body close through the far edge?
    require_body_close_through: bool = True

    def __post_init__(self):
        if self.fvg_config is None:
            self.fvg_config = FVGConfig()

@dataclass
class InverseFVG:
    original_fvg: FairValueGap
    inverted_at: pd.Timestamp
    new_direction: FVGDirection
    status: IFVGStatus = IFVGStatus.FRESH
    retest_time: Optional[pd.Timestamp] = None
    
    @property
    def top(self) -> float:
        return self.original_fvg.top
        
    @property
    def bottom(self) -> float:
        return self.original_fvg.bottom

# ==========================================
# 2. CORE LOGIC
# ==========================================

def get_active_ifvgs(df: pd.DataFrame, direction: Optional[FVGDirection] = None, config: IFVGConfig = IFVGConfig()) -> List[InverseFVG]:
    """
    Scans for FVGs that have been inverted by price action.
    """
    if len(df) < 3:
        return []

    ifvgs: List[InverseFVG] = []
    
    # We need to look at all gaps, not just active ones, because a 'filled' gap is a candidate for inversion
    # We temporarily disable the fill criteria so we can see the full lifecycle
    temp_fvg_config = FVGConfig(
        min_gap_atr_multiple=config.fvg_config.min_gap_atr_multiple,
        atr_period=config.fvg_config.atr_period,
        fill_criteria=config.fvg_config.fill_criteria
    )
    all_fvgs = get_active_fvgs(df, config=temp_fvg_config)
    
    for fvg in all_fvgs:
        # Find the candle that inverted the gap
        # We look at candles AFTER the FVG creation
        post_fvg_candles = df[df['time'] > fvg.creation_time]
        
        inversion_time = None
        current_status = IFVGStatus.FRESH
        retest_time = None
        
        for idx, candle in post_fvg_candles.iterrows():
            if inversion_time is None:
                # Check for Inversion
                if fvg.direction == FVGDirection.BULLISH:
                    # A bullish FVG is inverted if price CLOSES below the bottom
                    if config.require_body_close_through:
                        is_inverted = candle['close'] < fvg.bottom
                    else:
                        is_inverted = candle['low'] < fvg.bottom
                        
                    if is_inverted:
                        inversion_time = candle['time']
                elif fvg.direction == FVGDirection.BEARISH:
                    # A bearish FVG is inverted if price CLOSES above the top
                    if config.require_body_close_through:
                        is_inverted = candle['close'] > fvg.top
                    else:
                        is_inverted = candle['high'] > fvg.top
                        
                    if is_inverted:
                        inversion_time = candle['time']
            
            elif inversion_time is not None:
                # We have an IFVG, now track its status
                if fvg.direction == FVGDirection.BULLISH:
                    # Was Bullish FVG -> Now BEARISH IFVG (resistance)
                    if candle['high'] >= fvg.bottom and current_status == IFVGStatus.FRESH:
                        current_status = IFVGStatus.RETESTED
                        retest_time = candle['time']
                    # If price closes ABOVE the top of the old gap, the IFVG failed
                    if candle['close'] > fvg.top:
                        current_status = IFVGStatus.FAILED
                        break
                        
                elif fvg.direction == FVGDirection.BEARISH:
                    # Was Bearish FVG -> Now BULLISH IFVG (support)
                    if candle['low'] <= fvg.top and current_status == IFVGStatus.FRESH:
                        current_status = IFVGStatus.RETESTED
                        retest_time = candle['time']
                    # If price closes BELOW the bottom, the IFVG failed
                    if candle['close'] < fvg.bottom:
                        current_status = IFVGStatus.FAILED
                        break

        if inversion_time is not None:
            # Determine the new direction
            new_dir = FVGDirection.BEARISH if fvg.direction == FVGDirection.BULLISH else FVGDirection.BULLISH
            
            if direction is None or direction == new_dir:
                ifvgs.append(InverseFVG(
                    original_fvg=fvg,
                    inverted_at=inversion_time,
                    new_direction=new_dir,
                    status=current_status,
                    retest_time=retest_time
                ))

    return ifvgs

# ==========================================
# 3. UTILITY FUNCTIONS
# ==========================================

def get_nearest_ifvg(ifvgs: List[InverseFVG], current_price: float) -> Optional[InverseFVG]:
    """Finds the closest active (FRESH or RETESTED) IFVG."""
    valid = [i for i in ifvgs if i.status in [IFVGStatus.FRESH, IFVGStatus.RETESTED]]
    if not valid:
        return None
        
    # Find the one with the smallest distance to current price
    return min(valid, key=lambda x: min(abs(current_price - x.top), abs(current_price - x.bottom)))

# ==========================================
# 4. ANALYZE WRAPPER
# ==========================================

def analyze(df: pd.DataFrame, config: IFVGConfig = IFVGConfig()) -> Dict[str, Any]:
    """
    Main entry point. Returns active IFVGs and their context.
    """
    if df.empty:
        return {"error": "Empty DataFrame"}
        
    ifvgs = get_active_ifvgs(df, config=config)
    current_price = float(df.iloc[-1]['close'])
    
    fresh = [i for i in ifvgs if i.status == IFVGStatus.FRESH]
    retested = [i for i in ifvgs if i.status == IFVGStatus.RETESTED]
    failed = [i for i in ifvgs if i.status == IFVGStatus.FAILED]
    if ifvgs:
        descriptions = []
        for item in ifvgs:
            description = (
                f"{item.new_direction.value.lower()} inverse fair value gap "
                f"from {item.bottom} to {item.top}, originally created at "
                f"{item.original_fvg.creation_time}, inverted at {item.inverted_at}; "
                f"status {item.status.value.lower()}."
            )
            if item.retest_time is not None:
                description += f" Retested at {item.retest_time}."
            descriptions.append(description)
        summary = " ".join(descriptions)
    else:
        summary = "No inverse fair value gaps were found."
    
    return {
        "summary": summary,
        "current_price": current_price,
        "fresh_bearish_ifvgs": [i for i in fresh if i.new_direction == FVGDirection.BEARISH],
        "fresh_bullish_ifvgs": [i for i in fresh if i.new_direction == FVGDirection.BULLISH],
        "retested_bearish_ifvgs": [i for i in retested if i.new_direction == FVGDirection.BEARISH],
        "retested_bullish_ifvgs": [i for i in retested if i.new_direction == FVGDirection.BULLISH],
        "failed_bearish_ifvgs": [i for i in failed if i.new_direction == FVGDirection.BEARISH],
        "failed_bullish_ifvgs": [i for i in failed if i.new_direction == FVGDirection.BULLISH],
        "nearest_ifvg": get_nearest_ifvg(ifvgs, current_price)
    }