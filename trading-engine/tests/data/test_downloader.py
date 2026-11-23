import contextlib
import io
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pandas as pd

from data import bar_store, downloader
from data.downloader import (
    HistoryDownloader,
    parse_overrides,
    plan_chunks,
    resolve_symbols,
    sync_start,
    trendbars_to_frame,
)


class PureHelperTests(unittest.TestCase):
    def test_chunks_cover_the_range_without_gaps(self):
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = start + timedelta(days=10)
        chunks = plan_chunks(start, end, 3)
        self.assertEqual(len(chunks), 4)
        self.assertEqual(chunks[0][0], int(start.timestamp() * 1000))
        self.assertEqual(chunks[-1][1], int(end.timestamp() * 1000))
        for earlier, later in zip(chunks, chunks[1:]):
            self.assertEqual(earlier[1], later[0])

    def test_no_chunks_for_an_empty_range(self):
        moment = datetime(2025, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(plan_chunks(moment, moment, 3), [])

    def test_chunk_size_must_be_above_zero(self):
        moment = datetime(2025, 1, 1, tzinfo=timezone.utc)
        with self.assertRaises(ValueError):
            plan_chunks(moment, moment + timedelta(days=1), 0)

    def test_first_download_starts_at_the_window_start(self):
        now = datetime(2025, 6, 1, tzinfo=timezone.utc)
        start = sync_start(None, now, 3)
        self.assertAlmostEqual((now - start).days, 1096, delta=2)

    def test_update_resumes_one_day_before_the_newest_candle(self):
        now = datetime(2025, 6, 1, tzinfo=timezone.utc)
        last = pd.Timestamp("2025-05-30 12:00", tz="UTC")
        self.assertEqual(sync_start(last, now, 3), datetime(2025, 5, 29, 12, tzinfo=timezone.utc))

    def test_update_never_starts_before_the_window(self):
        now = datetime(2025, 6, 1, tzinfo=timezone.utc)
        ancient = pd.Timestamp("2010-01-01", tz="UTC")
        self.assertEqual(sync_start(ancient, now, 3), sync_start(None, now, 3))

    def test_trendbars_are_converted_to_candles(self):
        bar = SimpleNamespace(low=110000, deltaOpen=50, deltaHigh=120, deltaClose=80, volume=42, utcTimestampInMinutes=28_000_000)
        frame = trendbars_to_frame([bar])
        row = frame.iloc[0]
        self.assertEqual(list(frame.columns), bar_store.COLUMNS)
        self.assertAlmostEqual(row["low"], 1.1)
        self.assertAlmostEqual(row["open"], 1.1005)
        self.assertAlmostEqual(row["high"], 1.1012)
        self.assertAlmostEqual(row["close"], 1.1008)
        self.assertEqual(row["volume"], 42.0)
        self.assertEqual(row["time"], datetime.fromtimestamp(28_000_000 * 60, timezone.utc))

    def test_no_trendbars_give_an_empty_frame_with_the_right_columns(self):
        frame = trendbars_to_frame([])
        self.assertEqual(len(frame), 0)
        self.assertEqual(list(frame.columns), bar_store.COLUMNS)

    def test_instrument_names_are_matched_to_broker_names(self):
        broker = {"GER40": 1, "GOLD": 2, "US30.cash": 3, "USTEC": 4, "EURUSD": 5, "BTCUSD": 6, "AUDCAD": 7}
        resolved, missing = resolve_symbols(broker, ["DAX", "XAUUSD", "US30", "NAS100", "EURUSD", "BTCUSD", "USDJPY"])
        self.assertEqual(resolved["DAX"], ("GER40", 1))
        self.assertEqual(resolved["XAUUSD"], ("GOLD", 2))
        self.assertEqual(resolved["US30"], ("US30.cash", 3))
        self.assertEqual(resolved["NAS100"], ("USTEC", 4))
        self.assertEqual(missing, ["USDJPY"])

    def test_names_can_be_overridden(self):
        resolved, missing = resolve_symbols({"MyDax": 9, "GER40": 1}, ["DAX"], {"dax": "mydax"})
        self.assertEqual(resolved["DAX"], ("MyDax", 9))
        self.assertEqual(missing, [])

    def test_map_option_is_parsed(self):
        self.assertEqual(parse_overrides(["dax=GER40", "XAUUSD = GOLD"]), {"DAX": "GER40", "XAUUSD": "GOLD"})
        with self.assertRaises(ValueError):
            parse_overrides(["nonsense"])

    def test_credentials_are_read_from_the_environment(self):
        values = {
            "CTRADER_CLIENT_ID": "id",
            "CTRADER_SECRET": "secret",
            "CTRADER_ACCESS_TOKEN": "token",
            "CTRADER_ACCOUNT_ID": "123",
        }
        with mock.patch.dict(os.environ, values):
            credentials, missing = downloader.load_credentials()
        self.assertEqual(missing, [])
        self.assertEqual(credentials["CTRADER_ACCOUNT_ID"], "123")


# ----- A pretend cTrader, to check the download loop without a connection -----

class FakeRequest:
    pass


class FakeClient:
    def __init__(self):
        self.sent = []

    def send(self, request):
        self.sent.append(request)


class FakeReactor:
    def __init__(self):
        self.running = True
        self.scheduled = []

    def callLater(self, delay, function, *args):
        self.scheduled.append(function)

    def stop(self):
        self.running = False


PAYLOAD = SimpleNamespace(
    PROTO_OA_ERROR_RES=1,
    PROTO_OA_APPLICATION_AUTH_RES=2,
    PROTO_OA_ACCOUNT_AUTH_RES=3,
    PROTO_OA_SYMBOLS_LIST_RES=4,
    PROTO_OA_GET_TRENDBARS_RES=5,
)


def message(kind, **body):
    return SimpleNamespace(payloadType=kind, body=SimpleNamespace(**body))


def symbols_message(names):
    items = [SimpleNamespace(symbolName=name, symbolId=symbol_id) for name, symbol_id in names.items()]
    return message(PAYLOAD.PROTO_OA_SYMBOLS_LIST_RES, symbol=items)


def trendbars_message(minutes, has_more=False):
    bars = [
        SimpleNamespace(low=200_000_000 + i, deltaOpen=10, deltaHigh=50, deltaClose=20, volume=7, utcTimestampInMinutes=minute)
        for i, minute in enumerate(minutes)
    ]
    return message(PAYLOAD.PROTO_OA_GET_TRENDBARS_RES, trendbar=bars, hasMore=has_more)


class DownloadLoopTests(unittest.TestCase):
    def setUp(self):
        self._folder = tempfile.TemporaryDirectory()
        self.store = Path(self._folder.name) / "store"
        self.reactor = FakeReactor()
        self.client = FakeClient()

    def tearDown(self):
        self._folder.cleanup()

    def make(self, mode="sync", wanted=("XAUUSD",), years=0.05, show_all=False):
        pretend = HistoryDownloader(mode, list(wanted), years=years, store_dir=self.store, show_all=show_all)
        pretend.api = SimpleNamespace(
            Protobuf=SimpleNamespace(extract=lambda msg: msg.body),
            AppAuthReq=FakeRequest, AccountAuthReq=FakeRequest, SymbolsListReq=FakeRequest, TrendbarsReq=FakeRequest,
            PayloadType=PAYLOAD, Period=SimpleNamespace(M1="M1"),
        )
        pretend.reactor = self.reactor
        pretend.client = self.client
        pretend.credentials = {"CTRADER_ACCOUNT_ID": "123", "CTRADER_CLIENT_ID": "x", "CTRADER_SECRET": "y", "CTRADER_ACCESS_TOKEN": "z"}
        return pretend

    def quiet(self, function, *args):
        with contextlib.redirect_stdout(io.StringIO()) as captured:
            function(*args)
        return captured.getvalue()

    def reply_to_current_request(self, pretend, has_more=False, count=2):
        request = self.client.sent[-1]
        first_minute = request.fromTimestamp // 60000
        self.quiet(pretend.on_message, None, trendbars_message([first_minute + i for i in range(count)], has_more))

    def run_scheduled(self):
        while self.reactor.scheduled and self.reactor.running:
            self.reactor.scheduled.pop(0)()

    def test_full_download_saves_candles_and_stops(self):
        pretend = self.make()
        self.quiet(pretend.on_message, None, symbols_message({"XAUUSD": 5, "AUDCAD": 6}))
        self.assertEqual(self.client.sent[0].symbolId, 5)
        self.assertEqual(self.client.sent[0].period, "M1")
        total = len(pretend.jobs) + 1
        self.assertGreater(total, 3)
        for _ in range(total):
            self.reply_to_current_request(pretend)
            self.quiet(self.run_scheduled)
        self.assertFalse(self.reactor.running)
        self.assertEqual(pretend.exit_code, 0)
        stored = bar_store.load_m1("XAUUSD", self.store)
        self.assertEqual(len(stored), total * 2)
        self.assertAlmostEqual(stored.iloc[0]["low"], 2000.0, places=3)

    def test_more_bars_available_triggers_a_follow_up_request(self):
        pretend = self.make()
        self.quiet(pretend.on_message, None, symbols_message({"XAUUSD": 5}))
        request = self.client.sent[0]
        jobs_before = len(pretend.jobs)
        first_minute = request.fromTimestamp // 60000
        self.reply_to_current_request(pretend, has_more=True, count=3)
        self.assertEqual(len(pretend.jobs), jobs_before + 1)
        self.assertEqual(pretend.jobs[0]["from"], (first_minute + 3) * 60000)
        self.assertEqual(pretend.jobs[0]["to"], request.toTimestamp)

    def test_an_error_saves_what_was_downloaded_and_stops(self):
        pretend = self.make()
        self.quiet(pretend.on_message, None, symbols_message({"XAUUSD": 5}))
        self.reply_to_current_request(pretend, count=4)
        output = self.quiet(pretend.on_message, None, message(PAYLOAD.PROTO_OA_ERROR_RES, description="boom"))
        self.assertIn("boom", output)
        self.assertEqual(pretend.exit_code, 1)
        self.assertFalse(self.reactor.running)
        self.assertEqual(len(bar_store.load_m1("XAUUSD", self.store)), 4)

    def test_a_missing_instrument_is_reported_with_the_map_hint(self):
        pretend = self.make(wanted=("DAX",))
        output = self.quiet(pretend.on_message, None, symbols_message({"AUDCAD": 6}))
        self.assertIn("NOT FOUND", output)
        self.assertIn("--map DAX=", output)
        self.assertEqual(pretend.exit_code, 1)
        self.assertEqual(self.client.sent, [])

    def test_rerunning_continues_from_the_newest_stored_candle(self):
        newest = pd.Timestamp.now(tz="UTC").floor("min") - pd.Timedelta(hours=2)
        stored = pd.DataFrame(
            [{"time": newest, "open": 2000.0, "high": 2001.0, "low": 1999.0, "close": 2000.5, "volume": 5.0}]
        )
        bar_store.merge_m1("XAUUSD", stored, store_dir=self.store)
        again = self.make(years=3)
        self.quiet(again.on_message, None, symbols_message({"XAUUSD": 5}))
        # One day before the newest candle up to now is about 1.1 days: a single request.
        self.assertEqual(len(self.client.sent), 1)
        self.assertEqual(again.jobs, [])
        expected_start = int((newest - pd.Timedelta(days=1)).timestamp() * 1000)
        self.assertEqual(self.client.sent[0].fromTimestamp, expected_start)

    def test_symbols_command_lists_likely_names_only(self):
        pretend = self.make(mode="symbols", wanted=("DAX", "XAUUSD"))
        output = self.quiet(pretend.on_message, None, symbols_message({"GER40": 1, "GOLD": 2, "AUDCAD": 3, "BTCUSD": 4}))
        self.assertIn("GER40", output)
        self.assertIn("GOLD", output)
        self.assertNotIn("AUDCAD", output.split("Broker symbols")[1])
        self.assertEqual(pretend.exit_code, 0)
        self.assertEqual(self.client.sent, [])

    def test_symbols_command_can_list_everything(self):
        pretend = self.make(mode="symbols", wanted=("DAX",), show_all=True)
        output = self.quiet(pretend.on_message, None, symbols_message({"GER40": 1, "AUDCAD": 3}))
        self.assertIn("AUDCAD", output.split("Broker symbols")[1])


if __name__ == "__main__":
    unittest.main()