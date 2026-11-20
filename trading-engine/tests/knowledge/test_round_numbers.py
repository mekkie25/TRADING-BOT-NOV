import unittest
from datetime import datetime, timezone

from knowledge.round_numbers import analyze_round_numbers


class RoundNumberTests(unittest.TestCase):
    def setUp(self):
        self.quote_time = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)

    def test_reports_levels_around_price_using_supplied_step(self):
        report = analyze_round_numbers(
            "EURUSD",
            self.quote_time,
            price=1.2345,
            step=0.01,
        )

        self.assertEqual(report.lower_level, 1.23)
        self.assertEqual(report.upper_level, 1.24)
        self.assertFalse(report.is_exact_level)
        self.assertIn("1.23 and 1.24", report.summary)

    def test_reports_price_exactly_on_configured_level(self):
        report = analyze_round_numbers(
            "EURUSD",
            self.quote_time,
            price=1.23,
            step=0.01,
        )

        self.assertEqual(report.lower_level, report.upper_level)
        self.assertTrue(report.is_exact_level)
        self.assertEqual(report.distance_to_lower, 0.0)

    def test_rejects_missing_or_invalid_level_step(self):
        with self.assertRaises(ValueError):
            analyze_round_numbers("EURUSD", self.quote_time, 1.2345, 0)


if __name__ == "__main__":
    unittest.main()
