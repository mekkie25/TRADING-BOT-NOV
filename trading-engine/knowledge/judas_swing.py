"""
Module 11: Judas Swing
Depends on: sessions.py, market_structure.py, liquidity.py, candlesticks.py, common.py.

Purpose: Recognise the fake-out that traps traders before the real move.
"""

import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple

from .sessions import (
    get_current_session, get_session_start, SessionName, SessionConfig
)
from .liquidity import (
    get_liquidity_pools, LiquidityPool, PoolSide, PoolStatus, LiquidityConfig
)
from .candlesticks import describe_candle, CandleType, CandleConfig

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

class JudasState(Enum):
    NONE = "NONE"
    FORMING = "FORMING"
    CONFIRMED_BULLISH = "CONFIRMED_BULLISH"
    CONFIRMED_BEARISH = "CONFIRMED_BEARISH"

@dataclass
class JudasConfig:
    # Window in minutes after session open to look for the trap
    detection_window_minutes: int = 120
    
    # Must the fake move sweep a liquidity pool?
    require_liquidity_sweep: bool = True
    
    # Must the reversal candle close back through the session open price?
    require_close_through_open: bool = True
    
    session_config: SessionConfig = None
    liquidity_config: LiquidityConfig = None
    candle_config: CandleConfig = None

    def __post_init__(self):
        if self.session_config is None: self.session_config = SessionConfig()
        if self.liquidity_config is None: self.liquidity_config = LiquidityConfig()
        if self.candle_config is None: self.candle_config = CandleConfig()

@dataclass
class JudasSwingResult:
    state: JudasState
    session: Optional[SessionName] = None
    session_open_price: Optional[float] = None
    fake_move_extreme: Optional[float] = None
    swept_liquidity_level: Optional[float] = None
    confirmed_at: Optional[pd.Timestamp] = None
    reason: str = ""

# ==========================================
# 2. CORE LOGIC
# ==========================================

def _detect_liquidity_sweep(candles: pd.DataFrame, extreme_price: float, side: PoolSide, config: JudasConfig) -> Optional[float]:
    """Checks if a specific extreme price swept any known liquidity pools."""
    pools = get_liquidity_pools(candles, config.liquidity_config)
    
    for pool in pools:
        if pool.side != side:
            continue
            
        if side == PoolSide.BUY_SIDE:
            # We are looking for a sweep of highs
            if extreme_price > pool.level and pool.status == PoolStatus.SWEPT:
                return pool.level
        else:
            # We are looking for a sweep of lows
            if extreme_price < pool.level and pool.status == PoolStatus.SWEPT:
                return pool.level
                
    return None

