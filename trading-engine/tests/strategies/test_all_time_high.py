import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import InstrumentSpec, get_instrument_spec
from engine.models import Direction
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.volume_profile import VolumeProfileReport
from strategies.all_time_high import evaluate
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
    pivots=None,
    acs=2.0,
    current_time=None,
):
    now = current_time or datetime(2025, 1, 2, 8, 30, tzinfo=timezone.utc)
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
            close=100.0,
            equilibrium=95.0,
            pivots=pivots or {"R1": 102.0, "R2": 105.0, "R3": 110.0, "R4": 115.0, "P": 95.0},
        ),
        daily_flip=DailyFlipReport(
            day=now.date(),
            level=98.0,
            source_candle_time=pd.Timestamp(now),
            summary="Daily Flip at 98",
        ),
        ema_200=92.0,
        volume_profile=VolumeProfileReport(
            poc=95.0,
            vah=100.0,
            val=90.0,
            bin_size=0.2,
            value_area_fraction=0.7,
            source="tick_approx",
            approximate=True,
            candle_count=10,
            summary="Profile available",
        ),
    )


class TestAllTimeHighStrategy(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("XAUUSD")

    def test_missing_ath_price_returns_none(self):
        # Even with high candles, missing ath_price in parameters should return None
        candles = make_test_candles(
            [
                [2000.0, 2050.0, 1990.0, 2040.0],
                [2040.0, 2110.0, 2035.0, 2100.0],
            ]
        )
        facts = make_test_facts()
        signal = evaluate(candles, facts, self.spec, parameters={})
        self.assertIsNone(signal)

    def test_breakout_fails_without_daily_r3(self):
        # Candle closes above ATH (2050) but daily_r3 is missing (None in pivots and parameters)
        candles = make_test_candles(
            [
                [2000.0, 2040.0, 1990.0, 2030.0],
                [2030.0, 2080.0, 2025.0, 2070.0],
            ]
        )
        facts = make_test_facts(pivots={"R1": 2010.0, "R2": 2020.0})  # No R3
        params = {"ath_price": 2050.0}
        signal = evaluate(candles, facts, self.spec, parameters=params, variant="breakout")
        self.assertIsNone(signal)

    def test_breakout_fails_when_close_below_daily_r3(self):
        # Candle closes above ATH (2050) at 2060, but below Daily R3 (2070)
        candles = make_test_candles(
            [
                [2000.0, 2040.0, 1990.0, 2030.0],
                [2030.0, 2065.0, 2025.0, 2060.0],
            ]
        )
        facts = make_test_facts(pivots={"R3": 2070.0, "R4": 2100.0})
        params = {"ath_price": 2050.0}
        signal = evaluate(candles, facts, self.spec, parameters=params, variant="breakout")
        self.assertIsNone(signal)

    def test_breakout_success_when_above_ath_and_daily_r3(self):
        # Candle closes above ATH (2050) and Daily R3 (2070) at 2080
        candles = make_test_candles(
            [
                [2000.0, 2040.0, 1990.0, 2030.0],
                [2030.0, 2090.0, 2025.0, 2080.0],
            ]
        )
        facts = make_test_facts(pivots={"R3": 2070.0, "R4": 2100.0}, acs=10.0)
        params = {"ath_price": 2050.0}
        signal = evaluate(candles, facts, self.spec, parameters=params, variant="breakout")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.variant, "breakout")

    def test_retest_success(self):
        # Previous close > ATH (2050), current low <= 2050, current close > 2050
        candles = make_test_candles(
            [
                [2040.0, 2070.0, 2035.0, 2060.0],
                [2060.0, 2065.0, 2048.0, 2055.0],
            ]
        )
        facts = make_test_facts()
        params = {"ath_price": 2050.0}
        signal = evaluate(candles, facts, self.spec, parameters=params, variant="retest")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)


if __name__ == "__main__":
    unittest.main()
