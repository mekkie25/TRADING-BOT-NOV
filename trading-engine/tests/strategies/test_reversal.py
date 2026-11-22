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
from strategies.reversal import ReversalStrategy, evaluate


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
    pdh=105.0,
    pdl=85.0,
    asia_high=100.0,
    asia_low=90.0,
    equilibrium=95.0,
    session_name="London",
    acs=2.0,
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
            high=asia_high,
            low=asia_low,
            candle_count=12,
            level_mode="wick",
            session_complete=True,
            summary="Asia complete",
        ),
        previous_day=PreviousDayFacts(
            high=pdh,
            low=pdl,
            close=98.0,
            equilibrium=equilibrium,
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


class TestReversalStrategy(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    def test_pdl_sweep_and_reclaim_bullish(self):
        # PDL = 85.0. Candle 1 sweeps to 84.0 (< 85.0) and closes at 86.0 (> 85.0)
        rows = [
            (88.0, 89.0, 87.0, 87.5),
            (87.0, 87.5, 84.0, 86.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(pdh=105.0, pdl=85.0, equilibrium=95.0)

        sig = evaluate(candles, facts, self.spec, variant="pdh_pdl")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)
        self.assertEqual(sig.strategy_name, "reversal")
        self.assertEqual(sig.variant, "pdh_pdl")
        self.assertEqual(sig.structural_stop_price, 84.0)
        self.assertEqual(sig.structural_target_price, 95.0)  # EQ target

    def test_pdh_sweep_and_reclaim_bearish(self):
        # PDH = 105.0. Candle 1 sweeps to 106.5 (> 105.0) and closes at 104.0 (< 105.0)
        rows = [
            (102.0, 103.5, 101.5, 103.0),
            (103.0, 106.5, 102.8, 104.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(pdh=105.0, pdl=85.0, equilibrium=95.0)

        sig = evaluate(candles, facts, self.spec, variant="pdh_pdl")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.SELL)
        self.assertEqual(sig.structural_stop_price, 106.5)
        self.assertEqual(sig.structural_target_price, 95.0)

    def test_session_extreme_sweep_variant(self):
        # Asia High = 100.0. Swept to 101.2 and closed at 99.2
        rows = [
            (97.0, 98.5, 96.5, 98.0),
            (98.0, 101.2, 97.5, 99.2),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, equilibrium=95.0)

        sig = evaluate(candles, facts, self.spec, variant="session_extreme")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.SELL)
        self.assertEqual(sig.variant, "session_extreme")

    def test_engulfing_reversal_variant(self):
        # Candle 0: bearish down candle pushing below PDL (85.0)
        # Candle 1: strong bullish engulfing reclaiming PDL
        rows = [
            (86.0, 86.5, 84.2, 84.5),  # Bearish (open 86.0, close 84.5)
            (84.0, 87.0, 83.8, 86.8),  # Bullish engulfing (open 84.0 <= 84.5, close 86.8 >= 86.0)
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(pdh=105.0, pdl=85.0, equilibrium=95.0)

        sig = evaluate(candles, facts, self.spec, variant="engulfing")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)
        self.assertEqual(sig.variant, "engulfing")

    def test_target_choice_opposite_extreme(self):
        rows = [
            (88.0, 89.0, 87.0, 87.5),
            (87.0, 87.5, 84.0, 86.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(pdh=105.0, pdl=85.0, equilibrium=95.0)

        sig = evaluate(candles, facts, self.spec, parameters={"target_choice": "opposite_extreme"})
        self.assertIsNotNone(sig)
        self.assertEqual(sig.structural_target_price, 105.0)  # PDH

    def test_strategy_class_on_bar(self):
        base_time = datetime(2025, 1, 1, 22, 0, tzinfo=timezone.utc)
        data = []
        for i in range(120):
            t = base_time + timedelta(minutes=5 * i)
            data.append({"time": t, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0})
        last_time = base_time + timedelta(minutes=5 * 120)
        data.append({"time": last_time, "open": 99.0, "high": 99.5, "low": 97.0, "close": 99.2})
        df = pd.DataFrame(data)

        strategy = ReversalStrategy(timeframe="M5", symbols=["US30"])
        self.assertEqual(strategy.name, "reversal")

        ctx = BarContext(df=df, current_time=last_time + timedelta(minutes=10), symbol="US30")
        sig = strategy.on_bar(ctx)
        self.assertTrue(sig is None or isinstance(sig, Signal))


if __name__ == "__main__":
    unittest.main()