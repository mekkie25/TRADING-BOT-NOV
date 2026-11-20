import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import get_instrument_spec
from engine.models import Direction
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.strategy_sessions import StrategySession
from knowledge.volume_profile import VolumeProfileReport
from strategies.base import BarContext
from strategies.context import MarketFacts, PreviousDayFacts
from strategies.cracker import CrackerStrategy, evaluate


def make_test_candles(rows, start=None, step=timedelta(minutes=1)):
    first = start or datetime(2025, 1, 2, 13, 30, tzinfo=timezone.utc)
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


def make_test_facts(session_name="New York", current_time=None):
    now = current_time or datetime(2025, 1, 2, 13, 32, tzinfo=timezone.utc)
    return MarketFacts(
        current_time=now,
        timeframe="M1",
        session=StrategySession(
            name=session_name,
            observed_at_utc=now,
            local_time=now,
            is_open_window=True,
        ),
        daily_flip=DailyFlipReport(
            date="2025-01-02",
            session_name=session_name,
            level=43000.0,
            prior_close=42900.0,
            flip_occurred=True,
            first_flip_time=now,
            latest_status="ABOVE",
        ),
        asia=AsiaLevelsReport(
            session_date="2025-01-02",
            high=43100.0,
            low=42800.0,
            session_complete=True,
            wick_high=43100.0,
            wick_low=42800.0,
        ),
        previous_day=PreviousDayFacts(
            high=43200.0,
            low=42700.0,
            close=43000.0,
            equilibrium=42950.0,
            pivots={"P": 43000.0, "R1": 43300.0, "S1": 42700.0},
        ),
        volume_profile=VolumeProfileReport(
            session_name=session_name,
            poc=43000.0,
            vah=43150.0,
            val=42850.0,
        ),
        average_candle_size=30.0,
    )


class TestCrackerStrategy(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    def test_buy_call_trigger(self):
        # Caller supplies: call_direction = 'buy', call_levels = [43050, 43150]
        # Candle 1: Open 43020, High 43040, Low 43010, Close 43030
        # Candle 2: Open 43030, High 43080, Low 43025, Close 43070 (taps 43050 and closes above)
        candles = make_test_candles(
            [
                (43020.0, 43040.0, 43010.0, 43030.0),
                (43030.0, 43080.0, 43025.0, 43070.0),
            ]
        )
        facts = make_test_facts(
            current_time=datetime(2025, 1, 2, 13, 32, tzinfo=timezone.utc)
        )
        sig = evaluate(
            candles,
            facts,
            self.spec,
            parameters={
                "call_direction": "buy",
                "call_levels": [43050.0, 43150.0],
                "new_york_open_utc": datetime(2025, 1, 2, 13, 30, tzinfo=timezone.utc),
            },
        )
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)
        self.assertEqual(sig.metadata["strategy_name"], "cracker")
        self.assertEqual(sig.metadata["time_limit_seconds"], 90)

    def test_sell_call_trigger(self):
        # Caller supplies: call_direction = 'sell', call_levels = [42950, 42850]
        candles = make_test_candles(
            [
                (42980.0, 42990.0, 42960.0, 42970.0),
                (42970.0, 42975.0, 42930.0, 42940.0),
            ]
        )
        facts = make_test_facts(
            current_time=datetime(2025, 1, 2, 13, 32, tzinfo=timezone.utc)
        )
        sig = evaluate(
            candles,
            facts,
            self.spec,
            parameters={
                "call_direction": "sell",
                "call_levels": [42950.0, 42850.0],
                "new_york_open_utc": datetime(2025, 1, 2, 13, 30, tzinfo=timezone.utc),
                "sell_drive_confirmed": True,
            },
        )
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.SELL)

    def test_extended_edition_no_time_limit(self):
        candles = make_test_candles(
            [
                (43020.0, 43040.0, 43010.0, 43030.0),
                (43030.0, 43080.0, 43025.0, 43070.0),
            ]
        )
        facts = make_test_facts(
            current_time=datetime(2025, 1, 2, 13, 32, tzinfo=timezone.utc)
        )
        sig = evaluate(
            candles,
            facts,
            self.spec,
            parameters={
                "call_direction": "buy",
                "call_levels": [43050.0, 43150.0],
                "extended_edition": True,
            },
        )
        self.assertIsNotNone(sig)
        self.assertIsNone(sig.metadata.get("time_limit_seconds"))

    def test_level_invalidated_before_open_skips(self):
        candles = make_test_candles(
            [
                (43020.0, 43040.0, 43010.0, 43030.0),
                (43030.0, 43080.0, 43025.0, 43070.0),
            ]
        )
        facts = make_test_facts(
            current_time=datetime(2025, 1, 2, 13, 32, tzinfo=timezone.utc)
        )
        sig = evaluate(
            candles,
            facts,
            self.spec,
            parameters={
                "call_direction": "buy",
                "call_levels": [43050.0, 43150.0],
                "level_invalidated_before_open": True,
            },
        )
        self.assertIsNone(sig)

    def test_invalid_call_levels_raise(self):
        candles = make_test_candles([(43000, 43010, 42990, 43005)])
        facts = make_test_facts()
        with self.assertRaises(ValueError):
            evaluate(
                candles,
                facts,
                self.spec,
                parameters={"call_direction": "buy", "call_levels": [-10, 0]},
            )


if __name__ == "__main__":
    unittest.main()
