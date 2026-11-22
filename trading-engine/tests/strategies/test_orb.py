import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import get_instrument_spec
from engine.models import Direction
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.volume_profile import VolumeProfileReport
from strategies.context import MarketFacts, PreviousDayFacts, StrategySession
from strategies.orb import breakout_killed, evaluate

# London opens 08:00 SAST = 06:00 UTC. The 15-minute box covers 06:00-06:15 UTC.
LONDON_OPEN = datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc)

# Three 5-minute box candles. Box high = 103.0, box low = 98.0.
BOX_ROWS = [
    (100.0, 102.0, 99.0, 101.0),
    (101.0, 103.0, 100.0, 102.0),
    (102.0, 103.0, 98.0, 100.0),
]


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


def candles_and_facts(extra_rows):
    """Box candles plus the given extra candles. Time is the end of the last candle."""
    rows = BOX_ROWS + list(extra_rows)
    candles = make_candles(rows)
    now = LONDON_OPEN + timedelta(minutes=5 * len(rows))
    return candles, make_facts(now)


class OrbStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    # ----- Breakout signals -----

    def test_buy_when_candle_closes_above_box(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        signal = evaluate(candles, "M5", facts, self.spec)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.strategy_name, "orb")
        self.assertEqual(signal.variant, "orb_15m")

    def test_sell_when_candle_closes_below_box(self):
        candles, facts = candles_and_facts([(100.0, 101.0, 95.0, 96.0)])
        signal = evaluate(candles, "M5", facts, self.spec)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)

    def test_buy_structural_stop_is_below_box_low(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        signal = evaluate(candles, "M5", facts, self.spec, parameters={"sl_mode": "structural"})
        self.assertIsNotNone(signal)
        # Box low 98.0 minus a quarter of the average candle size (0.5).
        self.assertEqual(signal.structural_stop_price, 97.5)

    def test_sell_structural_stop_is_above_box_high(self):
        candles, facts = candles_and_facts([(100.0, 101.0, 95.0, 96.0)])
        signal = evaluate(candles, "M5", facts, self.spec, parameters={"sl_mode": "structural"})
        self.assertIsNotNone(signal)
        # Box high 103.0 plus a quarter of the average candle size (0.5).
        self.assertEqual(signal.structural_stop_price, 103.5)

    def test_no_signal_when_candle_closes_inside_box(self):
        candles, facts = candles_and_facts([(100.0, 104.0, 99.0, 101.0)])
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_when_wick_goes_outside_but_close_is_inside(self):
        candles, facts = candles_and_facts([(100.0, 110.0, 90.0, 101.0)])
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_before_box_is_finished(self):
        # Only two candles, so the clock is 06:10 and the 15-minute box is not done.
        candles = make_candles(BOX_ROWS[:2])
        facts = make_facts(LONDON_OPEN + timedelta(minutes=10))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_when_breakout_already_happened_earlier(self):
        candles, facts = candles_and_facts(
            [
                (100.0, 106.0, 99.0, 105.0),
                (105.0, 108.0, 104.0, 106.0),
            ]
        )
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_for_unknown_session(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        facts = make_facts(facts.current_time, session_name="Weekend")
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    # ----- Variants -----

    def test_five_minute_box_variant(self):
        # Box is just the first candle: high 103.0, low 98.0.
        rows = [
            (100.0, 103.0, 98.0, 101.0),
            (101.0, 106.0, 100.0, 105.0),
        ]
        candles = make_candles(rows)
        facts = make_facts(LONDON_OPEN + timedelta(minutes=10))
        signal = evaluate(candles, "M5", facts, self.spec, variant="orb_5m")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.variant, "orb_5m")

    def test_unknown_variant_is_rejected(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        with self.assertRaises(ValueError):
            evaluate(candles, "M5", facts, self.spec, variant="orb_99m")

    # ----- Two-candle confirmation option -----

    def test_two_candle_confirmation_needs_two_closes_outside(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        self.assertIsNone(
            evaluate(candles, "M5", facts, self.spec, parameters={"confirmation_candles": 2})
        )

    def test_two_candle_confirmation_signals_after_second_close(self):
        candles, facts = candles_and_facts(
            [
                (100.0, 106.0, 99.0, 105.0),
                (105.0, 108.0, 104.0, 106.0),
            ]
        )
        signal = evaluate(candles, "M5", facts, self.spec, parameters={"confirmation_candles": 2})
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)

    def test_confirmation_candles_must_be_whole_number(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        with self.assertRaises(ValueError):
            evaluate(candles, "M5", facts, self.spec, parameters={"confirmation_candles": 0})

    # ----- Two-bullet rule -----

    def test_bullet_two_needs_first_trade_direction(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        with self.assertRaises(ValueError):
            evaluate(candles, "M5", facts, self.spec, parameters={"bullet_number": 2})

    def test_bullet_two_takes_opposite_side(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        signal = evaluate(
            candles,
            "M5",
            facts,
            self.spec,
            parameters={"bullet_number": 2, "first_trade_direction": Direction.SELL},
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)

    def test_bullet_two_skips_same_side(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        signal = evaluate(
            candles,
            "M5",
            facts,
            self.spec,
            parameters={"bullet_number": 2, "first_trade_direction": Direction.BUY},
        )
        self.assertIsNone(signal)

    def test_bullet_three_never_trades(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        signal = evaluate(
            candles,
            "M5",
            facts,
            self.spec,
            parameters={"bullet_number": 3, "first_trade_direction": Direction.SELL},
        )
        self.assertIsNone(signal)

    # ----- Optional range cap -----

    def test_wide_box_is_skipped_when_cap_is_set(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        # Box is 5.0 wide, cap is 4.0.
        signal = evaluate(
            candles,
            "M5",
            facts,
            self.spec,
            parameters={"max_range": 4.0, "max_range_unit": "price"},
        )
        self.assertIsNone(signal)

    def test_narrow_box_still_trades_when_cap_is_set(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        signal = evaluate(
            candles,
            "M5",
            facts,
            self.spec,
            parameters={"max_range": 10.0, "max_range_unit": "price"},
        )
        self.assertIsNotNone(signal)

    # ----- Kill rule -----

    def test_buy_is_killed_when_close_returns_inside_box(self):
        candles, facts = candles_and_facts(
            [
                (100.0, 106.0, 99.0, 105.0),
                (105.0, 105.0, 100.0, 102.0),
            ]
        )
        self.assertTrue(breakout_killed(candles, "M5", facts, Direction.BUY))

    def test_buy_is_not_killed_while_close_stays_outside(self):
        candles, facts = candles_and_facts(
            [
                (100.0, 106.0, 99.0, 105.0),
                (105.0, 108.0, 104.0, 107.0),
            ]
        )
        self.assertFalse(breakout_killed(candles, "M5", facts, Direction.BUY))

    def test_sell_is_killed_when_close_returns_inside_box(self):
        candles, facts = candles_and_facts(
            [
                (100.0, 101.0, 95.0, 96.0),
                (96.0, 100.0, 95.0, 99.0),
            ]
        )
        self.assertTrue(breakout_killed(candles, "M5", facts, Direction.SELL))

    def test_sell_is_not_killed_while_close_stays_outside(self):
        candles, facts = candles_and_facts(
            [
                (100.0, 101.0, 95.0, 96.0),
                (96.0, 97.0, 93.0, 94.0),
            ]
        )
        self.assertFalse(breakout_killed(candles, "M5", facts, Direction.SELL))

    def test_kill_rule_is_false_with_no_candles(self):
        candles = pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
        facts = make_facts(LONDON_OPEN + timedelta(minutes=20))
        self.assertFalse(breakout_killed(candles, "M5", facts, Direction.BUY))

    def test_kill_rule_rejects_bad_direction(self):
        candles, facts = candles_and_facts([(100.0, 106.0, 99.0, 105.0)])
        with self.assertRaises(ValueError):
            breakout_killed(candles, "M5", facts, "up")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()