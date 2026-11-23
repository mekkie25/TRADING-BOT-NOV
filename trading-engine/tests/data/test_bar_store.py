import tempfile
import unittest
from pathlib import Path

import pandas as pd

from data import bar_store


def make_candles(start, count, step_minutes=1, base=100.0):
    start = pd.Timestamp(start, tz="UTC")
    rows = []
    for index in range(count):
        opened = base + index * 0.01
        rows.append(
            {
                "time": start + pd.Timedelta(minutes=index * step_minutes),
                "open": opened,
                "high": opened + 0.05,
                "low": opened - 0.05,
                "close": opened + 0.02,
                "volume": 10.0,
            }
        )
    return pd.DataFrame(rows, columns=bar_store.COLUMNS)


class BarStoreTests(unittest.TestCase):
    def setUp(self):
        self._folder = tempfile.TemporaryDirectory()
        self.store = Path(self._folder.name) / "store"
        self.raw = Path(self._folder.name) / "raw"

    def tearDown(self):
        self._folder.cleanup()

    # ----- saving and merging -----

    def test_first_merge_creates_the_file_and_a_gitignore(self):
        result = bar_store.merge_m1("XAUUSD", make_candles("2025-01-06 10:00", 60), store_dir=self.store)
        self.assertEqual(result.rows_after, 60)
        self.assertEqual(result.rows_before, 0)
        self.assertTrue((self.store / "XAUUSD_M1.parquet").exists())
        self.assertEqual((self.store / ".gitignore").read_text().strip(), "*")

    def test_no_temporary_file_is_left_behind(self):
        bar_store.merge_m1("XAUUSD", make_candles("2025-01-06 10:00", 5), store_dir=self.store)
        self.assertEqual([p.name for p in self.store.glob("*.tmp")], [])

    def test_overlapping_merge_has_no_duplicates_and_new_data_wins(self):
        bar_store.merge_m1("US30", make_candles("2025-01-06 10:00", 10), store_dir=self.store)
        newer = make_candles("2025-01-06 10:05", 10, base=500.0)
        result = bar_store.merge_m1("US30", newer, store_dir=self.store)
        stored = bar_store.load_m1("US30", self.store)
        self.assertEqual(result.rows_after, 15)
        self.assertEqual(stored["time"].is_unique, True)
        self.assertTrue(stored["time"].is_monotonic_increasing)
        row = stored[stored["time"] == pd.Timestamp("2025-01-06 10:05", tz="UTC")].iloc[0]
        self.assertAlmostEqual(row["open"], 500.0)

    def test_invalid_candles_are_rejected_and_counted(self):
        candles = make_candles("2025-01-06 10:00", 5)
        candles.loc[1, "high"] = candles.loc[1, "low"] - 1.0   # high below low
        candles.loc[2, "close"] = -5.0                          # negative price
        candles.loc[3, "open"] = float("nan")                   # missing value
        result = bar_store.merge_m1("EURUSD", candles, store_dir=self.store)
        self.assertEqual(result.rows_rejected, 3)
        self.assertEqual(result.rows_after, 2)

    def test_merging_nothing_keeps_what_is_stored(self):
        bar_store.merge_m1("EURUSD", make_candles("2025-01-06 10:00", 5), store_dir=self.store)
        result = bar_store.merge_m1("EURUSD", make_candles("2025-01-06 10:00", 0), store_dir=self.store)
        self.assertEqual(result.rows_after, 5)

    def test_missing_columns_are_rejected(self):
        with self.assertRaises(ValueError):
            bar_store.merge_m1("EURUSD", make_candles("2025-01-06 10:00", 5).drop(columns=["close"]), store_dir=self.store)

    # ----- rolling window -----

    def test_candles_older_than_three_years_are_dropped(self):
        old = make_candles("2021-12-01", 1)
        inside = make_candles("2022-01-10", 1)
        newest = make_candles("2025-01-06", 1)
        everything = pd.concat([old, inside, newest], ignore_index=True)
        result = bar_store.merge_m1("BTCUSD", everything, store_dir=self.store)
        stored = bar_store.load_m1("BTCUSD", self.store)
        self.assertEqual(result.rows_trimmed, 1)
        self.assertEqual(len(stored), 2)
        self.assertEqual(stored["time"].min(), pd.Timestamp("2022-01-10", tz="UTC"))

    def test_adding_a_new_day_drops_the_oldest_day(self):
        days = pd.concat(
            [make_candles(f"2022-01-{day:02d}", 1) for day in range(6, 11)] + [make_candles("2025-01-06", 1)],
            ignore_index=True,
        )
        bar_store.merge_m1("DAX", days, store_dir=self.store)
        self.assertEqual(len(bar_store.load_m1("DAX", self.store)), 6)   # 6 Jan 2022 is exactly on the edge and kept
        bar_store.merge_m1("DAX", make_candles("2025-01-07", 1), store_dir=self.store)
        stored = bar_store.load_m1("DAX", self.store)
        self.assertEqual(stored["time"].min(), pd.Timestamp("2022-01-07", tz="UTC"))
        self.assertEqual(stored["time"].max(), pd.Timestamp("2025-01-07", tz="UTC"))

    def test_window_is_counted_from_the_newest_candle_not_from_today(self):
        # Skipping the daily update must not make old data vanish.
        candles = pd.concat([make_candles("2020-03-01", 1), make_candles("2021-03-01", 1)], ignore_index=True)
        bar_store.merge_m1("GBPUSD", candles, store_dir=self.store)
        self.assertEqual(len(bar_store.load_m1("GBPUSD", self.store)), 2)

    def test_window_length_can_be_changed(self):
        candles = pd.concat([make_candles("2023-01-01", 1), make_candles("2025-01-01", 1)], ignore_index=True)
        result = bar_store.merge_m1("USDJPY", candles, years=1, store_dir=self.store)
        self.assertEqual(result.rows_after, 1)

    # ----- reading -----

    def test_loading_a_missing_symbol_gives_an_empty_frame(self):
        frame = bar_store.load_m1("NOTHING", self.store)
        self.assertEqual(len(frame), 0)
        self.assertEqual(list(frame.columns), bar_store.COLUMNS)

    def test_last_time(self):
        self.assertIsNone(bar_store.last_time("XAUUSD", self.store))
        bar_store.merge_m1("XAUUSD", make_candles("2025-01-06 10:00", 30), store_dir=self.store)
        self.assertEqual(bar_store.last_time("XAUUSD", self.store), pd.Timestamp("2025-01-06 10:29", tz="UTC"))

    def test_load_candles_builds_higher_timeframes(self):
        bar_store.merge_m1("XAUUSD", make_candles("2025-01-06 10:00", 60), store_dir=self.store)
        m5 = bar_store.load_candles("XAUUSD", "M5", self.store)
        self.assertEqual(len(m5), 12)
        h1 = bar_store.load_candles("XAUUSD", "H1", self.store)
        self.assertEqual(len(h1), 1)
        self.assertEqual(h1.iloc[0]["volume"], 600.0)

    def test_load_candles_can_filter_by_time(self):
        bar_store.merge_m1("XAUUSD", make_candles("2025-01-06 10:00", 60), store_dir=self.store)
        m5 = bar_store.load_candles(
            "XAUUSD", "M5", self.store, start="2025-01-06 10:20", end=pd.Timestamp("2025-01-06 10:35", tz="UTC")
        )
        self.assertEqual(m5["time"].min(), pd.Timestamp("2025-01-06 10:20", tz="UTC"))
        self.assertEqual(m5["time"].max(), pd.Timestamp("2025-01-06 10:35", tz="UTC"))

    def test_symbol_names_are_cleaned_for_file_names(self):
        self.assertEqual(bar_store.store_path("us30.cash", self.store).name, "US30CASH_M1.parquet")
        with self.assertRaises(ValueError):
            bar_store.store_path("...", self.store)

    # ----- status and export -----

    def test_status_reports_rows_range_and_longest_gap(self):
        candles = pd.concat([make_candles("2025-01-06 10:00", 3), make_candles("2025-01-08 10:00", 3)], ignore_index=True)
        bar_store.merge_m1("NAS100", candles, store_dir=self.store)
        info = bar_store.status("NAS100", self.store)
        self.assertEqual(info["rows"], 6)
        self.assertEqual(info["first"], pd.Timestamp("2025-01-06 10:00", tz="UTC"))
        self.assertEqual(info["last"], pd.Timestamp("2025-01-08 10:02", tz="UTC"))
        self.assertAlmostEqual(info["longest_gap_hours"], 47.97, places=1)

    def test_status_of_an_empty_store(self):
        self.assertEqual(bar_store.status("NAS100", self.store)["rows"], 0)

    def test_export_writes_the_four_csv_files_the_backtester_reads(self):
        bar_store.merge_m1("XAUUSD", make_candles("2025-01-06 10:00", 60), store_dir=self.store)
        paths = bar_store.export_for_backtester("XAUUSD", store_dir=self.store, raw_dir=self.raw)
        self.assertEqual(sorted(p.name for p in paths), ["XAUUSD_D1.csv", "XAUUSD_H1.csv", "XAUUSD_H4.csv", "XAUUSD_M5.csv"])
        loaded = pd.read_csv(self.raw / "XAUUSD_M5.csv")
        self.assertEqual(list(loaded.columns), ["time", "open", "high", "low", "close", "volume"])
        parsed = pd.to_datetime(loaded["time"], utc=True)
        self.assertEqual(parsed.iloc[0], pd.Timestamp("2025-01-06 10:00", tz="UTC"))
        self.assertEqual((self.raw / ".gitignore").read_text().strip(), "*.csv")


if __name__ == "__main__":
    unittest.main()