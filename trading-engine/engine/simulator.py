"""Chronological, single-symbol historical trade simulation."""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from broker.costs import calculate_round_trip_commission
from broker.fill import market_fill_price
from data.timeframes import TIMEFRAME_LENGTHS
from engine.models import Direction, Signal, Trade
from strategies.base import BarContext, Strategy


@dataclass(frozen=True)
class BacktestConfig:
    pip_size: float = 0.0001
    pip_value_per_lot: float = 10.0
    spread_pips: float = 1.0
    slippage_pips: float = 0.0
    commission_per_lot_per_side: float = 7.0
    atr_period: int = 14
    minimum_lots: float = 0.01
    lot_step: float = 0.01


@dataclass
class BacktestResult:
    starting_balance: float
    final_balance: float
    final_equity: float
    net_profit: float
    return_percent: float
    total_trades: int
    wins: int
    losses: int
    breakeven: int
    win_rate: float
    profit_factor: Optional[float]
    max_drawdown_percent: float
    expectancy_r: float
    trades: List[Trade]
    equity_curve: List[Dict[str, Any]]
    daily_equity: List[Dict[str, Any]]
    skipped_signals: List[Dict[str, Any]]
    assumptions: List[str]


class BacktestSimulator:
    """Replays closed bars and fills signals at the next bar's open."""

    def __init__(
        self,
        df: pd.DataFrame,
        strategy: Strategy,
        starting_balance: float,
        risk_percent: float,
        symbol: str = "EURUSD",
        config: Optional[BacktestConfig] = None,
    ) -> None:
        if not math.isfinite(starting_balance) or starting_balance <= 0:
            raise ValueError("starting_balance must be a positive finite number")
        if not math.isfinite(risk_percent) or not 0 < risk_percent <= 100:
            raise ValueError("risk_percent must be greater than 0 and no more than 100")

        self.config = config or BacktestConfig()
        self._validate_config(self.config)
        self.df = self._normalize_candles(df)
        self.strategy = strategy
        self.symbol = symbol.upper()
        self.timeframe = str(getattr(strategy, "timeframe", "")).upper()
        if self.timeframe not in TIMEFRAME_LENGTHS:
            raise ValueError(f"Unsupported strategy timeframe: {self.timeframe}")

        supported_symbols = getattr(strategy, "symbols", None)
        if supported_symbols and self.symbol not in [item.upper() for item in supported_symbols]:
            raise ValueError(f"Strategy does not support {self.symbol}")

        self.starting_balance = float(starting_balance)
        self.risk_percent = float(risk_percent)
        self.balance = self.starting_balance
        self.equity = self.starting_balance
        self.closed_trades: List[Trade] = []
        self.open_trade: Optional[Trade] = None
        self.equity_curve: List[Dict[str, Any]] = []
        self.daily_equity: List[Dict[str, Any]] = []
        self.skipped_signals: List[Dict[str, Any]] = []
        self._atr_values = self._calculate_atr(self.df, self.config.atr_period)
        self._has_run = False

    @staticmethod
    def _validate_config(config: BacktestConfig) -> None:
        positive_values = {
            "pip_size": config.pip_size,
            "pip_value_per_lot": config.pip_value_per_lot,
            "minimum_lots": config.minimum_lots,
            "lot_step": config.lot_step,
        }
        for name, value in positive_values.items():
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive finite number")

        non_negative_values = {
            "spread_pips": config.spread_pips,
            "slippage_pips": config.slippage_pips,
            "commission_per_lot_per_side": config.commission_per_lot_per_side,
        }
        for name, value in non_negative_values.items():
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite non-negative number")
        if config.atr_period < 1:
            raise ValueError("atr_period must be at least 1")

    @staticmethod
    def _normalize_candles(df: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(df, pd.DataFrame) or df.empty:
            raise ValueError("Candle data must be a non-empty DataFrame")

        candles = df.copy()
        if "time" not in candles.columns and "timestamp" in candles.columns:
            candles = candles.rename(columns={"timestamp": "time"})

        required_columns = ["time", "open", "high", "low", "close"]
        missing_columns = [name for name in required_columns if name not in candles.columns]
        if missing_columns:
            raise ValueError(f"Missing candle columns: {', '.join(missing_columns)}")

        candles["time"] = pd.to_datetime(candles["time"], utc=True, errors="coerce")
        if candles["time"].isna().any():
            raise ValueError("Candle times must all be valid UTC timestamps")

        for name in ["open", "high", "low", "close"]:
            candles[name] = pd.to_numeric(candles[name], errors="coerce")
        price_values = candles[["open", "high", "low", "close"]].to_numpy(dtype=float)
        if not np.isfinite(price_values).all():
            raise ValueError("Candle prices must all be finite numbers")
        if (price_values <= 0).any():
            raise ValueError("Candle prices must be positive")

        candles = candles.sort_values("time").reset_index(drop=True)
        if candles["time"].duplicated().any():
            raise ValueError("Candle timestamps must be unique")
        if (
            (candles["high"] < candles["low"]).any()
            or (candles["high"] < candles["open"]).any()
            or (candles["high"] < candles["close"]).any()
            or (candles["low"] > candles["open"]).any()
            or (candles["low"] > candles["close"]).any()
        ):
            raise ValueError("Candle high and low values do not contain open and close")

        return candles

    @staticmethod
    def _calculate_atr(candles: pd.DataFrame, period: int) -> pd.Series:
        previous_close = candles["close"].shift(1)
        true_range = pd.concat(
            [
                candles["high"] - candles["low"],
                (candles["high"] - previous_close).abs(),
                (candles["low"] - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        return true_range.rolling(window=period, min_periods=period).mean()

    def _record_skipped_signal(self, signal: Signal, signal_time: datetime, reason: str) -> None:
        self.skipped_signals.append(
            {
                "signal_time": signal_time,
                "direction": signal.direction.value,
                "reason": reason,
            }
        )

    def _open_position(
        self,
        signal: Signal,
        atr: float,
        signal_time: datetime,
        entry_bar: pd.Series,
    ) -> Optional[Trade]:
        if self.open_trade is not None:
            self._record_skipped_signal(signal, signal_time, "position_already_open")
            return None
        if not math.isfinite(atr) or atr <= 0:
            self._record_skipped_signal(signal, signal_time, "atr_not_ready")
            return None
        if self.config.spread_pips > signal.max_spread_pips:
            self._record_skipped_signal(signal, signal_time, "spread_above_strategy_limit")
            return None
        if signal.sl_atr_multiple <= 0 or signal.tp_atr_multiple <= 0:
            self._record_skipped_signal(signal, signal_time, "invalid_atr_multiple")
            return None

        entry_mid = float(entry_bar["open"])
        direction = signal.direction
        entry_side = direction
        entry_price = market_fill_price(
            entry_mid,
            entry_side,
            self.config.pip_size,
            self.config.spread_pips,
            self.config.slippage_pips,
        )
        stop_distance = atr * signal.sl_atr_multiple
        target_distance = atr * signal.tp_atr_multiple

        if direction == Direction.BUY:
            stop_loss = entry_mid - stop_distance
            take_profit = entry_mid + target_distance
        elif direction == Direction.SELL:
            stop_loss = entry_mid + stop_distance
            take_profit = entry_mid - target_distance
        else:
            raise ValueError(f"Unsupported signal direction: {direction}")

        if stop_loss <= 0 or take_profit <= 0:
            self._record_skipped_signal(signal, signal_time, "invalid_stop_or_target")
            return None

        round_trip_cost_per_lot = (
            (self.config.spread_pips / 2 + 2 * self.config.slippage_pips)
            * self.config.pip_value_per_lot
            + calculate_round_trip_commission(
                1.0,
                self.config.commission_per_lot_per_side,
            )
        )
        stop_risk_per_lot = (
            stop_distance / self.config.pip_size * self.config.pip_value_per_lot
            + round_trip_cost_per_lot
        )
        risk_cash = self.equity * self.risk_percent / 100
        raw_lots = risk_cash / stop_risk_per_lot
        lots = math.floor(raw_lots / self.config.lot_step + 1e-12) * self.config.lot_step
        lots = round(lots, 8)
        if lots < self.config.minimum_lots:
            self._record_skipped_signal(signal, signal_time, "minimum_lot_exceeds_risk_budget")
            return None

        risk_cash = lots * stop_risk_per_lot
        trade = Trade(
            id=f"trd-{len(self.closed_trades)}",
            symbol=self.symbol,
            direction=direction,
            entry_time=entry_bar["time"].to_pydatetime(),
            entry_price=entry_price,
            size_lots=lots,
            sl_price=stop_loss,
            tp_price=take_profit,
            signal_time=signal_time,
            entry_mid_price=entry_mid,
            risk_cash=risk_cash,
        )
        self.open_trade = trade
        return trade

    def _exit_for_bar(
        self,
        trade: Trade,
        candle: pd.Series,
    ) -> Optional[Tuple[float, str, datetime]]:
        half_spread = self.config.spread_pips * self.config.pip_size / 2
        bar_open = float(candle["open"])
        bar_high = float(candle["high"])
        bar_low = float(candle["low"])
        bar_time = candle["time"].to_pydatetime()
        bar_close_time = bar_time + TIMEFRAME_LENGTHS[self.timeframe]

        if trade.direction == Direction.BUY:
            open_quote = bar_open - half_spread
            high_quote = bar_high - half_spread
            low_quote = bar_low - half_spread
            stop_hit_at_open = open_quote <= trade.sl_price
            target_hit_at_open = open_quote >= trade.tp_price
            stop_hit = low_quote <= trade.sl_price
            target_hit = high_quote >= trade.tp_price
            quote_to_mid = half_spread
        else:
            open_quote = bar_open + half_spread
            high_quote = bar_high + half_spread
            low_quote = bar_low + half_spread
            stop_hit_at_open = open_quote >= trade.sl_price
            target_hit_at_open = open_quote <= trade.tp_price
            stop_hit = high_quote >= trade.sl_price
            target_hit = low_quote <= trade.tp_price
            quote_to_mid = -half_spread

        if stop_hit_at_open:
            return bar_open, "stop_loss_gap", bar_time
        if target_hit_at_open:
            return bar_open, "take_profit_gap", bar_time
        if stop_hit and target_hit:
            trigger_quote = trade.sl_price
            reason = "stop_loss_both_touched"
        elif stop_hit:
            trigger_quote = trade.sl_price
            reason = "stop_loss"
        elif target_hit:
            trigger_quote = trade.tp_price
            reason = "take_profit"
        else:
            return None

        return trigger_quote + quote_to_mid, reason, bar_close_time

    def _close_position(
        self,
        trade: Trade,
        exit_mid: float,
        exit_time: datetime,
        reason: str,
    ) -> None:
        exit_side = Direction.SELL if trade.direction == Direction.BUY else Direction.BUY
        trade.exit_mid_price = exit_mid
        trade.exit_price = market_fill_price(
            exit_mid,
            exit_side,
            self.config.pip_size,
            self.config.spread_pips,
            self.config.slippage_pips,
        )
        trade.exit_time = exit_time

        direction_sign = 1.0 if trade.direction == Direction.BUY else -1.0
        trade.gross_pnl = (
            direction_sign
            * (exit_mid - trade.entry_mid_price)
            / self.config.pip_size
            * self.config.pip_value_per_lot
            * trade.size_lots
        )
        trade.spread_cost = (
            self.config.spread_pips
            * self.config.pip_value_per_lot
            * trade.size_lots
        )
        trade.slippage_cost = (
            2
            * self.config.slippage_pips
            * self.config.pip_value_per_lot
            * trade.size_lots
        )
        trade.commission = calculate_round_trip_commission(
            trade.size_lots,
            self.config.commission_per_lot_per_side,
        )
        trade.pnl = (
            trade.gross_pnl
            - trade.spread_cost
            - trade.slippage_cost
            - trade.commission
        )
        trade.r_multiple = trade.pnl / trade.risk_cash if trade.risk_cash > 0 else 0.0
        trade.exit_reason = reason

        self.balance += trade.pnl
        self.equity = self.balance
        self.closed_trades.append(trade)
        self.open_trade = None

    def _unrealized_pnl(self, close_mid: float) -> float:
        trade = self.open_trade
        if trade is None:
            return 0.0

        direction_sign = 1.0 if trade.direction == Direction.BUY else -1.0
        gross_pnl = (
            direction_sign
            * (close_mid - trade.entry_mid_price)
            / self.config.pip_size
            * self.config.pip_value_per_lot
            * trade.size_lots
        )
        spread_cost = (
            self.config.spread_pips
            * self.config.pip_value_per_lot
            * trade.size_lots
        )
        slippage_cost = (
            2
            * self.config.slippage_pips
            * self.config.pip_value_per_lot
            * trade.size_lots
        )
        commission = calculate_round_trip_commission(
            trade.size_lots,
            self.config.commission_per_lot_per_side,
        )
        return gross_pnl - spread_cost - slippage_cost - commission

    def _record_equity(self, timestamp: datetime, close_mid: float) -> None:
        unrealized_pnl = self._unrealized_pnl(close_mid)
        self.equity = self.balance + unrealized_pnl
        previous_peak = max(
            (point["equity"] for point in self.equity_curve),
            default=self.starting_balance,
        )
        peak = max(previous_peak, self.equity)
        drawdown_percent = (
            (peak - self.equity) / peak * 100
            if peak > 0
            else 0.0
        )
        self.equity_curve.append(
            {
                "time": timestamp,
                "balance": self.balance,
                "equity": self.equity,
                "unrealized_pnl": unrealized_pnl,
                "return_percent": (self.equity / self.starting_balance - 1) * 100,
                "drawdown_percent": drawdown_percent,
            }
        )

    def _build_daily_equity(self) -> List[Dict[str, Any]]:
        by_day: Dict[str, List[Dict[str, Any]]] = {}
        for point in self.equity_curve:
            day = point["time"].date().isoformat()
            by_day.setdefault(day, []).append(point)

        daily = []
        for day, points in sorted(by_day.items()):
            opening_equity = points[0]["equity"]
            closing_equity = points[-1]["equity"]
            daily.append(
                {
                    "date": day,
                    "open_equity": opening_equity,
                    "close_equity": closing_equity,
                    "pnl": closing_equity - opening_equity,
                    "return_percent": (
                        (closing_equity / opening_equity - 1) * 100
                        if opening_equity > 0
                        else 0.0
                    ),
                }
            )
        return daily

    def run(self) -> BacktestResult:
        if self._has_run:
            raise RuntimeError("A BacktestSimulator instance can only run once")
        self._has_run = True

        first_time = self.df.iloc[0]["time"].to_pydatetime()
        self.equity_curve.append(
            {
                "time": first_time,
                "balance": self.balance,
                "equity": self.equity,
                "unrealized_pnl": 0.0,
                "return_percent": 0.0,
                "drawdown_percent": 0.0,
            }
        )

        pending_signal: Optional[Tuple[Signal, float, datetime]] = None
        for index, candle in self.df.iterrows():
            candle_time = candle["time"].to_pydatetime()
            candle_close_time = candle_time + TIMEFRAME_LENGTHS[self.timeframe]
            opened_this_bar = False

            if self.open_trade is not None:
                exit_event = self._exit_for_bar(self.open_trade, candle)
                if exit_event is not None:
                    exit_mid, reason, exit_time = exit_event
                    self._close_position(self.open_trade, exit_mid, exit_time, reason)

            if pending_signal is not None:
                signal, atr, signal_time = pending_signal
                if self.open_trade is None and self.equity > 0:
                    opened_this_bar = self._open_position(
                        signal,
                        atr,
                        signal_time,
                        candle,
                    ) is not None
                elif self.equity <= 0:
                    self._record_skipped_signal(signal, signal_time, "non_positive_equity")
                else:
                    self._record_skipped_signal(signal, signal_time, "position_already_open")
                pending_signal = None

            if opened_this_bar and self.open_trade is not None:
                exit_event = self._exit_for_bar(self.open_trade, candle)
                if exit_event is not None:
                    exit_mid, reason, exit_time = exit_event
                    self._close_position(self.open_trade, exit_mid, exit_time, reason)

            if index == len(self.df) - 1 and self.open_trade is not None:
                self._close_position(
                    self.open_trade,
                    float(candle["close"]),
                    candle_close_time,
                    "end_of_data",
                )

            self._record_equity(candle_close_time, float(candle["close"]))

            context = BarContext(
                df=self.df.iloc[: index + 1].copy(),
                current_time=candle_close_time,
                symbol=self.symbol,
            )
            signal = self.strategy.on_bar(context)
            if signal is None:
                continue
            if not isinstance(signal, Signal):
                raise TypeError("Strategies must return engine.models.Signal or None")
            if not isinstance(signal.direction, Direction):
                raise TypeError("Signal direction must be a Direction")
            signal_values = (
                signal.sl_atr_multiple,
                signal.tp_atr_multiple,
                signal.max_spread_pips,
            )
            if not all(math.isfinite(value) for value in signal_values):
                raise ValueError("Signal values must all be finite numbers")
            if signal.max_spread_pips < 0:
                raise ValueError("Signal max_spread_pips must be non-negative")
            if index == len(self.df) - 1:
                self._record_skipped_signal(signal, candle_close_time, "no_next_bar_for_entry")
                continue
            if self.open_trade is not None:
                self._record_skipped_signal(signal, candle_close_time, "position_already_open")
                continue

            atr = float(self._atr_values.iloc[index])
            if not math.isfinite(atr) or atr <= 0:
                self._record_skipped_signal(signal, candle_close_time, "atr_not_ready")
                continue
            pending_signal = (signal, atr, candle_close_time)

        self.daily_equity = self._build_daily_equity()
        return self._build_result()

    def _build_result(self) -> BacktestResult:
        wins = [trade for trade in self.closed_trades if trade.pnl > 0]
        losses = [trade for trade in self.closed_trades if trade.pnl < 0]
        breakeven = len(self.closed_trades) - len(wins) - len(losses)
        gross_profit = sum(trade.pnl for trade in wins)
        gross_loss = abs(sum(trade.pnl for trade in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else None
        max_drawdown_percent = max(
            (point["drawdown_percent"] for point in self.equity_curve),
            default=0.0,
        )
        expectancy_r = (
            sum(trade.r_multiple for trade in self.closed_trades) / len(self.closed_trades)
            if self.closed_trades
            else 0.0
        )
        net_profit = self.balance - self.starting_balance

        return BacktestResult(
            starting_balance=self.starting_balance,
            final_balance=self.balance,
            final_equity=self.equity,
            net_profit=net_profit,
            return_percent=(self.equity / self.starting_balance - 1) * 100,
            total_trades=len(self.closed_trades),
            wins=len(wins),
            losses=len(losses),
            breakeven=breakeven,
            win_rate=len(wins) / len(self.closed_trades) * 100 if self.closed_trades else 0.0,
            profit_factor=profit_factor,
            max_drawdown_percent=max_drawdown_percent,
            expectancy_r=expectancy_r,
            trades=list(self.closed_trades),
            equity_curve=list(self.equity_curve),
            daily_equity=list(self.daily_equity),
            skipped_signals=list(self.skipped_signals),
            assumptions=[
                f"Risk: {self.risk_percent:g}% of current equity per trade.",
                (
                    "Data range: "
                    f"{self.df.iloc[0]['time'].isoformat()} through "
                    f"{self.df.iloc[-1]['time'].isoformat()} "
                    f"({(self.df.iloc[-1]['time'] - self.df.iloc[0]['time']).days} days)."
                ),
                f"Spread: fixed at {self.config.spread_pips:g} pips.",
                f"Commission: ${self.config.commission_per_lot_per_side:g} per lot per side.",
                f"Slippage: fixed at {self.config.slippage_pips:g} pips per fill.",
                "Overnight swap is not modeled.",
                "Only one position is open at a time.",
                "When a bar touches both stop loss and take profit, stop loss is counted first.",
                "Signals use closed bars and enter at the next bar's open.",
                "Price gaps can cause stop losses to exceed the configured risk amount.",
                "Margin and leverage limits are not modeled.",
                "Market-condition analysis, setup grades, MAE/MFE, optimization, and robustness tests are not implemented.",
            ],
        )
