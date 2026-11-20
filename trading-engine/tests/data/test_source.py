import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from data.source import InMemoryCandleDataSource


class CandleDataSourceTests(unittest.TestCase):
    def test_source_returns_filtered_copy_for_symbol_and_timeframe(self):
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        candles = pd.DataFrame(
            {
                "time": [start, start + timedelta(hours=1)],
                "open": [1.0, 1.1],
                "high": [1.2, 1.3],
                "low": [0.9, 1.0],
                "close": [1.1, 1.2],
            }
        )
        source = InMemoryCandleDataSource({("eurusd", "h1"): candles})

        loaded = source.load_candles(
            "EURUSD",
            "H1",
            start_time=start + timedelta(minutes=30),
        )

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded.iloc[0]["open"], 1.1)
        loaded.loc[0, "open"] = 9.0
        self.assertEqual(candles.iloc[1]["open"], 1.1)

    def test_source_rejects_unsorted_and_unknown_frames(self):
        frame = pd.DataFrame({"time": ["2025-01-02", "2025-01-01"]})
        source = InMemoryCandleDataSource({("EURUSD", "M1"): frame})
        with self.assertRaisesRegex(ValueError, "chronological"):
            source.load_candles("EURUSD", "M1")
        with self.assertRaises(KeyError):
            source.load_candles("XAUUSD", "M1")


if __name__ == "__main__":
    unittest.main()
