"""Owns the cTrader feed lifecycle and exposes thread-safe market snapshots."""

import logging
import os
from datetime import datetime, timedelta, timezone
from threading import Event, Lock, Thread
from typing import Optional

from twisted.internet import reactor
from twisted.internet.defer import maybeDeferred

from data.live_feed import (
    ACCOUNT_FACTS_REFRESH_SECONDS,
    AccountFacts,
    BrokerSymbolInfo,
    Candle,
    LiveCTraderFeed,
    LiveQuote,
)

logger = logging.getLogger(__name__)
ACCOUNT_FACTS_MAX_AGE_SECONDS = ACCOUNT_FACTS_REFRESH_SECONDS * 2


class LiveFeedManager:
    def __init__(self) -> None:
        configured_environment = os.getenv("CTRADER_ENV", "demo").strip().lower()
        self._environment = (
            configured_environment.title()
            if configured_environment in ("demo", "live")
            else "Unknown"
        )
        self._lock = Lock()
        self._reactor_ready = Event()
        self._connection_state = "Disconnected"
        self._message = "The cTrader feed has not started."
        self._last_quote: Optional[LiveQuote] = None
        self._last_closed_candle: Optional[Candle] = None
        self._account_facts: Optional[AccountFacts] = None
        self._symbol_info: Optional[BrokerSymbolInfo] = None
        self._feed: Optional[LiveCTraderFeed] = None
        self._thread: Optional[Thread] = None
        self._start_attempted = False

    def start(self) -> None:
        with self._lock:
            if self._start_attempted:
                return
            self._start_attempted = True

        enabled = os.getenv("CTRADER_FEED_ENABLED", "true").strip().lower()
        if enabled == "false":
            self._set_status("Disconnected", "cTrader feed disabled by configuration.")
            return
        if enabled != "true":
            self._set_status(
                "Error",
                "CTRADER_FEED_ENABLED must be either 'true' or 'false'.",
            )
            return
        if self._environment == "Unknown":
            self._set_status(
                "Error",
                "CTRADER_ENV must be either 'demo' or 'live'.",
            )
            return

        try:
            feed = LiveCTraderFeed(
                symbol_name="EURUSD",
                on_quote=self._record_quote,
                on_closed_candle=self._record_closed_candle,
                on_account_facts=self._record_account_facts,
                on_symbol_info=self._record_symbol_info,
                on_status=self._record_feed_status,
            )
        except ValueError as error:
            self._set_status("Error", str(error))
            return

        thread = Thread(
            target=self._run_feed,
            args=(feed,),
            name=f"ctrader-{self._environment.lower()}-feed",
            daemon=True,
        )
        with self._lock:
            self._feed = feed
            self._thread = thread
            self._connection_state = "Connecting"
            self._message = f"Starting the cTrader {self._environment} market-data feed."
        thread.start()

    def stop(self) -> None:
        with self._lock:
            feed = self._feed
            thread = self._thread
        if feed is None or thread is None or not thread.is_alive():
            return
        if not self._reactor_ready.wait(timeout=5):
            self._set_status("Error", "The cTrader feed reactor did not become ready.")
            return

        def stop_feed() -> None:
            maybeDeferred(feed.client.stopService).addBoth(
                lambda result: self._stop_reactor(result)
            )

        reactor.callFromThread(stop_feed)
        thread.join(timeout=5)

    def get_snapshot(self) -> dict:
        with self._lock:
            quote = self._last_quote
            candle = self._last_closed_candle
            return {
                "connectionState": self._connection_state,
                "environment": self._environment,
                "symbol": "EURUSD",
                "message": self._message,
                "quote": (
                    {
                        "symbol": quote.symbol,
                        "time": quote.time.isoformat(),
                        "bid": quote.bid,
                        "ask": quote.ask,
                    }
                    if quote is not None
                    else None
                ),
                "lastClosedCandle": (
                    {
                        "symbol": candle.symbol,
                        "timeframe": candle.timeframe,
                        "time": candle.time.isoformat(),
                        "open": candle.open,
                        "high": candle.high,
                        "low": candle.low,
                        "close": candle.close,
                        "volume": candle.volume,
                    }
                    if candle is not None
                    else None
                ),
            }

    def get_account_facts(self) -> Optional[dict]:
        with self._lock:
            facts = self._account_facts
        if facts is None:
            return None
        oldest_received_at = min(
            facts.balance_received_at,
            facts.unrealized_pnl_received_at,
        )
        if (
            datetime.now(timezone.utc) - oldest_received_at
            > timedelta(seconds=ACCOUNT_FACTS_MAX_AGE_SECONDS)
        ):
            return None

        return {
            "accountId": facts.account_id,
            "observedAt": facts.observed_at.isoformat(),
            "balanceReceivedAt": facts.balance_received_at.isoformat(),
            "unrealizedPnlReceivedAt": facts.unrealized_pnl_received_at.isoformat(),
            "balance": facts.balance,
            "netUnrealizedPnl": facts.net_unrealized_pnl,
            "equity": facts.equity,
            "leverage": facts.leverage,
            "depositAssetId": facts.deposit_asset_id,
            "equityCalculation": facts.equity_calculation,
            "equityNote": facts.equity_note,
        }

    def get_symbol_info(self) -> Optional[BrokerSymbolInfo]:
        with self._lock:
            return self._symbol_info

    def _run_feed(self, feed: LiveCTraderFeed) -> None:
        reactor.callWhenRunning(self._reactor_ready.set)
        try:
            feed.start(install_signal_handlers=False)
        except RuntimeError as error:
            self._set_status("Error", f"Could not run the cTrader feed: {error}")

    def _record_feed_status(self, state: str, message: str) -> None:
        if state == "warning":
            with self._lock:
                self._message = message
            return

        if state == "subscribed":
            connection_state = "Connected"
        elif state in ("connecting", "connected", "authenticated", "subscribing"):
            connection_state = "Connecting"
        elif state == "error":
            connection_state = "Error"
        else:
            connection_state = "Disconnected"
        if connection_state in ("Error", "Disconnected"):
            with self._lock:
                self._account_facts = None
                self._symbol_info = None
        self._set_status(connection_state, message)

    def _record_quote(self, quote: LiveQuote) -> None:
        with self._lock:
            self._last_quote = quote

    def _record_closed_candle(self, candle: Candle) -> None:
        with self._lock:
            self._last_closed_candle = candle

    def _record_account_facts(self, facts: AccountFacts) -> None:
        with self._lock:
            self._account_facts = facts

    def _record_symbol_info(
        self,
        symbol_info: Optional[BrokerSymbolInfo],
    ) -> None:
        with self._lock:
            self._symbol_info = symbol_info

    def _set_status(self, state: str, message: str) -> None:
        if state == "Error":
            logger.error(message)
        else:
            logger.info(message)
        with self._lock:
            self._connection_state = state
            self._message = message

    @staticmethod
    def _stop_reactor(result):
        if reactor.running:
            reactor.stop()
        return result


live_feed_manager = LiveFeedManager()
