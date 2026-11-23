"""Known-answer tests for the backtester.

Every test feeds the simulator a tiny set of hand-made candles and checks the
result against a number worked out on paper, NOT against the simulator's own
helper functions.

Set-up shared by every test (all numbers are plain EURUSD H1):
- 14 quiet warm-up bars, each 20 pips tall, so the average candle range (ATR) is
  exactly 0.0020 (20 pips) from the 14th bar on.
- The strategy fires once, on the close of the 14th bar. The trade is entered at
  the open of the next bar (bar 15, index 14), at a mid price of 1.1000.
- Stop = 1.0 x ATR = 20 pips. Target = 2.0 x ATR = 40 pips.
- Spread 1 pip, no slippage, commission $7 per lot per side, 1 pip = $10 per lot.
- Risk 2.19% of $10,000 = $219. One lot risks 20 pips x $10 = $200, plus the
  trade costs of $5 (half spread) + $14 (round-trip commission) = $219.
  So the trade size is exactly 1.00 lot.

Hand arithmetic (BUY):
- A buy is filled at the ask (mid + 0.5 pip) and closed at the bid (mid - 0.5 pip).
- Target hit: the target sits on the bid side at 1.1040. Ask entry 1.10005 to bid
  exit 1.1040 = 39.5 pips = $395. Minus $14 commission = +$381.
- Stop hit: the stop sits on the bid side at 1.0980. Ask entry 1.10005 to bid
  exit 1.0980 = -20.5 pips = -$205. Minus $14 commission = -$219 (exactly the risk).
"""

import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from engine.models import Direction, Signal
from engine.simulator import BacktestConfig, BacktestSimulator

START = datetime(2026, 1, 5, tzinfo=timezone.utc)
SIGNAL_BAR_INDEX = 13
CONFIG = BacktestConfig(
    spread_pips=1.0,
    slippage_pips=0.0,
    commission_per_lot_per_side=7.0,
)
STARTING_BALANCE = 10000.0
RISK_PERCENT = 2.19

# (open, high, low, close)
QUIET_BAR = (1.1000, 1.1010, 1.0990, 1.1000)


class OneShotStrategy:
    """Fires exactly one signal, on the close of the 14th bar."""

    name = "known_answer_test"
    timeframe = "H1"
    symbols = ["EURUSD"]

    def __init__(self, direction):
        self.direction = direction
        self.calls = []

    def on_bar(self, ctx):
        self.calls.append((len(ctx.df), ctx.df.iloc[-1]["time"], ctx.current_time))
        if len(ctx.df) == SIGNAL_BAR_INDEX + 1:
            return Signal(
                direction=self.direction,
                sl_atr_multiple=1.0,
                tp_atr_multiple=2.0,
                max_spread_pips=2.0,
            )
        return None


def make_candles(later_bars):
    """14 warm-up bars + the quiet entry bar (index 14) + the given later bars."""
    rows = [QUIET_BAR] * 15 + list(later_bars)
    return pd.DataFrame(
        {
            "time": [START + timedelta(hours=i) for i in range(len(rows))],
            "open": [row[0] for row in rows],
            "high": [row[1] for row in rows],
            "low": [row[2] for row in rows],
            "close": [row[3] for row in rows],
        }
    )


def run_backtest(direction, later_bars):
    strategy = OneShotStrategy(direction)
    simulator = BacktestSimulator(
        df=make_candles(later_bars),
        strategy=strategy,
        starting_balance=STARTING_BALANCE,
        risk_percent=RISK_PERCENT,
        config=CONFIG,
    )
    return simulator.run(), strategy


