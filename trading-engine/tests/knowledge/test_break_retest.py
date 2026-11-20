import unittest

import pandas as pd

from knowledge.break_retest import analyze_break_retest


def make_candles(rows):
    return pd.DataFrame(
        rows,
        columns=["open", "high", "low", "close"],
        index=pd.date_range(
            "2026-11-18",
            periods=len(rows),
            freq="h",
            tz="UTC",
            name="time",
        ),
    ).rename_axis("time").reset_index()


class BreakRetestTests(unittest.TestCase):
    def test_reports_later_retest_touch_without_claiming_the_level_held(self):
        candles = make_candles(
            [
                (1.09, 1.10, 1.08, 1.09),
                (1.09, 1.12, 1.09, 1.11),
                (1.11, 1.12, 1.099, 1.10),
            ]
        )

        report = analyze_break_retest(candles, 1.10, "bullish")

        self.assertEqual(report.status, "retest_observed")
        self.assertEqual(report.break_time, candles.iloc[1]["time"])
        self.assertEqual(report.retest_time, candles.iloc[2]["time"])
        self.assertIn("does not show that the level held", report.summary)

    def test_wick_break_can_be_reported_with_no_later_retest(self):
        candles = make_candles(
            [
                (1.11, 1.12, 1.10, 1.11),
                (1.11, 1.12, 1.08, 1.10),
                (1.08, 1.09, 1.07, 1.08),
            ]
        )

        report = analyze_break_retest(
            candles,
            1.10,
            "bearish",
            confirmation="wick",
        )

        self.assertEqual(report.status, "waiting_for_retest")
        self.assertEqual(report.break_price, 1.08)
        self.assertIsNone(report.retest_time)

    def test_does_not_call_a_level_touch_before_a_break_a_retest(self):
        candles = make_candles(
            [
                (1.09, 1.10, 1.08, 1.09),
                (1.09, 1.11, 1.09, 1.10),
                (1.10, 1.12, 1.09, 1.10),
            ]
        )

        report = analyze_break_retest(candles, 1.10, "bullish")

        self.assertEqual(report.status, "no_break")
        self.assertIsNone(report.retest_time)


if __name__ == "__main__":
    unittest.main()
