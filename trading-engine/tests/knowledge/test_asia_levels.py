import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from knowledge.asia_levels import analyze_asia_levels
from knowledge.daily_flip import analyze_daily_flip


class SessionLevelTests(unittest.TestCase):
    def test_asia_levels_use_only_completed_candles_inside_sast_window(self):
        start = datetime(2025, 1, 1, 22, 0, tzinfo=timezone.utc)
        candles = pd.DataFrame(
            [
                {"time": start + timedelta(hours=i), "open": 100, "high": 110 + i,
                 "low": 90 - i, "close": 101}
                for i in range(7)
            ]
        )
        report = analyze_asia_levels(
            candles,
            "H1",
            datetime(2025, 1, 2, 4, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(report.candle_count, 5)
        self.assertEqual(report.high, 115.0)
        self.assertEqual(report.low, 85.0)
        self.assertTrue(report.session_complete)

    def test_daily_flip_is_first_current_utc_day_open(self):
        day_start = datetime(2025, 1, 2, tzinfo=timezone.utc)
        candles = pd.DataFrame(
            {
                "time": [day_start - timedelta(hours=1), day_start],
                "open": [1.0, 1.2],
            }
        )
        report = analyze_daily_flip(candles, day_start + timedelta(minutes=5))
        self.assertEqual(report.level, 1.2)


if __name__ == "__main__":
    unittest.main()
