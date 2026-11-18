import unittest

import pandas as pd

from knowledge.liquidity import (
    LiquidityConfig,
    PoolSide,
    PoolStatus,
    analyze,
    get_liquidity_pools,
    get_recent_sweeps,
)
from knowledge.market_structure import MarketStructureConfig


def make_candles(rows):
    times = pd.date_range(
        "2026-11-18",
        periods=len(rows),
        freq="h",
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


class LiquidityTests(unittest.TestCase):
    def setUp(self):
        self.config = LiquidityConfig(
            equality_tolerance_atr=0.1,
            atr_period=1,
            min_swings_for_pool=2,
            ms_config=MarketStructureConfig(
                swing_lookback_left=1,
                swing_lookback_right=1,
            ),
        )
        self.rows = [
            (1.10, 1.11, 1.09, 1.10),
            (1.11, 1.12, 1.10, 1.11),
            (1.10, 1.11, 1.09, 1.10),
            (1.11, 1.1205, 1.10, 1.11),
            (1.10, 1.11, 1.09, 1.10),
            (1.10, 1.11, 1.09, 1.10),
            (1.09, 1.10, 1.08, 1.09),
            (1.09, 1.10, 1.08, 1.09),
            (1.09, 1.10, 1.08, 1.09),
            (1.09, 1.10, 1.08, 1.09),
        ]

    def test_reports_equal_high_pool_level_and_formation_time(self):
        candles = make_candles(self.rows)

        pools = get_liquidity_pools(candles, self.config)
        buy_side_pool = next(pool for pool in pools if pool.side == PoolSide.BUY_SIDE)

        self.assertAlmostEqual(buy_side_pool.level, 1.1205)
        self.assertEqual(buy_side_pool.swing_count, 2)
        self.assertEqual(buy_side_pool.status, PoolStatus.UNTOUCHED)
        self.assertEqual(buy_side_pool.formed_at, candles.iloc[3]["time"])

    def test_reports_a_sweep_with_time_and_wick_extreme(self):
        rows = self.rows + [(1.11, 1.1210, 1.10, 1.1200)]
        candles = make_candles(rows)

        sweeps = get_recent_sweeps(candles, config=self.config)

        self.assertEqual(len(sweeps), 1)
        self.assertEqual(sweeps[0].event_type.value, "SWEEP")
        self.assertEqual(sweeps[0].event_time, candles.iloc[-1]["time"])
        self.assertAlmostEqual(sweeps[0].wick_extreme, 1.1210)
        self.assertIn("swept at", analyze(candles, self.config)["summary"])


if __name__ == "__main__":
    unittest.main()
