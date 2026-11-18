import unittest
from datetime import datetime, timezone

import pandas as pd

from knowledge.average_daily_range import analyze_average_daily_range


class AverageDailyRangeTests(unittest.TestCase):
    def test_averages_latest_requested_completed_daily_candles(self):
        candles = pd.DataFrame(
            {
                "time": pd.to_datetime(
                    [
                        "2026-01-01 00:00:00+00:00",
                        "2026-01-02 00:00:00+00:00",
                        "2026-01-03 00:00:00+00:00",
                        "2026-01-04 00:00:00+00:00",
                        "2026-01-05 00:00:00+00:00",
                    ],
                    utc=True,
                ),
                "high": [10.0, 20.0, 30.0, 40.0, 50.0],
                "low": [8.0, 14.0, 24.0, 32.0, 40.0],
            }
        )

        report = analyze_average_daily_range(
            candles,
            "D1",
            3,
            datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc),
        )

        self.assertAlmostEqual(report.average_range, 20.0 / 3.0)
        self.assertEqual(report.sample_count, 3)
        self.assertEqual(report.requested_candles, 3)
        self.assertEqual(
            report.first_candle_time,
            pd.Timestamp("2026-01-02 00:00:00+00:00"),
        )
        self.assertEqual(
            report.last_candle_time,
            pd.Timestamp("2026-01-04 00:00:00+00:00"),
        )

    def test_reports_partial_sample_and_its_average(self):
        candles = pd.DataFrame(
            {
                "time": pd.to_datetime(
                    ["2026-01-01 00:00:00+00:00"],
                    utc=True,
                ),
                "high": [1.12],
                "low": [1.08],
            }
        )

        report = analyze_average_daily_range(
            candles,
            "D1",
            5,
            datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
        )

        self.assertAlmostEqual(report.average_range, 0.04)
        self.assertEqual(report.sample_count, 1)
        self.assertIn("1 of 5 requested candles", report.summary)

    def test_reports_when_no_daily_candle_is_complete(self):
        candles = pd.DataFrame(
            {
                "time": pd.to_datetime(
                    ["2026-01-01 00:00:00+00:00"],
                    utc=True,
                ),
                "high": [1.12],
                "low": [1.08],
            }
        )

        report = analyze_average_daily_range(
            candles,
            "D1",
            5,
            datetime(2026, 1, 1, 23, 59, tzinfo=timezone.utc),
        )

        self.assertIsNone(report.average_range)
        self.assertEqual(report.sample_count, 0)
        self.assertIn("no completed D1 candles", report.summary)

    def test_rejects_non_daily_timeframe_and_invalid_lookback(self):
        candles = pd.DataFrame()
        as_of = datetime(2026, 1, 2, tzinfo=timezone.utc)

        with self.assertRaisesRegex(ValueError, "requires the D1 timeframe"):
            analyze_average_daily_range(candles, "H4", 5, as_of)
        with self.assertRaisesRegex(ValueError, "positive whole number"):
            analyze_average_daily_range(candles, "D1", 0, as_of)


if __name__ == "__main__":
    unittest.main()
