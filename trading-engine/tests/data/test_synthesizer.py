import unittest

import pandas as pd

from data.synthesizer import TIMEFRAMES, build, build_all


def make_m1(start, minutes, base=100.0):
    """Deterministic 1-minute candles. Candle i opens at base + i * 0.1."""
    start = pd.Timestamp(start, tz="UTC")
    rows = []
    for index in range(minutes):
        opened = base + index * 0.1
        rows.append(
            {
                "time": start + pd.Timedelta(minutes=index),
                "open": opened,
                "high": opened + 0.5,
                "low": opened - 0.5,
                "close": opened + 0.2,
                "volume": 1.0,
            }
        )
    return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])


def times(frame):
    return [stamp.strftime("%Y-%m-%d %H:%M") for stamp in frame["time"]]


class FixedTimeframeTests(unittest.TestCase):
    def test_five_minute_candle_values(self):
        m1 = make_m1("2025-01-06 10:00", 10)
        m5 = build(m1, "M5")
        self.assertEqual(times(m5), ["2025-01-06 10:00", "2025-01-06 10:05"])
        first = m5.iloc[0]
        self.assertAlmostEqual(first["open"], 100.0)
        self.assertAlmostEqual(first["high"], 100.4 + 0.5)
        self.assertAlmostEqual(first["low"], 100.0 - 0.5)
        self.assertAlmostEqual(first["close"], 100.4 + 0.2)
        self.assertEqual(first["volume"], 5.0)

    def test_unfinished_last_candle_is_dropped(self):
        m5 = build(make_m1("2025-01-06 10:00", 7), "M5")
        self.assertEqual(times(m5), ["2025-01-06 10:00"])

    def test_unfinished_last_candle_is_kept_when_asked(self):
        m5 = build(make_m1("2025-01-06 10:00", 7), "M5", complete_only=False)
        self.assertEqual(times(m5), ["2025-01-06 10:00", "2025-01-06 10:05"])
        self.assertEqual(m5.iloc[1]["volume"], 2.0)

    def test_candle_is_kept_when_as_of_is_after_its_end(self):
        m5 = build(make_m1("2025-01-06 10:00", 7), "M5", as_of=pd.Timestamp("2025-01-06 10:10", tz="UTC"))
        self.assertEqual(times(m5), ["2025-01-06 10:00", "2025-01-06 10:05"])

    def test_hourly_candles_follow_the_utc_clock(self):
        h1 = build(make_m1("2025-01-06 09:30", 150), "H1", complete_only=False)
        self.assertEqual(times(h1), ["2025-01-06 09:00", "2025-01-06 10:00", "2025-01-06 11:00"])

    def test_market_closed_periods_leave_no_candles(self):
        part_one = make_m1("2025-01-06 10:00", 5)
        part_two = make_m1("2025-01-06 12:00", 5)
        m5 = build(pd.concat([part_one, part_two]), "M5")
        self.assertEqual(times(m5), ["2025-01-06 10:00", "2025-01-06 12:00"])

    def test_unsorted_input_is_sorted(self):
        m1 = make_m1("2025-01-06 10:00", 10).sample(frac=1.0, random_state=1)
        self.assertEqual(times(build(m1, "M5")), ["2025-01-06 10:00", "2025-01-06 10:05"])


