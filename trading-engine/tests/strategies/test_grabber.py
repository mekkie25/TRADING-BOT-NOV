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
from strategies.grabber import GrabberStrategy, evaluate


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


class GrabberStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    def test_standard_grabber_bullish_sweep_low_and_eq_hold(self):
        # Asia low = 90.0, EQ = 95.0, ACS = 2.0
        # Candle 0: sweeps below Asia low (89.0) and closes back inside (91.0)
        # Candle 1: tests EQ (open 91.0, low 91.0, high 95.8, close 95.5)
        # Candle 2: holds EQ as support (open 95.5, high 96.5, low 94.8, close 96.0)
        rows = [
            (91.0, 92.0, 89.0, 91.0),   # sweep Asia low (89.0 < 90.0) & close inside (91.0 > 90.0)
            (91.0, 95.8, 91.0, 95.5),   # rise to EQ (touches 95.0, close above)
            (95.5, 96.5, 94.8, 96.0),   # EQ holds as support
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, equilibrium=95.0)

        signal = evaluate(candles, facts, self.spec, variant="standard")

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.strategy_name, "grabber")
        self.assertEqual(signal.variant, "standard")
        self.assertEqual(signal.session, "London")
        # Structural target should point toward Asia High
        self.assertEqual(signal.structural_target_price, 100.0)
        # Sweep extreme is lowest low across sweep window
        self.assertEqual(signal.structural_stop_price, 89.0)

    def test_standard_grabber_bearish_sweep_high_and_eq_hold(self):
        # Asia high = 100.0, EQ = 95.0, ACS = 2.0
        # Candle 0: sweeps above Asia high (101.5) and closes back inside (99.0)
        # Candle 1: drops to EQ (open 99.0, high 99.0, low 94.0, close 94.5)
        # Candle 2: holds EQ as resistance (open 94.5, high 95.2, low 93.8, close 94.0)
        rows = [
            (99.0, 101.5, 98.5, 99.0),   # sweep Asia high (101.5 > 100.0) & close inside (99.0 < 100.0)
            (99.0, 99.0, 94.0, 94.5),    # drop to EQ
            (94.5, 95.2, 93.8, 94.0),    # EQ holds as resistance
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, equilibrium=95.0)

        signal = evaluate(candles, facts, self.spec, variant="standard")

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)
        self.assertEqual(signal.strategy_name, "grabber")
        self.assertEqual(signal.variant, "standard")
        self.assertEqual(signal.structural_target_price, 90.0)  # Asia Low
        self.assertEqual(signal.structural_stop_price, 101.5)  # Sweep high

    def test_reverse_kick_short_after_asia_low_sweep_and_eq_rejection(self):
        # Asia low = 90.0, EQ = 95.0. Sweep low, rally to EQ, but rejects under EQ -> Short!
        rows = [
            (91.0, 92.0, 89.0, 91.0),   # sweep low & reclaim
            (91.0, 95.2, 91.0, 94.8),   # rally to EQ, tested EQ
            (94.8, 95.3, 93.5, 94.0),   # rejects under EQ: close < 95.0
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, equilibrium=95.0)

        signal = evaluate(candles, facts, self.spec, variant="reverse_kick")

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)
        self.assertEqual(signal.variant, "reverse_kick")
        self.assertEqual(signal.structural_target_price, 90.0)  # Asia Low target

    def test_reverse_kick_long_after_asia_high_sweep_and_eq_rejection(self):
        # Asia high = 100.0, EQ = 95.0. Sweep high, drop to EQ, rejects above EQ -> Long!
        rows = [
            (99.0, 101.5, 98.5, 99.0),   # sweep high & reclaim
            (99.0, 99.0, 94.8, 95.2),    # drop to EQ
            (95.2, 96.5, 94.7, 95.8),    # rejects above EQ: close > 95.0
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, equilibrium=95.0)

        signal = evaluate(candles, facts, self.spec, variant="reverse_kick")

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.variant, "reverse_kick")
        self.assertEqual(signal.structural_target_price, 100.0)  # Asia High target

    def test_eq_confirmation_variant(self):
        # EQ confirmation waits for candle closing away from EQ in trade direction
        rows = [
            (91.0, 92.0, 89.0, 91.0),   # sweep Asia low
            (91.0, 95.5, 91.0, 95.2),   # reach EQ
            (95.2, 97.0, 95.1, 96.8),   # strong bullish confirmation closing away from EQ
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(asia_high=100.0, asia_low=90.0, equilibrium=95.0)

        signal = evaluate(candles, facts, self.spec, variant="eq_confirmation")

        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.variant, "eq_confirmation")

    def test_tunable_stop_and_target_parameters(self):
        rows = [
            (91.0, 92.0, 89.0, 91.0),
            (91.0, 95.8, 91.0, 95.5),
            (95.5, 96.5, 94.8, 96.0),
        ]
        candles = make_test_candles(rows)
        facts = make_test_facts(acs=2.0)

        # 1. Volatility-scaled mode
        signal_vol = evaluate(
            candles, facts, self.spec,
            parameters={"sl_mode": "volatility_scaled", "sl_multiple": 2.0, "tp_mode": "volatility_scaled", "tp_multiple": 4.0},
        )
        self.assertIsNotNone(signal_vol)
        self.assertAlmostEqual(signal_vol.stop_distance, 4.0)   # 2.0 * 2.0
        self.assertAlmostEqual(signal_vol.target_distance, 8.0) # 4.0 * 2.0

        # 2. Fixed mode (points for US30)
        signal_fixed = evaluate(
            candles, facts, self.spec,
            parameters={"sl_mode": "fixed", "fixed_stop": 35.0, "tp_mode": "fixed", "fixed_target": 70.0},
        )
        self.assertIsNotNone(signal_fixed)
        self.assertEqual(signal_fixed.stop_distance, 35.0)
        self.assertEqual(signal_fixed.target_distance, 70.0)

        # 3. Structural mode
        signal_struct = evaluate(
            candles, facts, self.spec,
            parameters={"sl_mode": "structural", "tp_mode": "structural", "structural_buffer_acs": 0.5},
        )
        self.assertIsNotNone(signal_struct)
        # Structural stop: sweep low 89.0 minus buffer (0.5 * 2.0 = 1.0) -> 88.0
        self.assertAlmostEqual(signal_struct.structural_stop_price, 88.0)
        self.assertEqual(signal_struct.structural_target_price, 100.0)

    def test_kill_and_skip_rules(self):
        facts = make_test_facts()

        # 1. Off-session skip
        off_session_facts = make_test_facts(session_name="Off Session")
        candles = make_test_candles([
            (91.0, 92.0, 89.0, 91.0),
            (91.0, 95.8, 91.0, 95.5),
            (95.5, 96.5, 94.8, 96.0),
        ])
        self.assertIsNone(evaluate(candles, off_session_facts, self.spec))

        # 2. Candle keeps closing outside Asia range (no reclaim)
        candles_no_reclaim = make_test_candles([
            (90.0, 90.0, 88.0, 89.5),   # closed below 90.0, never reclaimed
            (89.5, 90.0, 88.0, 88.5),
            (88.5, 89.0, 87.5, 88.0),
        ])
        self.assertIsNone(evaluate(candles_no_reclaim, facts, self.spec))

        # 3. Sweep reclaimed, but later candle breaks back below Asia low (kill rule)
        candles_killed = make_test_candles([
            (91.0, 92.0, 89.0, 91.0),   # sweep & reclaim
            (91.0, 95.5, 91.0, 95.5),   # rally
            (95.5, 95.5, 88.0, 89.0),   # dumped back below Asia low -> killed
        ])
        self.assertIsNone(evaluate(candles_killed, facts, self.spec))

        # 4. Missing Asia levels or EQ
        incomplete_facts = MarketFacts(
            current_time=facts.current_time,
            timeframe="M5",
            session=facts.session,
            average_candle_size=2.0,
            asia=AsiaLevelsReport(
                observed_at_utc=facts.current_time,
                session_date="2025-01-02",
                high=None,
                low=None,
                candle_count=0,
                level_mode="wick",
                session_complete=False,
                summary="unavailable",
            ),
            previous_day=facts.previous_day,
            daily_flip=facts.daily_flip,
            ema_200=facts.ema_200,
            volume_profile=facts.volume_profile,
        )
        self.assertIsNone(evaluate(candles, incomplete_facts, self.spec))

    def test_grabber_strategy_on_bar(self):
        # Create enough closed candles to allow build_market_facts to populate
        # Asia session runs 01:00 to 06:00 SAST (23:00 to 04:00 UTC)
        base_time = datetime(2025, 1, 1, 22, 0, tzinfo=timezone.utc)
        # Create candles covering Asia session plus London open
        data = []
        for i in range(120): # 10 hours of 5M candles -> up to 08:00 UTC (10:00 SAST)
            t = base_time + timedelta(minutes=5 * i)
            # Normal range around 100
            data.append({"time": t, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0})

        # Add sweep and EQ hold candles at the end
        last_time = base_time + timedelta(minutes=5 * 120)
        data.append({"time": last_time, "open": 99.0, "high": 99.5, "low": 97.0, "close": 99.2})
        data.append({"time": last_time + timedelta(minutes=5), "open": 99.2, "high": 100.2, "low": 99.1, "close": 100.1})
        df = pd.DataFrame(data)

        strategy = GrabberStrategy(timeframe="M5", symbols=["US30"])
        self.assertEqual(strategy.name, "grabber")
        self.assertEqual(strategy.timeframe, "M5")
        self.assertIn("US30", strategy.symbols)

        ctx = BarContext(
            df=df,
            current_time=last_time + timedelta(minutes=10),
            symbol="US30",
        )
        # on_bar can be called causally
        sig = strategy.on_bar(ctx)
        # Even if market facts don't match specific sweep pattern, on_bar should execute without error
        self.assertTrue(sig is None or isinstance(sig, Signal))


if __name__ == "__main__":
    unittest.main()
