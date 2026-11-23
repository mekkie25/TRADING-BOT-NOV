"""Owns the cTrader feed lifecycle and exposes thread-safe market snapshots."""

import logging
import os
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
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
from market.market_snapshot import build_market_snapshot

logger = logging.getLogger(__name__)
ACCOUNT_FACTS_MAX_AGE_SECONDS = ACCOUNT_FACTS_REFRESH_SECONDS * 2
CANDLE_HISTORY_LIMIT = 10_080


class LiveFeedManager:
    def __init__(self, symbol_name: str = "EURUSD", track_account: bool = True) -> None:
        if not symbol_name or not symbol_name.strip():
            raise ValueError("symbol_name must not be empty.")
        self._symbol_name = symbol_name.strip().upper()
        self._track_account = track_account
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
        self._closed_candles = {
            timeframe: deque(maxlen=CANDLE_HISTORY_LIMIT)
            for timeframe in ("M1", "M5")
        }
        self._market_snapshot: Optional[dict] = None
        self._market_snapshot_error: Optional[str] = None
        self._market_snapshot_executor: Optional[ThreadPoolExecutor] = None
        self._market_snapshot_update_complete = Event()
        self._account_facts: Optional[AccountFacts] = None
        self._symbol_info: Optional[BrokerSymbolInfo] = None
        self._feed: Optional[LiveCTraderFeed] = None
        self._thread: Optional[Thread] = None
        self._start_attempted = False
        self._shared_managers: list["LiveFeedManager"] = []

    @property
    def symbol_name(self) -> str:
        return self._symbol_name

    def share_connection_with(self, other: "LiveFeedManager") -> None:
        """Let another instrument ride on this manager's cTrader connection.

        Call this before start(). cTrader allows one login per account, so every
        instrument uses the connection of the manager that is started.
        """
        if other is not self and other not in self._shared_managers:
            self._shared_managers.append(other)

    def _prepare_feed(self, parent: Optional[LiveCTraderFeed] = None) -> Optional[LiveCTraderFeed]:
        """Check the settings and build the feed. Returns None when it cannot or must not start."""
        with self._lock:
            if self._start_attempted:
                return None
            self._start_attempted = True

        enabled = os.getenv("CTRADER_FEED_ENABLED", "true").strip().lower()
        if enabled == "false":
            self._set_status("Disconnected", "cTrader feed disabled by configuration.")
            return None
        if enabled != "true":
            self._set_status(
                "Error",
                "CTRADER_FEED_ENABLED must be either 'true' or 'false'.",
            )
            return None
        if self._environment == "Unknown":
            self._set_status(
                "Error",
                "CTRADER_ENV must be either 'demo' or 'live'.",
            )
            return None

        try:
            return LiveCTraderFeed(
                symbol_name=self._symbol_name,
                on_quote=self._record_quote,
                on_closed_candle=self._record_closed_candle,
                on_account_facts=self._record_account_facts,
                on_symbol_info=self._record_symbol_info,
                on_status=self._record_feed_status,
                track_account=self._track_account,
                parent=parent,
            )
        except ValueError as error:
            self._set_status("Error", str(error))
            return None

    def start(self) -> None:
        """Start this feed and run the Twisted reactor on its own thread."""
        feed = self._prepare_feed()
        if feed is None:
            # Nothing runs, so the shared instruments show the same reason.
            with self._lock:
                state, message = self._connection_state, self._message
            for other in self._shared_managers:
                other._set_status(state, message)
            return
        for other in self._shared_managers:
            other._join_connection(feed)

        thread = Thread(
            target=self._run_feed,
            args=(feed,),
            name=f"ctrader-{self._environment.lower()}-{self._symbol_name}-feed",
            daemon=True,
        )
        with self._lock:
            self._feed = feed
            self._thread = thread
            self._connection_state = "Connecting"
            self._message = f"Starting the cTrader {self._environment} market-data feed."
        thread.start()

    def _join_connection(self, parent: LiveCTraderFeed) -> None:
        """Use the connection of another manager's feed. No thread and no login of its own."""
        feed = self._prepare_feed(parent=parent)
        if feed is None:
            return
        with self._lock:
            self._feed = feed
            self._connection_state = "Connecting"
            self._message = f"Starting the cTrader {self._environment} market-data feed."

    def stop(self) -> None:
        with self._lock:
            feed = self._feed
            thread = self._thread
        if feed is not None and thread is not None and thread.is_alive():
            if self._reactor_ready.wait(timeout=5):
                def stop_feed() -> None:
                    maybeDeferred(feed.client.stopService).addBoth(
                        lambda result: self._stop_reactor(result)
                    )

                reactor.callFromThread(stop_feed)
                thread.join(timeout=5)
            else:
                self._set_status(
                    "Error",
                    "The cTrader feed reactor did not become ready.",
                )

        self._shutdown_snapshot_executor()

    def _shutdown_snapshot_executor(self) -> None:
        with self._lock:
            snapshot_executor = self._market_snapshot_executor
        if snapshot_executor is not None:
            snapshot_executor.shutdown(wait=True)

    def get_snapshot(self) -> dict:
        with self._lock:
            quote = self._last_quote
            candle = self._last_closed_candle
            return {
                "connectionState": self._connection_state,
                "environment": self._environment,
                "symbol": self._symbol_name,
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
                    self._serialize_candle(candle)
                    if candle is not None
                    else None
                ),
                "lastClosedCandles": {
                    timeframe: (
                        self._serialize_candle(history[-1])
                        if history
                        else None
                    )
                    for timeframe, history in self._closed_candles.items()
                },
                "candleHistoryCounts": {
                    timeframe: len(history)
                    for timeframe, history in self._closed_candles.items()
                },
                "marketSnapshotError": self._market_snapshot_error,
            }

    def get_market_snapshot(self) -> Optional[dict]:
        with self._lock:
            if self._market_snapshot is None:
                return None
            if self._market_snapshot_error is None:
                return self._market_snapshot
            return {
                **self._market_snapshot,
                "latest_snapshot_error": self._market_snapshot_error,
            }

    def get_market_snapshot_error(self) -> Optional[str]:
        with self._lock:
            return self._market_snapshot_error

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
        snapshot_arguments = None
        with self._lock:
            history = self._closed_candles.get(candle.timeframe)
            if history is None:
                logger.error(
                    "Ignoring unsupported live candle timeframe %s.",
                    candle.timeframe,
                )
                return
            if history and candle.time <= history[-1].time:
                logger.error(
                    "Ignoring out-of-order closed %s candle at %s.",
                    candle.timeframe,
                    candle.time.isoformat(),
                )
                return

            history.append(candle)
            if candle.timeframe == "M5":
                self._last_closed_candle = candle
            if candle.timeframe == "M1":
                candle_close_time = candle.time + timedelta(minutes=1)
                as_of = max(
                    candle_close_time,
                    self._last_quote.time if self._last_quote is not None else candle_close_time,
                )
                snapshot_arguments = (
                    candle.symbol,
                    as_of,
                    self._last_quote,
                    {
                        timeframe: list(candle_history)
                        for timeframe, candle_history in self._closed_candles.items()
                    },
                )

        if snapshot_arguments is not None:
            with self._lock:
                if self._market_snapshot_executor is None:
                    self._market_snapshot_executor = ThreadPoolExecutor(
                        max_workers=1,
                        thread_name_prefix=f"market-snapshot-{self._symbol_name}",
                    )
                snapshot_executor = self._market_snapshot_executor
                self._market_snapshot_update_complete.clear()
            future = snapshot_executor.submit(
                build_market_snapshot,
                *snapshot_arguments,
            )
            future.add_done_callback(self._store_market_snapshot)

    def _store_market_snapshot(self, future: Future) -> None:
        try:
            snapshot = future.result()
        except Exception as error:
            logger.exception("Could not build the one-minute market snapshot.")
            with self._lock:
                self._market_snapshot_error = str(error)
        else:
            with self._lock:
                self._market_snapshot = snapshot
                self._market_snapshot_error = None
        finally:
            self._market_snapshot_update_complete.set()


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
    def _serialize_candle(candle: Candle) -> dict:
        return {
            "symbol": candle.symbol,
            "timeframe": candle.timeframe,
            "time": candle.time.isoformat(),
            "open": candle.open,
            "high": candle.high,
            "low": candle.low,
            "close": candle.close,
            "volume": candle.volume,
        }

    @staticmethod
    def _stop_reactor(result):
        if reactor.running:
            reactor.stop()
        return result


live_feed_manager = LiveFeedManager()