def get_judas_swing(df: pd.DataFrame, target_session: Optional[SessionName] = None, config: JudasConfig = JudasConfig()) -> JudasSwingResult:
    """
    Analyzes the current data to detect a Judas Swing.
    """
    if df.empty:
        return JudasSwingResult(state=JudasState.NONE, reason="Empty DataFrame")
        
    # 1. Determine current session
    current_time = df.iloc[-1]['time']
    session_info = get_current_session(current_time, config.session_config)
    
    # If user requested a specific session, check we are in it
    if target_session and session_info.name != target_session:
        return JudasSwingResult(state=JudasState.NONE, reason=f"Not in {target_session.value} session")

    if session_info.name == SessionName.OFF_SESSION:
        return JudasSwingResult(state=JudasState.NONE, reason="Off-session")

    # 2. Get session start and open price
    session_start = get_session_start(current_time, session_info.name, config.session_config)
    if not session_start:
        return JudasSwingResult(state=JudasState.NONE, reason="Could not find session start")

    # Check if we are within the detection window
    minutes_elapsed = (current_time - session_start).total_seconds() / 60
    if minutes_elapsed > config.detection_window_minutes:
        return JudasSwingResult(state=JudasState.NONE, reason="Outside detection window")

    # Get all candles since session start
    session_candles = df[df['time'] >= session_start].reset_index(drop=True)
    if session_candles.empty:
        return JudasSwingResult(state=JudasState.NONE, reason="No candles since session open")

    session_open_price = float(session_candles.iloc[0]['open'])

    # 3. Look for a Fake Move (Down or Up)
    # We need to find if there was an extreme that "reversed"
    
    # --- Bearish Judas (Fake move UP, Reversal DOWN) ---
    highest_high_idx = session_candles['high'].idxmax()
    highest_high = float(session_candles.loc[highest_high_idx, 'high'])
    
    # If the high happened somewhere in the middle (not the last candle)
    if highest_high_idx < len(session_candles) - 1 and highest_high > session_open_price:
        # Check if the current price has reversed back below the session open
        current_close = float(session_candles.iloc[-1]['close'])
        
        if current_close < session_open_price:
            # It might be confirmed. Let's verify the liquidity sweep.
            swept_level = None
            if config.require_liquidity_sweep:
                swept_level = _detect_liquidity_sweep(session_candles, highest_high, PoolSide.BUY_SIDE, config)
                if not swept_level:
                    return JudasSwingResult(state=JudasState.FORMING, reason="Reversal detected, but no liquidity sweep above")
            
            # Confirmed! The fake move was up, and price closed back below open.
            return JudasSwingResult(
                state=JudasState.CONFIRMED_BEARISH,
                session=session_info.name,
                session_open_price=session_open_price,
                fake_move_extreme=highest_high,
                swept_liquidity_level=swept_level,
                # Important: The confirmation time is the CLOSE of the reversal candle
                confirmed_at=session_candles.iloc[-1]['time'], 
                reason="Fake move up swept liquidity, reversed below open."
            )

    # --- Bullish Judas (Fake move DOWN, Reversal UP) ---
    lowest_low_idx = session_candles['low'].idxmin()
    lowest_low = float(session_candles.loc[lowest_low_idx, 'low'])
    
    if lowest_low_idx < len(session_candles) - 1 and lowest_low < session_open_price:
        current_close = float(session_candles.iloc[-1]['close'])
        
        if current_close > session_open_price:
            swept_level = None
            if config.require_liquidity_sweep:
                swept_level = _detect_liquidity_sweep(session_candles, lowest_low, PoolSide.SELL_SIDE, config)
                if not swept_level:
                    return JudasSwingResult(state=JudasState.FORMING, reason="Reversal detected, but no liquidity sweep below")
            
            return JudasSwingResult(
                state=JudasState.CONFIRMED_BULLISH,
                session=session_info.name,
                session_open_price=session_open_price,
                fake_move_extreme=lowest_low,
                swept_liquidity_level=swept_level,
                confirmed_at=session_candles.iloc[-1]['time'],
                reason="Fake move down swept liquidity, reversed above open."
            )

    # 4. Check for FORMING state
    # If we are making an extreme but haven't reversed yet
    last_candle = session_candles.iloc[-1]
    if last_candle['high'] > session_open_price and highest_high_idx == len(session_candles) - 1:
        return JudasSwingResult(state=JudasState.FORMING, session=session_info.name, session_open_price=session_open_price, fake_move_extreme=highest_high, reason="Fake move up in progress...")
    if last_candle['low'] < session_open_price and lowest_low_idx == len(session_candles) - 1:
        return JudasSwingResult(state=JudasState.FORMING, session=session_info.name, session_open_price=session_open_price, fake_move_extreme=lowest_low, reason="Fake move down in progress...")

    return JudasSwingResult(state=JudasState.NONE, reason="No Judas swing detected")

# ==========================================
# 3. ANALYZE WRAPPER
# ==========================================

def analyze(df: pd.DataFrame, session: Optional[SessionName] = None, config: JudasConfig = JudasConfig()) -> Dict[str, Any]:
    """Main entry point for Judas Swing analysis."""
    result = get_judas_swing(df, session, config)
    return {
        "state": result.state,
        "session": result.session,
        "session_open_price": result.session_open_price,
        "fake_move_extreme": result.fake_move_extreme,
        "swept_liquidity_level": result.swept_liquidity_level,
        "confirmed_at": result.confirmed_at,
        "reason": result.reason
    }