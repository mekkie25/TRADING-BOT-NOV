import unittest

import pandas as pd

from knowledge.market_structure import (
    MarketStructureConfig,
    TrendState,
    analyze,
    get_market_structure,
)


def make_candles(highs, lows, closes=None):
    if closes is None:
        closes = lows
    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-11-18",
                periods=len(highs),
                freq="h",
                tz="UTC",
            ),
            "open": lows,
            "high": highs,
            "low": lows,
            "close": closes,
        }
    )


class MarketStructureTests(unittest.TestCase):
    def setUp(self):
        self.config = MarketStructureConfig(
            swing_lookback_left=1,
            swing_lookback_right=1,
        )

    def test_reports_bullish_structure_and_latest_levels(self):
        candles = make_candles(
            [1.10, 1.12, 1.11, 1.13, 1.12, 1.14, 1.13, 1.12],
            [1.00, 1.02, 0.99, 1.01, 1.00, 1.02, 1.01, 1.02],
        )

        result = analyze(candles, self.config)

        self.assertEqual(get_market_structure(candles, self.config), TrendState.BULLISH)
        self.assertIn("bullish", result["summary"])
        self.assertEqual(result["last_swing_high"].price, 1.14)
        self.assertEqual(result["last_swing_low"].price, 1.01)
        self.assertEqual(result["last_swing_high"].occurred_at, candles.iloc[5]["time"])
        self.assertEqual(result["last_swing_high"].confirmed_at, candles.iloc[6]["time"])
        self.assertEqual(result["last_swing_low"].occurred_at, candles.iloc[6]["time"])
        self.assertEqual(result["last_swing_low"].confirmed_at, candles.iloc[7]["time"])

    def test_reports_bearish_structure(self):
        candles = make_candles(
            [1.13, 1.14, 1.12, 1.13, 1.11, 1.12, 1.11, 1.10],
            [1.06, 1.05, 1.00, 1.04, 0.99, 1.03, 0.98, 1.02],
        )

        result = analyze(candles, self.config)

        self.assertEqual(result["trend"], TrendState.BEARISH)
        self.assertIn("bearish", result["summary"])

    def test_reports_ranging_when_swings_do_not_show_one_direction(self):
        candles = make_candles(
            [1.10, 1.12, 1.11, 1.13, 1.12, 1.14, 1.13, 1.12],
            [1.00, 1.02, 0.99, 1.01, 0.98, 1.02, 0.97, 1.02],
        )

        result = analyze(candles, self.config)

        self.assertEqual(result["trend"], TrendState.RANGING)
        self.assertIn("ranging", result["summary"])

    def test_empty_data_is_reported_without_guessing(self):
        result = analyze(pd.DataFrame(), self.config)

        self.assertEqual(result, {"error": "Empty DataFrame"})

    def test_reports_bos_after_a_close_breaks_confirmed_structure(self):
        highs = [1.10, 1.12, 1.11, 1.13, 1.12, 1.14, 1.13, 1.12, 1.15]
        lows = [1.00, 1.02, 0.99, 1.01, 1.00, 1.02, 1.01, 1.02, 1.12]
        closes = lows[:-1] + [1.15]

        result = analyze(make_candles(highs, lows, closes), self.config)

        self.assertEqual(result["last_break"].type.value, "BOS")
        self.assertEqual(result["last_break"].direction.value, "BULLISH")
        self.assertEqual(result["last_break"].break_price, 1.15)
        self.assertIn("BOS", result["summary"])

    def test_reports_choch_for_a_break_against_the_current_structure(self):
        highs = [1.10, 1.12, 1.11, 1.13, 1.12, 1.14, 1.13, 1.12, 1.03]
        lows = [1.00, 1.02, 0.99, 1.01, 1.00, 1.02, 1.01, 1.02, 1.00]
        closes = lows

        result = analyze(make_candles(highs, lows, closes), self.config)

        self.assertEqual(result["last_break"].type.value, "CHOCH")
        self.assertEqual(result["last_break"].direction.value, "BEARISH")
        self.assertEqual(result["last_break"].break_price, 1.00)

    def test_wick_break_reports_the_wick_level_not_the_close(self):
        highs = [1.10, 1.12, 1.11, 1.13, 1.12, 1.14, 1.13, 1.12, 1.15]
        lows = [1.00, 1.02, 0.99, 1.01, 1.00, 1.02, 1.01, 1.02, 1.12]
        closes = lows[:-1] + [1.13]
        wick_config = MarketStructureConfig(
            swing_lookback_left=1,
            swing_lookback_right=1,
            require_close_for_break=False,
        )

        result = analyze(make_candles(highs, lows, closes), wick_config)

        self.assertEqual(result["last_break"].break_price, 1.15)


if __name__ == "__main__":
    unittest.main()
