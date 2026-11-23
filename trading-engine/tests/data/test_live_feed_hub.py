import os
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAAccountAuthRes,
    ProtoOAApplicationAuthRes,
    ProtoOAErrorRes,
    ProtoOASpotEvent,
    ProtoOASubscribeLiveTrendbarRes,
    ProtoOASubscribeSpotsRes,
    ProtoOASymbolByIdRes,
    ProtoOASymbolsListRes,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOATrendbarPeriod
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

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


def plain_message(event):
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


BROKER_SYMBOLS = (
    ("EURUSD", 1),
    ("GBPUSD", 2),
    ("USDJPY", 3),
    ("XAUUSD", 4),
    ("BTCUSD", 5),
    ("GER40", 6),
    ("US30", 7),
    ("NAS100", 8),
)
FIRST_PRICE_TIME = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)


def sent_requests(client, name):
    return [
        call.args[0]
        for call in client.send.call_args_list
        if call.args[0].DESCRIPTOR.name == name
    ]


class OneConnectionTests(unittest.TestCase):
    """All eight instruments share one cTrader connection and one login."""

    def start_hub(self, **environment):
        patcher = patch.dict(os.environ, valid_environment(**environment), clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        client_patcher = patch("data.live_feed.Client")
        self.client_class = client_patcher.start()
        self.addCleanup(client_patcher.stop)
        self.primary = LiveFeedManager()
        self.hub = LiveFeedHub(self.primary)
        with patch.object(self.primary, "_run_feed"):
            self.hub.start()
            self.primary._thread.join(timeout=1)
        self.addCleanup(self.hub.stop)
        self.feed = self.primary._feed
        self.client = self.client_class.return_value
        return self.hub

    def log_in_and_list_symbols(self, names_and_ids=BROKER_SYMBOLS):
        self.feed._on_message(self.client, plain_message(ProtoOAApplicationAuthRes()))
        self.feed._on_message(self.client, make_message(ProtoOAAccountAuthRes()))
        self.feed._on_message(self.client, make_message(symbols_response(*names_and_ids)))

    def spot_event(self, symbol_id, bid, offset_seconds=0):
        event = ProtoOASpotEvent()
        event.symbolId = symbol_id
        event.timestamp = int(
            (FIRST_PRICE_TIME + timedelta(seconds=offset_seconds)).timestamp() * 1000
        )
        event.bid = bid
        event.ask = bid + 10
        return make_message(event)

    def test_hub_covers_all_eight_instruments_and_only_one_reads_the_account(self):
        hub = self.start_hub()

        self.assertEqual(sorted(hub.symbols), sorted(WATCHED_INSTRUMENTS))
        self.assertIs(hub.get("eurusd"), self.primary)
        readers = [symbol for symbol in hub.symbols if hub.get(symbol)._track_account]
        self.assertEqual(readers, ["EURUSD"])

    def test_unknown_instrument_raises_key_error(self):
        hub = self.start_hub()

        with self.assertRaises(KeyError):
            hub.get("DOGEUSD")

    def test_starting_all_eight_instruments_creates_exactly_one_client(self):
        self.start_hub()

        self.assertEqual(self.client_class.call_count, 1)
        for symbol in WATCHED_INSTRUMENTS:
            self.assertEqual(self.hub.get(symbol).get_snapshot()["connectionState"], "Connecting")

    def test_the_application_and_the_account_log_in_only_once(self):
        self.start_hub()

        self.log_in_and_list_symbols()

        self.assertEqual(len(sent_requests(self.client, "ProtoOAAccountAuthReq")), 1)
        self.assertEqual(len(sent_requests(self.client, "ProtoOASymbolsListReq")), 1)
        self.assertEqual(len(sent_requests(self.client, "ProtoOATraderReq")), 1)

    def test_every_instrument_is_subscribed_with_quote_timestamps(self):
        self.start_hub()

        self.log_in_and_list_symbols()

        spot_requests = sent_requests(self.client, "ProtoOASubscribeSpotsReq")
        self.assertEqual(
            sorted(request.symbolId[0] for request in spot_requests),
            [1, 2, 3, 4, 5, 6, 7, 8],
        )
        self.assertTrue(all(request.subscribeToSpotTimestamp for request in spot_requests))
        trendbar_requests = sent_requests(self.client, "ProtoOASubscribeLiveTrendbarReq")
        self.assertEqual(len(trendbar_requests), 16)
        for symbol_id in range(1, 9):
            periods = {r.period for r in trendbar_requests if r.symbolId == symbol_id}
            self.assertEqual(periods, {ProtoOATrendbarPeriod.M1, ProtoOATrendbarPeriod.M5})

    def test_each_quote_goes_only_to_its_own_instrument(self):
        hub = self.start_hub()
        self.log_in_and_list_symbols()

        self.feed._on_message(self.client, self.spot_event(6, 1800000000))
        self.feed._on_message(self.client, self.spot_event(4, 200000000))

        dax = hub.get("DAX").get_snapshot()["quote"]
        gold = hub.get("XAUUSD").get_snapshot()["quote"]
        self.assertEqual(dax["symbol"], "DAX")
        self.assertEqual(dax["bid"], 18000.0)
        self.assertEqual(gold["symbol"], "XAUUSD")
        self.assertEqual(gold["bid"], 2000.0)
        self.assertIsNone(hub.get("EURUSD").get_snapshot()["quote"])
        self.assertIsNone(hub.get("US30").get_snapshot()["quote"])

    def test_a_quote_without_a_timestamp_is_still_ignored(self):
        hub = self.start_hub()
        self.log_in_and_list_symbols()
        event = ProtoOASpotEvent()
        event.symbolId = 1
        event.bid = 110000
        event.ask = 110010

        self.feed._on_message(self.client, make_message(event))

        self.assertIsNone(hub.get("EURUSD").get_snapshot()["quote"])

    def test_all_instruments_show_connected_only_after_every_subscription_is_confirmed(self):
        hub = self.start_hub()
        self.log_in_and_list_symbols()
        self.assertEqual(hub.get("DAX").get_snapshot()["connectionState"], "Connecting")

        for _ in range(23):
            self.feed._on_message(self.client, make_message(ProtoOASubscribeSpotsRes()))
        self.feed._on_message(self.client, make_message(ProtoOASubscribeLiveTrendbarRes()))
        # cTrader answers 24 times (3 for each of the 8 instruments). All 24 have arrived.
        for symbol in WATCHED_INSTRUMENTS:
            self.assertEqual(hub.get(symbol).get_snapshot()["connectionState"], "Connected")

    def test_first_real_price_marks_only_that_instrument_connected(self):
        hub = self.start_hub()
        self.log_in_and_list_symbols()

        self.feed._on_message(self.client, self.spot_event(6, 1800000000))

        self.assertEqual(hub.get("DAX").get_snapshot()["connectionState"], "Connected")
        self.assertEqual(hub.get("US30").get_snapshot()["connectionState"], "Connecting")
        self.assertEqual(hub.get("EURUSD").get_snapshot()["connectionState"], "Connecting")

    def test_a_quote_that_is_ignored_does_not_mark_the_instrument_connected(self):
        hub = self.start_hub()
        self.log_in_and_list_symbols()
        event = ProtoOASpotEvent()
        event.symbolId = 6
        event.bid = 1800000000
        event.ask = 1800010000

        self.feed._on_message(self.client, make_message(event))

        self.assertEqual(hub.get("DAX").get_snapshot()["connectionState"], "Connecting")

    def test_unanswered_subscription_names_the_instrument(self):
        self.start_hub()
        deferred = Deferred()
        self.client.send.return_value = deferred
        dax_feed = next(f for f in self.feed._group() if f.symbol_name == "DAX")
        dax_feed.symbol_id = 6

        with self.assertLogs("data.live_feed", level="WARNING") as logs:
            dax_feed._subscribe(self.client)
            deferred.errback(Failure(TimeoutError("no answer")))

        self.assertIn("ProtoOASubscribeSpotsReq for DAX", logs.output[0])

    def test_connected_is_not_reported_while_answers_are_still_missing(self):
        hub = self.start_hub()
        self.log_in_and_list_symbols()

        self.feed._on_message(self.client, make_message(ProtoOASubscribeSpotsRes()))
        self.feed._on_message(self.client, make_message(ProtoOASubscribeLiveTrendbarRes()))

        for symbol in WATCHED_INSTRUMENTS:
            self.assertEqual(hub.get(symbol).get_snapshot()["connectionState"], "Connecting")

    def test_an_instrument_the_broker_lacks_does_not_stop_the_others(self):
        hub = self.start_hub()
        without_dax = tuple(item for item in BROKER_SYMBOLS if item[0] != "GER40")

        self.log_in_and_list_symbols(without_dax)

        self.client.stopService.assert_not_called()
        self.assertEqual(hub.get("DAX").get_snapshot()["connectionState"], "Error")
        self.assertIn("DAX", hub.get("DAX").get_snapshot()["message"])
        spot_requests = sent_requests(self.client, "ProtoOASubscribeSpotsReq")
        self.assertEqual(len(spot_requests), 7)
        # 7 instruments x 3 answers = 21 answers.
        for _ in range(20):
            self.feed._on_message(self.client, make_message(ProtoOASubscribeSpotsRes()))
        self.feed._on_message(self.client, make_message(ProtoOASubscribeLiveTrendbarRes()))
        self.assertEqual(hub.get("EURUSD").get_snapshot()["connectionState"], "Connected")
        self.assertEqual(hub.get("DAX").get_snapshot()["connectionState"], "Error")

    def test_a_symbol_details_reply_for_one_instrument_is_not_an_error_for_the_others(self):
        hub = self.start_hub()
        self.log_in_and_list_symbols()
        details = ProtoOASymbolByIdRes()
        details.ctidTraderAccountId = 123456
        symbol = details.symbol.add()
        symbol.symbolId = 6
        symbol.digits = 2
        symbol.pipPosition = 1
        symbol.lotSize = 100
        symbol.minVolume = 1
        symbol.stepVolume = 1
        symbol.maxVolume = 1000

        self.feed._on_message(self.client, make_message(details))

        self.assertIsNotNone(hub.get("DAX").get_symbol_info())
        self.assertEqual(hub.get("DAX").get_symbol_info().symbol, "DAX")
        self.assertIsNone(hub.get("EURUSD").get_symbol_info())
        self.assertNotIn("specifications", hub.get("EURUSD").get_snapshot()["message"])

    def test_a_connection_error_is_shown_for_every_instrument(self):
        hub = self.start_hub()
        error = ProtoOAErrorRes()
        error.errorCode = "ALREADY_LOGGED_IN"
        error.description = "Trading account is already authorized in this channel"

        self.feed._on_message(self.client, make_message(error))

        for symbol in WATCHED_INSTRUMENTS:
            snapshot = hub.get(symbol).get_snapshot()
            self.assertEqual(snapshot["connectionState"], "Error")
            self.assertIn("already authorized", snapshot["message"])

    def test_disconnect_clears_every_instrument(self):
        hub = self.start_hub()
        self.log_in_and_list_symbols()
        self.feed._on_message(self.client, self.spot_event(6, 1800000000))

        self.feed._on_disconnected(self.client, "test disconnect")

        for symbol in WATCHED_INSTRUMENTS:
            self.assertEqual(hub.get(symbol).get_snapshot()["connectionState"], "Disconnected")
        for feed in self.feed._group():
            self.assertIsNone(feed._latest_bid)

    def test_a_request_that_gets_no_answer_is_logged_not_left_unhandled(self):
        self.start_hub()
        deferred = Deferred()
        self.client.send.return_value = deferred

        with self.assertLogs("data.live_feed", level="WARNING") as logs:
            self.feed._send(self.client, ProtoOAAccountAuthRes())
            deferred.errback(Failure(TimeoutError("no answer")))

        self.assertIn("did not answer", logs.output[0])

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
            self.assertIn("disabled", snapshot["message"])

    def test_missing_credentials_are_shown_for_every_instrument(self):
        with patch.dict(os.environ, {"CTRADER_ENV": "demo"}, clear=True):
            with patch("data.live_feed.Client") as client_class:
                hub = LiveFeedHub(LiveFeedManager())
                hub.start()

        client_class.assert_not_called()
        for snapshot in hub.get_all_snapshots().values():
            self.assertEqual(snapshot["connectionState"], "Error")
            self.assertIn("CTRADER_CLIENT_ID", snapshot["message"])

    def test_each_manager_reports_its_own_instrument(self):
        with patch.dict(os.environ, valid_environment(), clear=True):
            hub = LiveFeedHub(LiveFeedManager())

        snapshots = hub.get_all_snapshots()

        self.assertEqual(set(snapshots), set(WATCHED_INSTRUMENTS))
        self.assertEqual(snapshots["DAX"]["symbol"], "DAX")
        self.assertEqual(snapshots["EURUSD"]["symbol"], "EURUSD")


if __name__ == "__main__":
    unittest.main()