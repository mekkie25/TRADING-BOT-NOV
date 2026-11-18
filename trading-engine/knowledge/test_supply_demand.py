import unittest
from datetime import datetime, timezone

import pandas as pd

from knowledge.market_structure import MarketStructureConfig
from knowledge.supply_demand import analyze_supply_demand


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


class SupplyDemandTests(unittest.TestCase):
    def setUp(self):
        self.config = MarketStructureConfig(
            swing_lookback_left=1,
            swing_lookback_right=1,
        )
        self.as_of = datetime(2026, 11, 19, 0, 0, tzinfo=timezone.utc)

    def test_reports_swing_candle_ranges_as_candidate_zones(self):
        report = analyze_supply_demand(
            make_candles(),
            "h1",
            self.as_of,
            self.config,
        )

        supply_zones = [
            zone for zone in report.zones if zone.type == "candidate_supply"
        ]
        demand_zones = [
            zone for zone in report.zones if zone.type == "candidate_demand"
        ]
        self.assertEqual(
            [(zone.low, zone.high) for zone in supply_zones],
            [(1.02, 1.12), (1.01, 1.13), (1.02, 1.14)],
        )
        self.assertEqual(
            [(zone.low, zone.high) for zone in demand_zones],
            [(0.99, 1.11), (1.00, 1.12), (1.01, 1.13)],
        )
        self.assertEqual(report.timeframe, "H1")
        self.assertIn("does not prove resting orders", report.summary)

    def test_does_not_use_an_unfinished_candle_to_confirm_a_swing(self):
        candles = make_candles()
        incomplete_candle = pd.DataFrame(
            {
                "time": [pd.Timestamp("2026-11-19 00:00", tz="UTC")],
                "open": [1.12],
                "high": [1.00],
                "low": [0.90],
                "close": [0.95],
            }
        )
        candles = pd.concat([candles, incomplete_candle], ignore_index=True)
        candles.loc[6, "high"] = 1.10

        report = analyze_supply_demand(
            candles,
            "H1",
            datetime(2026, 11, 19, 0, 30, tzinfo=timezone.utc),
            self.config,
        )
        after_close_report = analyze_supply_demand(
            candles,
            "H1",
            datetime(2026, 11, 19, 1, 0, tzinfo=timezone.utc),
            self.config,
        )

        self.assertNotIn(candles.loc[7, "time"], [z.occurred_at for z in report.zones])
        self.assertIn(
            candles.loc[7, "time"],
            [z.occurred_at for z in after_close_report.zones],
        )

    def test_reports_missing_completed_candles_without_guessing(self):
        report = analyze_supply_demand(
            pd.DataFrame(),
            "W1",
            self.as_of,
            self.config,
        )

        self.assertEqual(report.zones, [])
        self.assertIn("W1", report.unavailable)
        self.assertIn("No candidate supply or demand zones", report.summary)

    def test_rejects_an_unsupported_timeframe(self):
        with self.assertRaisesRegex(ValueError, "Unsupported timeframe"):
            analyze_supply_demand(
                make_candles(),
                "M2",
                self.as_of,
                self.config,
            )


if __name__ == "__main__":
    unittest.main()
