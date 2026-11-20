import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from knowledge.operational_definitions import (
    aligned_levels,
    average_candle_size,
    average_candle_size_by_time_of_day,
    close_back_rejection,
    chop_present,
    level_holds,
    momentum_break,
    volume_present,
    wick_rejection,
)


def candles(rows, start=None, step=timedelta(minutes=5)):
    first = start or datetime(2025, 1, 1, tzinfo=timezone.utc)
    return pd.DataFrame(
        [
            {
                "time": first + index * step,
                "open": row[0],
                "high": row[1],
                "low": row[2],
                "close": row[3],
            }
            for index, row in enumerate(rows)
        ]
    )


class OperationalDefinitionTests(unittest.TestCase):
    def test_average_candle_size_and_body_size(self):
        frame = candles([(10, 12, 9, 11), (11, 15, 10, 14)])
        self.assertEqual(average_candle_size(frame), 4.0)

    def test_time_of_day_average_uses_only_prior_matching_slots(self):
        start = datetime(2025, 1, 1, 8, 0, tzinfo=timezone.utc)
        rows = [(10, 12, 9, 11), (11, 15, 10, 14)]
        frame = candles(rows, start)
        next_day = candles(rows, start + timedelta(days=1))
        combined = pd.concat([frame, next_day], ignore_index=True)

        result = average_candle_size_by_time_of_day(
            combined,
            "M5",
            start + timedelta(days=1, minutes=5),
            days=2,
        )

        self.assertEqual(result, 3.0)

    def test_volume_drive_rejection_hold_and_momentum_are_parameterized(self):
        impulse = pd.Series({"open": 10.0, "high": 16.0, "low": 9.8, "close": 15.8})
        self.assertTrue(volume_present(impulse, 2.0, 1.5, 0.6))
        self.assertTrue(momentum_break(pd.DataFrame([impulse]), 15.0, "bullish", 2.0))
        self.assertTrue(wick_rejection(pd.Series({
            "open": 10.2, "high": 10.5, "low": 9.0, "close": 10.4,
        }), 9.5, "bullish", 0.5))
        hold = candles([(10.5, 10.8, 10.0, 10.6), (10.6, 10.9, 10.1, 10.7)])
        self.assertTrue(level_holds(hold, 10.0, "bullish", 1.0, hold_candles=2))
        self.assertTrue(close_back_rejection(
            candles([(10.0, 10.2, 9.5, 10.1)]), 10.0, "bullish", 1.0,
            minimum_sweep_acs=0.1, maximum_sweep_acs=1.0,
        ))

    def test_chop_and_aligned_levels(self):
        frame = candles([(10, 11, 9.5, 10.2)] * 5)
        self.assertTrue(chop_present(frame, 2.0, candle_count=5))
        self.assertTrue(aligned_levels([10, 10.5], average_size=1.0))
        self.assertFalse(aligned_levels([10, 11], average_size=1.0))


if __name__ == "__main__":
    unittest.main()
