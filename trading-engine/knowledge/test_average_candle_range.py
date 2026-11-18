import unittest
from datetime import datetime, timezone

import pandas as pd

from data.timeframes import TIMEFRAME_LENGTHS
from knowledge.average_candle_range import analyze_average_candle_range


class AverageCandleRangeTests(unittest.TestCase):
    def test_supports_every_configured_timeframe(self):
        start = pd.Timestamp("2026-01-01 00:00:00+00:00")

        for timeframe, duration in TIMEFRAME_LENGTHS.items():
            with self.subTest(timeframe=timeframe):
                candles = pd.DataFrame(
                    {
                        "time": pd.DatetimeIndex([start, start + duration]),
                        "high": [1.12, 1.20],
                        "low": [1.08, 1.10],
                    }
                )

                report = analyze_average_candle_range(
                    candles,
                    timeframe,
                    1,
                    (start + duration).to_pydatetime(),
                )

                self.assertEqual(report.timeframe, timeframe)
                self.assertAlmostEqual(report.average_range, 0.04)
                self.assertEqual(report.sample_count, 1)

    def test_averages_latest_completed_candles_for_explicit_timeframe(self):
        candles = pd.DataFrame(
            {
                "time": pd.to_datetime(
                    [
                        "2026-01-01 10:00:00+00:00",
                        "2026-01-01 11:00:00+00:00",
                        "2026-01-01 12:00:00+00:00",
                        "2026-01-01 13:00:00+00:00",
                        "2026-01-01 14:00:00+00:00",
                    ],
                    utc=True,
                ),
                "high": [10.0, 20.0, 30.0, 40.0, 50.0],
                "low": [8.0, 16.0, 24.0, 32.0, 40.0],
            }
        )

        report = analyze_average_candle_range(
            candles,
            "H1",
            3,
            datetime(2026, 1, 1, 14, 30, tzinfo=timezone.utc),
        )

        self.assertAlmostEqual(report.average_range, 6.0)
        self.assertEqual(report.timeframe, "H1")
        self.assertEqual(report.sample_count, 3)
        self.assertEqual(
            report.first_candle_time,
            pd.Timestamp("2026-01-01 11:00:00+00:00"),
        )
        self.assertEqual(
            report.last_candle_time,
            pd.Timestamp("2026-01-01 13:00:00+00:00"),
        )

    def test_reports_partial_sample_and_its_average(self):
        candles = pd.DataFrame(
            {
                "time": pd.to_datetime(
                    ["2026-01-01 10:00:00+00:00"],
                    utc=True,
                ),
                "high": [1.12],
                "low": [1.08],
            }
        )

        report = analyze_average_candle_range(
            candles,
            "M15",
            4,
            datetime(2026, 1, 1, 10, 30, tzinfo=timezone.utc),
        )

        self.assertAlmostEqual(report.average_range, 0.04)
        self.assertEqual(report.sample_count, 1)
        self.assertIn("1 of 4 requested candles", report.summary)

    def test_reports_when_no_candle_is_complete(self):
        candles = pd.DataFrame(
            {
                "time": pd.to_datetime(
                    ["2026-01-01 10:00:00+00:00"],
                    utc=True,
                ),
                "high": [1.12],
                "low": [1.08],
            }
        )

        report = analyze_average_candle_range(
            candles,
            "M15",
            4,
            datetime(2026, 1, 1, 10, 14, tzinfo=timezone.utc),
        )

        self.assertIsNone(report.average_range)
        self.assertEqual(report.sample_count, 0)
        self.assertIn("no completed candles", report.summary)

    def test_rejects_unsupported_timeframe_and_invalid_lookback(self):
        candles = pd.DataFrame()
        as_of = datetime(2026, 1, 1, tzinfo=timezone.utc)

        with self.assertRaisesRegex(ValueError, "Unsupported timeframe"):
            analyze_average_candle_range(candles, "M2", 5, as_of)
        with self.assertRaisesRegex(ValueError, "positive whole number"):
            analyze_average_candle_range(candles, "M5", 0, as_of)


if __name__ == "__main__":
    unittest.main()
