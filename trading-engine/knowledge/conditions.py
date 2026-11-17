"""
Module 16: Pre-Trade Conditions Checklist
Depends on: news.py, sessions.py, market_conditions.py, daily_bias.py, daily_profiles.py, common.py.

Purpose: Run a pre-trade check and know when sitting out is the right call.
"""

import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Callable
from datetime import time

# Import all our knowledge modules
from .news import is_news_blackout, NewsConfig
from .sessions import get_current_session, SessionName, SessionConfig
from .market_conditions import get_market_condition, MarketCondition
from .daily_bias import get_daily_bias, BiasDirection, BiasConfig
from .daily_profiles import classify_so_far, ProfileName, ProfileConfig
from .time_structure import get_time_window, TimeStructureConfig

# ==========================================
# 1. CONFIGURATION & ENUMS
# ==========================================

class CheckResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"

class TradeDecision(Enum):
    TRADE = "TRADE"
    SIT_OUT = "SIT_OUT"
    REDUCE_SIZE = "REDUCE_SIZE"

@dataclass
class CheckOutcome:
    check_name: str
    result: CheckResult
    reason: str
    is_required: bool = True

@dataclass
class PreTradeContext:
    df: pd.DataFrame
    daily_df: pd.DataFrame # Needed for daily bias
    time: pd.Timestamp
    symbol: str
    spread_pips: float
    intended_direction: BiasDirection # BULLISH or BEARISH
    
    # Optional: For risk checks
    trades_today: int = 0
    daily_loss_percent: float = 0.0

@dataclass
class StrategyConditions:
    """Defines which checks are required for a specific strategy."""
    # News
    check_news: bool = True
    news_config: NewsConfig = None
    
    # Session
    check_session: bool = True
    allowed_sessions: List[SessionName] = field(default_factory=lambda: [SessionName.LONDON, SessionName.NEW_YORK, SessionName.LONDON_NY_OVERLAP])
    session_config: SessionConfig = None
    
    # Volatility / Market Condition
    check_market_condition: bool = True
    allowed_conditions: List[MarketCondition] = field(default_factory=lambda: [MarketCondition.TRENDING])
    
    # Daily Bias
    check_daily_bias: bool = True
    min_bias_confidence: float = 50.0
    bias_config: BiasConfig = None
    
    # Spread
    check_spread: bool = True
    max_spread_pips: float = 2.0
    
    # Time Window
    check_time_window: bool = True
    time_config: TimeStructureConfig = None
    
    # Weekday
    check_weekday: bool = True
    allowed_weekdays: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4]) # Mon-Fri
    
    # Daily Profile
    check_daily_profile: bool = True
    allowed_profiles: List[ProfileName] = field(default_factory=lambda: [
        ProfileName.TREND_DAY, ProfileName.JUDAS_THEN_TREND, ProfileName.REVERSAL_DAY
    ])
    profile_config: ProfileConfig = None

    # Risk (Placeholders)
    check_max_trades: bool = True
    max_trades_per_day: int = 4
    check_daily_loss: bool = True
    max_daily_loss_percent: float = 3.0

    def __post_init__(self):
        if self.news_config is None: self.news_config = NewsConfig()
        if self.session_config is None: self.session_config = SessionConfig()
        if self.bias_config is None: self.bias_config = BiasConfig()
        if self.time_config is None: self.time_config = TimeStructureConfig()
        if self.profile_config is None: self.profile_config = ProfileConfig()

# ==========================================
# 2. INDIVIDUAL CHECKS
# ==========================================

def _check_news(ctx: PreTradeContext, config: StrategyConditions) -> CheckOutcome:
    # news.py expects SAST time. Assuming ctx.time is UTC, SAST is UTC+2
    time_sast = ctx.time + pd.Timedelta(hours=2)
    news = is_news_blackout(time_sast.to_pydatetime(), ctx.symbol, config.news_config)
    if news.blocked:
        return CheckOutcome("News Blackout", CheckResult.FAIL, news.reason)
    return CheckOutcome("News Blackout", CheckResult.PASS, "No high-impact news nearby")

