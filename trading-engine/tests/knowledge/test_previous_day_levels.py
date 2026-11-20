import unittest
from datetime import datetime, timezone

import pandas as pd

from knowledge.previous_day_levels import analyze_previous_day_levels


class PreviousDayLevelsTests(unittest.TestCase):
    def test_reports_only_completed_candles_inside_previous_utc_day(self):
        candles = pd.DataFrame(
            {
                "time": pd.to_datetime(
                    [
                        "2026-11-18 23:30:00+00:00",
                        "2026-11-19 00:00:00+00:00",
                        "2026-11-19 23:00:00+00:00",
                        "2026-11-20 00:00:00+00:00",
                    ],
                    utc=True,
                ),
                "high": [99.0, 1.12, 1.15, 2.0],
                "low": [1.0, 1.08, 1.09, 1.0],
            }
        )

        report = analyze_previous_day_levels(
            candles,
            "H1",
            datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(report.day.isoformat(), "2026-11-19")
        self.assertEqual(report.observed_high, 1.15)
        self.assertEqual(report.observed_low, 1.08)
        self.assertEqual(report.candle_count, 2)

    def test_reports_missing_previous_day_data_without_guessing(self):
        candles = pd.DataFrame(
            {
                "time": pd.to_datetime(
                    ["2026-11-20 00:00:00+00:00"],
                    utc=True,
                ),
                "high": [1.2],
                "low": [1.1],
            }
        )

        report = analyze_previous_day_levels(
            candles,
            "H1",
            datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc),
        )

        self.assertIsNone(report.observed_high)
        self.assertIsNone(report.observed_low)
        self.assertIn("No observed levels", report.summary)


if __name__ == "__main__":
    unittest.main()
