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
from strategies.asia_breakout import AsiaBreakoutStrategy, evaluate


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
    asia_high=100.0,
    asia_low=90.0,
    equilibrium=95.0,
    session_name="London",
    acs=2.0,
    current_time=None,
    session_complete=True,
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
            session_complete=session_complete,
            summary="Asia complete",
        ),
        previous_day=PreviousDayFacts(
            high=105.0,
            low=85.0,
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


class AsiaBreakoutStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    def test_bullish_breakout_with_volume(self):
        # Asia high = 100.0, Asia low = 90.0, ACS = 2.0
        # Candle 0: inside range (close 97.5 <= 100.0)
        # Candle 1: closes above 100.0 with volume (range = 4.5 >= 1.5*2.0=3.0, body = 4.0 >= 0.6*4.5=2.7)
        rows = [
            (95.0, 96.0, 94.0, 95.0),
            (97.0, 98.0, 96.5, 97.5),
            (98.0, 102.5, 98.0, 102.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, acs=2.0)

        signal = evaluate(candles, facts, self.spec, variant="close_and_volume")

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.strategy_name, "asia_breakout")
        self.assertEqual(signal.variant, "close_and_volume")
        self.assertEqual(signal.structural_target_price, 107.0)  # Default target is R1
        self.assertEqual(signal.structural_stop_price, 98.0)    # Low of breakout candle

    def test_bearish_breakout_with_volume(self):
        # Candle 0: inside range (close 92.5 >= 90.0)
        # Candle 1: closes below 90.0 with volume (range = 4.5, body = 4.0)
        rows = [
            (95.0, 96.0, 94.0, 95.0),
            (93.0, 94.0, 92.0, 92.5),
            (91.5, 91.5, 87.0, 87.5),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, acs=2.0)

        signal = evaluate(candles, facts, self.spec, variant="close_and_volume")

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)
        self.assertEqual(signal.strategy_name, "asia_breakout")
        self.assertEqual(signal.variant, "close_and_volume")
        self.assertEqual(signal.structural_target_price, 87.0)  # Default target is S1
        self.assertEqual(signal.structural_stop_price, 91.5)    # High of breakout candle

    def test_oi_oi_bullish_variant(self):
        # Outside (candle 0 > 100), Inside (candle 1 <= 100), Outside again (candle 2 > 100)
        rows = [
            (99.0, 101.5, 98.5, 101.0),   # Outside 1 (> 100.0)
            (101.0, 101.0, 98.5, 99.5),   # Inside 2 (<= 100.0)
            (99.5, 103.5, 99.0, 103.0),   # Outside 3 (> 100.0 with volume: range 4.5, body 3.5)
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, acs=2.0)

        signal = evaluate(candles, facts, self.spec, variant="oi_oi")

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.variant, "oi_oi")
        self.assertEqual(signal.structural_target_price, 107.0)

    def test_oi_oi_bearish_variant(self):
        # Outside (candle 0 < 90), Inside (candle 1 >= 90), Outside again (candle 2 < 90)
        rows = [
            (91.0, 91.5, 88.5, 89.0),   # Outside 1 (< 90.0)
            (89.0, 91.0, 89.0, 90.5),   # Inside 2 (>= 90.0)
            (90.5, 91.0, 86.5, 87.0),   # Outside 3 (< 90.0 with volume: range 4.5, body 3.5)
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, acs=2.0)

        signal = evaluate(candles, facts, self.spec, variant="oi_oi")

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)
        self.assertEqual(signal.variant, "oi_oi")
        self.assertEqual(signal.structural_target_price, 87.0)

    def test_retest_continuation_variant(self):
        # Candle 0: breaks above Asia high (close 102.0 > 100.0)
        # Candle 1: pulls back to retest (low 99.8, close 101.5 > 100.0) and holds as support
        rows = [
            (97.0, 98.0, 96.5, 97.5),
            (98.0, 102.5, 98.0, 102.0),
            (102.0, 102.0, 99.8, 101.5),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, acs=2.0)

        signal = evaluate(candles, facts, self.spec, variant="retest", parameters={"require_volume": False})

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.variant, "retest")
        self.assertEqual(signal.structural_target_price, 107.0)

    def test_volume_filter_rejection(self):
        # Candle breaks out but has weak range (2.2 < 1.5 * 2.0 = 3.0)
        rows = [
            (95.0, 96.0, 94.0, 95.0),
            (97.0, 98.0, 96.5, 97.5),
            (98.0, 100.5, 98.0, 100.2), # small range 2.5
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, acs=2.0)

        # Rejected with require_volume=True
        sig_vol = evaluate(candles, facts, self.spec, parameters={"require_volume": True})
        self.assertIsNone(sig_vol)

        # Accepted with require_volume=False
        sig_no_vol = evaluate(candles, facts, self.spec, parameters={"require_volume": False})
        self.assertIsNotNone(sig_no_vol)

    def test_target_choice_parameters(self):
        rows = [
            (95.0, 96.0, 94.0, 95.0),
            (97.0, 98.0, 96.5, 97.5),
            (98.0, 102.5, 98.0, 102.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, acs=2.0)

        # 1. Target R2
        sig_r2 = evaluate(candles, facts, self.spec, parameters={"target_choice": "pivot_r2"})
        self.assertIsNotNone(sig_r2)
        self.assertEqual(sig_r2.structural_target_price, 116.0)

        # 2. Target previous day high (105.0)
        sig_pdh = evaluate(candles, facts, self.spec, parameters={"target_choice": "previous_day"})
        self.assertIsNotNone(sig_pdh)
        self.assertEqual(sig_pdh.structural_target_price, 105.0)

    def test_gold_instrument_specs_and_tunable_stops(self):
        spec_gold = get_instrument_spec("XAUUSD")
        self.assertEqual(spec_gold.pip_size, 0.10)
        rows = [
            (2635.0, 2638.0, 2634.0, 2637.0),
            (2637.0, 2640.0, 2636.0, 2639.0),
            (2639.0, 2652.0, 2639.0, 2650.0), # breakout with volume
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(
            asia_high=2640.0,
            asia_low=2620.0,
            acs=5.0,
        )

        # Fixed mode on Gold defaults to 50 pips (5.00 in price)
        sig_fixed = evaluate(
            candles, facts, spec_gold,
            parameters={"sl_mode": "fixed", "tp_mode": "fixed", "fixed_stop": 50.0, "fixed_target": 100.0},
        )
        self.assertIsNotNone(sig_fixed)
        self.assertAlmostEqual(sig_fixed.stop_distance, 5.00)
        self.assertAlmostEqual(sig_fixed.target_distance, 10.00)

        # Volatility-scaled mode on Gold
        sig_vol = evaluate(
            candles, facts, spec_gold,
            parameters={"sl_mode": "volatility_scaled", "sl_multiple": 2.0, "tp_mode": "volatility_scaled", "tp_multiple": 4.0},
        )
        self.assertIsNotNone(sig_vol)
        self.assertAlmostEqual(sig_vol.stop_distance, 10.0)  # 2.0 * 5.0
        self.assertAlmostEqual(sig_vol.target_distance, 20.0) # 4.0 * 5.0

    def test_session_and_pre_trade_filters(self):
        rows = [
            (95.0, 96.0, 94.0, 95.0),
            (97.0, 98.0, 96.5, 97.5),
            (98.0, 102.5, 98.0, 102.0),
        ]
        candles = make_test_candles(rows)

        # 1. Asia session rejects
        facts_asia = make_test_facts(session_name="Asia")
        self.assertIsNone(evaluate(candles, facts_asia, self.spec))

        # 2. Session incomplete rejects
        facts_incomplete = make_test_facts(session_complete=False)
        self.assertIsNone(evaluate(candles, facts_incomplete, self.spec))

    def test_asia_breakout_strategy_on_bar(self):
        base_time = datetime(2025, 1, 1, 22, 0, tzinfo=timezone.utc)
        data = []
        for i in range(120):
            t = base_time + timedelta(minutes=5 * i)
            data.append({"time": t, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0})
        last_time = base_time + timedelta(minutes=5 * 120)
        data.append({"time": last_time, "open": 99.0, "high": 99.5, "low": 97.0, "close": 99.2})
        df = pd.DataFrame(data)

        strategy = AsiaBreakoutStrategy(timeframe="M5", symbols=["US30"])
        self.assertEqual(strategy.name, "asia_breakout")
        self.assertEqual(strategy.timeframe, "M5")

        ctx = BarContext(
            df=df,
            current_time=last_time + timedelta(minutes=10),
            symbol="US30",
        )
        sig = strategy.on_bar(ctx)
        self.assertTrue(sig is None or isinstance(sig, Signal))


if __name__ == "__main__":
    unittest.main()
