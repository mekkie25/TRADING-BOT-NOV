import unittest
from unittest.mock import patch

from fastapi import HTTPException

from data.live_feed import BrokerSymbolInfo
from api import (
    LotSizingRequest,
    get_account_summary,
    get_account_facts,
    get_equity_curve,
    get_live_lot_size,
    get_live_market_data,
    get_open_positions,
    get_settings,
)


class LiveFeedApiTests(unittest.TestCase):
    def test_live_market_endpoint_returns_the_feed_snapshot(self):
        snapshot = {
            "connectionState": "Disconnected",
            "environment": "Demo",
            "symbol": "EURUSD",
            "message": "Feed disabled by configuration.",
            "quote": None,
            "lastClosedCandle": None,
        }
        with patch("api.live_feed_manager.get_snapshot", return_value=snapshot):
            self.assertEqual(get_live_market_data(), snapshot)

    def test_settings_uses_the_feed_connection_state(self):
        snapshot = {"connectionState": "Connected"}
        with patch("api.live_feed_manager.get_snapshot", return_value=snapshot):
            self.assertEqual(get_settings()["broker"]["connectionState"], "Connected")

    def test_account_summary_does_not_return_sample_values_as_broker_facts(self):
        with self.assertRaises(HTTPException) as error:
            get_account_summary()

        self.assertEqual(error.exception.status_code, 503)
        self.assertIn("unavailable", error.exception.detail)

    def test_account_facts_endpoint_returns_only_available_feed_snapshot(self):
        facts = {"balance": 100.0, "equity": 101.5, "leverage": 50.0}
        with patch("api.live_feed_manager.get_account_facts", return_value=facts):
            self.assertEqual(get_account_facts(), facts)

        with patch("api.live_feed_manager.get_account_facts", return_value=None):
            with self.assertRaises(HTTPException) as error:
                get_account_facts()
        self.assertEqual(error.exception.status_code, 503)

    def test_live_lot_sizing_uses_fresh_account_and_symbol_facts(self):
        account_facts = {"equity": 10000.0, "depositAssetId": 2}
        symbol_info = BrokerSymbolInfo(
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
            maximum_exposure_cents=None,
        )
        request = LotSizingRequest(
            entryPrice=1.1,
            stopLossPrice=1.09,
            riskPercent=1.0,
        )
        with (
            patch(
                "api.live_feed_manager.get_account_facts",
                return_value=account_facts,
            ),
            patch(
                "api.live_feed_manager.get_symbol_info",
                return_value=symbol_info,
            ),
        ):
            report = get_live_lot_size(request)

        self.assertEqual(report["volume_units"], 10000)
        self.assertEqual(report["lots"], 0.1)
        self.assertEqual(report["planned_loss_cash"], 100.0)

    def test_live_lot_sizing_is_unavailable_without_broker_facts(self):
        with (
            patch("api.live_feed_manager.get_account_facts", return_value=None),
            patch("api.live_feed_manager.get_symbol_info", return_value=None),
        ):
            with self.assertRaises(HTTPException) as error:
                get_live_lot_size(
                    LotSizingRequest(
                        entryPrice=1.1,
                        stopLossPrice=1.09,
                        riskPercent=1.0,
                    )
                )

        self.assertEqual(error.exception.status_code, 503)
        self.assertIn("complete symbol specifications", error.exception.detail)

    def test_account_history_and_positions_do_not_claim_empty_sample_data(self):
        for endpoint in (get_equity_curve, get_open_positions):
            with self.subTest(endpoint=endpoint.__name__):
                with self.assertRaises(HTTPException) as error:
                    endpoint()
                self.assertEqual(error.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