class KnownAnswerTests(unittest.TestCase):
    def assert_one_trade(self, result, reason, pnl, exit_mid):
        self.assertEqual(result.total_trades, 1)
        trade = result.trades[0]
        self.assertEqual(trade.exit_reason, reason)
        self.assertAlmostEqual(trade.size_lots, 1.0, places=8)
        self.assertAlmostEqual(trade.entry_mid_price, 1.1000, places=8)
        self.assertAlmostEqual(trade.exit_mid_price, exit_mid, places=8)
        self.assertAlmostEqual(trade.pnl, pnl, places=6)
        self.assertAlmostEqual(result.final_balance, STARTING_BALANCE + pnl, places=6)
        self.assertAlmostEqual(result.net_profit, pnl, places=6)
        self.assertAlmostEqual(result.equity_curve[-1]["equity"], STARTING_BALANCE + pnl, places=6)
        return trade

    def test_buy_hits_target_and_makes_381_dollars(self):
        result, _ = run_backtest(Direction.BUY, [(1.1010, 1.1050, 1.1005, 1.1045)])

        trade = self.assert_one_trade(result, "take_profit", 381.0, 1.10405)

        self.assertEqual((result.wins, result.losses), (1, 0))
        self.assertAlmostEqual(trade.risk_cash, 219.0, places=6)
        self.assertAlmostEqual(trade.r_multiple, 381.0 / 219.0, places=6)

    def test_buy_hits_stop_and_loses_exactly_the_219_dollar_risk(self):
        result, _ = run_backtest(Direction.BUY, [(1.0990, 1.0995, 1.0970, 1.0975)])

        trade = self.assert_one_trade(result, "stop_loss", -219.0, 1.09805)

        self.assertEqual((result.wins, result.losses), (0, 1))
        self.assertAlmostEqual(trade.r_multiple, -1.0, places=6)

    def test_sell_hits_target_and_makes_381_dollars(self):
        result, _ = run_backtest(Direction.SELL, [(1.0990, 1.0995, 1.0950, 1.0955)])

        self.assert_one_trade(result, "take_profit", 381.0, 1.09595)

    def test_bar_touching_both_stop_and_target_counts_the_stop_first(self):
        result, _ = run_backtest(Direction.BUY, [(1.1000, 1.1050, 1.0970, 1.1000)])

        self.assert_one_trade(result, "stop_loss_both_touched", -219.0, 1.09805)

    def test_price_gap_through_the_stop_loses_more_than_the_risk(self):
        # Opens 50 pips down, past the stop: filled at the open, not at the stop.
        # (1.0950 - 1.1000) = -50 pips = -$500, minus $10 spread, minus $14 commission.
        result, _ = run_backtest(Direction.BUY, [(1.0950, 1.0960, 1.0940, 1.0945)])

        trade = self.assert_one_trade(result, "stop_loss_gap", -524.0, 1.0950)

        self.assertLess(trade.pnl, -trade.risk_cash)

    def test_trade_still_open_at_the_end_is_closed_at_the_last_close_costs_only(self):
        # No later bars: the price never moves, so only costs are lost:
        # $10 spread + $14 commission = -$24.
        result, _ = run_backtest(Direction.BUY, [])

        self.assert_one_trade(result, "end_of_data", -24.0, 1.1000)

    def test_trade_enters_on_the_bar_after_the_signal(self):
        result, _ = run_backtest(Direction.BUY, [(1.1010, 1.1050, 1.1005, 1.1045)])

        trade = result.trades[0]
        self.assertEqual(trade.entry_time, START + timedelta(hours=SIGNAL_BAR_INDEX + 1))

    def test_strategy_is_only_shown_bars_that_have_already_closed(self):
        _, strategy = run_backtest(Direction.BUY, [(1.1010, 1.1050, 1.1005, 1.1045)])

        self.assertEqual(len(strategy.calls), 16)
        for position, (rows_seen, last_bar_time, current_time) in enumerate(strategy.calls):
            self.assertEqual(rows_seen, position + 1)
            self.assertEqual(current_time, last_bar_time.to_pydatetime() + timedelta(hours=1))


if __name__ == "__main__":
    unittest.main()