import os
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from ctrader_open_api import EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAAccountAuthRes,
    ProtoOAGetPositionUnrealizedPnLRes,
    ProtoOASpotEvent,
    ProtoOASymbolByIdRes,
    ProtoOASymbolChangedEvent,
    ProtoOASymbolsListRes,
    ProtoOATraderRes,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOATrendbarPeriod

from data.live_feed import (
    ACCOUNT_FACTS_REFRESH_SECONDS,
    BrokerSymbolInfo,
    LiveCTraderFeed,
)


def valid_environment():
    return {
        "CTRADER_CLIENT_ID": "test-client",
        "CTRADER_SECRET": "test-secret",
        "CTRADER_ACCESS_TOKEN": "test-token",
        "CTRADER_ACCOUNT_ID": "123456",
    }


def make_message(event):
    event.ctidTraderAccountId = 123456
    return SimpleNamespace(
        payloadType=event.payloadType,
        payload=event.SerializeToString(),
    )


class LiveCTraderFeedTests(unittest.TestCase):
    def create_feed(self, **callbacks):
        with patch.dict(os.environ, valid_environment(), clear=True):
            with patch("data.live_feed.Client") as client_class:
                feed = LiveCTraderFeed(**callbacks)
        return feed, client_class.return_value

    def make_bar_event(self, candle_time):
        event = ProtoOASpotEvent()
        event.symbolId = 7
        trendbar = event.trendbar.add()
        trendbar.period = ProtoOATrendbarPeriod.M5
        trendbar.utcTimestampInMinutes = int(candle_time.timestamp() // 60)
        trendbar.low = 110000
        trendbar.deltaOpen = 100
        trendbar.deltaHigh = 300
        trendbar.deltaClose = 200
        trendbar.volume = 10
        return event

    def test_requires_project_secret_name_and_does_not_create_client(self):
        environment = valid_environment()
        environment.pop("CTRADER_SECRET")
        environment["CTRADER_CLIENT_SECRET"] = "legacy-secret-name"
        with patch.dict(os.environ, environment, clear=True):
            with patch("data.live_feed.Client") as client_class:
                with self.assertRaisesRegex(ValueError, "CTRADER_SECRET"):
                    LiveCTraderFeed()
        client_class.assert_not_called()

    def test_defaults_to_demo_and_rejects_unknown_environment(self):
        with patch.dict(os.environ, valid_environment(), clear=True):
            with patch("data.live_feed.Client") as client_class:
                LiveCTraderFeed()
        self.assertEqual(client_class.call_args.args[0], EndPoints.PROTOBUF_DEMO_HOST)

        environment = valid_environment()
        environment["CTRADER_ENV"] = "demoo"
        with patch.dict(os.environ, environment, clear=True):
            with patch("data.live_feed.Client") as client_class:
                with self.assertRaisesRegex(ValueError, "CTRADER_ENV"):
                    LiveCTraderFeed()
        client_class.assert_not_called()

    def test_emits_utc_bid_ask_quote_and_uses_last_unchanged_side(self):
        quotes = []
        feed, _ = self.create_feed(on_quote=quotes.append)
        feed.symbol_id = 7
        quote_time = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)

        event = ProtoOASpotEvent()
        event.symbolId = 7
        event.timestamp = int(quote_time.timestamp() * 1000)
        event.bid = 110000
        event.ask = 110010
        feed._on_message(None, make_message(event))

        next_event = ProtoOASpotEvent()
        next_event.symbolId = 7
        next_event.timestamp = int((quote_time + timedelta(seconds=1)).timestamp() * 1000)
        next_event.ask = 110020
        feed._on_message(None, make_message(next_event))

        self.assertEqual(len(quotes), 2)
        self.assertEqual(quotes[0].time, quote_time)
        self.assertEqual(quotes[0].bid, 1.1)
        self.assertEqual(quotes[0].ask, 1.1001)
        self.assertEqual(quotes[1].bid, 1.1)
        self.assertEqual(quotes[1].ask, 1.1002)

    def test_emits_only_the_previous_m5_candle_after_a_new_one_starts(self):
        closed_candles = []
        feed, _ = self.create_feed(on_closed_candle=closed_candles.append)
        feed.symbol_id = 7
        first_candle_time = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)

        feed._on_message(None, make_message(self.make_bar_event(first_candle_time)))
        self.assertEqual(closed_candles, [])

        feed._on_message(
            None,
            make_message(self.make_bar_event(first_candle_time + timedelta(minutes=5))),
        )

        self.assertEqual(len(closed_candles), 1)
        self.assertEqual(closed_candles[0].time, first_candle_time)
        self.assertEqual(closed_candles[0].time.tzinfo, timezone.utc)
        self.assertEqual(closed_candles[0].open, 1.101)
        self.assertEqual(closed_candles[0].high, 1.103)
        self.assertEqual(closed_candles[0].low, 1.1)
        self.assertEqual(closed_candles[0].close, 1.102)

    def test_disconnect_discards_unfinished_candle(self):
        closed_candles = []
        feed, client = self.create_feed(on_closed_candle=closed_candles.append)
        feed.symbol_id = 7
        first_candle_time = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
        feed._on_message(None, make_message(self.make_bar_event(first_candle_time)))

        feed._on_disconnected(client, "test disconnect")
        feed._on_message(
            None,
            make_message(self.make_bar_event(first_candle_time + timedelta(minutes=5))),
        )

        self.assertEqual(closed_candles, [])

    def test_account_auth_requests_balance_leverage_and_unrealized_pnl(self):
        feed, client = self.create_feed()
        auth_response = ProtoOAAccountAuthRes()
        auth_response.ctidTraderAccountId = 123456

        with patch("data.live_feed.LoopingCall") as looping_call:
            feed._on_message(client, make_message(auth_response))

        sent_types = [call.args[0].DESCRIPTOR.name for call in client.send.call_args_list]
        self.assertIn("ProtoOATraderReq", sent_types)
        self.assertIn("ProtoOAGetPositionUnrealizedPnLReq", sent_types)
        looping_call.return_value.start.assert_called_once_with(
            ACCOUNT_FACTS_REFRESH_SECONDS,
            now=False,
        )
        feed._on_disconnected(client, "test disconnect")
        looping_call.return_value.stop.assert_called_once()

    def test_account_facts_scale_money_leverage_and_calculate_equity(self):
        facts = []
        feed, _ = self.create_feed(on_account_facts=facts.append)
        feed._pending_account_responses = {"trader", "position_pnl"}

        trader_response = ProtoOATraderRes()
        trader_response.ctidTraderAccountId = 123456
        trader_response.trader.ctidTraderAccountId = 123456
        trader_response.trader.balance = 10053099944
        trader_response.trader.moneyDigits = 8
        trader_response.trader.depositAssetId = 1
        trader_response.trader.leverageInCents = 5000
        feed._on_message(None, make_message(trader_response))

        pnl_response = ProtoOAGetPositionUnrealizedPnLRes()
        pnl_response.ctidTraderAccountId = 123456
        pnl_response.moneyDigits = 8
        pnl_response.positionUnrealizedPnL.add(
            positionId=10,
            grossUnrealizedPnL=20000000,
            netUnrealizedPnL=15000000,
        )
        feed._on_message(None, make_message(pnl_response))

        self.assertEqual(len(facts), 1)
        self.assertAlmostEqual(facts[0].balance, 100.53099944)
        self.assertAlmostEqual(facts[0].net_unrealized_pnl, 0.15)
        self.assertAlmostEqual(facts[0].equity, 100.68099944)
        self.assertEqual(facts[0].leverage, 50)
        self.assertEqual(facts[0].deposit_asset_id, 1)
        self.assertIn("does not include potential closing commissions", facts[0].equity_note)

    def test_account_facts_wait_for_both_responses_and_ignore_other_accounts(self):
        facts = []
        feed, _ = self.create_feed(on_account_facts=facts.append)
        feed._pending_account_responses = {"trader", "position_pnl"}

        other_account = ProtoOATraderRes()
        other_account.ctidTraderAccountId = 999
        other_account.trader.ctidTraderAccountId = 999
        other_account.trader.balance = 10000
        other_account.trader.moneyDigits = 2
        other_account.trader.depositAssetId = 1
        feed._on_message(None, make_message(other_account))
        self.assertEqual(facts, [])

        trader_response = ProtoOATraderRes()
        trader_response.ctidTraderAccountId = 123456
        trader_response.trader.ctidTraderAccountId = 123456
        trader_response.trader.balance = 10000
        trader_response.trader.moneyDigits = 2
        trader_response.trader.depositAssetId = 1
        feed._on_message(None, make_message(trader_response))
        self.assertEqual(facts, [])

        pnl_response = ProtoOAGetPositionUnrealizedPnLRes()
        pnl_response.ctidTraderAccountId = 123456
        pnl_response.moneyDigits = 2
        feed._on_message(None, make_message(pnl_response))
        self.assertEqual(len(facts), 1)
        self.assertIsNone(facts[0].leverage)

    def test_account_facts_are_not_published_without_money_digits(self):
        facts = []
        feed, _ = self.create_feed(on_account_facts=facts.append)
        feed._pending_account_responses = {"trader", "position_pnl"}

        trader_response = ProtoOATraderRes()
        trader_response.ctidTraderAccountId = 123456
        trader_response.trader.ctidTraderAccountId = 123456
        trader_response.trader.balance = 10000
        trader_response.trader.depositAssetId = 1
        feed._on_message(None, make_message(trader_response))

        pnl_response = ProtoOAGetPositionUnrealizedPnLRes()
        pnl_response.ctidTraderAccountId = 123456
        pnl_response.moneyDigits = 2
        feed._on_message(None, make_message(pnl_response))

        self.assertEqual(facts, [])

    def test_requests_and_reports_full_broker_symbol_specifications(self):
        symbol_info = []
        feed, client = self.create_feed(on_symbol_info=symbol_info.append)

        symbols_response = ProtoOASymbolsListRes()
        symbols_response.ctidTraderAccountId = 123456
        light_symbol = symbols_response.symbol.add()
        light_symbol.symbolId = 7
        light_symbol.symbolName = "EURUSD"
        light_symbol.baseAssetId = 1
        light_symbol.quoteAssetId = 2
        feed._on_message(client, make_message(symbols_response))

        requests = [
            call.args[0].DESCRIPTOR.name for call in client.send.call_args_list
        ]
        self.assertIn("ProtoOASymbolByIdReq", requests)

        details_response = ProtoOASymbolByIdRes()
        details_response.ctidTraderAccountId = 123456
        symbol = details_response.symbol.add()
        symbol.symbolId = 7
        symbol.digits = 5
        symbol.pipPosition = 4
        symbol.lotSize = 10000000
        symbol.minVolume = 100000
        symbol.stepVolume = 100000
        symbol.maxVolume = 50000000
        feed._on_message(client, make_message(details_response))

        self.assertEqual(len(symbol_info), 1)
        self.assertEqual(symbol_info[0].symbol, "EURUSD")
        self.assertEqual(symbol_info[0].base_asset_id, 1)
        self.assertEqual(symbol_info[0].quote_asset_id, 2)
        self.assertEqual(symbol_info[0].lot_size_cents, 10000000)
        self.assertEqual(symbol_info[0].minimum_volume_cents, 100000)
        self.assertEqual(symbol_info[0].volume_step_cents, 100000)
        self.assertEqual(symbol_info[0].maximum_volume_cents, 50000000)
        self.assertIsNone(symbol_info[0].maximum_exposure_cents)

    def test_symbol_change_invalidates_old_spec_and_requests_updated_details(self):
        symbol_info = []
        feed, client = self.create_feed(on_symbol_info=symbol_info.append)
        feed.symbol_id = 7
        feed._base_asset_id = 1
        feed._quote_asset_id = 2
        feed.on_symbol_info(
            BrokerSymbolInfo(
                symbol="EURUSD",
                symbol_id=7,
                base_asset_id=1,
                quote_asset_id=2,
                digits=5,
                pip_position=4,
                lot_size_cents=10000000,
                minimum_volume_cents=100000,
                volume_step_cents=100000,
                maximum_volume_cents=50000000,
            )
        )
        changed_event = ProtoOASymbolChangedEvent()
        changed_event.ctidTraderAccountId = 123456
        changed_event.symbolId.append(7)

        feed._on_message(client, make_message(changed_event))

        self.assertIsNone(symbol_info[-1])
        self.assertEqual(
            client.send.call_args.args[0].DESCRIPTOR.name,
            "ProtoOASymbolByIdReq",
        )


if __name__ == "__main__":
    unittest.main()
