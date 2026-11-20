import unittest
from datetime import datetime, timezone

import pandas as pd

from knowledge.market_structure import (
    MarketStructureConfig,
    TrendState,
    get_last_break,
)
from knowledge.weekly_bias import analyze_weekly_bias


def make_candles(start, frequency, highs, lows):
    return pd.DataFrame(
        {
            "time": pd.date_range(
                start,
                periods=len(highs),
                freq=frequency,
                tz="UTC",
            ),
            "high": highs,
            "low": lows,
            "close": lows,
        }
    )


def bullish_candles(start, frequency):
    return make_candles(
        start,
        frequency,
        [10, 13, 11, 14, 12, 15, 13, 16, 14],
        [9, 8, 7, 9, 8, 10, 9, 12, 11],
    )


def bearish_candles(start, frequency):
    return make_candles(
        start,
        frequency,
        [16, 17, 15, 16, 14, 15, 13, 14, 12],
        [15, 14, 13, 14, 12, 13, 11, 12, 10],
    )


class WeeklyBiasTests(unittest.TestCase):
    def setUp(self):
        self.as_of = datetime(2026, 3, 20, tzinfo=timezone.utc)
        self.config = MarketStructureConfig(
            swing_lookback_left=1,
            swing_lookback_right=1,
        )
        self.weekly = bullish_candles("2026-01-05", "7D")
        self.daily = bullish_candles("2026-03-10", "D")

    def test_reports_weekly_structure_and_daily_alignment(self):
        report = analyze_weekly_bias(
            self.weekly,
            self.daily,
            self.as_of,
            self.config,
        )

        self.assertEqual(report.weekly_bias, "bullish")
        self.assertEqual(report.weekly_structure, TrendState.BULLISH)
        self.assertEqual(report.daily_structure, TrendState.BULLISH)
        self.assertEqual(report.alignment, "bullish")
        self.assertIn("not a trade decision", report.summary)

    def test_reports_mixed_daily_context_without_overriding_weekly_bias(self):
        report = analyze_weekly_bias(
            self.weekly,
            bearish_candles("2026-03-10", "D"),
            self.as_of,
            self.config,
        )

        self.assertEqual(report.weekly_bias, "bullish")
        self.assertEqual(report.daily_structure, TrendState.BEARISH)
        self.assertEqual(report.alignment, "mixed")
        self.assertIn("do not confirm the same direction", report.summary)

    def test_excludes_an_unfinished_weekly_candle_from_structure_and_breaks(self):
        incomplete = make_candles(
            "2026-01-05",
            "7D",
            [10, 13, 11, 14, 12, 15, 13, 16, 100],
            [9, 8, 7, 9, 8, 10, 9, 12, 1],
        )
        incomplete.loc[incomplete.index[-1], "close"] = 100
        as_of = datetime(2026, 3, 6, tzinfo=timezone.utc)

        report = analyze_weekly_bias(
            incomplete,
            self.daily,
            as_of,
            self.config,
        )

        final_candle_time = incomplete.iloc[-1]["time"]
        unfiltered_break = get_last_break(incomplete, self.config)
        self.assertEqual(unfiltered_break.break_time, final_candle_time)
        self.assertNotEqual(
            report.last_weekly_break.break_time
            if report.last_weekly_break
            else None,
            final_candle_time,
        )
        self.assertEqual(report.weekly_bias, "bullish")

    def test_marks_weekly_bias_unknown_when_no_weekly_candles_are_available(self):
        report = analyze_weekly_bias(
            pd.DataFrame(),
            self.daily,
            self.as_of,
            self.config,
        )

        self.assertEqual(report.weekly_bias, "unknown")
        self.assertIsNone(report.weekly_structure)
        self.assertIn("W1", report.unavailable)
        self.assertEqual(report.alignment, "not_assessed")
        self.assertIn("alignment was not assessed", report.summary)


if __name__ == "__main__":
    unittest.main()
