import unittest
from datetime import datetime, timedelta, timezone

from knowledge.drawdown import analyze_drawdown


class DrawdownTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)

    def test_reports_current_and_maximum_drawdown_from_opening_equity(self):
        history = [
            (self.start, 900.0),
            (self.start + timedelta(hours=1), 950.0),
        ]

        report = analyze_drawdown(history, opening_equity=1000.0)

        self.assertEqual(report.current.amount, 50.0)
        self.assertAlmostEqual(report.current.percent, 5.0)
        self.assertEqual(report.maximum_amount.amount, 100.0)
        self.assertAlmostEqual(report.maximum_percent.percent, 10.0)

    def test_reports_missing_history_without_inventing_a_value(self):
        report = analyze_drawdown([])

        self.assertIsNone(report.current)
        self.assertIsNone(report.maximum_amount)
        self.assertIn("no equity history", report.summary)

    def test_rejects_out_of_order_equity_history(self):
        history = [
            (self.start, 1000.0),
            (self.start, 900.0),
        ]

        with self.assertRaises(ValueError):
            analyze_drawdown(history)


if __name__ == "__main__":
    unittest.main()
