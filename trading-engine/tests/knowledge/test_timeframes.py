import unittest
from datetime import datetime, timedelta, timezone

from knowledge.timeframes import describe_timeframe


class TimeframeTests(unittest.TestCase):
    def test_describes_explicit_candle_window(self):
        candle_open = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)

        report = describe_timeframe("h1", candle_open)

        self.assertEqual(report.timeframe, "H1")
        self.assertEqual(report.duration, timedelta(hours=1))
        self.assertEqual(
            report.candle_close_time,
            datetime(2026, 11, 18, 13, 0, tzinfo=timezone.utc),
        )
        self.assertIn("only when that interval has ended", report.summary)

    def test_describes_weekly_candle_window(self):
        candle_open = datetime(2026, 11, 16, tzinfo=timezone.utc)

        report = describe_timeframe("w1", candle_open)

        self.assertEqual(report.timeframe, "W1")
        self.assertEqual(report.duration, timedelta(days=7))
        self.assertEqual(
            report.candle_close_time,
            datetime(2026, 11, 23, tzinfo=timezone.utc),
        )

    def test_rejects_unknown_timeframe_and_non_utc_time(self):
        candle_open = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError):
            describe_timeframe("M2", candle_open)
        with self.assertRaises(ValueError):
            describe_timeframe(
                "M5",
                candle_open.astimezone(timezone(timedelta(hours=1))),
            )


if __name__ == "__main__":
    unittest.main()
