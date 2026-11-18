import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from knowledge.market_structure import MarketStructureConfig
from knowledge.multi_timeframe_alignment import analyze_multi_timeframe_alignment


def make_candles(highs, lows):
    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-11-18",
                periods=len(highs),
                freq="h",
                tz="UTC",
            ),
            "high": highs,
            "low": lows,
            "close": lows,
        }
    )


class MultiTimeframeAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.as_of = datetime(2026, 11, 19, 0, 0, tzinfo=timezone.utc)
        self.config = MarketStructureConfig(
            swing_lookback_left=1,
            swing_lookback_right=1,
        )
        self.bullish = make_candles(
            [1.10, 1.12, 1.11, 1.13, 1.12, 1.14, 1.13, 1.12],
            [1.00, 1.02, 0.99, 1.01, 1.00, 1.02, 1.01, 1.02],
        )
        self.bearish = make_candles(
            [1.13, 1.14, 1.12, 1.13, 1.11, 1.12, 1.11, 1.10],
            [1.06, 1.05, 1.00, 1.04, 0.99, 1.03, 0.98, 1.02],
        )

    def test_reports_matching_structure_across_timeframes(self):
        report = analyze_multi_timeframe_alignment(
            {"H1": self.bullish, "H4": self.bullish},
            self.as_of,
            self.config,
        )

        self.assertEqual(report.alignment, "bullish")
        self.assertIn("All 2 available timeframes", report.summary)

    def test_reports_mixed_structure_instead_of_choosing_a_direction(self):
        report = analyze_multi_timeframe_alignment(
            {"H1": self.bullish, "H4": self.bearish},
            self.as_of,
            self.config,
        )

        self.assertEqual(report.alignment, "mixed")
        self.assertIn("do not all report the same direction", report.summary)

    def test_excludes_unfinished_candles_and_does_not_infer_alignment(self):
        as_of = datetime(2026, 11, 18, 0, 30, tzinfo=timezone.utc)
        report = analyze_multi_timeframe_alignment(
            {"H1": self.bullish},
            as_of,
            self.config,
        )

        self.assertEqual(report.alignment, "not_assessed")
        self.assertIn("H1", report.unavailable)


if __name__ == "__main__":
    unittest.main()
