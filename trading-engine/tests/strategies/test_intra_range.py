import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import get_instrument_spec
from engine.models import Direction
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.volume_profile import VolumeProfileReport
from strategies.context import MarketFacts, PreviousDayFacts, StrategySession
from strategies.intra_range import evaluate

# London opens 08:00 SAST = 06:00 UTC. The 15-minute box covers 06:00-06:15 UTC.
LONDON_OPEN = datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc)

# Three 5-minute box candles. Box high = 200.0, box low = 100.0, so the box is
# exactly 100 wide, the smallest range the spec allows.
BOX_ROWS = [
    (150.0, 180.0, 110.0, 160.0),
    (160.0, 200.0, 120.0, 170.0),
    (170.0, 190.0, 100.0, 150.0),
]

# Spec version: a candle pokes above 200 and closes back inside, the next candle
# tests 200 and is rejected (long upper wick, closes inside).
POKE_TOP = (195.0, 203.0, 190.0, 197.0)
REJECT_TOP = (193.0, 201.0, 192.0, 194.0)
# Mirror at the bottom (100).
POKE_BOTTOM = (105.0, 110.0, 97.0, 103.0)
REJECT_BOTTOM = (107.0, 108.0, 99.0, 106.0)

# Older version: a candle CLOSES above 200, the next candle closes back inside.
CLOSE_OUTSIDE_TOP = (195.0, 206.0, 194.0, 205.0)
CLOSE_BACK_TOP = (198.0, 201.0, 191.0, 192.0)


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
            high=210.0,
            low=90.0,
            candle_count=12,
            level_mode="wick",
            session_complete=True,
            summary="Asia complete",
        ),
        previous_day=PreviousDayFacts(
            high=205.0,
            low=85.0,
            close=150.0,
            equilibrium=145.0,
            pivots={"R1": 210.0, "S1": 80.0},
        ),
        daily_flip=DailyFlipReport(
            day=current_time.date(),
            level=140.0,
            source_candle_time=pd.Timestamp(current_time),
            summary="Daily Flip at 140",
        ),
        ema_200=130.0,
        volume_profile=VolumeProfileReport(
            poc=150.0,
            vah=170.0,
            val=130.0,
            bin_size=0.2,
            value_area_fraction=0.7,
            source="tick_approx",
            approximate=True,
            candle_count=10,
            summary="Profile available",
        ),
    )


def candles_and_facts(extra_rows, box_rows=BOX_ROWS):
    """Box candles plus the given extra candles. Time is the end of the last candle."""
    rows = list(box_rows) + list(extra_rows)
    candles = make_candles(rows)
    now = LONDON_OPEN + timedelta(minutes=5 * len(rows))
    return candles, make_facts(now)


class IntraRangeStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    # ----- Spec version: poke out, close back inside, then a rejection -----

    def test_sell_after_poke_above_and_rejection_at_the_top(self):
        candles, facts = candles_and_facts([POKE_TOP, REJECT_TOP])
        signal = evaluate(candles, "M5", facts, self.spec)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)
        self.assertEqual(signal.strategy_name, "intra_range")
        self.assertEqual(signal.variant, "poke_then_reject")

    def test_buy_after_poke_below_and_rejection_at_the_bottom(self):
        candles, facts = candles_and_facts([POKE_BOTTOM, REJECT_BOTTOM])
        signal = evaluate(candles, "M5", facts, self.spec)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)

    def test_sell_stop_is_above_both_candles_and_target_is_range_bottom(self):
        candles, facts = candles_and_facts([POKE_TOP, REJECT_TOP])
        signal = evaluate(candles, "M5", facts, self.spec)
        self.assertEqual(signal.sl_mode, "structural")
        self.assertEqual(signal.tp_mode, "structural")
        # Highest high 203.0 plus a quarter of the average candle size (0.5).
        self.assertEqual(signal.structural_stop_price, 203.5)
        self.assertEqual(signal.structural_target_price, 100.0)

    def test_buy_stop_is_below_both_candles_and_target_is_range_top(self):
        candles, facts = candles_and_facts([POKE_BOTTOM, REJECT_BOTTOM])
        signal = evaluate(candles, "M5", facts, self.spec)
        # Lowest low 97.0 minus a quarter of the average candle size (0.5).
        self.assertEqual(signal.structural_stop_price, 96.5)
        self.assertEqual(signal.structural_target_price, 200.0)

    def test_no_signal_when_first_candle_closes_outside_the_range(self):
        # The second candle is a real rejection, so only the first candle's close blocks this.
        candles, facts = candles_and_facts([CLOSE_OUTSIDE_TOP, REJECT_TOP])
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_when_first_candle_does_not_break_out(self):
        candles, facts = candles_and_facts([(195.0, 199.0, 190.0, 197.0), REJECT_TOP])
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_when_second_candle_does_not_reach_the_top(self):
        candles, facts = candles_and_facts([POKE_TOP, (193.0, 199.0, 192.0, 194.0)])
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_when_second_candle_has_no_clear_rejection_wick(self):
        # Reaches the top but the upper wick is only a small part of the candle.
        candles, facts = candles_and_facts([POKE_TOP, (198.0, 201.0, 190.0, 192.0)])
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_rejection_wick_size_can_be_relaxed(self):
        candles, facts = candles_and_facts([POKE_TOP, (198.0, 201.0, 190.0, 192.0)])
        signal = evaluate(
            candles, "M5", facts, self.spec, parameters={"rejection_wick_fraction": 0.2}
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)

    def test_no_signal_when_second_candle_closes_outside_the_range(self):
        candles, facts = candles_and_facts([POKE_TOP, (193.0, 205.0, 192.0, 204.0)])
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    # ----- Older version: close outside, then close back inside -----

    def test_older_version_sells_after_close_outside_then_back_inside(self):
        candles, facts = candles_and_facts([CLOSE_OUTSIDE_TOP, CLOSE_BACK_TOP])
        signal = evaluate(candles, "M5", facts, self.spec, variant="range_fade")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)
        self.assertEqual(signal.variant, "range_fade")
        # Current candle high 201.0 plus a quarter of the average candle size (0.5).
        self.assertEqual(signal.structural_stop_price, 201.5)
        self.assertEqual(signal.structural_target_price, 100.0)

    def test_older_version_does_not_trade_the_spec_pattern(self):
        candles, facts = candles_and_facts([POKE_TOP, REJECT_TOP])
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec, variant="range_fade"))

    def test_unknown_variant_is_rejected(self):
        candles, facts = candles_and_facts([POKE_TOP, REJECT_TOP])
        with self.assertRaises(ValueError):
            evaluate(candles, "M5", facts, self.spec, variant="fade_everything")

    # ----- Range size and timing -----

    def test_range_of_exactly_100_is_allowed(self):
        candles, facts = candles_and_facts([POKE_TOP, REJECT_TOP])
        self.assertIsNotNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_when_range_is_smaller_than_minimum(self):
        candles, facts = candles_and_facts([POKE_TOP, REJECT_TOP])
        self.assertIsNone(
            evaluate(candles, "M5", facts, self.spec, parameters={"minimum_range_size": 101.0})
        )

    def test_minimum_range_size_can_be_lowered(self):
        small_box = [
            (150.0, 160.0, 140.0, 155.0),
            (155.0, 165.0, 145.0, 150.0),
            (150.0, 170.0, 150.0, 160.0),
        ]
        # Box is 140-170 wide 30. Poke above 170 then reject.
        poke = (165.0, 173.0, 160.0, 167.0)
        reject = (163.0, 171.0, 162.0, 164.0)
        candles, facts = candles_and_facts([poke, reject], box_rows=small_box)
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))
        signal = evaluate(
            candles, "M5", facts, self.spec, parameters={"minimum_range_size": 30.0}
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)

    def test_no_signal_before_the_box_is_finished(self):
        candles = make_candles(BOX_ROWS[:2])
        facts = make_facts(LONDON_OPEN + timedelta(minutes=10))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_with_fewer_than_two_candles(self):
        candles = make_candles(BOX_ROWS[:1])
        facts = make_facts(LONDON_OPEN + timedelta(minutes=5))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_for_unknown_session(self):
        candles, facts = candles_and_facts([POKE_TOP, REJECT_TOP])
        facts = make_facts(facts.current_time, session_name="Weekend")
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    # ----- Stop and target options -----

    def test_fixed_mode_is_still_selectable(self):
        candles, facts = candles_and_facts([POKE_TOP, REJECT_TOP])
        signal = evaluate(
            candles,
            "M5",
            facts,
            self.spec,
            parameters={"sl_mode": "fixed", "tp_mode": "fixed"},
        )
        self.assertEqual(signal.sl_mode, "fixed")
        self.assertEqual(signal.tp_mode, "fixed")
        # Placeholder numbers, not from the spec: 40 stop and 100 target in points.
        self.assertEqual(signal.stop_distance, 40.0)
        self.assertEqual(signal.target_distance, 100.0)

    def test_volatility_scaled_mode_is_still_selectable(self):
        candles, facts = candles_and_facts([POKE_TOP, REJECT_TOP])
        signal = evaluate(
            candles,
            "M5",
            facts,
            self.spec,
            parameters={"sl_mode": "volatility_scaled", "tp_mode": "volatility_scaled"},
        )
        # Average candle size 2.0: stop 1.5 times, target 3.0 times.
        self.assertAlmostEqual(signal.stop_distance, 3.0)
        self.assertAlmostEqual(signal.target_distance, 6.0)

    def test_parameters_passed_in_are_not_changed(self):
        candles, facts = candles_and_facts([POKE_TOP, REJECT_TOP])
        parameters = {"rejection_wick_fraction": 0.5}
        evaluate(candles, "M5", facts, self.spec, parameters=parameters)
        self.assertEqual(parameters, {"rejection_wick_fraction": 0.5})


if __name__ == "__main__":
    unittest.main()