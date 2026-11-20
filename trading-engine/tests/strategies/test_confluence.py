import unittest

from strategies.confluence import ConfluenceReason, count_confluence


class ConfluenceTests(unittest.TestCase):
    def test_counts_groups_without_creating_a_trigger(self):
        report = count_confluence(
            [
                ConfluenceReason("Asia high", "level_alignment", True),
                ConfluenceReason("Daily pivot", "level_alignment", True),
                ConfluenceReason("London open", "timing_volume", True),
            ],
            minimum_count=2,
        )
        self.assertEqual(report.reason_count, 3)
        self.assertEqual(report.group_count, 2)
        self.assertTrue(report.meets_minimum)
        self.assertFalse(report.starts_trade)

    def test_allows_configured_minimum_of_zero(self):
        report = count_confluence([], minimum_count=0)
        self.assertTrue(report.meets_minimum)


if __name__ == "__main__":
    unittest.main()
