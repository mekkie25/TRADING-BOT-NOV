import unittest

import pandas as pd

from knowledge.market_structure import MarketStructureConfig
from knowledge.trend_lines import analyze_trend_lines


def make_candles():
    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-11-18",
                periods=8,
                freq="h",
                tz="UTC",
            ),
            "open": [1.00, 1.02, 0.99, 1.01, 1.00, 1.02, 1.01, 1.02],
            "high": [1.10, 1.12, 1.11, 1.13, 1.12, 1.14, 1.13, 1.12],
            "low": [1.00, 1.02, 0.99, 1.01, 1.00, 1.02, 1.01, 1.02],
            "close": [1.00, 1.02, 0.99, 1.01, 1.00, 1.02, 1.01, 1.02],
        }
    )


class TrendLineTests(unittest.TestCase):
    def setUp(self):
        self.config = MarketStructureConfig(
            swing_lookback_left=1,
            swing_lookback_right=1,
        )

    def test_reports_support_and_resistance_lines_per_timeframe(self):
        candles = make_candles()

        result = analyze_trend_lines(
            {"H1": candles, "H4": candles},
            self.config,
        )

        self.assertEqual(len(result.lines), 4)
        self.assertEqual(
            {line.timeframe for line in result.lines},
            {"H1", "H4"},
        )
        support = next(line for line in result.lines if line.type == "candidate_support")
        self.assertAlmostEqual(support.line_price, 1.015)
        self.assertIn("geometric observation", result.summary)

    def test_reports_why_lines_are_unavailable(self):
        candles = make_candles().iloc[:3]

        result = analyze_trend_lines({"M5": candles}, self.config)

        self.assertEqual(result.lines, [])
        self.assertIn("M5.support", result.unavailable)
        self.assertIn("M5.resistance", result.unavailable)

    def test_rejects_non_chronological_timeframes(self):
        candles = make_candles().iloc[::-1]

        with self.assertRaises(ValueError):
            analyze_trend_lines({"H1": candles}, self.config)


if __name__ == "__main__":
    unittest.main()
