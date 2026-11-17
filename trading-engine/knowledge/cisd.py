"""
Module 14: CISD (Change in State of Delivery)
Depends on: candlesticks.py, liquidity.py, market_structure.py, common.py.

Purpose: Spot the shift in delivery that often comes before a change in direction.

NOTE: The course definition was left blank, so the default draft logic is used:
'Delivery' is a run of consecutive candles closing in one direction. A change in state 
of delivery happens when price closes back through the opening price of that run.
"""

import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any

from .liquidity import get_liquidity_pools, PoolSide, PoolStatus, LiquidityConfig
from .market_structure import MarketStructureConfig

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

class CISDDirection(Enum):
    BULLISH = "BULLISH"  # Reversal up after down run
    BEARISH = "BEARISH"  # Reversal down after up run

@dataclass
class CISDConfig:
    # Minimum consecutive candles to be considered a "delivery run"
    min_run_length: int = 3
    
    # Does a break require a body close, or is a wick enough?
    require_body_close: bool = True
    
    # Optional: Only count a CISD if it follows a liquidity sweep
    require_liquidity_sweep: bool = False
    
    liquidity_config: LiquidityConfig = None
    ms_config: MarketStructureConfig = None

    def __post_init__(self):
        if self.liquidity_config is None: self.liquidity_config = LiquidityConfig()
        if self.ms_config is None: self.ms_config = MarketStructureConfig()

@dataclass
class DeliveryRun:
    direction: str # "UP" or "DOWN"
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    start_price: float # The OPEN of the first candle in the run
    end_price: float   # The CLOSE of the last candle in the run
    candle_count: int

@dataclass
class CISDEvent:
    direction: CISDDirection
    run: DeliveryRun
    broken_level: float
    break_time: pd.Timestamp
    confirmed_at: pd.Timestamp # The close time of the breaking candle
    had_liquidity_sweep: bool = False

# ==========================================
# 2. CORE LOGIC
# ==========================================

def _find_delivery_runs(df: pd.DataFrame, min_length: int) -> List[DeliveryRun]:
    """Scans the DataFrame for consecutive up/down candle closes."""
    runs = []
    if len(df) < min_length:
        return runs
        
    current_dir = None
    run_start_idx = 0
    
    for i in range(len(df)):
        candle = df.iloc[i]
        # Determine current candle direction
        if candle['close'] > candle['open']:
            c_dir = "UP"
        elif candle['close'] < candle['open']:
            c_dir = "DOWN"
        else:
            c_dir = "DOJI"
            
        # Check for run break
        if c_dir != current_dir or c_dir == "DOJI":
            # If a valid run just ended, save it
            if current_dir is not None:
                run_length = i - run_start_idx
                if run_length >= min_length:
                    start_candle = df.iloc[run_start_idx]
                    end_candle = df.iloc[i-1]
                    runs.append(DeliveryRun(
                        direction=current_dir,
                        start_time=start_candle['time'],
                        end_time=end_candle['time'],
                        start_price=float(start_candle['open']),
                        end_price=float(end_candle['close']),
                        candle_count=run_length
                    ))
            
            # Start new run
            current_dir = c_dir
            run_start_idx = i
            
    # Catch the last run if it ends on the last candle
    if current_dir is not None and current_dir != "DOJI":
        run_length = len(df) - run_start_idx
        if run_length >= min_length:
            start_candle = df.iloc[run_start_idx]
            end_candle = df.iloc[-1]
            runs.append(DeliveryRun(
                direction=current_dir,
                start_time=start_candle['time'],
                end_time=end_candle['time'],
                start_price=float(start_candle['open']),
                end_price=float(end_candle['close']),
                candle_count=run_length
            ))
            
    return runs

