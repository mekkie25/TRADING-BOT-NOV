import os
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAAccountAuthRes,
    ProtoOASpotEvent,
    ProtoOASymbolsListRes,
)

from data.live_feed import LiveCTraderFeed
from data.live_feed_hub import WATCHED_INSTRUMENTS, LiveFeedHub
from data.live_feed_manager import LiveFeedManager


def valid_environment(**extra):
    environment = {
        "CTRADER_CLIENT_ID": "test-client",
        "CTRADER_SECRET": "test-secret",
        "CTRADER_ACCESS_TOKEN": "test-token",
        "CTRADER_ACCOUNT_ID": "123456",
        "CTRADER_ENV": "demo",
    }
    environment.update(extra)
    return environment


def make_message(event):
    event.ctidTraderAccountId = 123456
    return SimpleNamespace(
        payloadType=event.payloadType,
        payload=event.SerializeToString(),
    )


def symbols_response(*names_and_ids):
    response = ProtoOASymbolsListRes()
    response.ctidTraderAccountId = 123456
    for name, symbol_id in names_and_ids:
        symbol = response.symbol.add()
        symbol.symbolId = symbol_id
        symbol.symbolName = name
        symbol.baseAssetId = 1
        symbol.quoteAssetId = 2
    return response


class FeedForOtherInstrumentsTests(unittest.TestCase):
    def create_feed(self, **kwargs):
        with patch.dict(os.environ, valid_environment(), clear=True):
            with patch("data.live_feed.Client") as client_class:
                feed = LiveCTraderFeed(**kwargs)
        return feed, client_class.return_value

    def test_dax_is_found_under_the_broker_name_ger40(self):
        feed, client = self.create_feed(symbol_name="DAX")
        response = symbols_response(("EURUSD", 1), ("GER40", 124))

        feed._on_message(client, make_message(response))

        self.assertEqual(feed.symbol_id, 124)

    def test_exact_broker_name_is_still_used_first(self):
        feed, client = self.create_feed(symbol_name="XAUUSD")
        response = symbols_response(("XAUEUR", 40), ("XAUUSD", 41))

        feed._on_message(client, make_message(response))

        self.assertEqual(feed.symbol_id, 41)

    def test_symbol_the_broker_does_not_have_is_reported_as_an_error(self):
        statuses = []
        feed, client = self.create_feed(
            symbol_name="DAX",
            on_status=lambda state, message: statuses.append((state, message)),
        )
        response = symbols_response(("EURUSD", 1))

        feed._on_message(client, make_message(response))

        self.assertIsNone(feed.symbol_id)
        self.assertEqual(statuses[-1][0], "error")
        self.assertIn("DAX", statuses[-1][1])

    def test_feed_that_does_not_track_the_account_skips_balance_requests(self):
        feed, client = self.create_feed(track_account=False)
        auth_response = ProtoOAAccountAuthRes()
        auth_response.ctidTraderAccountId = 123456

        with patch("data.live_feed.LoopingCall") as looping_call:
            feed._on_message(client, make_message(auth_response))

        sent_types = [call.args[0].DESCRIPTOR.name for call in client.send.call_args_list]
        self.assertIn("ProtoOASymbolsListReq", sent_types)
        self.assertNotIn("ProtoOATraderReq", sent_types)
        self.assertNotIn("ProtoOAGetPositionUnrealizedPnLReq", sent_types)
        looping_call.assert_not_called()

    def test_quote_carries_our_own_instrument_name(self):
        quotes = []
        feed, client = self.create_feed(symbol_name="DAX", on_quote=quotes.append)
        feed._on_message(client, make_message(symbols_response(("GER40", 124))))
        event = ProtoOASpotEvent()
        event.symbolId = 124
        event.timestamp = int(datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc).timestamp() * 1000)
        event.bid = 1800000000
        event.ask = 1800010000

        feed._on_message(client, make_message(event))

        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0].symbol, "DAX")


class LiveFeedHubTests(unittest.TestCase):
    def test_hub_covers_all_eight_instruments_and_only_one_reads_the_account(self):
        with patch.dict(os.environ, valid_environment(), clear=True):
            primary = LiveFeedManager()
            hub = LiveFeedHub(primary)

        self.assertEqual(sorted(hub.symbols), sorted(WATCHED_INSTRUMENTS))
        self.assertIs(hub.get("eurusd"), primary)
        readers = [symbol for symbol in hub.symbols if hub.get(symbol)._track_account]
        self.assertEqual(readers, ["EURUSD"])

    def test_unknown_instrument_raises_key_error(self):
        with patch.dict(os.environ, valid_environment(), clear=True):
            hub = LiveFeedHub(LiveFeedManager())

        with self.assertRaises(KeyError):
            hub.get("DOGEUSD")

    def test_each_manager_reports_its_own_instrument(self):
        with patch.dict(os.environ, valid_environment(), clear=True):
            hub = LiveFeedHub(LiveFeedManager())

        snapshots = hub.get_all_snapshots()

        self.assertEqual(set(snapshots), set(WATCHED_INSTRUMENTS))
        self.assertEqual(snapshots["DAX"]["symbol"], "DAX")
        self.assertEqual(snapshots["EURUSD"]["symbol"], "EURUSD")

    def test_disabled_feed_creates_no_clients_for_any_instrument(self):
        environment = valid_environment(CTRADER_FEED_ENABLED="false")
        with patch.dict(os.environ, environment, clear=True):
            with patch("data.live_feed.Client") as client_class:
                hub = LiveFeedHub(LiveFeedManager())
                hub.start()
                hub.stop()

        client_class.assert_not_called()
        for snapshot in hub.get_all_snapshots().values():
            self.assertEqual(snapshot["connectionState"], "Disconnected")

    def test_other_instruments_connect_through_the_shared_engine(self):
        with patch.dict(os.environ, valid_environment(), clear=True):
            with patch("data.live_feed.Client"):
                primary = LiveFeedManager()
                hub = LiveFeedHub(primary, symbols=["EURUSD", "XAUUSD"])
                with (
                    patch.object(primary, "_run_feed"),
                    patch("data.live_feed_manager.reactor") as fake_reactor,
                ):
                    primary._reactor_ready.set()
                    hub.start()
                    gold = hub.get("XAUUSD")
                    gold._thread.join(timeout=2)

        fake_reactor.callFromThread.assert_called_once()
        self.assertEqual(fake_reactor.callFromThread.call_args.args[0], gold._feed.connect)
        self.assertEqual(gold.get_snapshot()["connectionState"], "Connecting")

    def test_other_instruments_report_an_error_if_the_engine_never_starts(self):
        with patch.dict(os.environ, valid_environment(), clear=True):
            with patch("data.live_feed.Client"):
                primary = LiveFeedManager()
                gold = LiveFeedManager(symbol_name="XAUUSD", track_account=False)
                with patch("data.live_feed_manager.SHARED_REACTOR_WAIT_SECONDS", 0.05):
                    gold.start_attached(primary)
                    gold._thread.join(timeout=2)

        self.assertEqual(gold.get_snapshot()["connectionState"], "Error")


if __name__ == "__main__":
    unittest.main()