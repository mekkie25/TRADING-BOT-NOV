import unittest
from datetime import datetime, timezone

from knowledge.stop_loss import analyze_stop_loss


class StopLossTests(unittest.TestCase):
    def test_long_uses_bid_and_reports_a_reached_level(self):
        quote_time = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)

        result = analyze_stop_loss("LONG", 1.1, 1.1, 1.1002, quote_time)

        self.assertEqual(result.status, "reached")
        self.assertEqual(result.reference_price, 1.1)
        self.assertEqual(result.time, quote_time)
        self.assertIn("has reached or passed", result.description)

    def test_short_uses_ask_and_reports_a_reached_level(self):
        result = analyze_stop_loss(
            "SHORT",
            1.101,
            1.1008,
            1.101,
            datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(result.status, "reached")
        self.assertEqual(result.reference_price, 1.101)

    def test_reports_level_not_reached(self):
        result = analyze_stop_loss(
            "LONG",
            1.099,
            1.1,
            1.1002,
            datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(result.status, "not_reached")
        self.assertIn("has not reached", result.description)

    def test_rejects_invalid_quote_and_non_utc_time(self):
        quote_time = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError):
            analyze_stop_loss(
                "LONG",
                1.1,
                1.1002,
                1.1,
                quote_time,
            )
        with self.assertRaises(ValueError):
            analyze_stop_loss("LONG", 1.1, 1.1, 1.1002, datetime(2026, 11, 18))


if __name__ == "__main__":
    unittest.main()
