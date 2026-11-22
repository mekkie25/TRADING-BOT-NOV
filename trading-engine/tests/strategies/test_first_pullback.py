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


# Bullish trend: impulse, a pullback into the 30 to 60 percent zone, then a candle
# that closes above the pullback high.
IMPULSE_UP = (95.0, 100.0, 94.5, 99.5)
PULLBACK_UP = (99.3, 99.4, 97.5, 98.0)
CONFIRM_UP = (98.2, 100.2, 98.0, 99.9)
# Bearish trend mirror (needs the 200 EMA above price).
IMPULSE_DOWN = (99.0, 99.5, 93.5, 94.0)
PULLBACK_DOWN = (94.5, 96.0, 94.2, 95.0)
CONFIRM_DOWN = (95.0, 95.1, 93.0, 93.8)


class FirstPullbackTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("XAUUSD")

    def run_pullback(self, rows, parameters=None, ema_200=91.0, acs=1.0):
        from strategies.first_pullback import evaluate

        candles = make_test_candles(rows)
        facts = make_test_facts(len(candles), acs=acs, ema_200=ema_200)
        return evaluate(candles, facts, self.spec, parameters)

    def test_first_pullback_in_an_uptrend_is_a_buy(self):
        signal = self.run_pullback([IMPULSE_UP, PULLBACK_UP, CONFIRM_UP])
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.variant, "trend_pullback")
        self.assertEqual(signal.structural_stop_price, 97.5)
        self.assertEqual(signal.structural_target_price, 110.0)

    def test_first_pullback_in_a_downtrend_is_a_sell(self):
        signal = self.run_pullback(
            [IMPULSE_DOWN, PULLBACK_DOWN, CONFIRM_DOWN], ema_200=100.0
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)
        self.assertEqual(signal.structural_stop_price, 96.0)
        self.assertEqual(signal.structural_target_price, 80.0)

    def test_pullback_that_is_too_deep_is_skipped(self):
        too_deep = (99.0, 99.2, 96.0, 97.0)
        self.assertIsNone(self.run_pullback([IMPULSE_UP, too_deep, CONFIRM_UP]))

    def test_pullback_that_is_too_shallow_is_skipped(self):
        too_shallow = (99.5, 99.8, 99.0, 99.2)
        self.assertIsNone(self.run_pullback([IMPULSE_UP, too_shallow, CONFIRM_UP]))

    def test_needs_a_candle_that_closes_above_the_pullback_high(self):
        not_confirmed = (98.2, 99.2, 98.0, 99.0)
        self.assertIsNone(self.run_pullback([IMPULSE_UP, PULLBACK_UP, not_confirmed]))

    def test_trend_must_agree_with_the_200_ema(self):
        self.assertIsNone(
            self.run_pullback([IMPULSE_UP, PULLBACK_UP, CONFIRM_UP], ema_200=105.0)
        )

    def test_retracement_bounds_are_tunable(self):
        deep = (99.0, 99.2, 96.0, 97.0)
        confirm = (97.2, 99.5, 97.0, 99.3)
        rows = [IMPULSE_UP, deep, confirm]
        self.assertIsNone(self.run_pullback(rows))
        signal = self.run_pullback(rows, {"pullback_max_fraction": 0.8})
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)

    def test_bad_retracement_bounds_are_rejected(self):
        with self.assertRaises(ValueError):
            self.run_pullback(
                [IMPULSE_UP, PULLBACK_UP, CONFIRM_UP],
                {"pullback_min_fraction": 0.7, "pullback_max_fraction": 0.5},
            )

    def test_needs_three_candles_and_a_200_ema(self):
        self.assertIsNone(self.run_pullback([IMPULSE_UP, PULLBACK_UP]))
        self.assertIsNone(
            self.run_pullback([IMPULSE_UP, PULLBACK_UP, CONFIRM_UP], ema_200=None)
        )

    def test_exits_stay_tunable(self):
        signal = self.run_pullback(
            [IMPULSE_UP, PULLBACK_UP, CONFIRM_UP],
            {"sl_mode": "structural", "tp_mode": "structural"},
        )
        self.assertIsNotNone(signal)
        # Pullback low 97.5 less the 0.25 x average candle size buffer.
        self.assertAlmostEqual(signal.structural_stop_price, 97.25)


if __name__ == "__main__":
    unittest.main()