import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from ctrader_open_api import EndPoints

from data.live_feed import AccountFacts, BrokerSymbolInfo, Candle, LiveQuote
from data.live_feed_manager import LiveFeedManager


class LiveFeedManagerTests(unittest.TestCase):
    def test_disabled_feed_stays_disconnected_without_creating_a_client(self):
        environment = {
            "CTRADER_FEED_ENABLED": "false",
            "CTRADER_ENV": "demo",
        }
        with patch.dict(os.environ, environment, clear=True):
            with patch("data.live_feed.Client") as client_class:
                manager = LiveFeedManager()
                manager.start()

        snapshot = manager.get_snapshot()
        self.assertEqual(snapshot["connectionState"], "Disconnected")
        self.assertIn("disabled", snapshot["message"])
        client_class.assert_not_called()

    def test_live_environment_starts_data_feed_on_live_endpoint(self):
        environment = {
            "CTRADER_FEED_ENABLED": "true",
            "CTRADER_ENV": "live",
            "CTRADER_CLIENT_ID": "test-client",
            "CTRADER_SECRET": "test-secret",
            "CTRADER_ACCESS_TOKEN": "test-token",
            "CTRADER_ACCOUNT_ID": "123456",
        }
        with (
            patch.dict(os.environ, environment, clear=True),
            patch("data.live_feed.Client") as client_class,
        ):
            manager = LiveFeedManager()
            with patch.object(manager, "_run_feed") as run_feed:
                manager.start()
                manager._thread.join(timeout=1)

        snapshot = manager.get_snapshot()
        self.assertEqual(snapshot["connectionState"], "Connecting")
        self.assertEqual(snapshot["environment"], "Live")
        self.assertIn("Live market-data feed", snapshot["message"])
        self.assertEqual(client_class.call_args.args[0], EndPoints.PROTOBUF_LIVE_HOST)
        run_feed.assert_called_once()

    def test_unknown_environment_is_rejected_before_client_creation(self):
        environment = {
            "CTRADER_FEED_ENABLED": "true",
            "CTRADER_ENV": "invalid",
        }
        with patch.dict(os.environ, environment, clear=True):
            with patch("data.live_feed.Client") as client_class:
                manager = LiveFeedManager()
                manager.start()

        snapshot = manager.get_snapshot()
        self.assertEqual(snapshot["connectionState"], "Error")
        self.assertIn("CTRADER_ENV", snapshot["message"])
        client_class.assert_not_called()

    def test_missing_credentials_are_reported_without_creating_a_client(self):
        environment = {
            "CTRADER_FEED_ENABLED": "true",
            "CTRADER_ENV": "demo",
        }
        with patch.dict(os.environ, environment, clear=True):
            with patch("data.live_feed.Client") as client_class:
                manager = LiveFeedManager()
                manager.start()

        snapshot = manager.get_snapshot()
        self.assertEqual(snapshot["connectionState"], "Error")
        self.assertIn("CTRADER_CLIENT_ID", snapshot["message"])
        client_class.assert_not_called()

    def test_snapshot_contains_quote_and_only_closed_candle_data(self):
        manager = LiveFeedManager()
        quote_time = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
        candle_time = datetime(2026, 1, 5, 11, 55, tzinfo=timezone.utc)
        manager._record_feed_status("subscribed", "Receiving EURUSD data.")
        manager._record_quote(
            LiveQuote(
                symbol="EURUSD",
                time=quote_time,
                bid=1.1,
                ask=1.1001,
            )
        )
        manager._record_closed_candle(
            Candle(
                symbol="EURUSD",
                timeframe="M5",
                time=candle_time,
                open=1.1,
                high=1.101,
                low=1.099,
                close=1.1005,
                volume=10,
            )
        )

        snapshot = manager.get_snapshot()

        self.assertEqual(snapshot["connectionState"], "Connected")
        self.assertEqual(snapshot["quote"]["bid"], 1.1)
        self.assertEqual(snapshot["quote"]["time"], quote_time.isoformat())
        self.assertEqual(snapshot["lastClosedCandle"]["time"], candle_time.isoformat())
        self.assertEqual(snapshot["lastClosedCandle"]["timeframe"], "M5")

    def test_account_facts_snapshot_contains_broker_values_and_calculation_note(self):
        manager = LiveFeedManager()
        observed_at = datetime.now(timezone.utc)
        facts = AccountFacts(
            account_id=123456,
            observed_at=observed_at,
            balance_received_at=observed_at,
            unrealized_pnl_received_at=observed_at,
            balance=100.0,
            net_unrealized_pnl=1.5,
            equity=101.5,
            leverage=50.0,
            deposit_asset_id=1,
            equity_calculation="balance + net unrealized PnL",
            equity_note="Potential closing commissions are excluded.",
        )

        manager._record_account_facts(facts)
        snapshot = manager.get_account_facts()

        self.assertEqual(snapshot["accountId"], 123456)
        self.assertEqual(snapshot["equity"], 101.5)
        self.assertEqual(snapshot["leverage"], 50.0)
        self.assertEqual(snapshot["equityCalculation"], "balance + net unrealized PnL")

    def test_disconnecting_clears_account_facts(self):
        manager = LiveFeedManager()
        facts = AccountFacts(
            account_id=123456,
            observed_at=datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc),
            balance_received_at=datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc),
            unrealized_pnl_received_at=datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc),
            balance=100.0,
            net_unrealized_pnl=1.5,
            equity=101.5,
            leverage=50.0,
            deposit_asset_id=1,
            equity_calculation="balance + net unrealized PnL",
            equity_note="Potential closing commissions are excluded.",
        )
        manager._record_account_facts(facts)

        manager._record_feed_status("disconnected", "cTrader disconnected.")

        self.assertIsNone(manager.get_account_facts())

    def test_account_facts_older_than_two_refresh_intervals_are_unavailable(self):
        manager = LiveFeedManager()
        observed_at = datetime.now(timezone.utc) - timedelta(minutes=2)
        manager._record_account_facts(
            AccountFacts(
                account_id=123456,
                observed_at=observed_at,
                balance_received_at=observed_at,
                unrealized_pnl_received_at=observed_at,
                balance=100.0,
                net_unrealized_pnl=1.5,
                equity=101.5,
                leverage=50.0,
                deposit_asset_id=1,
                equity_calculation="balance + net unrealized PnL",
                equity_note="Potential closing commissions are excluded.",
            )
        )

        self.assertIsNone(manager.get_account_facts())

    def test_broker_symbol_info_is_stored_and_cleared_on_disconnect(self):
        manager = LiveFeedManager()
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
        )

        manager._record_symbol_info(symbol_info)
        self.assertEqual(manager.get_symbol_info(), symbol_info)

        manager._record_feed_status("disconnected", "cTrader disconnected.")
        self.assertIsNone(manager.get_symbol_info())


if __name__ == "__main__":
    unittest.main()
