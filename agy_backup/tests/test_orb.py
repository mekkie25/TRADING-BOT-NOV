import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction, Signal
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.strategy_sessions import StrategySession
from knowledge.volume_profile import VolumeProfileReport
from strategies.base import BarContext
from strategies.context import MarketFacts, PreviousDayFacts
from strategies.orb import OrbStrategy, VARIANTS, evaluate


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


def make_test_facts(
    session_name="London",
    current_time=None,
    ema_200=None,
):
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
        ema_200=ema_200,
    )


class TestOrbStrategy(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("EURUSD")

    def test_unknown_variant_raises(self):
        candles = make_test_candles([(100, 102, 99, 101)])
        facts = make_test_facts()
        with self.assertRaises(ValueError):
            evaluate(candles, facts, self.spec, variant="unknown_orb")

    def test_buy_breakout(self):
        # London opens 08:00 SAST = 06:00 UTC.
        # Range 06:00-06:15 UTC (3 candles): High 102, Low 99.
        # Candle 4 at 06:15 closes at 104 (breakout above range_high).
        candles = make_test_candles(
            [
                (100.0, 101.5, 99.5, 101.0),
                (101.0, 102.0, 100.0, 100.5),
                (100.5, 101.0, 99.0, 100.0),
                (100.0, 104.5, 100.0, 104.0),
            ],
            start=datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc),
        )
        facts = make_test_facts(
            session_name="London",
            current_time=datetime(2025, 1, 2, 6, 20, tzinfo=timezone.utc),
        )
        sig = evaluate(candles, facts, self.spec, variant="orb_15m")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)
        self.assertEqual(sig.metadata["strategy_name"], "orb")
        self.assertEqual(sig.metadata["variant"], "orb_15m")

    def test_sell_breakout(self):
        # Range 06:00-06:15: High 102, Low 99.
        # Candle 4 at 06:15 closes at 97 (breakout below range_low).
        candles = make_test_candles(
            [
                (100.0, 101.5, 99.5, 101.0),
                (101.0, 102.0, 100.0, 100.5),
                (100.5, 101.0, 99.0, 100.0),
                (100.0, 100.0, 96.5, 97.0),
            ],
            start=datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc),
        )
        facts = make_test_facts(
            session_name="London",
            current_time=datetime(2025, 1, 2, 6, 20, tzinfo=timezone.utc),
        )
        sig = evaluate(candles, facts, self.spec, variant="orb_15m")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.SELL)

    def test_no_breakout_inside_box(self):
        # Candle 4 closes inside range
        candles = make_test_candles(
            [
                (100.0, 102.0, 99.0, 101.0),
                (101.0, 101.5, 100.0, 100.5),
                (100.5, 101.0, 99.5, 100.0),
                (100.0, 101.0, 99.5, 100.5),
            ],
            start=datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc),
        )
        facts = make_test_facts(
            session_name="London",
            current_time=datetime(2025, 1, 2, 6, 20, tzinfo=timezone.utc),
        )
        sig = evaluate(candles, facts, self.spec, variant="orb_15m")
        self.assertIsNone(sig)

    def test_100_pip_range_switch_skips(self):
        # Range is 100 pips or more on EURUSD (100 pips = 0.0100)
        candles = make_test_candles(
            [
                (1.1000, 1.1150, 1.0950, 1.1050),
                (1.1050, 1.1120, 1.1000, 1.1080),
                (1.1080, 1.1100, 1.0900, 1.1000),
                (1.1000, 1.1200, 1.1000, 1.1180),
            ],
            start=datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc),
        )
        facts = make_test_facts(
            session_name="London",
            current_time=datetime(2025, 1, 2, 6, 20, tzinfo=timezone.utc),
        )
        sig = evaluate(
            candles,
            facts,
            self.spec,
            parameters={"range_size_unit": "pips", "maximum_range_units": 100.0},
            variant="orb_15m",
        )
        self.assertIsNone(sig)

    def test_strategy_class(self):
        strat = OrbStrategy(timeframe="M5", variant="orb_15m")
        candles = make_test_candles(
            [
                (100.0, 101.5, 99.5, 101.0),
                (101.0, 102.0, 100.0, 100.5),
                (100.5, 101.0, 99.0, 100.0),
                (100.0, 104.5, 100.0, 104.0),
            ],
            start=datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc),
        )
        ctx = BarContext(
            df=candles,
            current_time=datetime(2025, 1, 2, 6, 20, tzinfo=timezone.utc),
            symbol="EURUSD",
        )
        sig = strat.on_bar(ctx)
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)


if __name__ == "__main__":
    unittest.main()
