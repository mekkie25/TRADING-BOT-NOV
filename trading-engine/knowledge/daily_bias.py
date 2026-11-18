"""
Module 12: Daily Bias
Depends on: market_structure.py, liquidity_types.py, fvg.py, equilibrium.py, sessions.py, candlesticks.py, common.py.

Purpose: Walk into each day with a clear view of direction, and why.
"""

import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple

from .sessions import get_current_session, SessionName, SessionConfig
from .market_structure import get_market_structure, TrendState, MarketStructureConfig
from .equilibrium import analyze as analyze_eq, RangeMode, PriceZone
from .fair_value_gap import get_active_fvgs, FVGStatus, FVGConfig
from .candlestick_anatomy import describe_candle, CandleType, CandleConfig
from .liquidity_types import (
    get_most_significant_pool, PoolSide, ClassifiedPool, 
    LiquidityType, LiquidityTypeConfig
)

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

class BiasDirection(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"

@dataclass
class BiasEvidence:
    check_name: str
    seen: str
    vote: BiasDirection
    weight: float

@dataclass
class BiasConfig:
    # Weights for each evidence type
    weight_htf_structure: float = 30.0
    weight_prev_day_close: float = 20.0
    weight_liquidity_target: float = 25.0
    weight_fvg_draw: float = 15.0
    weight_prev_day_candle: float = 10.0
    
    # Toggles
    use_htf_structure: bool = True
    use_prev_day_close: bool = True
    use_liquidity_target: bool = True
    use_fvg_draw: bool = True
    use_prev_day_candle: bool = True
    
    # Confidence Thresholds
    # If the net score is below this, return NEUTRAL
    neutral_threshold: float = 15.0
    
    # Sub-configs
    ms_config: MarketStructureConfig = None
    fvg_config: FVGConfig = None
    candle_config: CandleConfig = None
    liq_config: LiquidityTypeConfig = None
    session_config: SessionConfig = None

    def __post_init__(self):
        if self.ms_config is None: self.ms_config = MarketStructureConfig()
        if self.fvg_config is None: self.fvg_config = FVGConfig()
        if self.candle_config is None: self.candle_config = CandleConfig()
        if self.liq_config is None: self.liq_config = LiquidityTypeConfig()
        if self.session_config is None: self.session_config = SessionConfig()

@dataclass
class DailyBiasResult:
    bias: BiasDirection
    confidence: float # 0 to 100
    reasons: List[BiasEvidence]
    invalidation_level: Optional[float]
    total_score: float

# ==========================================
# 2. EVIDENCE GATHERING
# ==========================================

def _check_htf_structure(daily_df: pd.DataFrame, config: BiasConfig) -> BiasEvidence:
    """Checks the trend on the daily timeframe."""
    trend = get_market_structure(daily_df, config.ms_config)
    
    if trend == TrendState.BULLISH:
        return BiasEvidence("HTF Market Structure", "Daily trend is BULLISH (HH/HL)", BiasDirection.BULLISH, config.weight_htf_structure)
    elif trend == TrendState.BEARISH:
        return BiasEvidence("HTF Market Structure", "Daily trend is BEARISH (LH/LL)", BiasDirection.BEARISH, config.weight_htf_structure)
    else:
        return BiasEvidence("HTF Market Structure", "Daily trend is RANGING", BiasDirection.NEUTRAL, config.weight_htf_structure)

def _check_prev_day_close(daily_df: pd.DataFrame, config: BiasConfig) -> BiasEvidence:
    """Checks where the previous day closed within its own range."""
    if len(daily_df) < 2:
        return BiasEvidence("Prev Day Close", "Insufficient data", BiasDirection.NEUTRAL, config.weight_prev_day_close)
        
    prev_day = daily_df.iloc[-2]
    high = prev_day['high']
    low = prev_day['low']
    close = prev_day['close']
    
    if high == low:
        return BiasEvidence("Prev Day Close", "Zero range candle", BiasDirection.NEUTRAL, config.weight_prev_day_close)
        
    close_pct = (close - low) / (high - low)
    
    if close_pct >= 0.75:
        return BiasEvidence("Prev Day Close", f"Closed in PREMIUM ({close_pct:.0%} of range)", BiasDirection.BULLISH, config.weight_prev_day_close)
    elif close_pct <= 0.25:
        return BiasEvidence("Prev Day Close", f"Closed in DISCOUNT ({close_pct:.0%} of range)", BiasDirection.BEARISH, config.weight_prev_day_close)
    else:
        return BiasEvidence("Prev Day Close", f"Closed in EQUILIBRIUM ({close_pct:.0%} of range)", BiasDirection.NEUTRAL, config.weight_prev_day_close)

def _check_prev_day_candle(daily_df: pd.DataFrame, config: BiasConfig) -> BiasEvidence:
    """Reads the anatomy of the previous day's candle."""
    if len(daily_df) < 2:
        return BiasEvidence("Prev Day Candle", "Insufficient data", BiasDirection.NEUTRAL, config.weight_prev_day_candle)
        
    prev_day = daily_df.iloc[-2]
    anat = describe_candle(prev_day, config.candle_config)
    
    if anat.direction == CandleType.BULLISH:
        # If it's a strong bullish candle (small wicks), it's a bullish signal
        if anat.upper_wick < anat.body_size * 0.3:
            return BiasEvidence("Prev Day Candle", "Strong Bullish Close (no upper wick)", BiasDirection.BULLISH, config.weight_prev_day_candle)
    elif anat.direction == CandleType.BEARISH:
        if anat.lower_wick < anat.body_size * 0.3:
            return BiasEvidence("Prev Day Candle", "Strong Bearish Close (no lower wick)", BiasDirection.BEARISH, config.weight_prev_day_candle)
            
    return BiasEvidence("Prev Day Candle", "Indecision candle", BiasDirection.NEUTRAL, config.weight_prev_day_candle)

def _check_liquidity_target(intraday_df: pd.DataFrame, config: BiasConfig) -> BiasEvidence:
    """Checks which major liquidity pool is the next magnet."""
    # Get the most significant pool above and below
    buy_side = get_most_significant_pool(intraday_df, PoolSide.BUY_SIDE, config.liq_config)
    sell_side = get_most_significant_pool(intraday_df, PoolSide.SELL_SIDE, config.liq_config)
    
    # We need at least one to judge
    if not buy_side and not sell_side:
        return BiasEvidence("Liquidity Target", "No major pools identified", BiasDirection.NEUTRAL, config.weight_liquidity_target)
        
    if buy_side and not sell_side:
        return BiasEvidence("Liquidity Target", f"Only major target is BUY-SIDE at {buy_side.pool.level:.4f}", BiasDirection.BULLISH, config.weight_liquidity_target)
    elif sell_side and not buy_side:
        return BiasEvidence("Liquidity Target", f"Only major target is SELL-SIDE at {sell_side.pool.level:.4f}", BiasDirection.BEARISH, config.weight_liquidity_target)
    else:
        # Both exist, judge by significance and proximity
        current_price = intraday_df.iloc[-1]['close']
        dist_buy = abs(buy_side.pool.level - current_price)
        dist_sell = abs(current_price - sell_side.pool.level)
        
        # If the buy-side pool is much more significant or much closer, bias is bullish
        if buy_side.significance_score > sell_side.significance_score * 1.5:
            return BiasEvidence("Liquidity Target", "Buy-side pool is much stronger", BiasDirection.BULLISH, config.weight_liquidity_target)
        elif sell_side.significance_score > buy_side.significance_score * 1.5:
            return BiasEvidence("Liquidity Target", "Sell-side pool is much stronger", BiasDirection.BEARISH, config.weight_liquidity_target)
            
        return BiasEvidence("Liquidity Target", "Balanced liquidity on both sides", BiasDirection.NEUTRAL, config.weight_liquidity_target)

def _check_fvg_draw(intraday_df: pd.DataFrame, config: BiasConfig) -> BiasEvidence:
    """Checks for unfilled FVGs that act as magnets."""
    fvgs = get_active_fvgs(intraday_df, config=config.fvg_config)
    
    # Get only the unfilled ones
    active = [f for f in fvgs if f.status != FVGStatus.FILLED]
    
    bullish_fvgs = [f for f in active if f.direction.value == "BULLISH"]
    bearish_fvgs = [f for f in active if f.direction.value == "BEARISH"]
    
    current_price = intraday_df.iloc[-1]['close']
    
    # Count how many FVGs are "below" price (bullish draw) vs "above" price (bearish draw)
    below = [f for f in bullish_fvgs if f.top < current_price]
    above = [f for f in bearish_fvgs if f.bottom > current_price]
    
    if len(below) > len(above) * 2:
        return BiasEvidence("FVG Draw", f"{len(below)} unfilled bullish FVGs below price", BiasDirection.BULLISH, config.weight_fvg_draw)
    elif len(above) > len(below) * 2:
        return BiasEvidence("FVG Draw", f"{len(above)} unfilled bearish FVGs above price", BiasDirection.BEARISH, config.weight_fvg_draw)
        
    return BiasEvidence("FVG Draw", "Balanced FVG draw", BiasDirection.NEUTRAL, config.weight_fvg_draw)

# ==========================================
# 3. CORE LOGIC
# ==========================================

def get_daily_bias(
    daily_df: pd.DataFrame, 
    intraday_df: pd.DataFrame, 
    time: pd.Timestamp,
    config: BiasConfig = BiasConfig()
) -> DailyBiasResult:
    """
    Calculates the daily bias using only information available up to 'time'.
    """
    if daily_df.empty or intraday_df.empty:
        return DailyBiasResult(BiasDirection.NEUTRAL, 0, [], None, 0)

    # 1. NO LOOK-AHEAD: Cut DataFrames up to the given time
    daily_df_closed = daily_df[daily_df['time'] < time].copy()
    
    # For intraday, we only look at candles up to 'time'
    intraday_df_closed = intraday_df[intraday_df['time'] <= time].copy()
    
    if daily_df_closed.empty or intraday_df_closed.empty:
        return DailyBiasResult(BiasDirection.NEUTRAL, 0, [], None, 0)

    # 2. Gather Evidence
    evidence = []
    
    if config.use_htf_structure:
        evidence.append(_check_htf_structure(daily_df_closed, config))
        
    if config.use_prev_day_close:
        evidence.append(_check_prev_day_close(daily_df_closed, config))
        
    if config.use_prev_day_candle:
        evidence.append(_check_prev_day_candle(daily_df_closed, config))
        
    if config.use_liquidity_target:
        evidence.append(_check_liquidity_target(intraday_df_closed, config))
        
    if config.use_fvg_draw:
        evidence.append(_check_fvg_draw(intraday_df_closed, config))

    # 3. Tally Scores
    total_score = 0.0
    for e in evidence:
        if e.vote == BiasDirection.BULLISH:
            total_score += e.weight
        elif e.vote == BiasDirection.BEARISH:
            total_score -= e.weight

    # 4. Determine Bias
    bias = BiasDirection.NEUTRAL
    if total_score >= config.neutral_threshold:
        bias = BiasDirection.BULLISH
    elif total_score <= -config.neutral_threshold:
        bias = BiasDirection.BEARISH

    # 5. Confidence (0 to 100)
    # Max possible score is sum of all weights
    max_possible = sum(e.weight for e in evidence)
    confidence = (abs(total_score) / max_possible) * 100 if max_possible > 0 else 0

    # 6. Invalidation Level
    # If bias is bullish, we need a price level that would invalidate it (e.g., the previous day's low)
    invalidation = None
    if bias == BiasDirection.BULLISH:
        invalidation = float(daily_df_closed.iloc[-1]['low']) # Today's low so far? Or prev day low?
    elif bias == BiasDirection.BEARISH:
        invalidation = float(daily_df_closed.iloc[-1]['high'])

    return DailyBiasResult(
        bias=bias,
        confidence=round(confidence, 2),
        reasons=evidence,
        invalidation_level=invalidation,
        total_score=total_score
    )

# ==========================================
# 4. ANALYZE WRAPPER
# ==========================================

def analyze(daily_df: pd.DataFrame, intraday_df: pd.DataFrame, time: pd.Timestamp, config: BiasConfig = BiasConfig()) -> Dict[str, Any]:
    """Main entry point for daily bias analysis."""
    result = get_daily_bias(daily_df, intraday_df, time, config)
    
    return {
        "bias": result.bias.value,
        "confidence": result.confidence,
        "invalidation_level": result.invalidation_level,
        "total_score": result.total_score,
        "reasons": [
            {
                "check": e.check_name,
                "seen": e.seen,
                "vote": e.vote.value,
                "weight": e.weight
            } for e in result.reasons
        ]
    }