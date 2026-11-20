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
from strategies.oes import OES_STUBS, OESStrategy, evaluate


def make_test_candles(rows, start=None, step=timedelta(minutes=5)):
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
    now = current_time or datetime(2025, 1, 2, 13, 40, tzinfo=timezone.utc)
    return MarketFacts(
        current_time=now,
        timeframe="M5",
        session=StrategySession(
            name=session_name,
            observed_at_utc=now,
            local_time=now,
            is_open_window=True,
        ),
        daily_flip=DailyFlipReport(
            date="2025-01-02",
            session_name=session_name,
            level=100.0,
            prior_close=99.0,
            flip_occurred=True,
            first_flip_time=now,
            latest_status="ABOVE",
        ),
        asia=AsiaLevelsReport(
            session_date="2025-01-02",
            high=105.0,
            low=95.0,
            session_complete=True,
            wick_high=105.0,
            wick_low=95.0,
        ),
        previous_day=PreviousDayFacts(
            high=110.0,
            low=90.0,
            close=100.0,
            equilibrium=100.0,
            pivots={"P": 100.0, "R1": 115.0, "S1": 85.0},
        ),
        volume_profile=VolumeProfileReport(
            session_name=session_name,
            poc=100.0,
            vah=104.0,
            val=96.0,
        ),
        average_candle_size=2.0,
    )


class TestOESStrategy(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("EURUSD")

    def test_stubs_registered_and_blocked_by_default(self):
        self.assertIn("oes_5m", OES_STUBS)
        self.assertIn("oes_4h", OES_STUBS)
        self.assertIn("oes_inverse_4h", OES_STUBS)
        self.assertEqual(
            OES_STUBS["oes_5m"].status,
            "BLOCKED_UNDISCLOSED_ENTRY_CRITERIA",
        )

        candles = make_test_candles(
            [(100.0, 102.0, 99.0, 101.0), (101.0, 104.0, 100.5, 103.5)]
        )
        facts = make_test_facts()
        sig = evaluate(candles, facts, self.spec, variant="oes_5m")
        self.assertIsNone(sig)

    def test_experimental_5m_candle_fade(self):
        # Candle 1: High 102, Low 99
        # Candle 2: Closes at 103 (> 102) -> 5M candle fade enters SELL
        candles = make_test_candles(
            [(100.0, 102.0, 99.0, 101.0), (101.0, 103.5, 100.5, 103.0)]
        )
        facts = make_test_facts()
        sig = evaluate(
            candles,
            facts,
            self.spec,
            parameters={"allow_experimental": True},
            variant="oes_5m",
        )
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.SELL)
        self.assertEqual(sig.metadata["strategy_name"], "oes")

    def test_experimental_4h_continuation(self):
        candles = make_test_candles(
            [(100.0, 102.0, 99.0, 101.0), (101.0, 103.5, 100.5, 103.0)]
        )
        facts = make_test_facts()
        sig = evaluate(
            candles,
            facts,
            self.spec,
            parameters={"allow_experimental": True, "zone_high": 102.0},
            variant="oes_4h",
        )
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)

    def test_oes_strategy_class(self):
        strat = OESStrategy(timeframe="M5", variant="oes_5m")
        candles = make_test_candles([(100.0, 102.0, 99.0, 101.0)])
        ctx = BarContext(
            df=candles,
            current_time=datetime(2025, 1, 2, 13, 40, tzinfo=timezone.utc),
            symbol="EURUSD",
        )
        sig = strat.on_bar(ctx)
        self.assertIsNone(sig)


if __name__ == "__main__":
    unittest.main()
