import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from engine.models import Direction, PositionSide, Signal, Trade
from engine.simulator import BacktestConfig, BacktestSimulator


class FirstBarSignalStrategy:
    timeframe = "H1"
    symbols = ["EURUSD"]
    name = "first_bar_signal"

    def __init__(self, sl_atr_multiple=5.0, tp_atr_multiple=10.0):
        self.sl_atr_multiple = sl_atr_multiple
        self.tp_atr_multiple = tp_atr_multiple
        self.context_lengths = []
        self.context_times = []

    def on_bar(self, ctx):
        self.context_lengths.append(len(ctx.df))
        self.context_times.append(ctx.current_time)
        if len(ctx.df) == 1:
            return Signal(
                direction=Direction.BUY,
                sl_atr_multiple=self.sl_atr_multiple,
                tp_atr_multiple=self.tp_atr_multiple,
            )
        return None


class TwoSignalStrategy:
    timeframe = "H1"
    symbols = ["EURUSD"]
    name = "two_signal_strategy"

    def on_bar(self, ctx):
        if len(ctx.df) in (1, 2):
            return Signal(
                direction=Direction.BUY,
                sl_atr_multiple=1,
                tp_atr_multiple=0.5,
            )
        return None


def make_candles(rows):
    start = datetime(2025, 1, 6, tzinfo=timezone.utc)
    return pd.DataFrame(
        [
            {
                "timestamp": start + timedelta(hours=index),
                "open": row[0],
                "high": row[1],
                "low": row[2],
                "close": row[3],
            }
            for index, row in enumerate(rows)
        ]
    )


class BacktestSimulatorTests(unittest.TestCase):
    def test_trade_side_is_separate_from_market_direction(self):
        entry_time = datetime(2025, 1, 6, tzinfo=timezone.utc)
        long_trade = Trade(
            id="long",
            symbol="EURUSD",
            direction=Direction.BUY,
            entry_time=entry_time,
            entry_price=1.1,
            size_lots=0.1,
            sl_price=1.09,
            tp_price=1.12,
        )
        short_trade = Trade(
            id="short",
            symbol="EURUSD",
            direction=Direction.SELL,
            entry_time=entry_time,
            entry_price=1.1,
            size_lots=0.1,
            sl_price=1.11,
            tp_price=1.08,
        )

        self.assertEqual(long_trade.position_side, PositionSide.LONG)
        self.assertEqual(short_trade.position_side, PositionSide.SHORT)

    def test_strategy_sees_only_closed_prefix_and_enters_next_bar_open(self):
        strategy = FirstBarSignalStrategy()
        simulator = BacktestSimulator(
            df=make_candles(
                [
                    (1.1000, 1.1005, 1.0995, 1.1001),
                    (1.1001, 1.1005, 1.0999, 1.1002),
                    (1.1002, 1.1005, 1.0999, 1.1002),
                ]
            ),
            strategy=strategy,
            starting_balance=10000,
            risk_percent=2,
            config=BacktestConfig(atr_period=1),
        )

        result = simulator.run()
        trade = result.trades[0]

        self.assertEqual(strategy.context_lengths, [1, 2, 3])
        self.assertTrue(all(time.tzinfo == timezone.utc for time in strategy.context_times))
        self.assertEqual(trade.signal_time, datetime(2025, 1, 6, 1, tzinfo=timezone.utc))
        self.assertEqual(trade.entry_time, datetime(2025, 1, 6, 1, tzinfo=timezone.utc))
        self.assertAlmostEqual(trade.entry_price, 1.10015)
        self.assertEqual(trade.exit_reason, "end_of_data")

    def test_stop_loss_wins_when_one_bar_touches_stop_and_target(self):
        simulator = BacktestSimulator(
            df=make_candles(
                [
                    (1.1000, 1.1005, 1.0995, 1.1001),
                    (1.1001, 1.1025, 1.0985, 1.1000),
                    (1.1000, 1.1002, 1.0998, 1.1000),
                ]
            ),
            strategy=FirstBarSignalStrategy(sl_atr_multiple=1, tp_atr_multiple=2),
            starting_balance=10000,
            risk_percent=2,
            config=BacktestConfig(atr_period=1),
        )

        trade = simulator.run().trades[0]

        self.assertEqual(trade.exit_reason, "stop_loss_both_touched")
        self.assertLess(trade.pnl, 0)

    def test_profit_and_loss_include_spread_slippage_and_round_trip_commission(self):
        simulator = BacktestSimulator(
            df=make_candles(
                [
                    (1.1000, 1.1005, 1.0995, 1.1001),
                    (1.1001, 1.1005, 1.0999, 1.1002),
                ]
            ),
            strategy=FirstBarSignalStrategy(),
            starting_balance=10000,
            risk_percent=2,
            config=BacktestConfig(atr_period=1, slippage_pips=0.2),
        )

        trade = simulator.run().trades[0]
        expected_gross = (
            (trade.exit_mid_price - trade.entry_mid_price)
            / 0.0001
            * 10
            * trade.size_lots
        )
        expected_spread = 1 * 10 * trade.size_lots
        expected_slippage = 2 * 0.2 * 10 * trade.size_lots
        expected_commission = 2 * 7 * trade.size_lots

        self.assertAlmostEqual(trade.gross_pnl, expected_gross)
        self.assertAlmostEqual(trade.spread_cost, expected_spread)
        self.assertAlmostEqual(trade.slippage_cost, expected_slippage)
        self.assertAlmostEqual(trade.commission, expected_commission)
        self.assertAlmostEqual(
            trade.pnl,
            expected_gross - expected_spread - expected_slippage - expected_commission,
        )

    def test_skips_signal_when_minimum_lot_would_exceed_risk_budget(self):
        simulator = BacktestSimulator(
            df=make_candles(
                [
                    (1.1000, 1.1005, 1.0995, 1.1001),
                    (1.1001, 1.1005, 1.0999, 1.1002),
                ]
            ),
            strategy=FirstBarSignalStrategy(sl_atr_multiple=1, tp_atr_multiple=2),
            starting_balance=50,
            risk_percent=2,
            config=BacktestConfig(atr_period=1),
        )

        result = simulator.run()

        self.assertEqual(result.total_trades, 0)
        self.assertEqual(
            result.skipped_signals[0]["reason"],
            "minimum_lot_exceeds_risk_budget",
        )

    def test_next_trade_size_uses_equity_after_previous_profit(self):
        simulator = BacktestSimulator(
            df=make_candles(
                [
                    (1.1000, 1.1010, 1.0990, 1.1000),
                    (1.1000, 1.1011, 1.1000, 1.1008),
                    (1.1008, 1.1009, 1.1007, 1.1008),
                ]
            ),
            strategy=TwoSignalStrategy(),
            starting_balance=10000,
            risk_percent=2,
            config=BacktestConfig(atr_period=1),
        )

        result = simulator.run()

        self.assertEqual(result.total_trades, 2)
        self.assertGreater(result.trades[0].pnl, 0)
        self.assertGreater(result.trades[1].size_lots, result.trades[0].size_lots)


if __name__ == "__main__":
    unittest.main()
