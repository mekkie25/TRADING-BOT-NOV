import unittest
from datetime import datetime, timezone

import pandas as pd

from indicators.exponential_moving_average import (
    EMA_PERIODS,
    analyze_exponential_moving_averages,
)


class ExponentialMovingAverageTests(unittest.TestCase):
    def test_calculates_all_four_emas_from_supplied_close_history(self):
        start = pd.Timestamp("2026-11-18 00:00:00", tz="UTC")
        candles = pd.DataFrame(
            {
                "time": pd.date_range(start, periods=3, freq="h"),
                "close": [10.0, 11.0, 12.0],
            }
        )

        report = analyze_exponential_moving_averages(
            candles,
            "H1",
            datetime(2026, 11, 18, 3, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(tuple(report.values), EMA_PERIODS)
        for period in EMA_PERIODS:
            alpha = 2.0 / (period + 1)
            self.assertAlmostEqual(
                report.values[period],
                10.0 + 3.0 * alpha - alpha**2,
            )
        self.assertEqual(report.candle_count, 3)
        self.assertEqual(report.latest_candle_time, candles.iloc[-1]["time"])

    def test_ignores_an_unfinished_candle(self):
        start = pd.Timestamp("2026-11-18 00:00:00", tz="UTC")
        candles = pd.DataFrame(
            {
                "time": pd.date_range(start, periods=4, freq="h"),
                "close": [10.0, 11.0, 12.0, 100.0],
            }
        )

        report = analyze_exponential_moving_averages(
            candles,
            "H1",
            datetime(2026, 11, 18, 3, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(report.candle_count, 3)
        self.assertEqual(report.latest_candle_time, candles.iloc[2]["time"])
        self.assertLess(report.values[20], 20.0)

    def test_reports_missing_completed_history_without_ema_values(self):
        candles = pd.DataFrame(
            {
                "time": pd.to_datetime(["2026-11-18 00:00:00+00:00"], utc=True),
                "close": [1.1],
            }
        )

        report = analyze_exponential_moving_averages(
            candles,
            "H1",
            datetime(2026, 11, 18, 0, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(report.values, {})
        self.assertEqual(report.candle_count, 0)
        self.assertIsNone(report.latest_candle_time)
        self.assertIn("No completed H1 candles", report.summary)

    def test_rejects_bad_timeframe_and_invalid_close_values(self):
        candles = pd.DataFrame(
            {
                "time": pd.to_datetime(["2026-11-18 00:00:00+00:00"], utc=True),
                "close": [1.1],
            }
        )
        as_of = datetime(2026, 11, 18, 1, 0, tzinfo=timezone.utc)

        with self.assertRaisesRegex(ValueError, "Unsupported timeframe"):
            analyze_exponential_moving_averages(candles, "M2", as_of)

        candles.loc[0, "close"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite numbers"):
            analyze_exponential_moving_averages(candles, "M1", as_of)


if __name__ == "__main__":
    unittest.main()