def _check_session(ctx: PreTradeContext, config: StrategyConditions) -> CheckOutcome:
    session = get_current_session(ctx.time.to_pydatetime(), config.session_config)
    if session.name not in config.allowed_sessions:
        return CheckOutcome("Session", CheckResult.FAIL, f"Current session ({session.name.value}) is not allowed")
    return CheckOutcome("Session", CheckResult.PASS, f"In allowed session ({session.name.value})")

def _check_market_condition(ctx: PreTradeContext, config: StrategyConditions) -> CheckOutcome:
    condition = get_market_condition(ctx.df)
    if condition not in config.allowed_conditions:
        return CheckOutcome("Market Condition", CheckResult.FAIL, f"Market is {condition.value}")
    return CheckOutcome("Market Condition", CheckResult.PASS, f"Market is {condition.value}")

def _check_daily_bias(ctx: PreTradeContext, config: StrategyConditions) -> CheckOutcome:
    if ctx.daily_df.empty:
        return CheckOutcome("Daily Bias", CheckResult.UNKNOWN, "No daily data provided")
        
    bias = get_daily_bias(ctx.daily_df, ctx.df, ctx.time, config.bias_config)
    
    if bias.bias == BiasDirection.NEUTRAL:
        return CheckOutcome("Daily Bias", CheckResult.FAIL, f"Daily bias is NEUTRAL")
        
    if bias.confidence < config.min_bias_confidence:
        return CheckOutcome("Daily Bias", CheckResult.FAIL, f"Bias confidence too low ({bias.confidence}%)")
        
    if bias.bias != ctx.intended_direction:
        return CheckOutcome("Daily Bias", CheckResult.FAIL, f"Daily bias is {bias.bias.value}, but trade is {ctx.intended_direction.value}")
        
    return CheckOutcome("Daily Bias", CheckResult.PASS, f"Bias aligns ({bias.bias.value} at {bias.confidence}%)")

def _check_spread(ctx: PreTradeContext, config: StrategyConditions) -> CheckOutcome:
    if ctx.spread_pips > config.max_spread_pips:
        return CheckOutcome("Spread", CheckResult.FAIL, f"Spread {ctx.spread_pips} > max {config.max_spread_pips}")
    return CheckOutcome("Spread", CheckResult.PASS, f"Spread {ctx.spread_pips} is acceptable")

def _check_time_window(ctx: PreTradeContext, config: StrategyConditions) -> CheckOutcome:
    window = get_time_window(ctx.time, config.time_config)
    if window is None:
        return CheckOutcome("Time Window", CheckResult.FAIL, "Outside key time windows")
    return CheckOutcome("Time Window", CheckResult.PASS, f"In {window.name} (weight {window.weight})")

def _check_weekday(ctx: PreTradeContext, config: StrategyConditions) -> CheckOutcome:
    if ctx.time.weekday() not in config.allowed_weekdays:
        return CheckOutcome("Weekday", CheckResult.FAIL, f"{ctx.time.day_name()} is not allowed")
    return CheckOutcome("Weekday", CheckResult.PASS, f"{ctx.time.day_name()} is allowed")

def _check_daily_profile(ctx: PreTradeContext, config: StrategyConditions) -> CheckOutcome:
    profile = classify_so_far(ctx.df, ctx.time, config.profile_config)
    if profile.is_too_early:
        return CheckOutcome("Daily Profile", CheckResult.UNKNOWN, "Too early to classify day")
    if profile.best_match not in config.allowed_profiles:
        return CheckOutcome("Daily Profile", CheckResult.FAIL, f"Profile is {profile.best_match.value}, not in allowed list")
    return CheckOutcome("Daily Profile", CheckResult.PASS, f"Profile is {profile.best_match.value}")

