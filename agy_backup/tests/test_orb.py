import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import get_instrument_spec
from engine.models import Direction
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.volume_profile import VolumeProfileReport
from strategies.context import MarketFacts, PreviousDayFacts, StrategySession
from strategies.orb import VARIANTS, breakout_killed, evaluate

# London box starts 08:00 SAST, which is 06:00 UTC. A 15 minute box on M5
# candles is the first three candles (06:00, 06:05, 06:10), range 90 to 100.
START = datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc)
BOX = [(95.0, 100.0, 90.0, 95.0)] * 3
BREAK_UP = (96.0, 103.0, 95.0, 102.0)
BREAK_DOWN = (94.0, 95.0, 87.0, 88.0)
INSIDE = (95.0, 99.0, 94.0, 98.0)


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


def make_test_facts(candle_count, acs=1.0, session_name="London"):
    # The last candle has finished by the time we look at the market.
    now = START + timedelta(minutes=5 * candle_count)
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
            pivots={"R1": 110.0, "S1": 80.0},
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


class OrbStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    def run_orb(self, extra_rows, parameters=None, variant="orb_15m"):
        candles = make_test_candles(BOX + list(extra_rows))
        facts = make_test_facts(len(candles))
        return evaluate(candles, "M5", facts, self.spec, parameters=parameters, variant=variant)

    def test_close_above_box_is_a_buy_with_stop_at_opposite_edge(self):
        signal = self.run_orb([BREAK_UP])
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.variant, "orb_15m")
        self.assertEqual(signal.structural_stop_price, 90.0)

    def test_close_below_box_is_a_sell_with_stop_at_opposite_edge(self):
        signal = self.run_orb([BREAK_DOWN])
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)
        self.assertEqual(signal.structural_stop_price, 100.0)

    def test_structural_stop_sits_just_beyond_the_box_edge(self):
        signal = self.run_orb([BREAK_UP], parameters={"sl_mode": "structural"})
        self.assertIsNotNone(signal)
        # Box low 90 minus the 0.25 x average candle size buffer.
        self.assertAlmostEqual(signal.structural_stop_price, 89.75)

    def test_no_signal_while_price_stays_inside_the_box(self):
        self.assertIsNone(self.run_orb([INSIDE]))

    def test_no_signal_before_the_box_is_finished(self):
        candles = make_test_candles(BOX[:2])
        facts = make_test_facts(len(candles))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_only_the_first_close_outside_gives_a_signal(self):
        second_close_outside = (102.0, 104.0, 101.0, 103.0)
        self.assertIsNone(self.run_orb([BREAK_UP, second_close_outside]))

    def test_two_candle_confirmation_waits_for_the_second_close(self):
        parameters = {"confirmation_candles": 2}
        self.assertIsNone(self.run_orb([BREAK_UP], parameters=parameters))
        second_close_outside = (102.0, 104.0, 101.0, 103.0)
        signal = self.run_orb([BREAK_UP, second_close_outside], parameters=parameters)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)

    def test_two_candle_confirmation_fails_if_second_candle_closes_back_inside(self):
        self.assertIsNone(self.run_orb([BREAK_UP, INSIDE], parameters={"confirmation_candles": 2}))

    def test_kill_rule_true_when_buy_breakout_closes_back_inside(self):
        candles = make_test_candles(BOX + [BREAK_UP, INSIDE])
        facts = make_test_facts(len(candles))
        self.assertTrue(breakout_killed(candles, "M5", facts, Direction.BUY))

    def test_kill_rule_false_when_buy_breakout_holds(self):
        holds = (102.0, 104.0, 101.0, 103.0)
        candles = make_test_candles(BOX + [BREAK_UP, holds])
        facts = make_test_facts(len(candles))
        self.assertFalse(breakout_killed(candles, "M5", facts, Direction.BUY))

    def test_kill_rule_for_sell_breakout(self):
        back_inside = (89.0, 93.0, 88.0, 92.0)
        candles = make_test_candles(BOX + [BREAK_DOWN, back_inside])
        facts = make_test_facts(len(candles))
        self.assertTrue(breakout_killed(candles, "M5", facts, Direction.SELL))
        holds = (88.0, 89.0, 86.0, 87.0)
        candles = make_test_candles(BOX + [BREAK_DOWN, holds])
        facts = make_test_facts(len(candles))
        self.assertFalse(breakout_killed(candles, "M5", facts, Direction.SELL))

    def test_second_bullet_only_allows_the_opposite_side(self):
        after_buy = {"bullet_number": 2, "first_trade_direction": Direction.BUY}
        self.assertIsNone(self.run_orb([BREAK_UP], parameters=after_buy))
        signal = self.run_orb([BREAK_DOWN], parameters=after_buy)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)

    def test_second_bullet_needs_the_first_trade_direction(self):
        with self.assertRaises(ValueError):
            self.run_orb([BREAK_UP], parameters={"bullet_number": 2})

    def test_no_third_bullet(self):
        parameters = {"bullet_number": 3, "first_trade_direction": Direction.BUY}
        self.assertIsNone(self.run_orb([BREAK_DOWN], parameters=parameters))

    def test_wide_box_is_skipped_when_the_range_cap_is_set(self):
        # The box is 10 wide. A cap of 5 price units skips it, a cap of 50 does not.
        too_wide = {"max_range": 5.0, "max_range_unit": "price"}
        self.assertIsNone(self.run_orb([BREAK_UP], parameters=too_wide))
        wide_enough = {"max_range": 50.0, "max_range_unit": "price"}
        self.assertIsNotNone(self.run_orb([BREAK_UP], parameters=wide_enough))

    def test_unknown_variant_is_rejected(self):
        with self.assertRaises(ValueError):
            self.run_orb([BREAK_UP], variant="not_a_variant")

    def test_listed_variants_exist(self):
        self.assertEqual(
            set(VARIANTS),
            {"orb_30m", "orb_15m", "orb_5m", "orb_2m", "pre_orb_15m"},
        )

    def test_thirty_minute_box_uses_six_candles(self):
        box_30 = [(95.0, 100.0, 90.0, 95.0)] * 6
        candles = make_test_candles(box_30 + [BREAK_UP])
        facts = make_test_facts(len(candles))
        signal = evaluate(candles, "M5", facts, self.spec, variant="orb_30m")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.variant, "orb_30m")


if __name__ == "__main__":
    unittest.main()