def get_cisd_events(df: pd.DataFrame, lookback: int = 200, config: CISDConfig = CISDConfig()) -> List[CISDEvent]:
    """
    Finds all CISD events in the recent lookback.
    """
    events = []
    if df.empty:
        return events
        
    # Use recent data for performance
    recent_df = df.tail(lookback).reset_index(drop=True)
    
    # Find all historical runs
    runs = _find_delivery_runs(recent_df, config.min_run_length)
    
    # Optional: Get liquidity sweeps for filtering
    swept_levels = []
    if config.require_liquidity_sweep:
        pools = get_liquidity_pools(recent_df, config.liquidity_config)
        swept_levels = [p.level for p in pools if p.status == PoolStatus.SWEPT]
        
    for run in runs:
        # Find candles AFTER the run ended
        post_run = recent_df[recent_df['time'] > run.end_time]
        
        for _, candle in post_run.iterrows():
            is_cisd = False
            
            if run.direction == "DOWN":
                # Bullish CISD: Close above the run's start price (open of the first down candle)
                if config.require_body_close:
                    is_cisd = candle['close'] > run.start_price
                else:
                    is_cisd = candle['high'] > run.start_price
                    
                if is_cisd:
                    # Optional: Check if a liquidity sweep happened before this break
                    sweep_found = False
                    if config.require_liquidity_sweep:
                        # Check if the lowest low of the run swept any liquidity
                        run_low = recent_df[(recent_df['time'] >= run.start_time) & (recent_df['time'] <= run.end_time)]['low'].min()
                        sweep_found = any(run_low <= lvl for lvl in swept_levels)
                        if not sweep_found:
                            continue # Skip this event, filter failed
                            
                    events.append(CISDEvent(
                        direction=CISDDirection.BULLISH,
                        run=run,
                        broken_level=run.start_price,
                        break_time=candle['time'],
                        confirmed_at=candle['time'],
                        had_liquidity_sweep=sweep_found
                    ))
                    break # Move to next run once we find the break
                    
            elif run.direction == "UP":
                # Bearish CISD: Close below the run's start price (open of the first up candle)
                if config.require_body_close:
                    is_cisd = candle['close'] < run.start_price
                else:
                    is_cisd = candle['low'] < run.start_price
                    
                if is_cisd:
                    sweep_found = False
                    if config.require_liquidity_sweep:
                        run_high = recent_df[(recent_df['time'] >= run.start_time) & (recent_df['time'] <= run.end_time)]['high'].max()
                        sweep_found = any(run_high >= lvl for lvl in swept_levels)
                        if not sweep_found:
                            continue
                            
                    events.append(CISDEvent(
                        direction=CISDDirection.BEARISH,
                        run=run,
                        broken_level=run.start_price,
                        break_time=candle['time'],
                        confirmed_at=candle['time'],
                        had_liquidity_sweep=sweep_found
                    ))
                    break
                    
    events.sort(key=lambda x: x.confirmed_at)
    return events

# ==========================================
# 3. UTILITY FUNCTIONS
# ==========================================

def get_last_cisd(df: pd.DataFrame, config: CISDConfig = CISDConfig()) -> Optional[CISDEvent]:
    """Returns the most recent CISD event."""
    events = get_cisd_events(df, config=config)
    if not events:
        return None
    return events[-1]

def has_cisd_since(df: pd.DataFrame, since_time: pd.Timestamp, direction: CISDDirection, config: CISDConfig = CISDConfig()) -> bool:
    """Checks if a specific CISD has happened since a given time."""
    events = get_cisd_events(df, config=config)
    for e in reversed(events):
        if e.confirmed_at < since_time:
            break
        if e.direction == direction:
            return True
    return False

# ==========================================
# 4. ANALYZE WRAPPER
# ==========================================

def describe() -> str:
    return (
        "CISD (Change in State of Delivery): 'Delivery' is a run of consecutive candles closing in one direction. "
        "A change in state of delivery happens when price closes back through the opening price of that run. "
        "After a run of down candles, a close above the run's opening price is a bullish CISD, and the reverse for a bearish CISD. "
        "(Using default draft definition; course definition was left blank)."
    )

def analyze(df: pd.DataFrame, config: CISDConfig = CISDConfig()) -> Dict[str, Any]:
    """Main entry point for CISD analysis."""
    if df.empty:
        return {"error": "Empty DataFrame"}
        
    events = get_cisd_events(df, config=config)
    last = events[-1] if events else None
    
    return {
        "definition": describe(),
        "total_cisd_events": len(events),
        "last_cisd": {
            "direction": last.direction.value,
            "broken_level": last.broken_level,
            "run_length": last.run.candle_count,
            "confirmed_at": last.confirmed_at,
            "had_sweep": last.had_liquidity_sweep
        } if last else None,
        "recent_events": [
            {
                "direction": e.direction.value,
                "confirmed_at": e.confirmed_at,
                "broken_level": e.broken_level
            } for e in events[-5:]
        ]
    }