def _check_max_trades(ctx: PreTradeContext, config: StrategyConditions) -> CheckOutcome:
    # Placeholder: Requires Risk Module to track real trades
    if ctx.trades_today >= config.max_trades_per_day:
         return CheckOutcome("Max Trades", CheckResult.FAIL, f"Already hit max trades today ({ctx.trades_today})")
    return CheckOutcome("Max Trades", CheckResult.UNKNOWN, "Risk module not connected yet")

def _check_daily_loss(ctx: PreTradeContext, config: StrategyConditions) -> CheckOutcome:
    # Placeholder
    if ctx.daily_loss_percent >= config.max_daily_loss_percent:
        return CheckOutcome("Daily Loss", CheckResult.FAIL, f"Daily loss limit hit ({ctx.daily_loss_percent}%)")
    return CheckOutcome("Daily Loss", CheckResult.UNKNOWN, "Risk module not connected yet")

# ==========================================
# 3. MAIN CHECKLIST ENGINE
# ==========================================

def run_pre_trade_check(ctx: PreTradeContext, strategy_conditions: StrategyConditions) -> Dict[str, Any]:
    """
    Runs all configured checks and returns the final decision.
    """
    checklist = []
    
    # Register checks
    if strategy_conditions.check_news: checklist.append(_check_news(ctx, strategy_conditions))
    if strategy_conditions.check_session: checklist.append(_check_session(ctx, strategy_conditions))
    if strategy_conditions.check_market_condition: checklist.append(_check_market_condition(ctx, strategy_conditions))
    if strategy_conditions.check_daily_bias: checklist.append(_check_daily_bias(ctx, strategy_conditions))
    if strategy_conditions.check_spread: checklist.append(_check_spread(ctx, strategy_conditions))
    if strategy_conditions.check_time_window: checklist.append(_check_time_window(ctx, strategy_conditions))
    if strategy_conditions.check_weekday: checklist.append(_check_weekday(ctx, strategy_conditions))
    if strategy_conditions.check_daily_profile: checklist.append(_check_daily_profile(ctx, strategy_conditions))
    if strategy_conditions.check_max_trades: checklist.append(_check_max_trades(ctx, strategy_conditions))
    if strategy_conditions.check_daily_loss: checklist.append(_check_daily_loss(ctx, strategy_conditions))

    # Evaluate Decision
    fail_count = sum(1 for c in checklist if c.result == CheckResult.FAIL and c.is_required)
    unknown_count = sum(1 for c in checklist if c.result == CheckResult.UNKNOWN and c.is_required)
    
    if fail_count > 0:
        decision = TradeDecision.SIT_OUT
        reason = f"{fail_count} required check(s) failed."
    elif unknown_count > 0:
        decision = TradeDecision.SIT_OUT
        reason = f"{unknown_count} required check(s) are UNKNOWN. Safety: SIT_OUT."
    else:
        # All pass
        decision = TradeDecision.TRADE
        reason = "All required checks passed."

    # Optional: Determine if we should REDUCE_SIZE (e.g., 1 or 2 non-required checks failed, or low confidence)
    # If there are non-required fails but all required passed:
    non_req_fails = sum(1 for c in checklist if c.result == CheckResult.FAIL and not c.is_required)
    if decision == TradeDecision.TRADE and non_req_fails > 0:
        decision = TradeDecision.REDUCE_SIZE
        reason = f"All required pass, but {non_req_fails} optional check(s) failed. Reduce size."

    return {
        "decision": decision.value,
        "reason": reason,
        "checklist": [
            {
                "name": c.check_name,
                "result": c.result.value,
                "reason": c.reason,
                "is_required": c.is_required
            } for c in checklist
        ],
        "passed_count": sum(1 for c in checklist if c.result == CheckResult.PASS),
        "total_checks": len(checklist)
    }