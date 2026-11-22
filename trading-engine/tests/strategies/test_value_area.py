import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import get_instrument_spec
from engine.models import Direction, Signal
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.strategy_sessions import StrategySession
from knowledge.volume_profile import VolumeProfileReport
from strategies.base import BarContext
from strategies.context import MarketFacts, PreviousDayFacts
from strategies.value_area import ValueAreaStrategy, evaluate


def make_test_candles(rows, start=None, step=timedelta(minutes=5)):
    first = start or datetime(2025, 1, 2, 8, 0, tzinfo=timezone.utc)
    return pd.DataFrame(
        [
            {
                "time": first + index * step,
                "open": float(row[0]),
                "high": float(row[1]),
                "low": float(row[2]),
                "close": float(row[3]),
            }
            for index, row in enumerate(rows)
        ]
    )


def make_test_facts(
    poc=95.0,
    vah=100.0,
    val=90.0,
    bin_size=0.5,
    acs=2.0,
    session_name="London",
    current_time=None,
):
    now = current_time or datetime(2025, 1, 2, 8, 30, tzinfo=timezone.utc)
    return MarketFacts(
        current_time=now,
        timeframe="M5",
        session=StrategySession(
            name=session_name,
            observed_at_utc=now,
            local_time=now,
            is_open_window=True,
        ),
        average_candle_size=acs,
        asia=AsiaLevelsReport(
            observed_at_utc=now,
            session_date="2025-01-02",
            high=102.0,
            low=88.0,
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
            pivots={"P": 96.0, "R1": 107.0, "S1": 87.0, "R2": 116.0, "S2": 76.0},
        ),
        daily_flip=DailyFlipReport(
            day=now.date(),
            level=92.0,
            source_candle_time=pd.Timestamp(now),
            summary="Daily Flip at 92",
        ),
        ema_200=91.0,
        volume_profile=VolumeProfileReport(
            poc=poc,
            vah=vah,
            val=val,
            bin_size=bin_size,
            value_area_fraction=0.7,
            source="tick_approx",
            approximate=True,
            candle_count=10,
            summary="Profile available",
        ),
    )


class TestValueAreaStrategy(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    def test_bullish_fade_from_val_rejection(self):
        # VAL = 90.0, POC = 95.0, VAH = 100.0
        # Candle 1 tests VAL (low 89.5 <= 90.0) and closes inside (close 91.5 > 90.0)
        rows = [
            (93.0, 93.5, 91.0, 91.5),
            (91.5, 92.5, 89.5, 91.5),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(poc=95.0, vah=100.0, val=90.0)

        sig = evaluate(candles, facts, self.spec, variant="fade")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)
        self.assertEqual(sig.strategy_name, "value_area")
        self.assertEqual(sig.variant, "fade")
        self.assertEqual(sig.structural_stop_price, 89.5)
        self.assertEqual(sig.structural_target_price, 95.0)  # Targets POC by default

    def test_bearish_fade_from_vah_rejection(self):
        # VAH = 100.0, POC = 95.0
        # Candle 1 tests VAH (high 100.8 >= 100.0) and closes inside (close 98.8 < 100.0)
        rows = [
            (97.0, 98.5, 96.5, 98.0),
            (98.0, 100.8, 97.5, 98.8),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(poc=95.0, vah=100.0, val=90.0)

        sig = evaluate(candles, facts, self.spec, variant="fade")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.SELL)
        self.assertEqual(sig.structural_stop_price, 100.8)
        self.assertEqual(sig.structural_target_price, 95.0)  # Targets POC

    def test_fade_targeting_opposite_edge(self):
        # Target opposite edge: VAL rejection targeting VAH (100.0)
        rows = [
            (93.0, 93.5, 91.0, 91.5),
            (91.5, 92.5, 89.5, 91.5),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(poc=95.0, vah=100.0, val=90.0)

        sig = evaluate(candles, facts, self.spec, variant="fade", parameters={"target_choice": "opposite_edge"})
        self.assertIsNotNone(sig)
        self.assertEqual(sig.structural_target_price, 100.0)  # VAH

    def test_breakout_retest_bullish(self):
        # VAH = 100.0.
        # Candle 0 closes above VAH (101.5 > 100.0)
        # Candle 1 retests VAH (low 99.8 <= 100.0) and holds (close 101.0 > 100.0)
        rows = [
            (98.0, 102.0, 98.0, 101.5),
            (101.5, 102.5, 99.8, 101.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(poc=95.0, vah=100.0, val=90.0)

        sig = evaluate(candles, facts, self.spec, variant="breakout_retest")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)
        self.assertEqual(sig.variant, "breakout_retest")
        self.assertEqual(sig.structural_target_price, 107.0)  # Daily R1

    def test_breakout_retest_bearish(self):
        # VAL = 90.0.
        # Candle 0 closes below VAL (88.5 < 90.0)
        # Candle 1 retests VAL (high 90.3 >= 90.0) and holds (close 89.0 < 90.0)
        rows = [
            (92.0, 92.0, 88.0, 88.5),
            (88.5, 90.3, 88.0, 89.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(poc=95.0, vah=100.0, val=90.0)

        sig = evaluate(candles, facts, self.spec, variant="breakout_retest")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.SELL)
        self.assertEqual(sig.structural_target_price, 87.0)  # Daily S1

    def test_skip_when_sitting_directly_at_poc(self):
        # Current close is 95.1, right inside POC bin (POC 95.0, bin_size 0.5)
        rows = [
            (93.0, 93.5, 91.0, 91.5),
            (91.5, 95.5, 89.5, 95.1),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(poc=95.0, vah=100.0, val=90.0, bin_size=0.5)

        sig = evaluate(candles, facts, self.spec, variant="fade")
        self.assertIsNone(sig)

    def test_missing_profile_returns_none(self):
        candles = make_test_candles([(95, 96, 94, 95), (95, 96, 94, 95)])
        now = datetime(2025, 1, 2, 8, 30, tzinfo=timezone.utc)
        empty_facts = MarketFacts(
            current_time=now,
            timeframe="M5",
            session=StrategySession("London", now, now, True),
            average_candle_size=2.0,
            asia=AsiaLevelsReport(now, "2025-01-02", 100, 90, 12, "wick", True, ""),
            previous_day=PreviousDayFacts(105, 85, 98, 95, {}),
            daily_flip=DailyFlipReport(now.date(), 92, pd.Timestamp(now), ""),
            ema_200=91,
            volume_profile=VolumeProfileReport(None, None, None, None, 0.7, "tick_approx", True, 0, ""),
        )
        self.assertIsNone(evaluate(candles, empty_facts, self.spec))

    def test_strategy_class_on_bar(self):
        base_time = datetime(2025, 1, 1, 22, 0, tzinfo=timezone.utc)
        data = []
        for i in range(120):
            t = base_time + timedelta(minutes=5 * i)
            data.append({"time": t, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0})
        last_time = base_time + timedelta(minutes=5 * 120)
        data.append({"time": last_time, "open": 99.0, "high": 99.5, "low": 97.0, "close": 99.2})
        df = pd.DataFrame(data)

        strategy = ValueAreaStrategy(timeframe="M5", symbols=["US30"])
        self.assertEqual(strategy.name, "value_area")

        ctx = BarContext(df=df, current_time=last_time + timedelta(minutes=10), symbol="US30")
        sig = strategy.on_bar(ctx)
        self.assertTrue(sig is None or isinstance(sig, Signal))


if __name__ == "__main__":
    unittest.main()