import unittest
from datetime import datetime, timezone, timedelta

from knowledge.spread import analyze_spread


class SpreadTests(unittest.TestCase):
    def setUp(self):
        self.quote_time = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)

    def test_reports_price_spread_and_converts_only_using_supplied_sizes(self):
        report = analyze_spread(
            "EURUSD",
            self.quote_time,
            bid=1.0850,
            ask=1.0852,
            pip_size=0.0001,
            tick_size=0.00001,
        )

        self.assertAlmostEqual(report.spread_price, 0.0002)
        self.assertAlmostEqual(report.spread_pips, 2.0)
        self.assertAlmostEqual(report.spread_ticks, 20.0)
        self.assertIn("2 pips", report.summary)

    def test_without_pip_size_reports_price_units_not_assumed_pips(self):
        report = analyze_spread("EURUSD", self.quote_time, 1.0850, 1.0852)

        self.assertIsNone(report.spread_pips)
        self.assertIn("Pip size was not supplied", report.summary)

    def test_rejects_crossed_quotes_and_non_utc_timestamps(self):
        with self.assertRaises(ValueError):
            analyze_spread("EURUSD", self.quote_time, 1.0852, 1.0850)

        non_utc_time = self.quote_time.astimezone(
            timezone(timedelta(hours=1))
        )
        with self.assertRaises(ValueError):
            analyze_spread("EURUSD", non_utc_time, 1.0850, 1.0852)


if __name__ == "__main__":
    unittest.main()
