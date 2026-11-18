import unittest

import pandas as pd

from knowledge.market_structure import MarketStructureConfig
from knowledge.support_resistance import analyze_support_resistance


def make_candles():
    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-11-18",
                periods=8,
                freq="h",
                tz="UTC",
            ),
            "open": [1.00, 1.02, 0.99, 1.01, 1.00, 1.02, 1.01, 1.02],
            "high": [1.10, 1.12, 1.11, 1.13, 1.12, 1.14, 1.13, 1.12],
            "low": [1.00, 1.02, 0.99, 1.01, 1.00, 1.02, 1.01, 1.02],
            "close": [1.00, 1.02, 0.99, 1.01, 1.00, 1.02, 1.01, 1.02],
        }
    )


class SupportResistanceTests(unittest.TestCase):
    def test_reports_swing_levels_with_price_and_confirmation_time(self):
        result = analyze_support_resistance(
            make_candles(),
            MarketStructureConfig(
                swing_lookback_left=1,
                swing_lookback_right=1,
            ),
        )

        supports = [item for item in result.levels if item.type == "candidate_support"]
        resistances = [
            item for item in result.levels if item.type == "candidate_resistance"
        ]
        self.assertEqual([item.price for item in supports], [0.99, 1.0, 1.01])
        self.assertEqual([item.price for item in resistances], [1.12, 1.13, 1.14])
        self.assertEqual(supports[-1].occurred_at, make_candles().iloc[6]["time"])
        self.assertEqual(supports[-1].confirmed_at, make_candles().iloc[7]["time"])
        self.assertIn("not guarantees", result.summary)

    def test_empty_data_reports_no_levels(self):
        result = analyze_support_resistance(pd.DataFrame())

        self.assertEqual(result.levels, [])
        self.assertIn("no candles", result.summary)


if __name__ == "__main__":
    unittest.main()
