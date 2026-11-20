import unittest
from datetime import datetime, timezone

import pandas as pd

from knowledge.previous_week_levels import analyze_previous_week_levels


class PreviousWeekLevelsTests(unittest.TestCase):
    def test_reports_only_completed_candles_inside_previous_utc_week(self):
        candles = pd.DataFrame(
            {
                "time": pd.to_datetime(
                    [
                        "2026-11-08 23:00:00+00:00",
                        "2026-11-09 00:00:00+00:00",
                        "2026-11-15 23:00:00+00:00",
                        "2026-11-15 23:30:00+00:00",
                        "2026-11-16 00:00:00+00:00",
                    ],
                    utc=True,
                ),
                "high": [2.0, 1.12, 1.15, 9.0, 3.0],
                "low": [1.0, 1.08, 1.09, 0.5, 1.0],
            }
        )

        report = analyze_previous_week_levels(
            candles,
            "H1",
            datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(report.week_start.isoformat(), "2026-11-09")
        self.assertEqual(report.week_end.isoformat(), "2026-11-15")
        self.assertEqual(report.observed_high, 1.15)
        self.assertEqual(report.observed_low, 1.08)
        self.assertEqual(report.candle_count, 2)

    def test_reports_missing_previous_week_data_without_guessing(self):
        candles = pd.DataFrame(
            {
                "time": pd.to_datetime(
                    ["2026-11-16 00:00:00+00:00"],
                    utc=True,
                ),
                "high": [1.2],
                "low": [1.1],
            }
        )

        report = analyze_previous_week_levels(
            candles,
            "H1",
            datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
        )

        self.assertIsNone(report.observed_high)
        self.assertIsNone(report.observed_low)
        self.assertEqual(report.candle_count, 0)
        self.assertIn("no fully contained, completed candles", report.summary)

    def test_rejects_unsupported_timeframe(self):
        with self.assertRaisesRegex(ValueError, "Unsupported timeframe"):
            analyze_previous_week_levels(
                pd.DataFrame(),
                "M2",
                datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
            )


if __name__ == "__main__":
    unittest.main()
