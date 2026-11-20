import unittest
from datetime import datetime, timezone

from knowledge.break_even import analyze_break_even


class BreakEvenTests(unittest.TestCase):
    def test_reports_stop_at_entry_tick_and_quote_at_entry(self):
        quote_time = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)

        result = analyze_break_even(
            "LONG",
            1.1,
            1.10001,
            0.0001,
            1.1,
            1.1002,
            quote_time,
        )

        self.assertTrue(result.stop_is_at_entry)
        self.assertTrue(result.quote_is_at_entry)
        self.assertEqual(result.reference_price, 1.1)
        self.assertEqual(result.time, quote_time)
        self.assertIn("does not include", result.description)

    def test_reports_when_stop_is_not_at_entry(self):
        result = analyze_break_even(
            "SHORT",
            1.1,
            1.1002,
            0.0001,
            1.1001,
            1.1002,
            datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
        )

        self.assertFalse(result.stop_is_at_entry)
        self.assertFalse(result.quote_is_at_entry)
        self.assertEqual(result.reference_price, 1.1002)

    def test_rejects_invalid_tick_size_and_non_utc_time(self):
        quote_time = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError):
            analyze_break_even("LONG", 1.1, 1.1, 0, 1.1, 1.1002, quote_time)
        with self.assertRaises(ValueError):
            analyze_break_even(
                "LONG",
                1.1,
                1.1,
                0.0001,
                1.1,
                1.1002,
                datetime(2026, 11, 18),
            )


if __name__ == "__main__":
    unittest.main()