class RolloverTimeframeTests(unittest.TestCase):
    """Daily, 4-hour, weekly and monthly candles start at 17:00 New York time."""

    def test_daily_candle_starts_at_2200_utc_in_winter(self):
        d1 = build(make_m1("2025-01-06 21:55", 10), "D1", complete_only=False)
        self.assertEqual(times(d1), ["2025-01-05 22:00", "2025-01-06 22:00"])
        self.assertEqual(d1.iloc[0]["volume"], 5.0)
        self.assertEqual(d1.iloc[1]["volume"], 5.0)

    def test_daily_candle_starts_at_2100_utc_in_summer(self):
        d1 = build(make_m1("2025-07-08 20:55", 10), "D1", complete_only=False)
        self.assertEqual(times(d1), ["2025-07-07 21:00", "2025-07-08 21:00"])

    def test_daily_candle_across_the_spring_clock_change(self):
        # Clocks go forward on Sunday 9 March 2025: the rollover moves from 22:00 to 21:00 UTC.
        before = make_m1("2025-03-09 15:00", 3)
        after = make_m1("2025-03-09 21:05", 3)
        d1 = build(pd.concat([before, after]), "D1", complete_only=False)
        self.assertEqual(times(d1), ["2025-03-08 22:00", "2025-03-09 21:00"])

    def test_four_hour_candles_in_winter(self):
        h4 = build(make_m1("2025-01-07 05:58", 4), "H4", complete_only=False)
        self.assertEqual(times(h4), ["2025-01-07 02:00", "2025-01-07 06:00"])

    def test_four_hour_candles_in_summer(self):
        h4 = build(make_m1("2025-07-08 04:58", 4), "H4", complete_only=False)
        self.assertEqual(times(h4), ["2025-07-08 01:00", "2025-07-08 05:00"])

    def test_six_four_hour_candles_per_day(self):
        h4 = build(make_m1("2025-01-07 02:00", 24 * 60), "H4", complete_only=False)
        self.assertEqual(
            times(h4),
            [
                "2025-01-07 02:00",
                "2025-01-07 06:00",
                "2025-01-07 10:00",
                "2025-01-07 14:00",
                "2025-01-07 18:00",
                "2025-01-07 22:00",
            ],
        )

    def test_weekly_candle_starts_on_sunday_evening(self):
        friday = make_m1("2025-01-10 21:55", 5)
        sunday = make_m1("2025-01-12 22:05", 5)
        w1 = build(pd.concat([friday, sunday]), "W1", complete_only=False)
        self.assertEqual(times(w1), ["2025-01-05 22:00", "2025-01-12 22:00"])

    def test_monthly_candle_starts_at_the_rollover_before_the_first_trading_day(self):
        december = make_m1("2024-12-31 21:55", 5)
        january = make_m1("2024-12-31 22:05", 5)
        mn1 = build(pd.concat([december, january]), "MN1", complete_only=False)
        self.assertEqual(times(mn1), ["2024-11-30 22:00", "2024-12-31 22:00"])

    def test_week_candle_is_dropped_until_the_week_is_over(self):
        m1 = make_m1("2025-01-07 10:00", 60)
        self.assertEqual(len(build(m1, "W1")), 0)
        self.assertEqual(len(build(m1, "W1", as_of=pd.Timestamp("2025-01-13", tz="UTC"))), 1)

    def test_daily_candle_is_kept_when_data_reaches_the_friday_close(self):
        # Friday 17:00 New York time is 22:00 UTC in January; the last 1-minute candle is 21:59.
        m1 = make_m1("2025-01-10 21:50", 10)
        d1 = build(m1, "D1")
        self.assertEqual(times(d1), ["2025-01-09 22:00"])


class GeneralTests(unittest.TestCase):
    def test_one_minute_passes_through(self):
        m1 = make_m1("2025-01-06 10:00", 5)
        self.assertEqual(len(build(m1, "M1")), 5)

    def test_empty_input_gives_empty_output(self):
        empty = make_m1("2025-01-06 10:00", 0)
        self.assertEqual(len(build(empty, "H1")), 0)

    def test_unknown_timeframe_is_rejected(self):
        with self.assertRaises(ValueError):
            build(make_m1("2025-01-06 10:00", 5), "M7")

    def test_missing_columns_are_rejected(self):
        with self.assertRaises(ValueError):
            build(make_m1("2025-01-06 10:00", 5).drop(columns=["volume"]), "M5")

    def test_timeframe_names_are_not_case_sensitive(self):
        self.assertEqual(len(build(make_m1("2025-01-06 10:00", 10), "m5")), 2)

    def test_all_requested_timeframes_are_built(self):
        m1 = make_m1("2025-01-06 10:00", 600)
        built = build_all(m1, as_of=pd.Timestamp("2025-02-01", tz="UTC"))
        self.assertEqual(set(built), set(TIMEFRAMES[1:]))
        for frame in built.values():
            self.assertTrue((frame["high"] >= frame["low"]).all())

    def test_higher_timeframes_agree_with_lower_ones(self):
        m1 = make_m1("2025-01-06 10:00", 600)
        h1 = build(m1, "H1")
        m5 = build(m1, "M5")
        self.assertEqual(h1["volume"].sum(), 600.0)
        self.assertEqual(m5["volume"].sum(), 600.0)
        self.assertAlmostEqual(h1["high"].max(), m1["high"].max())
        self.assertAlmostEqual(h1["low"].min(), m1["low"].min())


if __name__ == "__main__":
    unittest.main()