import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import get_instrument_spec
from engine.models import Direction
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.volume_profile import VolumeProfileReport
from strategies.context import MarketFacts, PreviousDayFacts, StrategySession
from strategies.oes import OES_STUBS, evaluate

# London opens 08:00 SAST = 06:00 UTC. The OES candle is the first 5-minute candle.
LONDON_OPEN = datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc)
# New York opens 08:30 New York time = 13:30 UTC in January.
NY_OPEN = datetime(2025, 1, 2, 13, 30, tzinfo=timezone.utc)

# The OES candle: high 103.0, low 98.0.
OES_CANDLE = (100.0, 103.0, 98.0, 101.0)

# Failed break of the high: closes above 103, then closes back inside.
BREAK_HIGH = (101.0, 106.0, 100.0, 105.0)
BACK_INSIDE_FROM_HIGH = (105.0, 106.0, 101.0, 102.0)
# Failed break of the low: closes below 98, then closes back inside.
BREAK_LOW = (99.0, 100.0, 94.0, 95.0)
BACK_INSIDE_FROM_LOW = (95.0, 100.0, 94.5, 99.0)

ON = {"enabled": True}


def make_candles(rows, start=LONDON_OPEN, step=timedelta(minutes=5)):
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


def make_facts(current_time, acs=2.0, session_name="London"):
    return MarketFacts(
        current_time=current_time,
        timeframe="M5",
        session=StrategySession(
            name=session_name,
            observed_at_utc=current_time,
            local_time=current_time,
            is_open_window=True,
        ),
        average_candle_size=acs,
        asia=AsiaLevelsReport(
            observed_at_utc=current_time,
            session_date="2025-01-02",
            high=110.0,
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


def setup(extra_rows, start=LONDON_OPEN, session_name="London"):
    """The OES candle plus the given candles. Time is the end of the last candle."""
    rows = [OES_CANDLE] + list(extra_rows)
    candles = make_candles(rows, start=start)
    now = start + timedelta(minutes=5 * len(rows))
    return candles, make_facts(now, session_name=session_name)


class OesStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    # ----- Off by default -----

    def test_is_off_by_default(self):
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH])
        self.assertIsNone(evaluate(candles, facts, self.spec))

    def test_status_says_experimental_and_off(self):
        stub = OES_STUBS["oes_5m"]
        self.assertFalse(stub.enabled_by_default)
        self.assertIn("UNVERIFIED", stub.status)

    # ----- Entry: the break must fail, then a close back inside -----

    def test_sell_after_break_of_high_closes_back_inside(self):
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH])
        signal = evaluate(candles, facts, self.spec, ON)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)
        self.assertEqual(signal.strategy_name, "oes")
        self.assertEqual(signal.variant, "oes_5m")

    def test_buy_after_break_of_low_closes_back_inside(self):
        candles, facts = setup([BREAK_LOW, BACK_INSIDE_FROM_LOW])
        signal = evaluate(candles, facts, self.spec, ON)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)

    def test_no_signal_on_the_breaking_close_itself(self):
        candles, facts = setup([BREAK_HIGH])
        self.assertIsNone(evaluate(candles, facts, self.spec, ON))

    def test_no_signal_while_price_is_still_outside(self):
        candles, facts = setup([BREAK_HIGH, (105.0, 108.0, 104.0, 107.0)])
        self.assertIsNone(evaluate(candles, facts, self.spec, ON))

    def test_no_signal_when_a_wick_goes_outside_but_no_candle_closes_outside(self):
        candles, facts = setup([(101.0, 106.0, 100.0, 102.0), (102.0, 103.0, 100.0, 101.0)])
        self.assertIsNone(evaluate(candles, facts, self.spec, ON))

    def test_no_signal_when_the_candle_closes_through_the_whole_box(self):
        # Breaks the high, then closes below the low: not back inside.
        candles, facts = setup([BREAK_HIGH, (105.0, 105.0, 94.0, 95.0)])
        self.assertIsNone(evaluate(candles, facts, self.spec, ON))

    def test_only_the_first_side_to_break_counts_and_it_does_not_fire_twice(self):
        # Break high, back inside (this is the signal), then break low and back inside again.
        candles, facts = setup(
            [BREAK_HIGH, BACK_INSIDE_FROM_HIGH, BREAK_LOW, BACK_INSIDE_FROM_LOW]
        )
        self.assertIsNone(evaluate(candles, facts, self.spec, ON))

    def test_no_signal_if_price_returned_inside_before_the_latest_candle(self):
        candles, facts = setup(
            [BREAK_HIGH, BACK_INSIDE_FROM_HIGH, (102.0, 103.0, 100.0, 101.0)]
        )
        self.assertIsNone(evaluate(candles, facts, self.spec, ON))

    def test_no_signal_before_the_oes_candle_is_finished(self):
        candles = make_candles([OES_CANDLE])
        facts = make_facts(LONDON_OPEN + timedelta(minutes=3))
        self.assertIsNone(evaluate(candles, facts, self.spec, ON))

    def test_no_signal_for_unknown_session(self):
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH], session_name="Weekend")
        self.assertIsNone(evaluate(candles, facts, self.spec, ON))

    # ----- Session window cap (optional) -----

    def test_late_first_break_is_skipped_when_a_window_is_set(self):
        # The break candle starts 5 minutes after the open.
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH])
        params = dict(ON, max_minutes_after_open=3)
        self.assertIsNone(evaluate(candles, facts, self.spec, params))

    def test_first_break_inside_the_window_still_trades(self):
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH])
        params = dict(ON, max_minutes_after_open=10)
        self.assertIsNotNone(evaluate(candles, facts, self.spec, params))

    # ----- New York open -----

    def test_works_at_the_new_york_open(self):
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH], start=NY_OPEN)
        params = dict(ON, opening_session="New York")
        signal = evaluate(candles, facts, self.spec, params)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)

    # ----- Stop and target -----

    def test_default_stop_and_target_are_fixed_50_and_100(self):
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH])
        signal = evaluate(candles, facts, self.spec, ON)
        self.assertEqual(signal.sl_mode, "fixed")
        self.assertEqual(signal.tp_mode, "fixed")
        # US30 is measured in points, one point = 1.0 in price.
        self.assertEqual(signal.stop_distance, 50.0)
        self.assertEqual(signal.target_distance, 100.0)

    def test_scalp_target_and_gold_spread_stop_can_be_set(self):
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH])
        params = dict(ON, fixed_stop=53, fixed_target=53)
        signal = evaluate(candles, facts, self.spec, params)
        self.assertEqual(signal.stop_distance, 53.0)
        self.assertEqual(signal.target_distance, 53.0)

    def test_structural_sell_uses_break_extreme_and_previous_day_s1(self):
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH])
        params = dict(ON, sl_mode="structural", tp_mode="structural")
        signal = evaluate(candles, facts, self.spec, params)
        self.assertIsNotNone(signal)
        # Highest high of the failed break 106.0 plus a quarter of the average candle size (0.5).
        self.assertEqual(signal.structural_stop_price, 106.5)
        self.assertEqual(signal.structural_target_price, 80.0)

    def test_structural_buy_uses_break_extreme_and_previous_day_r1(self):
        candles, facts = setup([BREAK_LOW, BACK_INSIDE_FROM_LOW])
        params = dict(ON, sl_mode="structural", tp_mode="structural")
        signal = evaluate(candles, facts, self.spec, params)
        self.assertIsNotNone(signal)
        # Lowest low of the failed break 94.0 minus a quarter of the average candle size (0.5).
        self.assertEqual(signal.structural_stop_price, 93.5)
        self.assertEqual(signal.structural_target_price, 110.0)

    def test_volatility_scaled_mode_is_still_selectable(self):
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH])
        params = dict(ON, sl_mode="volatility_scaled", tp_mode="volatility_scaled")
        signal = evaluate(candles, facts, self.spec, params)
        # Average candle size 2.0: stop 1.5 times, target 3.0 times.
        self.assertAlmostEqual(signal.stop_distance, 3.0)
        self.assertAlmostEqual(signal.target_distance, 6.0)

    # ----- Blocked variants and inputs -----

    def test_four_hour_variants_stay_blocked(self):
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH])
        self.assertIsNone(evaluate(candles, facts, self.spec, ON, variant="oes_4h"))
        self.assertIsNone(evaluate(candles, facts, self.spec, ON, variant="oes_inverse_4h"))

    def test_unknown_variant_is_rejected(self):
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH])
        with self.assertRaises(ValueError):
            evaluate(candles, facts, self.spec, ON, variant="three_box")

    def test_parameters_passed_in_are_not_changed(self):
        candles, facts = setup([BREAK_HIGH, BACK_INSIDE_FROM_HIGH])
        params = {"enabled": True}
        evaluate(candles, facts, self.spec, params)
        self.assertEqual(params, {"enabled": True})


if __name__ == "__main__":
    unittest.main()