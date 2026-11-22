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
from strategies.vwap import VwapStrategy, evaluate


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
                "volume": float(row[4]) if len(row) > 4 else 100.0,
            }
            for index, row in enumerate(rows)
        ]
    )


def make_test_facts(
    pivots=None,
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
            high=105.0,
            low=95.0,
            candle_count=12,
            level_mode="wick",
            session_complete=True,
            summary="Asia complete",
        ),
        previous_day=PreviousDayFacts(
            high=110.0,
            low=90.0,
            close=100.0,
            equilibrium=100.0,
            pivots=pivots or {"P": 100.0, "R1": 110.0, "S1": 90.0, "R2": 120.0, "S2": 80.0},
        ),
        daily_flip=DailyFlipReport(
            day=now.date(),
            level=99.0,
            source_candle_time=pd.Timestamp(now),
            summary="Daily Flip at 99",
        ),
        ema_200=98.0,
        volume_profile=VolumeProfileReport(
            poc=100.0,
            vah=104.0,
            val=96.0,
            bin_size=0.5,
            value_area_fraction=0.7,
            source="tick_approx",
            approximate=True,
            candle_count=10,
            summary="Profile available",
        ),
    )


class TestVwapStrategy(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    def test_break_and_retest_bullish(self):
        # Equal volume = 100 on each bar.
        # Candle 0: HLC avg ~ 100
        # Candle 1: closes above VWAP (102.0 > VWAP ~ 100.5)
        # Candle 2: retests VWAP (low 100.0 <= VWAP), closes above VWAP (102.5 > VWAP)
        rows = [
            (99.0, 101.0, 99.0, 100.0, 100.0),
            (100.0, 102.5, 99.8, 102.0, 100.0),
            (102.0, 103.0, 100.0, 102.5, 100.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts()

        sig = evaluate(candles, facts, self.spec, variant="break_and_retest")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)
        self.assertEqual(sig.strategy_name, "vwap")
        self.assertEqual(sig.variant, "break_and_retest")
        self.assertEqual(sig.structural_stop_price, 100.0)
        self.assertEqual(sig.structural_target_price, 110.0)  # R1

    def test_break_and_retest_bearish(self):
        # Candle 0: HLC avg ~ 100
        # Candle 1: closes below VWAP (98.0 < VWAP ~ 99.5)
        # Candle 2: retests VWAP (high 100.0 >= VWAP), closes below VWAP (97.5 < VWAP)
        rows = [
            (101.0, 101.0, 99.0, 100.0, 100.0),
            (100.0, 100.2, 97.5, 98.0, 100.0),
            (98.0, 100.0, 97.0, 97.5, 100.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts()

        sig = evaluate(candles, facts, self.spec, variant="break_and_retest")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.SELL)
        self.assertEqual(sig.structural_stop_price, 100.0)
        self.assertEqual(sig.structural_target_price, 90.0)  # S1

    def test_mean_reversion_bullish_toward_vwap(self):
        # Price below VWAP (~100), candle 2 dips to 95.0, closes bullish at 98.0 (< VWAP)
        rows = [
            (99.0, 101.0, 99.0, 100.0, 100.0),
            (99.0, 99.0, 96.0, 96.5, 100.0),
            (96.5, 98.5, 95.0, 98.0, 100.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts()

        sig = evaluate(candles, facts, self.spec, variant="mean_reversion")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.BUY)
        self.assertEqual(sig.variant, "mean_reversion")
        self.assertEqual(sig.structural_stop_price, 95.0)
        # Structural target is VWAP itself
        self.assertGreater(sig.structural_target_price, 98.0)

    def test_mean_reversion_bearish_toward_vwap(self):
        # Price above VWAP (~100), candle 2 spikes to 105.0, closes bearish at 102.0 (> VWAP)
        rows = [
            (99.0, 101.0, 99.0, 100.0, 100.0),
            (101.0, 104.0, 100.5, 103.5, 100.0),
            (103.5, 105.0, 101.5, 102.0, 100.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts()

        sig = evaluate(candles, facts, self.spec, variant="mean_reversion")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, Direction.SELL)
        self.assertEqual(sig.structural_stop_price, 105.0)
        self.assertLess(sig.structural_target_price, 102.0)

    def test_missing_volume_column_returns_none(self):
        candles = pd.DataFrame(
            [
                {"time": datetime(2025, 1, 2, 8, 0, tzinfo=timezone.utc), "open": 100, "high": 101, "low": 99, "close": 100},
                {"time": datetime(2025, 1, 2, 8, 5, tzinfo=timezone.utc), "open": 100, "high": 101, "low": 99, "close": 100},
                {"time": datetime(2025, 1, 2, 8, 10, tzinfo=timezone.utc), "open": 100, "high": 101, "low": 99, "close": 100},
            ]
        )
        facts = make_test_facts()
        sig = evaluate(candles, facts, self.spec)
        self.assertIsNone(sig)

    def test_zero_volume_returns_none(self):
        rows = [
            (99.0, 101.0, 99.0, 100.0, 0.0),
            (100.0, 102.5, 99.8, 102.0, 0.0),
            (102.0, 103.0, 100.0, 102.5, 0.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts()
        sig = evaluate(candles, facts, self.spec)
        self.assertIsNone(sig)

    def test_fewer_than_three_candles_returns_none(self):
        rows = [
            (99.0, 101.0, 99.0, 100.0, 100.0),
            (100.0, 102.5, 99.8, 102.0, 100.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts()
        sig = evaluate(candles, facts, self.spec)
        self.assertIsNone(sig)

    def test_invalid_anchor_index_raises(self):
        rows = [
            (99.0, 101.0, 99.0, 100.0, 100.0),
            (100.0, 102.5, 99.8, 102.0, 100.0),
            (102.0, 103.0, 100.0, 102.5, 100.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts()
        with self.assertRaises(ValueError):
            evaluate(candles, facts, self.spec, parameters={"anchor_index": -1})
        with self.assertRaises(ValueError):
            evaluate(candles, facts, self.spec, parameters={"anchor_index": 10})

    def test_tunable_stop_and_target_parameters(self):
        rows = [
            (99.0, 101.0, 99.0, 100.0, 100.0),
            (100.0, 102.5, 99.8, 102.0, 100.0),
            (102.0, 103.0, 100.0, 102.5, 100.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(acs=2.0)

        # Fixed mode
        sig_fixed = evaluate(
            candles, facts, self.spec,
            parameters={"sl_mode": "fixed", "fixed_stop": 50.0, "tp_mode": "fixed", "fixed_target": 100.0},
        )
        self.assertIsNotNone(sig_fixed)
        self.assertEqual(sig_fixed.stop_distance, 50.0)
        self.assertEqual(sig_fixed.target_distance, 100.0)

        # Volatility-scaled mode
        sig_vol = evaluate(
            candles, facts, self.spec,
            parameters={"sl_mode": "volatility_scaled", "sl_multiple": 1.5, "tp_mode": "volatility_scaled", "tp_multiple": 3.0},
        )
        self.assertIsNotNone(sig_vol)
        self.assertAlmostEqual(sig_vol.stop_distance, 3.0)   # 1.5 * 2.0
        self.assertAlmostEqual(sig_vol.target_distance, 6.0) # 3.0 * 2.0

    def test_vwap_strategy_class_on_bar(self):
        base_time = datetime(2025, 1, 1, 22, 0, tzinfo=timezone.utc)
        data = []
        for i in range(120):
            t = base_time + timedelta(minutes=5 * i)
            data.append({"time": t, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 100.0})
        df = pd.DataFrame(data)

        strategy = VwapStrategy(timeframe="M5", symbols=["US30"])
        self.assertEqual(strategy.name, "vwap")
        self.assertEqual(strategy.timeframe, "M5")
        self.assertIn("US30", strategy.symbols)

        ctx = BarContext(
            df=df,
            current_time=base_time + timedelta(minutes=5 * 120),
            symbol="US30",
        )
        sig = strategy.on_bar(ctx)
        self.assertTrue(sig is None or isinstance(sig, Signal))


if __name__ == "__main__":
    unittest.main()