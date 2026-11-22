import unittest

import pandas as pd

from knowledge.fair_value_gap import FVGConfig, FVGDirection
from knowledge.inverse_fvg import (
    IFVGConfig,
    IFVGStatus,
    analyze,
    get_active_ifvgs,
)


def make_candles(rows):
    times = pd.date_range(
        "2026-11-18",
        periods=len(rows),
        freq="5min",
        tz="UTC",
    )
    return pd.DataFrame(
        [
            {
                "time": times[index],
                "open": row[0],
                "high": row[1],
                "low": row[2],
                "close": row[3],
            }
            for index, row in enumerate(rows)
        ]
    )


class InverseFairValueGapTests(unittest.TestCase):
    def setUp(self):
        self.config = IFVGConfig(
            fvg_config=FVGConfig(min_gap_atr_multiple=0, atr_period=1),
        )
        self.rows = [
            (1.0995, 1.1000, 1.0990, 1.0998),
            (1.1000, 1.1005, 1.0995, 1.1002),
            (1.1010, 1.1015, 1.1010, 1.1012),
            (1.1005, 1.1008, 1.0995, 1.0998),
            (1.0999, 1.1005, 1.0998, 1.1002),
            (1.1012, 1.1015, 1.1008, 1.1012),
        ]

    def test_reports_inversion_level_direction_and_time(self):
        candles = make_candles(self.rows[:4])

        result = analyze(candles, self.config)
        inverse_gap = result["fresh_bearish_ifvgs"][0]

        self.assertEqual(inverse_gap.new_direction, FVGDirection.BEARISH)
        self.assertAlmostEqual(inverse_gap.bottom, 1.1000)
        self.assertAlmostEqual(inverse_gap.top, 1.1010)
        self.assertEqual(inverse_gap.inverted_at, candles.iloc[3]["time"])
        self.assertIn("inverted at", result["summary"])

    def test_reports_retest_and_failure_separately(self):
        retested = analyze(make_candles(self.rows[:5]), self.config)
        failed = analyze(make_candles(self.rows), self.config)

        self.assertEqual(
            retested["retested_bearish_ifvgs"][0].status,
            IFVGStatus.RETESTED,
        )
        self.assertEqual(
            failed["failed_bearish_ifvgs"][0].status,
            IFVGStatus.FAILED,
        )
        self.assertIn("status failed", failed["summary"])

    def test_direction_filter_uses_new_inverse_direction(self):
        gaps = get_active_ifvgs(
            make_candles(self.rows[:4]),
            direction=FVGDirection.BEARISH,
            config=self.config,
        )

        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].new_direction, FVGDirection.BEARISH)


if __name__ == "__main__":
    unittest.main()
