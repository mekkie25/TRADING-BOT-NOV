import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction
from knowledge.asia_levels import AsiaLevelsReport
from strategies.asia_breakout import evaluate
from strategies.context import MarketFacts, PreviousDayFacts, StrategySession


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
                "volume": 100,
            }
            for index, row in enumerate(rows)
        ]
    )


def make_test_facts(
    asia_high=100.0,
    asia_low=90.0,
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
            high=105.0,
            low=85.0,
            close=98.0,
            equilibrium=95.0,
            pivots={"R1": 110.0, "S1": 80.0},
        ),
        daily_flip=DailyFlipReport(
            day=now.date(),
            level=92.0,
            source_candle_time=pd.Timestamp(now),
            summary="Daily Flip at 92",
        ),
        ema_200=91.0,
        volume_profile=None,
    )


class AsiaBreakoutStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    def test_bullish_close_and_volume(self):
        rows = [
            (95.0, 96.0, 94.0, 95.0), # Inside
            (95.0, 96.0, 94.0, 99.0), # Inside
            (95.0, 102.0, 94.0, 101.0), # Breakout
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, acs=1.0)
        
        signal = evaluate(candles, facts, self.spec, variant="close_and_volume")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.variant, "close_and_volume")
        self.assertEqual(signal.structural_stop_price, 94.0)

    def test_retest_variant(self):
        # Breakout occurs on candle 1, retest holds on candle 2
        rows = [
            (95.0, 96.0, 94.0, 95.0), # Inside
            (95.0, 102.0, 94.0, 101.0), # Breakout
            (95.0, 102.0, 99.0, 101.0), # Retest
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, acs=1.0)
        
        signal = evaluate(candles, facts, self.spec, variant="retest")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.variant, "retest")

    def test_oi_oi_variant(self):
        rows = [
            (95.0, 101.0, 94.0, 101.0), # Out
            (95.0, 101.0, 94.0, 99.0),   # In
            (95.0, 102.0, 94.0, 101.0), # Out
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, acs=1.0)
        
        signal = evaluate(candles, facts, self.spec, variant="oi_oi")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.variant, "oi_oi")
