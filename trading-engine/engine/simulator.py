"""
Module: Simulator (Backtester Engine)
Purpose: Loops through M5 data, reconstructs HTF without look-ahead, 
applies volatility filters, and simulates trades.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import math

from strategies.base import BaseStrategy, Signal, SignalDirection
from knowledge.conditions import run_pre_trade_check, PreTradeContext, StrategyConditions
from knowledge.daily_bias import BiasDirection

# ==========================================
# 1. ZERO LOOK-AHEAD AGGREGATOR (STOLEN FROM OLD BOT)
# ==========================================
class ZeroLookAheadAggregator:
    def __init__(self, d1_history: pd.DataFrame, h4_history: pd.DataFrame, h1_history: pd.DataFrame):
        self.d1_all = d1_history.copy()
        self.h4_all = h4_history.copy()
        self.h1_all = h1_history.copy()

        for df in [self.d1_all, self.h4_all, self.h1_all]:
            if not isinstance(df.index, pd.DatetimeIndex):
                df['dt'] = pd.to_datetime(df['time'], utc=True)
                df.set_index('dt', inplace=True)
                df.sort_index(inplace=True)

        self._d1_close_epochs = [int((t + pd.Timedelta(hours=24)).timestamp()) for t in self.d1_all.index]
        self._h4_close_epochs = [int((t + pd.Timedelta(hours=4)).timestamp()) for t in self.h4_all.index]
        self._h1_close_epochs = [int((t + pd.Timedelta(hours=1)).timestamp()) for t in self.h1_all.index]

        self._d1_buffer = self._init_buffer(self.d1_all, 150)
        self._h4_buffer = self._init_buffer(self.h4_all, 30)
        self._h1_buffer = self._init_buffer(self.h1_all, 30)

    def _init_buffer(self, source_df: pd.DataFrame, size: int) -> pd.DataFrame:
        cols = ['time', 'open', 'high', 'low', 'close', 'volume']
        sample = source_df[cols].tail(size).copy().reset_index(drop=True)
        if len(sample) < size:
            pad = pd.DataFrame(index=range(size - len(sample)), columns=cols)
            sample = pd.concat([pad, sample], ignore_index=True)
        return sample

    def get_feeds_at_time(self, m5_history_up_to_t: pd.DataFrame, current_time_utc: datetime):
        import bisect
        curr_epoch = int(current_time_utc.timestamp())
        m5_times = pd.to_datetime(m5_history_up_to_t['time'], utc=True)

        # --- D1 ---
        d1_idx = bisect.bisect_right(self._d1_close_epochs, curr_epoch)
        last_d1_open_hour = self.d1_all.index[d1_idx - 1].hour if d1_idx > 0 else 21
        d1_start = current_time_utc.replace(hour=last_d1_open_hour, minute=0, second=0, microsecond=0)
        if current_time_utc < d1_start:
            d1_start -= timedelta(days=1)
        m5_today = m5_history_up_to_t[m5_times >= d1_start]
        if not m5_today.empty:
            self._d1_buffer.iloc[149] = [
                d1_start.strftime("%Y-%m-%d %H:%M:%S"),
                float(m5_today['open'].iloc[0]), float(m5_today['high'].max()),
                float(m5_today['low'].min()), float(m5_today['close'].iloc[-1]),
                int(m5_today['volume'].sum())
            ]
            active_d1 = self._d1_buffer
        else:
            active_d1 = self._d1_buffer.iloc[:149].reset_index(drop=True)

        # --- H4 ---
        h4_idx = bisect.bisect_right(self._h4_close_epochs, curr_epoch)
        h4_start_hour = (current_time_utc.hour // 4) * 4
        h4_start = current_time_utc.replace(hour=h4_start_hour, minute=0, second=0, microsecond=0)
        m5_h4 = m5_history_up_to_t[m5_times >= h4_start]
        if not m5_h4.empty:
            self._h4_buffer.iloc[29] = [
                h4_start.strftime("%Y-%m-%d %H:%M:%S"),
                float(m5_h4['open'].iloc[0]), float(m5_h4['high'].max()),
                float(m5_h4['low'].min()), float(m5_h4['close'].iloc[-1]),
                int(m5_h4['volume'].sum())
            ]
            active_h4 = self._h4_buffer
        else:
            active_h4 = self._h4_buffer.iloc[:29].reset_index(drop=True)

        # --- H1 ---
        h1_idx = bisect.bisect_right(self._h1_close_epochs, curr_epoch)
        h1_start = current_time_utc.replace(minute=0, second=0, microsecond=0)
        m5_h1 = m5_history_up_to_t[m5_times >= h1_start]
        if not m5_h1.empty:
            self._h1_buffer.iloc[29] = [
                h1_start.strftime("%Y-%m-%d %H:%M:%S"),
                float(m5_h1['open'].iloc[0]), float(m5_h1['high'].max()),
                float(m5_h1['low'].min()), float(m5_h1['close'].iloc[-1]),
                int(m5_h1['volume'].sum())
            ]
            active_h1 = self._h1_buffer
        else:
            active_h1 = self._h1_buffer.iloc[:29].reset_index(drop=True)

        return active_h1, active_h4, active_d1

# ==========================================
# 2. VOLATILITY ENGINE (STOLEN FROM OLD BOT)
# ==========================================
class VolatilityEngine:
    def __init__(self):
        self._vol_cache = {}
    
    def compute_symbol_volatility(self, d1_df, m5_df, current_quote, symbol, as_of=None):
        # Simplified version for the new engine
        if d1_df.empty or len(d1_df) < 120:
            return {"valid": False, "reason": "Insufficient D1 history"}
            
        daily_ranges = (d1_df['high'] - d1_df['low']).dropna()
        r_5 = daily_ranges.rolling(5).mean()
        r_10 = daily_ranges.rolling(10).mean()
        r_20 = daily_ranges.rolling(20).mean()
        smoothed_series = ((0.50 * r_5) + (0.30 * r_10) + (0.20 * r_20)).dropna()
        
        current_adr = float(smoothed_series.iloc[-1])
        
        if current_adr == 0:
            return {"valid": False, "reason": "Zero ADR"}
            
        return {
            "valid": True,
            "adr": current_adr,
            "regime": "NORMAL" # Placeholder for now
        }

# ==========================================
# 3. TRADE DATA STRUCTURES
# ==========================================
class TradeStatus(Enum):
    OPEN = "OPEN"
    CLOSED_TP = "CLOSED_TP"
    CLOSED_SL = "CLOSED_SL"
    CLOSED_EOD = "CLOSED_EOD"

@dataclass
class SimulatedTrade:
    id: str
    symbol: str
    direction: SignalDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    size_lots: float
    entry_time: pd.Timestamp
    setup_grade: str
    strategy_name: str
    reason: str
    status: TradeStatus = TradeStatus.OPEN
    exit_price: Optional[float] = None
    exit_time: Optional[pd.Timestamp] = None
    pnl: float = 0.0
    r_multiple: float = 0.0

@dataclass
class BacktestConfig:
    starting_balance: float = 100000.0
    risk_per_trade_pct: float = 1.0
    pip_size: float = 0.0001
    pip_value_per_lot: float = 10.0
    spread_pips: float = 1.0
    commission_per_lot: float = 7.0

@dataclass
class BacktestResult:
    config: BacktestConfig
    trades: List[SimulatedTrade]
    equity_curve: List[Dict[str, Any]]
    total_trades: int
    win_rate: float
    profit_factor: float
    net_profit: float
    max_drawdown: float
    expectancy_r: float

# ==========================================
# 4. POSITION MANAGEMENT
# ==========================================
def _calculate_position_size(balance, risk_pct, entry, sl, config):
    sl_distance_pips = abs(entry - sl) / config.pip_size
    if sl_distance_pips == 0: return 0.01
    risk_amount = balance * (risk_pct / 100)
    risk_per_lot = sl_distance_pips * config.pip_value_per_lot
    lots = risk_amount / risk_per_lot
    return max(0.01, round(lots, 2))

def _update_open_trades(open_trades, candle, config):
    for trade in open_trades:
        if trade.status != TradeStatus.OPEN: continue
        
        # Check SL
        if trade.direction == SignalDirection.BUY and candle['low'] <= trade.stop_loss:
            trade.status = TradeStatus.CLOSED_SL
            trade.exit_price = trade.stop_loss
            trade.exit_time = candle['time']
        elif trade.direction == SignalDirection.SELL and candle['high'] >= trade.stop_loss:
            trade.status = TradeStatus.CLOSED_SL
            trade.exit_price = trade.stop_loss
            trade.exit_time = candle['time']
            
        # Check TP
        elif trade.direction == SignalDirection.BUY and candle['high'] >= trade.take_profit:
            trade.status = TradeStatus.CLOSED_TP
            trade.exit_price = trade.take_profit
            trade.exit_time = candle['time']
        elif trade.direction == SignalDirection.SELL and candle['low'] <= trade.take_profit:
            trade.status = TradeStatus.CLOSED_TP
            trade.exit_price = trade.take_profit
            trade.exit_time = candle['time']

        # EOD Close (21:00 SAST = 19:00 UTC)
        if trade.status == TradeStatus.OPEN and candle['time'].hour == 19 and candle['time'].minute == 0:
            trade.status = TradeStatus.CLOSED_EOD
            trade.exit_price = candle['close']
            trade.exit_time = candle['time']

        if trade.status in [TradeStatus.CLOSED_TP, TradeStatus.CLOSED_SL, TradeStatus.CLOSED_EOD]:
            price_diff = trade.exit_price - trade.entry_price if trade.direction == SignalDirection.BUY else trade.entry_price - trade.exit_price
            pips_gained = price_diff / config.pip_size
            gross_pnl = pips_gained * config.pip_value_per_lot * trade.size_lots
            commission = config.commission_per_lot * trade.size_lots * 2
            trade.pnl = gross_pnl - commission
            
            initial_risk = abs(trade.entry_price - trade.stop_loss) / config.pip_size * config.pip_value_per_lot * trade.size_lots
            trade.r_multiple = trade.pnl / initial_risk if initial_risk > 0 else 0

# ==========================================
# 5. MAIN BACKTEST ENGINE
# ==========================================
def run_backtest(df_m5, df_h1, df_h4, df_d1, strategy, strategy_conditions, symbol, config=BacktestConfig()):
    trades = []
    equity_curve = []
    current_balance = config.starting_balance
    open_trades = []
    
    aggregator = ZeroLookAheadAggregator(df_d1, df_h4, df_h1)
    vol_engine = VolatilityEngine()
    
    df_m5 = df_m5.sort_values('time').reset_index(drop=True)
    
    # Start at 120 to allow aggregator to warm up
    for i in range(120, len(df_m5)):
        current_candle = df_m5.iloc[i]
        current_time = current_candle['time']
        
        # 1. Manage existing trades
        _update_open_trades(open_trades, current_candle, config)
        
        # 2. Update balance
        for t in open_trades:
            if t.status != TradeStatus.OPEN:
                current_balance += t.pnl
        open_trades = [t for t in open_trades if t.status == TradeStatus.OPEN]
        
        # 3. Record Equity
        floating_pnl = sum(
            ((current_candle['close'] - t.entry_price) if t.direction == SignalDirection.BUY else (t.entry_price - current_candle['close'])) / config.pip_size * config.pip_value_per_lot * t.size_lots
            for t in open_trades
        )
        equity_curve.append({"time": current_time, "equity": current_balance + floating_pnl})
        
        # 4. Reconstruct HTF (No Look-Ahead)
        hist_m5 = df_m5.iloc[:i+1]
        h1_view, h4_view, d1_view = aggregator.get_feeds_at_time(hist_m5, current_time.to_pydatetime())
        
        # 5. Compute Volatility
        vol_metrics = vol_engine.compute_symbol_volatility(d1_view, hist_m5, current_candle['close'], symbol, current_time.to_pydatetime())
        
        # 6. Generate Signal
        ctx = {
            "df": hist_m5,
            "daily_df": d1_view,
            "h4_df": h4_view,
            "current_time": current_time,
            "symbol": symbol,
            "spread_pips": config.spread_pips,
            "vol_metrics": vol_metrics
        }
        signal = strategy.evaluate_signal(ctx)
        
        if signal:
            # 7. Volatility Filter (Stolen from old bot)
            if vol_metrics.get("valid"):
                sl_dist = abs(signal.entry_price - signal.stop_loss)
                if sl_dist > (vol_metrics['adr'] * 0.5): # SL cannot be wider than 50% of ADR
                    continue # Skip trade
            
            # 8. Checklist
            pre_ctx = PreTradeContext(
                df=hist_m5, daily_df=d1_view, time=current_time,
                symbol=symbol, spread_pips=config.spread_pips,
                intended_direction=BiasDirection.BULLISH if signal.direction == SignalDirection.BUY else BiasDirection.BEARISH
            )
            check = run_pre_trade_check(pre_ctx, strategy_conditions)
            
            if check["decision"] in ["TRADE", "REDUCE_SIZE"]:
                risk_mult = 1.0 if check["decision"] == "TRADE" else 0.5
                size = _calculate_position_size(current_balance, config.risk_per_trade_pct * risk_mult, signal.entry_price, signal.stop_loss, config)
                
                new_trade = SimulatedTrade(
                    id=f"trd-{len(trades)}", symbol=symbol, direction=signal.direction,
                    entry_price=signal.entry_price, stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit, size_lots=size,
                    entry_time=current_time, setup_grade=signal.setup_grade,
                    strategy_name=signal.strategy_name, reason=signal.reason
                )
                open_trades.append(new_trade)
                trades.append(new_trade)

    # Final Stats
    closed = [t for t in trades if t.status != TradeStatus.OPEN]
    if not closed:
        return BacktestResult(config, trades, equity_curve, 0, 0, 0, 0, 0, 0)
        
    wins = [t for t in closed if t.pnl > 0]
    gross_profit = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in closed if t.pnl <= 0))
    
    peak = -float('inf')
    max_dd = 0.0
    for p in equity_curve:
        peak = max(peak, p['equity'])
        max_dd = max(max_dd, (peak - p['equity']) / peak * 100)
        
    return BacktestResult(
        config=config, trades=trades, equity_curve=equity_curve,
        total_trades=len(closed),
        win_rate=round(len(wins)/len(closed)*100, 2),
        profit_factor=round(gross_profit/gross_loss, 2) if gross_loss > 0 else 99.9,
        net_profit=round(gross_profit - gross_loss, 2),
        max_drawdown=round(max_dd, 2),
        expectancy_r=round(sum(t.r_multiple for t in closed)/len(closed), 2)
    )