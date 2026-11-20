import unittest

import pandas as pd

from engine.models import Direction
from strategies.pivot_break_retest import evaluate_pivot_break_retest


class PivotBreakRetestTests(unittest.TestCase):
    def test_bearish_daily_s1_break_and_retest_requires_full_context(self):
        result = evaluate_pivot_break_retest(
            candles=self.make_candles(
                opens=[101.0, 99.0, 99.0],
                highs=[102.0, 99.5, 100.5],
                lows=[100.5, 98.5, 98.5],
                closes=[101.0, 99.0, 99.0],
            ),
            daily_r1=110.0,
            daily_s1=100.0,
            daily_r2=115.0,
            daily_s2=95.0,
            confluence_conditions={"ema_200_direction": True},
            narrow_range_day=False,
            stop_loss_price=102.0,
        )

        self.assertEqual(result.status, "TRIGGERED")
        self.assertEqual(result.direction, Direction.SELL)
        self.assertEqual(result.entry_reference_price, 99.0)
        self.assertEqual(result.stop_loss_price, 102.0)
        self.assertEqual(result.take_profit_prices, (95.0,))

    def test_bullish_daily_r1_break_and_retest(self):
        result = evaluate_pivot_break_retest(
            candles=self.make_candles(
                opens=[99.0, 101.0, 101.0],
                highs=[99.5, 101.5, 101.5],
                lows=[98.0, 100.5, 99.5],
                closes=[99.0, 101.0, 101.0],
            ),
            daily_r1=100.0,
            daily_s1=90.0,
            daily_r2=105.0,
            daily_s2=85.0,
            confluence_conditions={"daily_flip": True},
            narrow_range_day=False,
            stop_loss_price=99.0,
        )

        self.assertEqual(result.status, "TRIGGERED")
        self.assertEqual(result.direction, Direction.BUY)
        self.assertEqual(result.take_profit_prices, (105.0,))

    def test_pattern_without_a_required_confluence_is_blocked(self):
        result = evaluate_pivot_break_retest(
            candles=self.make_candles(
                opens=[101.0, 99.0, 99.0],
                highs=[102.0, 99.5, 100.5],
                lows=[100.5, 98.5, 98.5],
                closes=[101.0, 99.0, 99.0],
            ),
            daily_r1=110.0,
            daily_s1=100.0,
            daily_r2=115.0,
            daily_s2=95.0,
            confluence_conditions={"daily_flip": False, "ema_200": None},
            narrow_range_day=False,
            stop_loss_price=102.0,
        )

        self.assertEqual(result.status, "BLOCKED")
        self.assertTrue(any(check.name == "Required additional confluence" for check in result.checks))

    def test_missing_narrow_range_observation_or_stop_blocks_trigger(self):
        result = evaluate_pivot_break_retest(
            candles=self.make_candles(
                opens=[101.0, 99.0, 99.0],
                highs=[102.0, 99.5, 100.5],
                lows=[100.5, 98.5, 98.5],
                closes=[101.0, 99.0, 99.0],
            ),
            daily_r1=110.0,
            daily_s1=100.0,
            daily_r2=115.0,
            daily_s2=95.0,
            confluence_conditions={"daily_flip": True},
            narrow_range_day=None,
            stop_loss_price=None,
        )

        self.assertEqual(result.status, "BLOCKED")
        self.assertTrue(any(check.name == "Stop loss" and check.status == "UNKNOWN" for check in result.checks))

    def test_retest_without_a_prior_break_is_not_a_trigger(self):
        result = evaluate_pivot_break_retest(
            candles=self.make_candles(
                opens=[99.0, 99.0, 99.0],
                highs=[99.5, 100.5, 100.5],
                lows=[98.5, 98.5, 98.5],
                closes=[99.0, 99.0, 99.0],
            ),
            daily_r1=110.0,
            daily_s1=100.0,
            daily_r2=115.0,
            daily_s2=95.0,
            confluence_conditions={"daily_flip": True},
            narrow_range_day=False,
            stop_loss_price=102.0,
        )

        self.assertEqual(result.status, "NOT_TRIGGERED")

    def test_retest_after_a_close_back_across_the_pivot_is_not_a_trigger(self):
        result = evaluate_pivot_break_retest(
            candles=self.make_candles(
                opens=[101.0, 99.0, 101.0, 99.0],
                highs=[102.0, 99.5, 101.5, 100.5],
                lows=[100.5, 98.5, 100.5, 98.5],
                closes=[101.0, 99.0, 101.0, 99.0],
            ),
            daily_r1=110.0,
            daily_s1=100.0,
            daily_r2=115.0,
            daily_s2=95.0,
            confluence_conditions={"daily_flip": True},
            narrow_range_day=False,
            stop_loss_price=102.0,
        )

        self.assertEqual(result.status, "NOT_TRIGGERED")

    @staticmethod
    def make_candles(opens, highs, lows, closes):
        return pd.DataFrame(
            {
                "time": pd.date_range(
                    "2026-11-18 12:00",
                    periods=len(opens),
                    freq="5min",
                    tz="UTC",
                ),
                "open": opens,
                "high": highs,
                "low": lows,
                "close": closes,
            }
        )


if __name__ == "__main__":
    unittest.main()
