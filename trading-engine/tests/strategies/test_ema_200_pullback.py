import unittest
from datetime import datetime, timezone

import pandas as pd

from broker.instrument_specs import get_instrument_spec
from engine.models import Direction
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.strategy_sessions import StrategySession
from knowledge.volume_profile import VolumeProfileReport
from strategies.context import MarketFacts, PreviousDayFacts
from strategies.ema_200_pullback import evaluate


def make_test_candles(rows, start=None):
    first = start or datetime(2025, 1, 2, 8, 0, tzinfo=timezone.utc)
    return pd.DataFrame(
        [
            {
                "time": first,
                "open": float(row[0]),
                "high": float(row[1]),
                "low": float(row[2]),
                "close": float(row[3]),
            }
            for row in rows
        ]
    )


def make_test_facts(ema_200=100.0):
    now = datetime(2025, 1, 2, 8, 30, tzinfo=timezone.utc)
    return MarketFacts(
        current_time=now,
        timeframe="M5",
        session=StrategySession(
            name="London",
            observed_at_utc=now,
            local_time=now,
            is_open_window=True,
        ),
        average_candle_size=2.0,
        ema_200=ema_200,
        previous_day=PreviousDayFacts(
            high=105.0,
            low=85.0,
            close=98.0,
            equilibrium=95.0,
            pivots={"P": 96.0, "R1": 107.0, "S1": 87.0, "R2": 116.0, "S2": 76.0},
        ),
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
        daily_flip=DailyFlipReport(
            day=now.date(),
            level=92.0,
            source_candle_time=pd.Timestamp(now),
            summary="Daily Flip at 92",
        ),
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


class Ema200PullbackStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    def test_bullish_pullback_valid(self):
        rows = [
            (101.0, 101.5, 99.5, 100.0),
            (100.0, 101.5, 99.5, 101.5), 
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(ema_200=100.0)
        
        sig = evaluate(candles, facts, self.spec)
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)
        
        # The engine uses fixed_stop mode now
        self.assertAlmostEqual(sig.stop_distance, 50.0, delta=5.0)

    def test_bearish_pullback_valid(self):
        rows = [
            (99.0, 100.5, 98.5, 100.0),
            (100.0, 100.5, 98.0, 98.5),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(ema_200=100.0)
        
        sig = evaluate(candles, facts, self.spec)
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.SELL)

    def test_rejects_cross_through_without_pullback(self):
        rows_weak = [
            (101.0, 101.5, 99.5, 100.0),
            (100.0, 100.3, 99.9, 100.2), 
        ]
        candles_weak = make_test_candles(rows_weak)
        facts = make_test_facts(ema_200=100.0)
        
        sig_weak = evaluate(candles_weak, facts, self.spec)
        self.assertIsNone(sig_weak)

    def test_stop_100_pips_if_atr_above_4(self):
        rows = [
            (101.0, 101.5, 99.5, 100.0),
            (100.0, 101.5, 99.5, 101.5), 
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(ema_200=100.0)
        
        sig = evaluate(candles, facts, self.spec, parameters={"atr": 4.5})
        self.assertIsNotNone(sig)
        
        # The engine uses fixed_stop mode now, bumped to 100
        self.assertAlmostEqual(sig.stop_distance, 100.0, delta=5.0)


if __name__ == "__main__":
    unittest.main()