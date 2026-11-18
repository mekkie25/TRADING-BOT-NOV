import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from data.data_quality import inspect_candle_data


class CandleDataQualityTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 1, 5, tzinfo=timezone.utc)

    def candle(self, time, open_price=1.1, high=1.101, low=1.099, close=1.1):
        return {
            "timestamp": time,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
        }

    def test_market_closed_gap_is_reported_as_review_not_corruption(self):
        friday = datetime(2026, 1, 9, 21, tzinfo=timezone.utc)
        sunday = datetime(2026, 1, 11, 22, tzinfo=timezone.utc)
        report = inspect_candle_data(
            pd.DataFrame([self.candle(friday), self.candle(sunday)]),
            "H1",
        )

        self.assertEqual(report.status, "REVIEW")
        self.assertFalse(report.has_errors)
        self.assertEqual(report.gap_count, 1)
        self.assertEqual(report.weekend_shaped_gap_count, 1)
        self.assertEqual(report.gap_examples[0]["gapHours"], 49)
        self.assertEqual(report.gap_examples[0]["category"], "weekend-shaped")

    def test_finds_duplicate_out_of_order_timestamps_and_bad_ohlc(self):
        rows = [
            self.candle(self.start),
            self.candle(self.start + timedelta(hours=2)),
            self.candle(self.start + timedelta(hours=1)),
            self.candle(
                self.start + timedelta(hours=1),
                high=1.0,
                low=1.1,
            ),
        ]

        report = inspect_candle_data(pd.DataFrame(rows), "H1")

        self.assertEqual(report.duplicate_timestamp_count, 1)
        self.assertEqual(report.out_of_order_timestamp_count, 1)
        self.assertEqual(report.invalid_ohlc_row_count, 1)
        self.assertEqual(report.status, "ERROR")

    def test_finds_invalid_time_and_price_rows(self):
        rows = [
            self.candle("not a timestamp"),
            self.candle(
                self.start + timedelta(hours=1),
                open_price=0,
                close=float("inf"),
            ),
        ]

        report = inspect_candle_data(pd.DataFrame(rows), "H1")

        self.assertEqual(report.invalid_timestamp_count, 1)
        self.assertEqual(report.invalid_price_row_count, 1)
        self.assertEqual(report.non_positive_price_row_count, 1)
        self.assertEqual(report.status, "ERROR")

    def test_returns_largest_price_moves_as_review_candidates(self):
        rows = [
            self.candle(self.start, close=1.1),
            self.candle(
                self.start + timedelta(hours=1),
                open_price=1.1,
                high=1.112,
                low=1.1,
                close=1.111,
            ),
        ]

        report = inspect_candle_data(pd.DataFrame(rows), "H1")

        self.assertAlmostEqual(report.largest_candle_ranges[0]["rangePercent"], 100 * 0.012 / 1.1)
        self.assertAlmostEqual(report.largest_close_changes[0]["changePercent"], 100 * 0.011 / 1.1)
        self.assertIn("no automatic price-movement threshold", report.summary)

    def test_missing_columns_are_reported(self):
        report = inspect_candle_data(pd.DataFrame([{"close": 1.1}]), "H1")

        self.assertEqual(report.missing_columns, ["time", "open", "high", "low"])
        self.assertTrue(report.has_errors)
        self.assertEqual(report.status, "ERROR")


if __name__ == "__main__":
    unittest.main()
