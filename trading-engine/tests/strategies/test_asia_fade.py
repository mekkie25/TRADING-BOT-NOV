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
from strategies.asia_fade import AsiaFadeStrategy, evaluate


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


class AsiaFadeStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    def test_bullish_fade_on_asia_low_sweep_and_reclaim(self):
        # Asia low = 90.0, Asia high = 100.0
        # Candle 0: inside range (92.0)
        # Candle 1: sweeps below Asia low (89.0 < 90.0) and closes back inside (91.0 > 90.0)
        rows = [
            (93.0, 94.0, 92.0, 92.5),
            (92.0, 92.5, 89.0, 91.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, equilibrium=95.0)

        signal = evaluate(candles, facts, self.spec, variant="sweep_reclaim")

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.strategy_name, "asia_fade")
        self.assertEqual(signal.variant, "sweep_reclaim")
        self.assertEqual(signal.structural_stop_price, 89.0)
        self.assertEqual(signal.structural_target_price, 95.0)  # Default target is EQ

    def test_bearish_fade_on_asia_high_sweep_and_reclaim(self):
        # Asia high = 100.0, Asia low = 90.0
        # Candle 0: inside range
        # Candle 1: sweeps above Asia high (101.5 > 100.0) and closes back inside (99.0 < 100.0)
        rows = [
            (97.0, 98.0, 96.5, 97.5),
            (98.0, 101.5, 97.5, 99.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, equilibrium=95.0)

        signal = evaluate(candles, facts, self.spec, variant="sweep_reclaim")

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)
        self.assertEqual(signal.strategy_name, "asia_fade")
        self.assertEqual(signal.structural_stop_price, 101.5)
        self.assertEqual(signal.structural_target_price, 95.0)  # Default target is EQ

    def test_second_candle_confirmation_variant(self):
        # Candle 0: normal
        # Candle 1: sweeps Asia low and reclaims (89.0 low, 91.0 close)
        # Candle 2: confirms with higher close (close 92.5 > 91.0)
        rows = [
            (93.0, 94.0, 92.0, 92.5),
            (92.0, 92.5, 89.0, 91.0),
            (91.0, 93.0, 90.8, 92.5),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0)

        signal = evaluate(candles, facts, self.spec, variant="second_candle_confirmation")

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.variant, "second_candle_confirmation")

    def test_target_choice_parameters(self):
        rows = [
            (93.0, 94.0, 92.0, 92.5),
            (92.0, 92.5, 89.0, 91.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, equilibrium=95.0)

        # 1. Target opposite extreme
        sig_opp = evaluate(candles, facts, self.spec, parameters={"target_choice": "opposite_extreme"})
        self.assertIsNotNone(sig_opp)
        self.assertEqual(sig_opp.structural_target_price, 100.0)  # Asia High

        # 2. Target pivot
        sig_piv = evaluate(candles, facts, self.spec, parameters={"target_choice": "pivot"})
        self.assertIsNotNone(sig_piv)
        self.assertEqual(sig_piv.structural_target_price, 96.0)  # Pivot P

    def test_solid_body_filter(self):
        # Candle 1 has very small body (doji): open 90.9, close 91.0, range 89.0 to 92.5 (range = 3.5, body = 0.1)
        doji_rows = [
            (93.0, 94.0, 92.0, 92.5),
            (90.9, 92.5, 89.0, 91.0),
        ]
        candles = make_test_candles(doji_rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0)

        sig_filtered = evaluate(candles, facts, self.spec, parameters={"require_solid_body": True, "minimum_body_fraction": 0.5})
        self.assertIsNone(sig_filtered)

        # Candle 1 with solid body: open 89.2, close 91.8, range 89.0 to 92.0 (range = 3.0, body = 2.6)
        solid_rows = [
            (93.0, 94.0, 92.0, 92.5),
            (89.2, 92.0, 89.0, 91.8),
        ]
        sig_solid = evaluate(make_test_candles(solid_rows), facts, self.spec, parameters={"require_solid_body": True, "minimum_body_fraction": 0.5})
        self.assertIsNotNone(sig_solid)

    def test_skip_when_both_extremes_taken(self):
        # A day where price already swept above Asia high (101.0) and below Asia low (89.0), and is now in the middle (95.0)
        rows = [
            (95.0, 101.5, 95.0, 98.0),  # high taken
            (98.0, 98.0, 88.5, 91.0),   # low taken
            (91.0, 95.5, 91.0, 95.0),   # sitting in the middle
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0)

        signal = evaluate(candles, facts, self.spec, parameters={"skip_if_both_extremes_taken": True})
        self.assertIsNone(signal)

    def test_off_session_skip(self):
        rows = [
            (93.0, 94.0, 92.0, 92.5),
            (92.0, 92.5, 89.0, 91.0),
        ]
        candles = make_test_candles(rows)
        off_facts = make_test_facts(session_name="Off Session")
        self.assertIsNone(evaluate(candles, off_facts, self.spec))

    def test_tunable_sl_tp_modes(self):
        rows = [
            (93.0, 94.0, 92.0, 92.5),
            (92.0, 92.5, 89.0, 91.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(acs=2.0)

        # Volatility-scaled
        sig_vol = evaluate(candles, facts, self.spec, parameters={"sl_mode": "volatility_scaled", "sl_multiple": 1.5, "tp_mode": "volatility_scaled", "tp_multiple": 3.0})
        self.assertIsNotNone(sig_vol)
        self.assertAlmostEqual(sig_vol.stop_distance, 3.0)
        self.assertAlmostEqual(sig_vol.target_distance, 6.0)

        # Fixed mode
        sig_fix = evaluate(candles, facts, self.spec, parameters={"sl_mode": "fixed", "fixed_stop": 30.0, "tp_mode": "fixed", "fixed_target": 60.0})
        self.assertIsNotNone(sig_fix)
        self.assertEqual(sig_fix.stop_distance, 30.0)
        self.assertEqual(sig_fix.target_distance, 60.0)

    def test_asia_fade_strategy_on_bar(self):
        base_time = datetime(2025, 1, 1, 22, 0, tzinfo=timezone.utc)
        data = []
        for i in range(120):
            t = base_time + timedelta(minutes=5 * i)
            data.append({"time": t, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0})
        last_time = base_time + timedelta(minutes=5 * 120)
        data.append({"time": last_time, "open": 99.0, "high": 99.5, "low": 97.0, "close": 99.2})
        df = pd.DataFrame(data)

        strategy = AsiaFadeStrategy(timeframe="M5", symbols=["US30"])
        self.assertEqual(strategy.name, "asia_fade")
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
