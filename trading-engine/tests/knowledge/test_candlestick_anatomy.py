import unittest

import pandas as pd

from knowledge.candlestick_anatomy import (
    CandleConfig,
    CandleType,
    analyze,
    describe_candle,
)


class CandlestickAnatomyTests(unittest.TestCase):
    def test_describes_bullish_body_and_wicks(self):
        candle = pd.Series(
            {
                "open": 10.0,
                "high": 13.0,
                "low": 8.0,
                "close": 12.0,
            }
        )

        anatomy = describe_candle(candle)

        self.assertEqual(anatomy.direction, CandleType.BULLISH)
        self.assertEqual(anatomy.body_size, 2.0)
        self.assertEqual(anatomy.upper_wick, 1.0)
        self.assertEqual(anatomy.lower_wick, 2.0)
        self.assertEqual(anatomy.total_range, 5.0)
        self.assertAlmostEqual(anatomy.body_pct_of_range, 0.4)

    def test_identifies_doji_using_configured_body_threshold(self):
        candle = pd.Series(
            {
                "open": 100.0,
                "high": 103.0,
                "low": 97.0,
                "close": 100.4,
            }
        )

        anatomy = describe_candle(candle, CandleConfig(doji_body_threshold=0.1))

        self.assertEqual(anatomy.direction, CandleType.DOJI)

    def test_analyze_reports_single_candle_without_pattern_history(self):
        candles = pd.DataFrame(
            [
                {
                    "time": pd.Timestamp("2026-11-18T10:00:00Z"),
                    "open": 100.0,
                    "high": 103.0,
                    "low": 97.0,
                    "close": 100.4,
                }
            ]
        )

        result = analyze(candles)

        self.assertEqual(result["current_anatomy"].direction, CandleType.DOJI)
        self.assertIn("DOJI", result["patterns"])

    def test_analyze_rejects_non_positive_lookback(self):
        with self.assertRaisesRegex(ValueError, "at least one candle"):
            analyze(pd.DataFrame(), lookback=0)


if __name__ == "__main__":
    unittest.main()
