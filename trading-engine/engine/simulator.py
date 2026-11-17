import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from engine.models import Signal, Trade, Direction
from data.clock import DataClock

class BacktestSimulator:
    def __init__(self, df: pd.DataFrame, strategy, starting_balance: float = 10000.0, risk_percent: float = 1.0):
        self.df = df
        self.strategy = strategy
        self.balance = starting_balance
        self.risk_percent = risk_percent
        self.clock = DataClock(df)
        
        self.active_trade = None
        self.closed_trades: List[Trade] = []
        self.trade_id_counter = 1

    def run(self):
        print(f"Starting simulation on {len(self.df)} bars...")
        
        while self.clock.step_forward():
            current_bars = self.clock.get_visible_bars()
            current_bar = current_bars.iloc[-1]
            
            # 1. Check if we need to manage an open trade (SL/TP)
            if self.active_trade:
                self._check_exits(current_bar)

            # 2. Ask strategy for a new signal (if we aren't in a trade)
            if not self.active_trade:
                ctx = type('Context', (), {'bars': current_bars})()
                signal = self.strategy.on_bar(ctx)
                
                if signal:
                    self._open_trade(current_bar, signal)

        # Force close trade if data ends
        if self.active_trade:
            self._close_trade(self.df.iloc[-1], "END_OF_DATA")

        self._print_results()

    def _open_trade(self, bar, signal: Signal):
        entry_price = bar['close']
        
        sl_distance = signal.sl_atr_multiple * 0.0010 
        tp_distance = signal.tp_atr_multiple * 0.0010 
        
        if signal.direction == Direction.BUY:
            sl_price = entry_price - sl_distance
            tp_price = entry_price + tp_distance
        else:
            sl_price = entry_price + sl_distance
            tp_price = entry_price - tp_distance
            
        risk_amount = self.balance * (self.risk_percent / 100.0)
        size_lots = risk_amount / (sl_distance * 10000) 
        
        self.active_trade = Trade(
            id=f"T{self.trade_id_counter:04d}",
            symbol="EURUSD",
            direction=signal.direction,
            entry_time=bar['timestamp'],
            entry_price=entry_price,
            size_lots=size_lots,
            sl_price=sl_price,
            tp_price=tp_price
        )
        print(f"  [OPEN] {self.active_trade.direction.value} at {entry_price:.4f} | SL: {sl_price:.4f} | TP: {tp_price:.4f}")

    def _check_exits(self, bar):
        trade = self.active_trade
        
        if trade.direction == Direction.BUY:
            if bar['low'] <= trade.sl_price:
                self._close_trade(bar, "SL", trade.sl_price)
            elif bar['high'] >= trade.tp_price:
                self._close_trade(bar, "TP", trade.tp_price)
        else:
            if bar['high'] >= trade.sl_price:
                self._close_trade(bar, "SL", trade.sl_price)
            elif bar['low'] <= trade.tp_price:
                self._close_trade(bar, "TP", trade.tp_price)

    def _close_trade(self, bar, reason, fill_price=None):
        trade = self.active_trade
        trade.exit_time = bar['timestamp']
        trade.exit_reason = reason
        
        if fill_price:
            trade.exit_price = fill_price
        else:
            trade.exit_price = bar['close']
            
        if trade.direction == Direction.BUY:
            pnl = (trade.exit_price - trade.entry_price) * trade.size_lots * 100000
        else:
            pnl = (trade.entry_price - trade.exit_price) * trade.size_lots * 100000
            
        trade.pnl = pnl
        self.balance += pnl
        
        print(f"  [CLOSE] {reason} at {trade.exit_price:.4f} | PnL: ${pnl:.2f} | New Balance: ${self.balance:.2f}")
        
        self.closed_trades.append(trade)
        self.active_trade = None
        self.trade_id_counter += 1

    def _print_results(self):
        print("\n=== BACKTEST RESULTS ===")
        print(f"Final Balance: ${self.balance:.2f}")
        print(f"Total Trades:  {len(self.closed_trades)}")
        wins = len([t for t in self.closed_trades if t.pnl > 0])
        if len(self.closed_trades) > 0:
            print(f"Win Rate:      {(wins / len(self.closed_trades)) * 100:.1f}%")