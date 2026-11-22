import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from broker.instrument_specs import get_instrument_spec
from engine.models import Direction
from knowledge.asia_levels import AsiaLevelsReport
from knowledge.daily_flip import DailyFlipReport
from knowledge.volume_profile import VolumeProfileReport
from strategies.context import MarketFacts, PreviousDayFacts, StrategySession
from strategies.power_ranger import breakout_killed, evaluate

# London opens 08:00 SAST = 06:00 UTC. The 15-minute box covers 06:00-06:15 UTC.
LONDON_OPEN = datetime(2025, 1, 2, 6, 0, tzinfo=timezone.utc)
# Asia opens 01:00 SAST = 23:00 UTC the evening before.
ASIA_OPEN = datetime(2025, 1, 1, 23, 0, tzinfo=timezone.utc)

# Three 5-minute box candles. Box high = 103.0, box low = 98.0.
BOX_ROWS = [
    (100.0, 102.0, 99.0, 101.0),
    (101.0, 103.0, 100.0, 102.0),
    (102.0, 103.0, 98.0, 100.0),
]

# A clean buy: breakout closes at 105, retest dips to 102.5 and closes at 104
# (retest high 105.5), confirmation closes at 106 (above the retest high).
BUY_BREAKOUT = (102.0, 106.0, 101.0, 105.0)
BUY_RETEST = (105.0, 105.5, 102.5, 104.0)
BUY_CONFIRM = (104.0, 107.0, 103.5, 106.0)

# A clean sell: breakout closes at 96, retest rises to 98.5 and closes at 97
# (retest low 95.5), confirmation closes at 95 (below the retest low).
SELL_BREAKOUT = (99.0, 100.0, 95.0, 96.0)
SELL_RETEST = (96.0, 98.5, 95.5, 97.0)
SELL_CONFIRM = (97.0, 97.5, 94.0, 95.0)


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


def candles_and_facts(extra_rows, start=LONDON_OPEN):
    """Box candles plus the given extra candles. Time is the end of the last candle."""
    rows = BOX_ROWS + list(extra_rows)
    candles = make_candles(rows, start=start)
    now = start + timedelta(minutes=5 * len(rows))
    return candles, make_facts(now)


def buy_setup(breakout=BUY_BREAKOUT, retest=BUY_RETEST, confirm=BUY_CONFIRM):
    return candles_and_facts([breakout, retest, confirm])


def sell_setup(breakout=SELL_BREAKOUT, retest=SELL_RETEST, confirm=SELL_CONFIRM):
    return candles_and_facts([breakout, retest, confirm])


class PowerRangerStrategyTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_instrument_spec("US30")

    # ----- Entry on a confirmed close -----

    def test_buy_after_breakout_retest_and_confirming_close(self):
        candles, facts = buy_setup()
        signal = evaluate(candles, "M5", facts, self.spec)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.strategy_name, "power_ranger")
        self.assertEqual(signal.variant, "15m_range_5m_retest")

    def test_sell_after_breakout_retest_and_confirming_close(self):
        candles, facts = sell_setup()
        signal = evaluate(candles, "M5", facts, self.spec)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.SELL)

    def test_no_signal_when_confirmation_wicks_above_but_closes_below_retest_high(self):
        # Liquidity-grab case: the wick goes past the retest high, the close does not.
        candles, facts = buy_setup(confirm=(104.0, 108.0, 103.5, 105.0))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_when_sell_confirmation_wicks_below_but_closes_above_retest_low(self):
        candles, facts = sell_setup(confirm=(97.0, 97.5, 93.0, 96.0))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_when_confirmation_close_equals_retest_high(self):
        candles, facts = buy_setup(confirm=(104.0, 107.0, 103.5, 105.5))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_when_confirmation_closes_back_inside_the_box(self):
        candles, facts = buy_setup(confirm=(104.0, 105.0, 101.0, 102.0))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    # ----- Breakout and retest rules -----

    def test_no_signal_when_retest_closes_back_inside_the_box(self):
        candles, facts = buy_setup(retest=(105.0, 105.5, 100.0, 102.0))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_when_retest_never_touches_the_broken_edge(self):
        candles, facts = buy_setup(retest=(105.0, 106.0, 104.0, 105.5))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_when_breakout_candle_closes_inside_the_box(self):
        candles, facts = buy_setup(breakout=(102.0, 106.0, 101.0, 102.5))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_when_box_is_not_finished(self):
        # The clock says 06:10, so the 15-minute box (06:00-06:15) is not finished.
        candles = make_candles(BOX_ROWS)
        facts = make_facts(LONDON_OPEN + timedelta(minutes=10))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_with_fewer_than_three_candles(self):
        candles = make_candles(BOX_ROWS[:2])
        facts = make_facts(LONDON_OPEN + timedelta(minutes=10))
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    def test_no_signal_for_unknown_session(self):
        candles, facts = buy_setup()
        facts = make_facts(facts.current_time, session_name="Weekend")
        self.assertIsNone(evaluate(candles, "M5", facts, self.spec))

    # ----- Asia open -----

    def test_works_on_the_asia_open(self):
        candles, facts = candles_and_facts(
            [BUY_BREAKOUT, BUY_RETEST, BUY_CONFIRM], start=ASIA_OPEN
        )
        # The session name comes from the parameters, not from the facts.
        signal = evaluate(
            candles, "M5", facts, self.spec, parameters={"opening_session": "Asia"}
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, Direction.BUY)

    # ----- Stop and target defaults and options -----

    def test_default_stop_and_target_are_fixed_40_and_120(self):
        candles, facts = buy_setup()
        signal = evaluate(candles, "M5", facts, self.spec)
        self.assertEqual(signal.sl_mode, "fixed")
        self.assertEqual(signal.tp_mode, "fixed")
        # US30 is measured in points, one point = 1.0 in price.
        self.assertEqual(signal.stop_distance, 40.0)
        self.assertEqual(signal.target_distance, 120.0)

    def test_default_stop_and_target_use_pips_on_gold(self):
        gold = get_instrument_spec("XAUUSD")
        candles, facts = buy_setup()
        signal = evaluate(candles, "M5", facts, gold)
        # Gold pip size is 0.10, so 40 pips = 4.0 and 120 pips = 12.0 in price.
        self.assertAlmostEqual(signal.stop_distance, 4.0)
        self.assertAlmostEqual(signal.target_distance, 12.0)

    def test_fixed_stop_and_target_can_be_changed(self):
        candles, facts = buy_setup()
        signal = evaluate(
            candles,
            "M5",
            facts,
            self.spec,
            parameters={"fixed_stop": 30, "fixed_target": 90},
        )
        self.assertEqual(signal.stop_distance, 30.0)
        self.assertEqual(signal.target_distance, 90.0)

    def test_structural_buy_uses_retest_low_and_previous_day_r1(self):
        candles, facts = buy_setup()
        signal = evaluate(
            candles,
            "M5",
            facts,
            self.spec,
            parameters={"sl_mode": "structural", "tp_mode": "structural"},
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.sl_mode, "structural")
        self.assertEqual(signal.tp_mode, "structural")
        # Retest low 102.5 minus a quarter of the average candle size (0.5).
        self.assertEqual(signal.structural_stop_price, 102.0)
        self.assertEqual(signal.structural_target_price, 110.0)

    def test_structural_sell_uses_retest_high_and_previous_day_s1(self):
        candles, facts = sell_setup()
        signal = evaluate(
            candles,
            "M5",
            facts,
            self.spec,
            parameters={"sl_mode": "structural", "tp_mode": "structural"},
        )
        self.assertIsNotNone(signal)
        # Retest high 98.5 plus a quarter of the average candle size (0.5).
        self.assertEqual(signal.structural_stop_price, 99.0)
        self.assertEqual(signal.structural_target_price, 80.0)

    def test_parameters_passed_in_are_not_changed(self):
        candles, facts = buy_setup()
        parameters = {"fixed_stop": 30}
        evaluate(candles, "M5", facts, self.spec, parameters=parameters)
        self.assertEqual(parameters, {"fixed_stop": 30})

    # ----- Kill rule -----

    def test_buy_is_killed_when_close_returns_inside_the_box(self):
        candles, facts = candles_and_facts(
            [BUY_BREAKOUT, BUY_RETEST, BUY_CONFIRM, (106.0, 106.0, 101.0, 102.0)]
        )
        self.assertTrue(breakout_killed(candles, "M5", facts, Direction.BUY))

    def test_buy_is_not_killed_while_close_stays_outside(self):
        candles, facts = candles_and_facts(
            [BUY_BREAKOUT, BUY_RETEST, BUY_CONFIRM, (106.0, 109.0, 105.0, 108.0)]
        )
        self.assertFalse(breakout_killed(candles, "M5", facts, Direction.BUY))

    def test_sell_is_killed_when_close_returns_inside_the_box(self):
        candles, facts = candles_and_facts(
            [SELL_BREAKOUT, SELL_RETEST, SELL_CONFIRM, (95.0, 100.0, 94.0, 99.0)]
        )
        self.assertTrue(breakout_killed(candles, "M5", facts, Direction.SELL))

    def test_sell_is_not_killed_while_close_stays_outside(self):
        candles, facts = candles_and_facts(
            [SELL_BREAKOUT, SELL_RETEST, SELL_CONFIRM, (95.0, 96.0, 92.0, 93.0)]
        )
        self.assertFalse(breakout_killed(candles, "M5", facts, Direction.SELL))

    def test_kill_rule_is_false_with_no_candles(self):
        candles = pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
        facts = make_facts(LONDON_OPEN + timedelta(minutes=30))
        self.assertFalse(breakout_killed(candles, "M5", facts, Direction.BUY))

    def test_kill_rule_rejects_bad_direction(self):
        candles, facts = buy_setup()
        with self.assertRaises(ValueError):
            breakout_killed(candles, "M5", facts, "up")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()