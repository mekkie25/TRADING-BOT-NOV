import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import get_instrument_spec
from engine.models import Direction
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.volume_profile import VolumeProfileReport
from strategies.context import MarketFacts, PreviousDayFacts, StrategySession
from strategies.cracker import evaluate

# New York open 15:30 SAST = 13:30 UTC (January). 2025-01-02 is a Thursday.
NY_OPEN = datetime(2025, 1, 2, 13, 30, tzinfo=timezone.utc)
NY_OPEN_FRIDAY = datetime(2025, 1, 3, 13, 30, tzinfo=timezone.utc)


def make_candles(rows, start):
    return pd.DataFrame(
        [
            {
                "time": start + index * timedelta(minutes=1),
                "open": float(row[0]),
                "high": float(row[1]),
                "low": float(row[2]),
                "close": float(row[3]),
                "volume": 100,
            }
            for index, row in enumerate(rows)
        ]
    )


def make_facts(current_time, asia_low=90.0, equilibrium=95.0, acs=2.0):
    return MarketFacts(
        current_time=current_time,
        timeframe="M1",
        session=StrategySession(
            name="New York",
            observed_at_utc=current_time,
            local_time=current_time,
            is_open_window=True,
        ),
        average_candle_size=acs,
        asia=AsiaLevelsReport(
            observed_at_utc=current_time,
            session_date="2025-01-02",
            high=110.0,
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
            pivots={"R1": 110.0, "S1": 80.0},
        ),
        daily_flip=DailyFlipReport(
            day=current_time.date(),
            level=92.0,
            source_candle_time=pd.Timestamp(current_time),
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


# Buy call with levels 100 and 101. The previous candle closed under 100, the
# current candle touches 100 and closes above it.
BUY_PREVIOUS = (99.6, 99.9, 99.2, 99.5)
BUY_CURRENT = (99.8, 100.6, 99.6, 100.4)
# Sell call with levels 106 and 105. The previous candle closed above 106, the
# current candle touches 106 and closes below it.
SELL_PREVIOUS = (106.4, 106.6, 106.1, 106.3)
SELL_CURRENT = (105.8, 106.2, 105.4, 105.6)

BUY_PARAMS = {"call_direction": "buy", "call_levels": [100.0, 101.0]}
SELL_PARAMS = {"call_direction": "sell", "call_levels": [106.0, 105.0]}


def setup(previous, current, open_time=NY_OPEN, minutes_after_open=2, **facts_kwargs):
    candles = make_candles([previous, current], start=open_time + timedelta(minutes=minutes_after_open - 2))
    facts = make_facts(open_time + timedelta(minutes=minutes_after_open), **facts_kwargs)
    return candles, facts


def with_open(parameters, open_time=NY_OPEN):
    merged = dict(parameters)
    merged["new_york_open_utc"] = pd.Timestamp(open_time)
    return merged


class CrackerStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    # ----- Entry on a confirmed close -----

    def test_buy_call_and_close_through_level_gives_buy(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        signal = evaluate(candles, facts, self.spec, with_open(BUY_PARAMS))
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.strategy_name, "cracker")
        self.assertEqual(signal.variant, "call_based")

    def test_sell_call_and_close_through_level_gives_sell(self):
        candles, facts = setup(SELL_PREVIOUS, SELL_CURRENT)
        signal = evaluate(candles, facts, self.spec, with_open(SELL_PARAMS))
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)

    def test_no_signal_against_the_call(self):
        # A sell-style candle while the call is buy.
        candles, facts = setup(SELL_PREVIOUS, SELL_CURRENT)
        params = {"call_direction": "buy", "call_levels": [106.0, 105.0]}
        self.assertIsNone(evaluate(candles, facts, self.spec, with_open(params)))

    def test_no_signal_when_wick_taps_level_but_close_stays_below(self):
        current = (99.8, 100.6, 99.6, 99.9)
        candles, facts = setup(BUY_PREVIOUS, current)
        self.assertIsNone(evaluate(candles, facts, self.spec, with_open(BUY_PARAMS)))

    def test_no_signal_when_level_is_not_tapped(self):
        current = (101.5, 102.0, 101.2, 101.8)
        candles, facts = setup((101.6, 101.9, 101.3, 101.5), current)
        self.assertIsNone(evaluate(candles, facts, self.spec, with_open(BUY_PARAMS)))

    def test_no_signal_when_previous_candle_already_closed_through_the_level(self):
        previous = (100.2, 100.5, 100.0, 100.3)
        candles, facts = setup(previous, BUY_CURRENT)
        self.assertIsNone(evaluate(candles, facts, self.spec, with_open(BUY_PARAMS)))

    # ----- Call and level inputs -----

    def test_no_signal_without_a_call(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        params = {"call_levels": [100.0, 101.0]}
        self.assertIsNone(evaluate(candles, facts, self.spec, with_open(params)))

    def test_no_signal_with_unknown_call_word(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        params = {"call_direction": "up", "call_levels": [100.0, 101.0]}
        self.assertIsNone(evaluate(candles, facts, self.spec, with_open(params)))

    def test_no_signal_without_exactly_two_levels(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        params = {"call_direction": "buy", "call_levels": [100.0]}
        self.assertIsNone(evaluate(candles, facts, self.spec, with_open(params)))

    def test_non_positive_level_is_rejected(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        params = {"call_direction": "buy", "call_levels": [0.0, 100.0]}
        with self.assertRaises(ValueError):
            evaluate(candles, facts, self.spec, with_open(params))

    def test_no_signal_without_the_new_york_open_time(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        self.assertIsNone(evaluate(candles, facts, self.spec, dict(BUY_PARAMS)))

    def test_open_time_must_be_utc(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        params = dict(BUY_PARAMS)
        params["new_york_open_utc"] = pd.Timestamp("2025-01-02 13:30:00")
        with self.assertRaises(ValueError):
            evaluate(candles, facts, self.spec, params)

    # ----- Cancel rules -----

    def test_no_signal_before_the_open(self):
        candles = make_candles([BUY_PREVIOUS, BUY_CURRENT], start=NY_OPEN - timedelta(minutes=3))
        facts = make_facts(NY_OPEN - timedelta(minutes=1))
        self.assertIsNone(evaluate(candles, facts, self.spec, with_open(BUY_PARAMS)))

    def test_no_signal_after_the_first_five_minutes(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT, minutes_after_open=6)
        self.assertIsNone(evaluate(candles, facts, self.spec, with_open(BUY_PARAMS)))

    def test_no_signal_when_level_was_invalidated_before_the_open(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        params = with_open(BUY_PARAMS)
        params["level_invalidated_before_open"] = True
        self.assertIsNone(evaluate(candles, facts, self.spec, params))

    def test_no_signal_with_fewer_than_two_candles(self):
        candles = make_candles([BUY_CURRENT], start=NY_OPEN + timedelta(minutes=1))
        facts = make_facts(NY_OPEN + timedelta(minutes=2))
        self.assertIsNone(evaluate(candles, facts, self.spec, with_open(BUY_PARAMS)))

    # ----- Downgrade rules -----

    def test_buy_is_skipped_when_close_is_under_the_asia_low(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT, asia_low=101.0)
        self.assertIsNone(evaluate(candles, facts, self.spec, with_open(BUY_PARAMS)))

    def test_sell_under_equilibrium_needs_a_confirmed_drive(self):
        previous = (94.4, 94.6, 94.1, 94.4)
        current = (94.2, 94.3, 93.4, 93.6)
        params = {"call_direction": "sell", "call_levels": [94.0, 93.0]}
        candles, facts = setup(previous, current, equilibrium=95.0)
        self.assertIsNone(evaluate(candles, facts, self.spec, with_open(params)))
        confirmed = with_open(params)
        confirmed["sell_drive_confirmed"] = True
        signal = evaluate(candles, facts, self.spec, confirmed)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)

    def test_friday_is_skipped_by_default(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT, open_time=NY_OPEN_FRIDAY)
        params = with_open(BUY_PARAMS, open_time=NY_OPEN_FRIDAY)
        self.assertIsNone(evaluate(candles, facts, self.spec, params))

    def test_friday_can_be_allowed(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT, open_time=NY_OPEN_FRIDAY)
        params = with_open(BUY_PARAMS, open_time=NY_OPEN_FRIDAY)
        params["skip_friday"] = False
        self.assertIsNotNone(evaluate(candles, facts, self.spec, params))

    # ----- Stop, target and the 90-second rule -----

    def test_default_stop_and_target_are_fixed_60_and_60(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        signal = evaluate(candles, facts, self.spec, with_open(BUY_PARAMS))
        self.assertEqual(signal.sl_mode, "fixed")
        self.assertEqual(signal.tp_mode, "fixed")
        # US30 is measured in points, one point = 1.0 in price.
        self.assertEqual(signal.stop_distance, 60.0)
        self.assertEqual(signal.target_distance, 60.0)

    def test_target_can_be_changed_to_120(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        params = with_open(BUY_PARAMS)
        params["fixed_target"] = 120
        signal = evaluate(candles, facts, self.spec, params)
        self.assertEqual(signal.stop_distance, 60.0)
        self.assertEqual(signal.target_distance, 120.0)

    def test_volatility_scaled_mode_is_still_selectable(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        params = with_open(BUY_PARAMS)
        params.update({"sl_mode": "volatility_scaled", "tp_mode": "volatility_scaled"})
        signal = evaluate(candles, facts, self.spec, params)
        # Average candle size 2.0: stop 1.5 times, target 3.0 times.
        self.assertAlmostEqual(signal.stop_distance, 3.0)
        self.assertAlmostEqual(signal.target_distance, 6.0)

    def test_structural_buy_uses_candle_low_and_previous_day_equilibrium(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT, equilibrium=110.0)
        params = with_open(BUY_PARAMS)
        params.update({"sl_mode": "structural", "tp_mode": "structural"})
        signal = evaluate(candles, facts, self.spec, params)
        self.assertIsNotNone(signal)
        # Candle low 99.6 minus a quarter of the average candle size (0.5).
        self.assertAlmostEqual(signal.structural_stop_price, 99.1)
        self.assertEqual(signal.structural_target_price, 110.0)

    def test_ninety_second_rule_is_passed_on(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        signal = evaluate(candles, facts, self.spec, with_open(BUY_PARAMS))
        self.assertEqual(signal.time_limit_seconds, 90)

    def test_exit_seconds_can_be_changed(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        params = with_open(BUY_PARAMS)
        params["exit_after_seconds"] = 120
        signal = evaluate(candles, facts, self.spec, params)
        self.assertEqual(signal.time_limit_seconds, 120)

    def test_extended_edition_has_no_time_limit(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        params = with_open(BUY_PARAMS)
        params["extended_edition"] = True
        signal = evaluate(candles, facts, self.spec, params)
        self.assertIsNone(signal.time_limit_seconds)

    def test_parameters_passed_in_are_not_changed(self):
        candles, facts = setup(BUY_PREVIOUS, BUY_CURRENT)
        params = with_open(BUY_PARAMS)
        before = dict(params)
        evaluate(candles, facts, self.spec, params)
        self.assertEqual(params, before)


if __name__ == "__main__":
    unittest.main()