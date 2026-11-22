import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import get_instrument_spec
from engine.models import Direction
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.volume_profile import VolumeProfileReport
from strategies.context import MarketFacts, PreviousDayFacts, StrategySession

START = datetime(2025, 1, 2, 9, 0, tzinfo=timezone.utc)


def make_test_candles(rows, start=START, step=timedelta(minutes=5)):
    return pd.DataFrame(
        [
            {
                "time": start + index * step,
                "open": float(row[0]),
                "high": float(row[1]),
                "low": float(row[2]),
                "close": float(row[3]),
                "volume": 100,
            }
            for index, row in enumerate(rows)
        ]
    )


def make_test_facts(candle_count, acs=1.0, ema_200=91.0):
    now = START + timedelta(minutes=5 * candle_count)
    return MarketFacts(
        current_time=now,
        timeframe="M5",
        session=StrategySession(
            name="London",
            observed_at_utc=now,
            local_time=now,
            is_open_window=True,
        ),
        average_candle_size=acs,
        asia=AsiaLevelsReport(
            observed_at_utc=now,
            session_date="2025-01-02",
            high=100.0,
            low=90.0,
            candle_count=12,
            level_mode="wick",
            session_complete=True,
            summary="Asia complete",
        ),
        previous_day=PreviousDayFacts(
            high=105.0,
            low=85.0,
            close=98.0,
            equilibrium=95.0,
            pivots={"P": 95.0, "R1": 110.0, "S1": 80.0},
        ),
        daily_flip=DailyFlipReport(
            day=now.date(),
            level=92.0,
            source_candle_time=pd.Timestamp(now),
            summary="Daily Flip at 92",
        ),
        ema_200=ema_200,
        volume_profile=VolumeProfileReport(
            poc=94.0,
            vah=97.0,
            val=92.0,
            bin_size=0.2,
            value_area_fraction=0.7,
            source="tick_approx",
            approximate=True,
            candle_count=10,
            summary="Profile available",
        ),
    )


# Gold prices. Grid lines every 5 dollars: 2395, 2400, 2405, 2410.
SUPPORT_AT_2400 = [
    (2401.0, 2402.0, 2399.9, 2401.5),
    (2401.5, 2403.0, 2401.0, 2402.5),
]
RESISTANCE_AT_2405 = [
    (2403.5, 2405.1, 2403.0, 2403.8),
    (2403.8, 2404.2, 2402.4, 2402.9),
]
SUPPORT_AT_2395 = [
    (2396.0, 2397.0, 2394.9, 2396.5),
    (2396.5, 2398.0, 2396.0, 2397.5),
]


class GridStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("XAUUSD")

    def run_grid(self, rows, parameters=None, **fact_changes):
        from strategies.grids import evaluate

        candles = make_test_candles(rows)
        facts = make_test_facts(len(candles))
        if fact_changes:
            facts = replace(facts, **fact_changes)
        return evaluate(candles, facts, self.spec, parameters)

    def test_line_holding_as_support_gives_a_buy_to_the_next_line(self):
        signal = self.run_grid(SUPPORT_AT_2400)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.variant, "grid_hold")
        # Midpoint stop 2397.50, plus the 0.25 x average candle size buffer.
        self.assertAlmostEqual(signal.structural_stop_price, 2397.25)
        self.assertAlmostEqual(signal.structural_target_price, 2405.0)

    def test_line_holding_as_resistance_gives_a_sell_to_the_next_line_down(self):
        signal = self.run_grid(RESISTANCE_AT_2405)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)
        self.assertAlmostEqual(signal.structural_stop_price, 2407.75)
        self.assertAlmostEqual(signal.structural_target_price, 2400.0)

    def test_works_on_any_grid_line_not_just_one(self):
        signal = self.run_grid(SUPPORT_AT_2395)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertAlmostEqual(signal.structural_target_price, 2400.0)

    def test_no_trade_when_price_breaks_through_the_line(self):
        broke_through = [
            (2401.0, 2402.0, 2399.0, 2399.5),
            (2399.5, 2400.0, 2398.5, 2399.0),
        ]
        self.assertIsNone(self.run_grid(broke_through))

    def test_no_trade_when_price_is_far_from_every_line(self):
        middle = [
            (2402.4, 2403.0, 2402.2, 2402.8),
            (2402.8, 2403.1, 2402.3, 2402.6),
        ]
        self.assertIsNone(self.run_grid(middle))

    def test_no_trade_when_closes_are_not_beyond_the_line(self):
        # Touches 2400 but the second candle closes back below it.
        failed = [
            (2401.0, 2402.0, 2399.9, 2401.5),
            (2401.5, 2401.8, 2399.8, 2399.9),
        ]
        self.assertIsNone(self.run_grid(failed))

    def test_needs_enough_candles_to_confirm_the_hold(self):
        self.assertIsNone(self.run_grid(SUPPORT_AT_2400[:1]))

    def test_one_candle_hold_can_be_selected(self):
        signal = self.run_grid(SUPPORT_AT_2400[:1], {"hold_candles": 1})
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)

    def test_stop_fraction_one_gives_one_to_one(self):
        signal = self.run_grid(SUPPORT_AT_2400, {"stop_grid_fraction": 1.0})
        # Stop one full grid below the line (2395) less the 0.25 buffer.
        self.assertAlmostEqual(signal.structural_stop_price, 2394.75)

    def test_grid_size_is_a_setting(self):
        signal = self.run_grid(SUPPORT_AT_2400, {"grid_size": 10.0})
        self.assertIsNotNone(signal)
        self.assertAlmostEqual(signal.structural_target_price, 2410.0)
        self.assertAlmostEqual(signal.structural_stop_price, 2400.0 - 5.0 - 0.25)

    def test_volatility_scaled_exits_stay_selectable(self):
        signal = self.run_grid(
            SUPPORT_AT_2400,
            {"sl_mode": "volatility_scaled", "tp_mode": "volatility_scaled"},
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.sl_mode, "volatility_scaled")
        self.assertAlmostEqual(signal.stop_distance, 1.5)
        self.assertAlmostEqual(signal.target_distance, 3.0)

    def test_structural_is_the_default_exit_mode(self):
        signal = self.run_grid(SUPPORT_AT_2400)
        self.assertEqual(signal.sl_mode, "structural")
        self.assertEqual(signal.tp_mode, "structural")

    def test_bad_settings_are_rejected(self):
        for bad in (
            {"grid_size": 0},
            {"grid_size": -5.0},
            {"stop_grid_fraction": 0},
            {"stop_grid_fraction": 1.5},
            {"hold_candles": 0},
        ):
            with self.assertRaises(ValueError, msg=str(bad)):
                self.run_grid(SUPPORT_AT_2400, bad)

    def test_no_signal_without_an_average_candle_size(self):
        self.assertIsNone(self.run_grid(SUPPORT_AT_2400, average_candle_size=None))


if __name__ == "__main__":
    unittest.main()