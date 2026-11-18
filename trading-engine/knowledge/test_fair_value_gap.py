import unittest

import pandas as pd

from knowledge.fair_value_gap import (
    FVGConfig,
    FVGDirection,
    FVGStatus,
    FillCriteria,
    analyze,
    get_active_fvgs,
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


class FairValueGapTests(unittest.TestCase):
    def setUp(self):
        self.config = FVGConfig(
            min_gap_atr_multiple=0,
            atr_period=1,
            fill_criteria=FillCriteria.FIFTY_PERCENT,
        )

    def test_reports_bullish_gap_bounds_midpoint_and_creation_time(self):
        candles = make_candles(
            [
                (1.0995, 1.1000, 1.0990, 1.0998),
                (1.1000, 1.1005, 1.0995, 1.1002),
                (1.1010, 1.1015, 1.1010, 1.1012),
            ]
        )

        result = analyze(candles, self.config)
        gap = result["active_bullish_fvgs"][0]

        self.assertEqual(gap.direction, FVGDirection.BULLISH)
        self.assertAlmostEqual(gap.bottom, 1.1000)
        self.assertAlmostEqual(gap.top, 1.1010)
        self.assertAlmostEqual(gap.midpoint, 1.1005)
        self.assertEqual(gap.creation_time, candles.iloc[2]["time"])
        self.assertIn("from 1.1 to 1.101", result["summary"])

    def test_midpoint_fill_is_reported_as_partial_until_far_edge_close(self):
        candles = make_candles(
            [
                (1.0995, 1.1000, 1.0990, 1.0998),
                (1.1000, 1.1005, 1.0995, 1.1002),
                (1.1010, 1.1015, 1.1010, 1.1012),
                (1.1008, 1.1012, 1.1004, 1.1006),
            ]
        )

        gaps = get_active_fvgs(candles, config=self.config)

        self.assertEqual(gaps[0].status, FVGStatus.PARTIALLY_FILLED)

    def test_empty_data_is_reported(self):
        self.assertEqual(analyze(pd.DataFrame()), {"error": "Empty DataFrame"})


if __name__ == "__main__":
    unittest.main()
