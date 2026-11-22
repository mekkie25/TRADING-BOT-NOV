import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import get_instrument_spec
from engine.models import Direction
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.volume_profile import VolumeProfileReport
from strategies.context import MarketFacts, PreviousDayFacts, StrategySession

START = datetime(2025, 1, 2, 9, 0, tzinfo=timezone.utc)


def make_test_candles(rows, start=START, step=timedelta(minutes=5)):
    return pd.DataFrame(
        [
            {
                "time": start + index * step,
                "open": float(row[0]),
                "high": float(row[1]),
                "low": float(row[2]),
                "close": float(row[3]),
                "volume": 100,
            }
            for index, row in enumerate(rows)
        ]
    )


def make_test_facts(candle_count, acs=1.0, ema_200=91.0):
    now = START + timedelta(minutes=5 * candle_count)
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
            close=98.0,
            equilibrium=95.0,
            pivots={"P": 95.0, "R1": 110.0, "S1": 80.0},
        ),
        daily_flip=DailyFlipReport(
            day=now.date(),
            level=92.0,
            source_candle_time=pd.Timestamp(now),
            summary="Daily Flip at 92",
        ),
        ema_200=ema_200,
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


# 14 quiet candles first (the gap size filter needs about 14 candles of history).
FILLER = [(100.0, 100.6, 99.5, 100.2)] * 14

# Sell setup: price sweeps the Asia low (99.0), displaces up leaving a bullish gap
# (100.0 to 101.5), then closes back through it and retests it from below.
SELL_SETUP = [
    (99.8, 100.0, 98.5, 98.8),    # sweeps the Asia low, high 100.0 is the gap bottom
    (98.8, 102.5, 98.7, 102.3),   # displacement up
    (102.3, 103.5, 101.5, 103.0), # gap forms: low 101.5 is the gap top
    (103.0, 103.1, 99.0, 99.4),   # closes below the gap bottom: inverted
    (99.4, 99.8, 98.8, 99.2),     # drifts, no retest yet
]
SELL_TAP = (99.3, 100.6, 99.0, 99.6)  # taps the zone, closes back below it

# Buy setup: mirror image around the Asia high (101.0).
BUY_SETUP = [
    (100.2, 101.5, 100.0, 101.2),  # sweeps the Asia high, low 100.0 is the gap top
    (101.2, 101.3, 97.5, 97.7),    # displacement down
    (97.7, 98.5, 96.5, 97.0),      # gap forms: high 98.5 is the gap bottom
    (97.0, 100.9, 96.9, 100.6),    # closes above the gap top: inverted
    (100.6, 101.2, 100.2, 100.8),  # drifts, no retest yet
]
BUY_TAP = (100.7, 101.0, 99.4, 100.4)  # taps the zone, closes back above it


class IfvgStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("XAUUSD")

    def run_ifvg(self, rows, parameters=None, asia_low=99.0, asia_high=101.0, equilibrium=95.0):
        from strategies.ifvg import evaluate

        candles = make_test_candles(rows)
        facts = make_test_facts(len(candles))
        facts = replace(
            facts,
            asia=replace(facts.asia, low=asia_low, high=asia_high),
            previous_day=PreviousDayFacts(
                high=120.0, low=80.0, close=100.0, equilibrium=equilibrium,
                pivots={"P": 100.0, "R1": 110.0, "S1": 90.0},
            ),
        )
        return evaluate(candles, facts, self.spec, parameters)

    def test_retest_of_inverted_bullish_gap_is_a_sell(self):
        signal = self.run_ifvg(FILLER + SELL_SETUP + [SELL_TAP])
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)
        self.assertEqual(signal.variant, "ifvg_retest")
        # Stop above the zone top 101.5 plus the 0.25 buffer. Risk 1.9, so 1:2
        # target is 99.6 - 3.8.
        self.assertAlmostEqual(signal.structural_stop_price, 101.75)
        self.assertAlmostEqual(signal.structural_target_price, 95.8)

    def test_retest_of_inverted_bearish_gap_is_a_buy(self):
        signal = self.run_ifvg(FILLER + BUY_SETUP + [BUY_TAP])
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertAlmostEqual(signal.structural_stop_price, 98.25)
        self.assertAlmostEqual(signal.structural_target_price, 104.2)

    def test_no_trade_if_no_session_level_was_swept(self):
        self.assertIsNone(
            self.run_ifvg(FILLER + SELL_SETUP + [SELL_TAP], asia_low=90.0)
        )

    def test_sweep_requirement_can_be_switched_off(self):
        signal = self.run_ifvg(
            FILLER + SELL_SETUP + [SELL_TAP],
            {"require_sweep": False},
            asia_low=90.0,
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)

    def test_no_trade_before_price_taps_the_zone(self):
        self.assertIsNone(self.run_ifvg(FILLER + SELL_SETUP))

    def test_no_trade_if_the_tap_candle_closes_inside_the_zone(self):
        inside = (99.3, 100.8, 99.0, 100.5)
        self.assertIsNone(self.run_ifvg(FILLER + SELL_SETUP + [inside]))

    def test_no_trade_after_the_inverted_gap_already_failed(self):
        # The zone fails first (a candle closes above its top 101.5). A later tap
        # that closes back below the zone must not be traded.
        failure = (99.4, 102.0, 99.3, 101.8)
        late_tap = (101.6, 101.7, 99.2, 99.5)
        self.assertIsNone(self.run_ifvg(FILLER + SELL_SETUP + [failure, late_tap]))

    def test_no_trade_if_price_closes_through_the_zone(self):
        # Closes above the zone top 101.5, so the inverted gap has failed.
        through = (99.3, 101.8, 99.0, 101.6)
        self.assertIsNone(self.run_ifvg(FILLER + SELL_SETUP + [through]))

    def test_needs_session_levels_to_check_the_sweep(self):
        from strategies.ifvg import evaluate

        candles = make_test_candles(FILLER + SELL_SETUP + [SELL_TAP])
        facts = make_test_facts(len(candles))
        facts = replace(
            facts,
            asia=replace(facts.asia, low=None, high=None),
            previous_day=PreviousDayFacts(None, None, None, None, {}),
        )
        self.assertIsNone(evaluate(candles, facts, self.spec))

    def test_target_can_be_previous_day_equilibrium(self):
        signal = self.run_ifvg(
            FILLER + SELL_SETUP + [SELL_TAP], {"target_choice": "eq"}, equilibrium=95.0
        )
        self.assertAlmostEqual(signal.structural_target_price, 95.0)

    def test_target_can_be_the_opposite_asia_extreme(self):
        signal = self.run_ifvg(
            FILLER + SELL_SETUP + [SELL_TAP], {"target_choice": "asia_extreme"}
        )
        self.assertAlmostEqual(signal.structural_target_price, 99.0)

    def test_reward_to_risk_is_a_setting(self):
        signal = self.run_ifvg(
            FILLER + SELL_SETUP + [SELL_TAP], {"rr_multiple": 3.0}
        )
        self.assertAlmostEqual(signal.structural_target_price, 99.6 - 3 * 1.9)

    def test_volatility_scaled_exits_stay_selectable(self):
        signal = self.run_ifvg(
            FILLER + SELL_SETUP + [SELL_TAP],
            {"sl_mode": "volatility_scaled", "tp_mode": "volatility_scaled"},
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.sl_mode, "volatility_scaled")
        self.assertAlmostEqual(signal.stop_distance, 1.5)

    def test_bad_settings_are_rejected(self):
        for bad in (
            {"target_choice": "moon"},
            {"rr_multiple": 0},
            {"rr_multiple": -1.0},
            {"sweep_lookback": -1},
        ):
            with self.assertRaises(ValueError, msg=str(bad)):
                self.run_ifvg(FILLER + SELL_SETUP + [SELL_TAP], bad)

    def test_too_little_history_gives_no_trade_and_no_error(self):
        self.assertIsNone(self.run_ifvg(SELL_SETUP + [SELL_TAP]))
        self.assertIsNone(self.run_ifvg(SELL_SETUP[:2]))


if __name__ == "__main__":
    unittest.main()