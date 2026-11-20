import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from knowledge.volume_profile import ApproximateVolumeProfileProvider


class ApproximateVolumeProfileTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        self.provider = ApproximateVolumeProfileProvider(
            value_area_fraction=0.7,
            bin_size_acs_multiple=0.1,
        )

    def test_tick_volume_is_evenly_distributed_and_labeled_approximate(self):
        candles = pd.DataFrame(
            {
                "time": [self.start, self.start + timedelta(minutes=5)],
                "high": [10.0, 11.0],
                "low": [9.0, 10.0],
                "tick_volume": [100, 50],
            }
        )
        report = self.provider.calculate(
            candles, "M5", self.start, self.start + timedelta(minutes=10),
            self.start + timedelta(minutes=10), average_candle_size=1.0,
        )

        self.assertEqual(report.source, "tick_approx")
        self.assertTrue(report.approximate)
        self.assertIsNotNone(report.poc)
        self.assertIsNotNone(report.vah)
        self.assertIsNotNone(report.val)
        self.assertEqual(report.candle_count, 2)

    def test_absent_or_zero_volume_uses_time_approximation(self):
        candles = pd.DataFrame(
            {
                "time": [self.start],
                "high": [10.0],
                "low": [9.0],
                "volume": [0],
            }
        )
        report = self.provider.calculate(
            candles, "M5", self.start, self.start + timedelta(minutes=5),
            self.start + timedelta(minutes=5), average_candle_size=1.0,
        )
        self.assertEqual(report.source, "time_approx")
        self.assertIsNotNone(report.poc)

    def test_unclosed_candle_is_not_used(self):
        candles = pd.DataFrame(
            {
                "time": [self.start],
                "high": [10.0],
                "low": [9.0],
                "tick_volume": [10],
            }
        )
        report = self.provider.calculate(
            candles, "M5", self.start, self.start + timedelta(minutes=5),
            self.start + timedelta(minutes=2), average_candle_size=1.0,
        )
        self.assertIsNone(report.poc)
        self.assertEqual(report.candle_count, 0)


if __name__ == "__main__":
    unittest.main()
