import unittest

import pandas as pd

from knowledge.equilibrium import (
    EquilibriumConfig,
    PriceZone,
    RangeMode,
    analyze,
    get_equilibrium,
)


def make_candles(close):
    return pd.DataFrame(
        [
            {
                "time": pd.Timestamp("2026-11-18", tz="UTC"),
                "open": close,
                "high": close,
                "low": close,
                "close": close,
            }
        ]
    )


class EquilibriumTests(unittest.TestCase):
    def test_reports_midpoint_premium_and_quartile_levels(self):
        result = analyze(
            make_candles(1.15),
            range_mode=RangeMode.EXPLICIT,
            high=1.2,
            low=1.0,
            config=EquilibriumConfig(equilibrium_tolerance_pct=0.02),
        )

        self.assertEqual(result["zone"], PriceZone.PREMIUM)
        self.assertAlmostEqual(result["range_info"].equilibrium, 1.1)
        self.assertAlmostEqual(result["range_info"].quartile_low, 1.05)
        self.assertAlmostEqual(result["range_info"].quartile_high, 1.15)
        self.assertAlmostEqual(result["distance_to_eq_pct"], 25)
        self.assertTrue(result["at_or_above_upper_quartile"])
        self.assertIn("not a claim that either is a best trade area", result["summary"])

    def test_reports_price_at_equilibrium(self):
        result = analyze(
            make_candles(1.1),
            range_mode=RangeMode.EXPLICIT,
            high=1.2,
            low=1.0,
        )

        self.assertEqual(result["zone"], PriceZone.AT_EQUILIBRIUM)
        self.assertEqual(result["distance_to_eq_pct"], 0)

    def test_rejects_non_finite_range_prices(self):
        with self.assertRaises(ValueError):
            get_equilibrium(
                make_candles(1.1),
                RangeMode.EXPLICIT,
                high=float("inf"),
                low=1.0,
            )


if __name__ == "__main__":
    unittest.main()
