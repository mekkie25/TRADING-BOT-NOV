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
from strategies.power_ranger import PowerRangerStrategy, evaluate


def make_test_candles(rows, start=None, step=timedelta(minutes=5)):
    first = start or datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc)
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


def make_test_facts(session_name="London", current_time=None):
    now = current_time or datetime(2025, 1, 2, 6, 30, tzinfo=timezone.utc)
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


class TestPowerRangerStrategy(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("EURUSD")

    def test_buy_breakout_and_retest(self):
        # 15m range 06:00-06:15: High 102, Low 99
        # Candle 4 at 06:15: breakout closing at 104 (> 102)
        # Candle 5 at 06:20: retest low 101.5 (<= 102), close 103 (> 102)
        # Candle 6 at 06:25: confirmation close 105 (> retest high 103.5)
        candles = make_test_candles(
            [
                (100.0, 101.5, 99.5, 101.0),
                (101.0, 102.0, 100.0, 100.5),
                (100.5, 101.0, 99.0, 100.0),
                (100.0, 104.0, 100.0, 104.0),
                (103.5, 103.5, 101.5, 103.0),
                (103.0, 105.5, 102.5, 105.0),
            ],
            start=datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc),
        )
        facts = make_test_facts(
            session_name="London",
            current_time=datetime(2025, 1, 2, 6, 30, tzinfo=timezone.utc),
        )
        sig = evaluate(candles, facts, self.spec)
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)
        self.assertEqual(sig.metadata["strategy_name"], "power_ranger")
        self.assertEqual(sig.metadata["stop_loss_mode"], "fixed")

    def test_sell_breakout_and_retest(self):
        # 15m range: High 102, Low 99
        # Candle 4: breakout closing at 97 (< 99)
        # Candle 5: retest high 99.5 (>= 99), close 98 (< 99)
        # Candle 6: confirmation close 96 (< retest low 97.5)
        candles = make_test_candles(
            [
                (100.0, 101.5, 99.5, 101.0),
                (101.0, 102.0, 100.0, 100.5),
                (100.5, 101.0, 99.0, 100.0),
                (100.0, 100.0, 96.5, 97.0),
                (97.0, 99.5, 97.5, 98.0),
                (98.0, 98.0, 95.5, 96.0),
            ],
            start=datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc),
        )
        facts = make_test_facts(
            session_name="London",
            current_time=datetime(2025, 1, 2, 6, 30, tzinfo=timezone.utc),
        )
        sig = evaluate(candles, facts, self.spec)
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.SELL)

    def test_incomplete_retest_returns_none(self):
        # Candle 5 did not reach the broken level
        candles = make_test_candles(
            [
                (100.0, 101.5, 99.5, 101.0),
                (101.0, 102.0, 100.0, 100.5),
                (100.5, 101.0, 99.0, 100.0),
                (100.0, 104.0, 100.0, 104.0),
                (104.0, 106.0, 103.5, 105.0),  # Low 103.5 > range_high 102
                (105.0, 107.0, 104.5, 106.5),
            ],
            start=datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc),
        )
        facts = make_test_facts(
            session_name="London",
            current_time=datetime(2025, 1, 2, 6, 30, tzinfo=timezone.utc),
        )
        sig = evaluate(candles, facts, self.spec)
        self.assertIsNone(sig)

    def test_power_ranger_strategy_class(self):
        strat = PowerRangerStrategy(timeframe="M5")
        candles = make_test_candles(
            [
                (100.0, 101.5, 99.5, 101.0),
                (101.0, 102.0, 100.0, 100.5),
                (100.5, 101.0, 99.0, 100.0),
                (100.0, 104.0, 100.0, 104.0),
                (103.5, 103.5, 101.5, 103.0),
                (103.0, 105.5, 102.5, 105.0),
            ],
            start=datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc),
        )
        ctx = BarContext(
            df=candles,
            current_time=datetime(2025, 1, 2, 6, 30, tzinfo=timezone.utc),
            symbol="EURUSD",
        )
        sig = strat.on_bar(ctx)
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)


if __name__ == "__main__":
    unittest.main()
