import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from knowledge.economic_calendar import analyze_economic_calendar


class EconomicCalendarTests(unittest.TestCase):
    def test_loads_multiple_months_converts_event_time_to_utc_and_reports_freshness(self):
        checked_at = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            monthly = output_dir / "monthly"
            monthly.mkdir()
            payload = [
                {
                    "date": "18/11/2026",
                    "time": "17:00",
                    "timezone": "Asia/Karachi",
                    "currency": "USD",
                    "impact": "red",
                    "event": "Inflation report",
                    "scraped_at": "2026-11-18T11:00:00+00:00",
                }
            ]
            calendar_file = monthly / "2026-11.json"
            calendar_file.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            updated_at = checked_at.timestamp() - 3600
            os.utime(calendar_file, (updated_at, updated_at))

            report = analyze_economic_calendar(
                output_dir,
                checked_at,
                stale_after=timedelta(hours=2),
            )

        self.assertEqual(report.status, "fresh")
        self.assertEqual(len(report.events), 1)
        self.assertEqual(
            report.events[0].event_time_utc,
            datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
        )

    def test_reports_missing_calendar_files_as_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = analyze_economic_calendar(
                Path(temporary_directory),
                datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
                stale_after=timedelta(hours=2),
            )

        self.assertEqual(report.status, "unavailable")
        self.assertIn("no scraped event files", report.summary)

    def test_surfaces_malformed_event_data(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            monthly = output_dir / "monthly"
            monthly.mkdir()
            (monthly / "2026-11.json").write_text(
                json.dumps([{"event": "Missing required fields"}]),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                analyze_economic_calendar(
                    output_dir,
                    datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
                    stale_after=timedelta(hours=2),
                )


if __name__ == "__main__":
    unittest.main()
