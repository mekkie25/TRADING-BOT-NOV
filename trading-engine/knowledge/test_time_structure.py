import unittest
from datetime import datetime, timezone

from knowledge.sessions import SessionName
from knowledge.time_structure import report_market_time


class TimeStructureTests(unittest.TestCase):
    def test_reports_london_and_new_york_overlap_with_ny_killzone(self):
        report = report_market_time(
            datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc)
        )

        self.assertEqual(report.session, SessionName.LONDON_NY_OVERLAP)
        self.assertEqual(report.killzones, ["New York"])
        self.assertIn("do not measure trading volume", report.summary)

    def test_dst_is_reflected_in_local_session_clocks(self):
        winter = report_market_time(
            datetime(2026, 1, 15, 13, 30, tzinfo=timezone.utc)
        )
        summer = report_market_time(
            datetime(2026, 7, 15, 12, 30, tzinfo=timezone.utc)
        )

        self.assertEqual(winter.new_york_local_time.hour, 8)
        self.assertEqual(summer.new_york_local_time.hour, 8)
        self.assertEqual(winter.london_local_time.hour, 13)
        self.assertEqual(summer.london_local_time.hour, 13)

    def test_weekend_reports_no_active_session_or_killzone(self):
        report = report_market_time(
            datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)
        )

        self.assertEqual(report.session, SessionName.OFF_SESSION)
        self.assertFalse(report.is_active)
        self.assertEqual(report.killzones, [])


if __name__ == "__main__":
    unittest.main()
