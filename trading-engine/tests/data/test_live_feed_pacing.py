"""Tests that the shared instruments are subscribed one after another."""

import os
import unittest
from unittest.mock import MagicMock, patch

from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOASymbolsListRes

from data.live_feed import CHILD_SUBSCRIBE_SPACING_SECONDS, LiveCTraderFeed

ENVIRONMENT = {
    "CTRADER_CLIENT_ID": "test-client",
    "CTRADER_SECRET": "test-secret",
    "CTRADER_ACCESS_TOKEN": "test-token",
    "CTRADER_ACCOUNT_ID": "123",
    "CTRADER_ENV": "demo",
}
NAMES = ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD")


def symbols_response():
    response = ProtoOASymbolsListRes()
    for number, name in enumerate(NAMES, start=1):
        item = response.symbol.add()
        item.symbolId = number
        item.symbolName = name
        item.baseAssetId = number
        item.quoteAssetId = number + 100
    return response


def build_feeds():
    with patch("data.live_feed.Client"):
        parent = LiveCTraderFeed(symbol_name=NAMES[0])
        children = [
            LiveCTraderFeed(symbol_name=name, track_account=False, parent=parent)
            for name in NAMES[1:]
        ]
    return parent, children


class PacingTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.dict(os.environ, ENVIRONMENT)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_instruments_are_spaced_when_the_reactor_runs(self):
        parent, children = build_feeds()
        client = MagicMock()
        with patch("data.live_feed.reactor") as fake_reactor:
            fake_reactor.running = True
            parent._subscribe_children_paced(client, symbols_response())

        # The first shared instrument starts at once, the others are delayed.
        self.assertIsNotNone(children[0].symbol_id)
        self.assertIsNone(children[1].symbol_id)
        self.assertIsNone(children[2].symbol_id)
        delays = [call.args[0] for call in fake_reactor.callLater.call_args_list]
        self.assertEqual(
            delays,
            [CHILD_SUBSCRIBE_SPACING_SECONDS, CHILD_SUBSCRIBE_SPACING_SECONDS * 2],
        )

    def test_everything_starts_at_once_when_the_reactor_is_not_running(self):
        parent, children = build_feeds()
        client = MagicMock()
        with patch("data.live_feed.reactor") as fake_reactor:
            fake_reactor.running = False
            parent._subscribe_children_paced(client, symbols_response())

        fake_reactor.callLater.assert_not_called()
        for child in children:
            self.assertIsNotNone(child.symbol_id)

    def test_disconnect_cancels_instruments_still_waiting(self):
        parent, _children = build_feeds()
        client = MagicMock()
        waiting_calls = []

        def fake_call_later(*_args, **_kwargs):
            call = MagicMock()
            call.active.return_value = True
            waiting_calls.append(call)
            return call

        with patch("data.live_feed.reactor") as fake_reactor:
            fake_reactor.running = True
            fake_reactor.callLater.side_effect = fake_call_later
            parent._subscribe_children_paced(client, symbols_response())

        parent._on_disconnected(None, "test disconnect")

        self.assertEqual(len(waiting_calls), 2)
        for call in waiting_calls:
            call.cancel.assert_called_once()


if __name__ == "__main__":
    unittest.main()