import unittest
from datetime import datetime, timedelta, timezone

from data.live_feed import Candle, LiveQuote
from market.market_snapshot import build_market_snapshot


class MarketSnapshotTests(unittest.TestCase):
    def test_snapshot_uses_only_completed_m1_and_m5_candles(self):
        start = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
        m1_candles = [
            self.make_candle(start + timedelta(minutes=index), "M1", index)
            for index in range(7)
        ]
        m5_candles = [
            self.make_candle(start - timedelta(minutes=5), "M5", 0),
            self.make_candle(start, "M5", 1),
            self.make_candle(start + timedelta(minutes=5), "M5", 2),
        ]
        as_of = start + timedelta(minutes=6)
        quote = LiveQuote(
            symbol="EURUSD",
            time=as_of,
            bid=1.1000,
            ask=1.1001,
        )

        snapshot = build_market_snapshot(
            "EURUSD",
            as_of,
            quote,
            {"M1": m1_candles, "M5": m5_candles},
        )

        self.assertEqual(snapshot["candles"]["candle_count"], 6)
        self.assertEqual(
            snapshot["candles"]["latest_candle_time"],
            start + timedelta(minutes=5),
        )
        self.assertEqual(
            len(snapshot["reports"]["M5"]["market_structure"]["all_swings"]),
            0,
        )
        self.assertEqual(snapshot["reports"]["M1"]["average_candle_range"].sample_count, 6)
        self.assertFalse(snapshot["entry_criteria_evaluated"])
        self.assertIn("daily_bias", snapshot["unavailable_reports"])
        self.assertIn("judas_swing", snapshot["unavailable_reports"])
        self.assertIn("liquidity_types", snapshot["unavailable_reports"])

    def test_snapshot_rejects_a_quote_from_after_the_observation_time(self):
        as_of = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
        quote = LiveQuote(
            symbol="EURUSD",
            time=as_of + timedelta(seconds=1),
            bid=1.1,
            ask=1.1001,
        )

        with self.assertRaisesRegex(ValueError, "later than as_of"):
            build_market_snapshot("EURUSD", as_of, quote, {})

    @staticmethod
    def make_candle(time, timeframe, index):
        close = 1.1 + index * 0.0001
        return Candle(
            symbol="EURUSD",
            timeframe=timeframe,
            time=time,
            open=close - 0.00005,
            high=close + 0.0001,
            low=close - 0.0001,
            close=close,
            volume=100,
        )


if __name__ == "__main__":
    unittest.main()
