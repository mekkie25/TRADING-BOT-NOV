"""Data-only cTrader feed for quotes and completed M1/M5 candles.

One feed normally owns one cTrader connection. Extra instruments can share that
same connection: build them with parent=<the first feed>. The parent then logs in
once, asks for every instrument and hands each message to the right instrument.
cTrader rejects several logins of the same account, so this keeps it to one.

cTrader drops the last requests when about 30 arrive at once, so the shared
instruments are subscribed one after another, a short time apart.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional, Set

from dotenv import load_dotenv

from ctrader_open_api import Client, EndPoints, Protobuf, TcpProtocol
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAAccountAuthReq,
    ProtoOAAccountAuthRes,
    ProtoOAApplicationAuthReq,
    ProtoOAApplicationAuthRes,
    ProtoOAErrorRes,
    ProtoOAGetPositionUnrealizedPnLReq,
    ProtoOAGetPositionUnrealizedPnLRes,
    ProtoOASpotEvent,
    ProtoOASubscribeLiveTrendbarReq,
    ProtoOASubscribeLiveTrendbarRes,
    ProtoOASubscribeSpotsReq,
    ProtoOASubscribeSpotsRes,
    ProtoOASymbolByIdReq,
    ProtoOASymbolByIdRes,
    ProtoOASymbolChangedEvent,
    ProtoOASymbolsListReq,
    ProtoOASymbolsListRes,
    ProtoOATraderReq,
    ProtoOATraderRes,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOATrendbarPeriod
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

load_dotenv()

logger = logging.getLogger(__name__)
CTRADER_PRICE_SCALE = 100_000
ACCOUNT_FACTS_REFRESH_SECONDS = 30
# Gap between the instruments that share one connection. Each instrument sends
# 4 requests, so 0.3 seconds keeps the rate well below a burst.
CHILD_SUBSCRIBE_SPACING_SECONDS = 0.3


@dataclass(frozen=True)
class LiveQuote:
    symbol: str
    time: datetime
    bid: float
    ask: float


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class AccountFacts:
    account_id: int
    observed_at: datetime
    balance_received_at: datetime
    unrealized_pnl_received_at: datetime
    balance: float
    net_unrealized_pnl: float
    equity: float
    leverage: Optional[float]
    deposit_asset_id: int
    equity_calculation: str
    equity_note: str


@dataclass(frozen=True)
class BrokerSymbolInfo:
    symbol: str
    symbol_id: int
    base_asset_id: int
    quote_asset_id: int
    digits: int
    pip_position: int
    lot_size_cents: int
    minimum_volume_cents: int
    volume_step_cents: int
    maximum_volume_cents: int
    maximum_exposure_cents: Optional[int] = None


QuoteCallback = Callable[[LiveQuote], None]
CandleCallback = Callable[[Candle], None]
AccountCallback = Callable[[AccountFacts], None]
SymbolInfoCallback = Callable[[Optional[BrokerSymbolInfo]], None]
StatusCallback = Callable[[str, str], None]


class LiveCTraderFeed:
    def __init__(
        self,
        symbol_name: str = "EURUSD",
        on_quote: Optional[QuoteCallback] = None,
        on_closed_candle: Optional[CandleCallback] = None,
        on_account_facts: Optional[AccountCallback] = None,
        on_symbol_info: Optional[SymbolInfoCallback] = None,
        on_status: Optional[StatusCallback] = None,
        track_account: bool = True,
        parent: Optional["LiveCTraderFeed"] = None,
    ):
        self.client_id = self._required_environment_value("CTRADER_CLIENT_ID")
        self.client_secret = self._required_environment_value("CTRADER_SECRET")
        self.access_token = self._required_environment_value("CTRADER_ACCESS_TOKEN")
        self.account_id = self._read_account_id()

        self.env = os.getenv("CTRADER_ENV", "demo").strip().lower()
        if self.env not in ("demo", "live"):
            raise ValueError("CTRADER_ENV must be either 'demo' or 'live'.")
        if not symbol_name.strip():
            raise ValueError("symbol_name must not be empty.")

        # symbol_name is our own name for the instrument (for example DAX).
        # The broker may call it something else (for example GER40).
        self.symbol_name = symbol_name.strip()
        self.track_account = track_account
        self._parent = parent
        self._children: list["LiveCTraderFeed"] = []
        self._pending_subscriptions: list = []
        self._unavailable = False
        self._subscription_requests_sent = 0
        self._subscription_responses_received = 0
        self.symbol_id: Optional[int] = None
        self.connection_state = "disconnected"
        self.on_quote = on_quote
        self.on_closed_candle = on_closed_candle
        self.on_account_facts = on_account_facts
        self.on_symbol_info = on_symbol_info
        self.on_status = on_status
        self._latest_bid: Optional[float] = None
        self._latest_ask: Optional[float] = None
        self._active_candles: dict[str, Candle] = {}
        self._confirmed_subscriptions: Set[int] = set()
        self._base_asset_id: Optional[int] = None
        self._quote_asset_id: Optional[int] = None
        self._account_refresh: Optional[LoopingCall] = None
        self._pending_account_responses: Set[str] = set()
        self._account_balance: Optional[float] = None
        self._account_leverage: Optional[float] = None
        self._account_deposit_asset_id: Optional[int] = None
        self._account_balance_received_at: Optional[datetime] = None
        self._account_net_unrealized_pnl: Optional[float] = None
        self._account_pnl_received_at: Optional[datetime] = None

        if parent is not None:
            # Shares the parent's connection: no client of its own.
            self.client = parent.client
            parent._children.append(self)
            return

        host = (
            EndPoints.PROTOBUF_DEMO_HOST
            if self.env == "demo"
            else EndPoints.PROTOBUF_LIVE_HOST
        )
        self.client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)
        self.client.setConnectedCallback(self._on_connected)
        self.client.setDisconnectedCallback(self._on_disconnected)
        self.client.setMessageReceivedCallback(self._on_message)

    @staticmethod
    def _required_environment_value(name: str) -> str:
        value = os.getenv(name)
        if value is None or not value.strip():
            raise ValueError(f"{name} must be set.")
        return value.strip()

    @classmethod
    def _read_account_id(cls) -> int:
        value = cls._required_environment_value("CTRADER_ACCOUNT_ID")
        try:
            account_id = int(value)
        except ValueError:
            raise ValueError("CTRADER_ACCOUNT_ID must be an integer.") from None
        if account_id <= 0:
            raise ValueError("CTRADER_ACCOUNT_ID must be greater than zero.")
        return account_id

    def _group(self) -> list["LiveCTraderFeed"]:
        """This feed and every instrument that shares its connection."""
        return [self, *self._children]

    def _set_connection_state(
        self, state: str, message: str, broadcast: bool = True
    ) -> None:
        self.connection_state = state
        level = logging.ERROR if state == "error" else logging.INFO
        logger.log(level, message)
        if self.on_status is not None:
            self.on_status(state, message)
        if broadcast:
            for child in self._children:
                child._relay_connection_state(state, message)

    def _relay_connection_state(self, state: str, message: str) -> None:
        """Pass the shared connection's state to an instrument that rides on it."""
        if self._unavailable:
            return
        self.connection_state = state
        if self.on_status is not None:
            self.on_status(state, message)

    def _send(self, client, request, instrument: Optional[str] = None) -> None:
        """Send a request. A request nobody answers is logged, not left unhandled."""
        result = client.send(request)
        add_errback = getattr(result, "addErrback", None)
        if callable(add_errback):
            request_name = request.DESCRIPTOR.name
            add_errback(
                lambda failure: self._on_request_failed(request_name, instrument, failure)
            )

    @staticmethod
    def _on_request_failed(request_name: str, instrument: Optional[str], failure) -> None:
        logger.warning(
            "cTrader did not answer %s%s in time (%s).",
            request_name,
            f" for {instrument}" if instrument else "",
            failure.type.__name__,
        )
        return None

    def _mark_receiving_data(self) -> None:
        """First real data for this instrument proves its subscription works."""
        if self.connection_state == "subscribing":
            self._set_connection_state(
                "subscribed",
                f"Receiving {self.symbol_name} data.",
                broadcast=False,
            )

    def _report_data_error(self, message: str) -> None:
        logger.error(message)
        if self.on_status is not None:
            self.on_status("warning", message)

    def _on_connected(self, client) -> None:
        self._set_connection_state("connected", "Connected to cTrader.")
        request = ProtoOAApplicationAuthReq()
        request.clientId = self.client_id
        request.clientSecret = self.client_secret
        self._send(client, request)

    def _clear_session_data(self) -> None:
        self._latest_bid = None
        self._latest_ask = None
        self._active_candles.clear()
        self._confirmed_subscriptions.clear()
        self._pending_account_responses.clear()
        self._subscription_requests_sent = 0
        self._subscription_responses_received = 0

    def _on_disconnected(self, _, reason) -> None:
        if self._account_refresh is not None and self._account_refresh.running:
            self._account_refresh.stop()
        self._cancel_pending_subscriptions()
        for feed in self._group():
            feed._clear_session_data()
            feed._unavailable = False
        self._set_connection_state("disconnected", f"Disconnected from cTrader: {reason}")

    def _cancel_pending_subscriptions(self) -> None:
        """Forget instruments that were waiting for their turn to subscribe."""
        for call in self._pending_subscriptions:
            if call.active():
                call.cancel()
        self._pending_subscriptions.clear()

    def _subscribe_children_paced(self, client, response) -> None:
        """Subscribe the shared instruments one after another, a short time apart.

        The first one starts at once, the next one CHILD_SUBSCRIBE_SPACING_SECONDS
        later, and so on. When the reactor is not running nothing can be delayed,
        so every instrument starts at once.
        """
        self._cancel_pending_subscriptions()
        for position, child in enumerate(self._children):
            delay = position * CHILD_SUBSCRIBE_SPACING_SECONDS
            if delay <= 0 or not reactor.running:
                child._on_symbols_list(client, response)
            else:
                self._pending_subscriptions.append(
                    reactor.callLater(delay, child._on_symbols_list, client, response)
                )

    def _on_message(self, client, message) -> None:
        payload_type = message.payloadType

        if payload_type == ProtoOAErrorRes().payloadType:
            error = Protobuf.extract(message)
            description = error.description or "cTrader returned an unspecified error."
            self._set_connection_state("error", f"cTrader error: {description}")
            client.stopService()
        elif payload_type == ProtoOAApplicationAuthRes().payloadType:
            request = ProtoOAAccountAuthReq()
            request.ctidTraderAccountId = self.account_id
            request.accessToken = self.access_token
            self._send(client, request)
            self._set_connection_state("authenticated", "Application authenticated.")
        elif payload_type == ProtoOAAccountAuthRes().payloadType:
            request = ProtoOASymbolsListReq()
            request.ctidTraderAccountId = self.account_id
            self._send(client, request)
            if self.track_account:
                self._request_account_facts()
                self._account_refresh = LoopingCall(self._request_account_facts)
                self._account_refresh.start(ACCOUNT_FACTS_REFRESH_SECONDS, now=False)
            self._set_connection_state("authenticated", "Account authenticated.")
        elif payload_type == ProtoOATraderRes().payloadType:
            self._on_trader_response(Protobuf.extract(message))
        elif payload_type == ProtoOAGetPositionUnrealizedPnLRes().payloadType:
            self._on_position_pnl_response(Protobuf.extract(message))
        elif payload_type == ProtoOASymbolsListRes().payloadType:
            response = Protobuf.extract(message)
            self._on_symbols_list(client, response)
            if self.connection_state != "error":
                self._subscribe_children_paced(client, response)
        elif payload_type == ProtoOASymbolByIdRes().payloadType:
            response = Protobuf.extract(message)
            for feed in self._group():
                feed._on_symbol_details(response)
        elif payload_type == ProtoOASymbolChangedEvent().payloadType:
            event = Protobuf.extract(message)
            for feed in self._group():
                feed._on_symbol_changed(client, event)
        elif payload_type == ProtoOASpotEvent().payloadType:
            event = Protobuf.extract(message)
            for feed in self._group():
                feed._on_spot_event(event)
        elif payload_type in (
            ProtoOASubscribeSpotsRes().payloadType,
            ProtoOASubscribeLiveTrendbarRes().payloadType,
        ):
            self._on_subscription_confirmed(payload_type)

    def _request_account_facts(self) -> None:
        if self._pending_account_responses:
            return

        self._account_balance = None
        self._account_leverage = None
        self._account_deposit_asset_id = None
        self._account_balance_received_at = None
        self._account_net_unrealized_pnl = None
        self._account_pnl_received_at = None
        self._pending_account_responses = {"trader", "position_pnl"}

        trader_request = ProtoOATraderReq()
        trader_request.ctidTraderAccountId = self.account_id
        self._send(self.client, trader_request)

        pnl_request = ProtoOAGetPositionUnrealizedPnLReq()
        pnl_request.ctidTraderAccountId = self.account_id
        self._send(self.client, pnl_request)

    def _on_trader_response(self, response) -> None:
        if response.ctidTraderAccountId != self.account_id:
            return

        self._pending_account_responses.discard("trader")
        trader = response.trader
        if not trader.HasField("moneyDigits"):
            self._report_data_error(
                "Ignoring cTrader account balance without moneyDigits."
            )
            self._try_publish_account_facts()
            return

        self._account_balance = trader.balance / (10 ** trader.moneyDigits)
        self._account_balance_received_at = datetime.now(timezone.utc)
        self._account_deposit_asset_id = trader.depositAssetId
        if trader.HasField("leverageInCents") and trader.leverageInCents > 0:
            self._account_leverage = trader.leverageInCents / 100
        else:
            self._account_leverage = None
            self._report_data_error(
                "cTrader account leverage was not provided; leverage is unavailable."
            )
        self._try_publish_account_facts()

    def _on_position_pnl_response(self, response) -> None:
        if response.ctidTraderAccountId != self.account_id:
            return

        self._pending_account_responses.discard("position_pnl")
        if not response.HasField("moneyDigits"):
            self._report_data_error(
                "Ignoring cTrader unrealized PnL without moneyDigits."
            )
            self._try_publish_account_facts()
            return

        scale = 10 ** response.moneyDigits
        self._account_net_unrealized_pnl = sum(
            position.netUnrealizedPnL for position in response.positionUnrealizedPnL
        ) / scale
        self._account_pnl_received_at = datetime.now(timezone.utc)
        self._try_publish_account_facts()

    def _try_publish_account_facts(self) -> None:
        if self._pending_account_responses:
            return
        required_values = (
            self._account_balance,
            self._account_deposit_asset_id,
            self._account_balance_received_at,
            self._account_net_unrealized_pnl,
            self._account_pnl_received_at,
        )
        if any(value is None for value in required_values):
            return
        if self.on_account_facts is None:
            return

        balance = self._account_balance
        net_unrealized_pnl = self._account_net_unrealized_pnl
        balance_received_at = self._account_balance_received_at
        pnl_received_at = self._account_pnl_received_at
        if (
            balance is None
            or net_unrealized_pnl is None
            or balance_received_at is None
            or pnl_received_at is None
            or self._account_deposit_asset_id is None
        ):
            return

        self.on_account_facts(
            AccountFacts(
                account_id=self.account_id,
                observed_at=max(balance_received_at, pnl_received_at),
                balance_received_at=balance_received_at,
                unrealized_pnl_received_at=pnl_received_at,
                balance=balance,
                net_unrealized_pnl=net_unrealized_pnl,
                equity=balance + net_unrealized_pnl,
                leverage=self._account_leverage,
                deposit_asset_id=self._account_deposit_asset_id,
                equity_calculation="balance + net unrealized PnL",
                equity_note=(
                    "This calculated equity does not include potential closing "
                    "commissions."
                ),
            )
        )

    def _find_symbol_by_alias(self, symbols):
        """Match our instrument name to the broker's name (for example DAX to GER40)."""
        from data.downloader import resolve_symbols

        broker_names = {item.symbolName: item.symbolId for item in symbols}
        wanted = self.symbol_name.upper()
        resolved, _missing = resolve_symbols(broker_names, [wanted])
        hit = resolved.get(wanted)
        if hit is None:
            return None
        return next((item for item in symbols if item.symbolId == hit[1]), None)

    def _on_symbols_list(self, client, response) -> None:
        self._unavailable = False
        symbol = next(
            (item for item in response.symbol if item.symbolName == self.symbol_name),
            None,
        )
        if symbol is None:
            symbol = self._find_symbol_by_alias(response.symbol)
        if symbol is None:
            self._set_connection_state(
                "error",
                f"cTrader did not provide the requested symbol {self.symbol_name}.",
            )
            if self._parent is None:
                client.stopService()
            else:
                # One missing instrument must not stop the shared connection.
                self._unavailable = True
            return

        self.symbol_id = symbol.symbolId
        if (
            not symbol.HasField("baseAssetId")
            or not symbol.HasField("quoteAssetId")
            or symbol.baseAssetId <= 0
            or symbol.quoteAssetId <= 0
        ):
            self._report_data_error(
                f"Broker asset IDs are unavailable for {self.symbol_name}; "
                "lot sizing cannot be connected."
            )
        else:
            self._base_asset_id = symbol.baseAssetId
            self._quote_asset_id = symbol.quoteAssetId
            self._request_symbol_details(client)
        self._subscribe(client)

    def _on_symbol_changed(self, client, event) -> None:
        if (
            event.ctidTraderAccountId != self.account_id
            or self.symbol_id is None
            or self.symbol_id not in event.symbolId
        ):
            return
        if self.on_symbol_info is not None:
            self.on_symbol_info(None)
        self._request_symbol_details(client)

    def _request_symbol_details(self, client) -> None:
        if self.symbol_id is None:
            return
        symbol_request = ProtoOASymbolByIdReq()
        symbol_request.ctidTraderAccountId = self.account_id
        symbol_request.symbolId.append(self.symbol_id)
        self._send(client, symbol_request, self.symbol_name)

    def _on_symbol_details(self, response) -> None:
        if (
            response.ctidTraderAccountId != self.account_id
            or self.symbol_id is None
            or self._base_asset_id is None
            or self._quote_asset_id is None
        ):
            return

        symbol = next(
            (item for item in response.symbol if item.symbolId == self.symbol_id),
            None,
        )
        if symbol is None:
            if self._parent is not None or self._children:
                return  # the reply was about another instrument on this connection
            self._report_data_error(
                f"cTrader did not provide full broker specifications for "
                f"{self.symbol_name}."
            )
            return

        required_fields = (
            "digits",
            "pipPosition",
            "lotSize",
            "minVolume",
            "stepVolume",
            "maxVolume",
        )
        if any(not symbol.HasField(field) for field in required_fields):
            self._report_data_error(
                f"cTrader returned incomplete broker specifications for "
                f"{self.symbol_name}; lot sizing is unavailable."
            )
            return

        if self.on_symbol_info is not None:
            self.on_symbol_info(
                BrokerSymbolInfo(
                    symbol=self.symbol_name,
                    symbol_id=self.symbol_id,
                    base_asset_id=self._base_asset_id,
                    quote_asset_id=self._quote_asset_id,
                    digits=symbol.digits,
                    pip_position=symbol.pipPosition,
                    lot_size_cents=symbol.lotSize,
                    minimum_volume_cents=symbol.minVolume,
                    volume_step_cents=symbol.stepVolume,
                    maximum_volume_cents=symbol.maxVolume,
                    maximum_exposure_cents=(
                        symbol.maxExposure if symbol.HasField("maxExposure") else None
                    ),
                )
            )

    def _subscribe(self, client) -> None:
        if self.symbol_id is None:
            raise RuntimeError("Cannot subscribe before the symbol ID is known.")

        spot_request = ProtoOASubscribeSpotsReq()
        spot_request.ctidTraderAccountId = self.account_id
        spot_request.symbolId.append(self.symbol_id)
        # Without this flag cTrader sends quotes with no timestamp.
        spot_request.subscribeToSpotTimestamp = True
        self._send(client, spot_request, self.symbol_name)

        for period in (ProtoOATrendbarPeriod.M1, ProtoOATrendbarPeriod.M5):
            candle_request = ProtoOASubscribeLiveTrendbarReq()
            candle_request.ctidTraderAccountId = self.account_id
            candle_request.symbolId = self.symbol_id
            candle_request.period = period
            self._send(client, candle_request, self.symbol_name)
        root = self._parent if self._parent is not None else self
        root._subscription_requests_sent += 3
        self._set_connection_state(
            "subscribing",
            f"Subscribing to {self.symbol_name} quotes and M1/M5 candles.",
            broadcast=False,
        )

    def _on_subscription_confirmed(self, payload_type: int) -> None:
        self._confirmed_subscriptions.add(payload_type)
        self._subscription_responses_received += 1
        expected = {
            ProtoOASubscribeSpotsRes().payloadType,
            ProtoOASubscribeLiveTrendbarRes().payloadType,
        }
        if not expected.issubset(self._confirmed_subscriptions):
            return
        # Every instrument on this connection must be confirmed, not just the first.
        if self._subscription_responses_received < self._subscription_requests_sent:
            return
        for feed in self._group():
            if not feed._unavailable and feed.symbol_id is not None:
                feed._set_connection_state(
                    "subscribed",
                    f"Receiving {feed.symbol_name} data.",
                    broadcast=False,
                )

    def _on_spot_event(self, event) -> None:
        if (
            event.ctidTraderAccountId != self.account_id
            or event.symbolId != self.symbol_id
        ):
            return

        has_bid = event.HasField("bid")
        has_ask = event.HasField("ask")
        if has_bid or has_ask:
            if event.timestamp <= 0:
                self._report_data_error("Ignoring a quote without a valid UTC timestamp.")
            elif (has_bid and event.bid <= 0) or (has_ask and event.ask <= 0):
                self._report_data_error("Ignoring a quote with a non-positive price.")
            else:
                self._mark_receiving_data()
                if has_bid:
                    self._latest_bid = event.bid / CTRADER_PRICE_SCALE
                if has_ask:
                    self._latest_ask = event.ask / CTRADER_PRICE_SCALE
                if (
                    self._latest_bid is not None
                    and self._latest_ask is not None
                    and self.on_quote is not None
                ):
                    quote_time = datetime.fromtimestamp(
                        event.timestamp / 1000,
                        tz=timezone.utc,
                    )
                    self.on_quote(
                        LiveQuote(
                            symbol=self.symbol_name,
                            time=quote_time,
                            bid=self._latest_bid,
                            ask=self._latest_ask,
                        )
                    )

        closed_candles = []
        periods = {
            ProtoOATrendbarPeriod.M1: "M1",
            ProtoOATrendbarPeriod.M5: "M5",
        }
        for trendbar in sorted(
            event.trendbar,
            key=lambda item: item.utcTimestampInMinutes,
        ):
            timeframe = periods.get(trendbar.period)
            if timeframe is not None:
                if trendbar.utcTimestampInMinutes > 0:
                    self._mark_receiving_data()
                closed_candle = self._update_candle(trendbar, timeframe)
                if closed_candle is not None:
                    closed_candles.append(closed_candle)

        closed_candles.sort(
            key=lambda candle: (
                candle.time,
                -timedelta(minutes=int(candle.timeframe[1:])).total_seconds(),
            )
        )
        if self.on_closed_candle is not None:
            for candle in closed_candles:
                self.on_closed_candle(candle)

    def _decode_candle(self, trendbar, timeframe: str) -> Optional[Candle]:
        if trendbar.utcTimestampInMinutes <= 0:
            self._report_data_error(
                f"Ignoring a {timeframe} candle without a valid UTC timestamp."
            )
            return None

        low = trendbar.low / CTRADER_PRICE_SCALE
        open_price = (trendbar.low + trendbar.deltaOpen) / CTRADER_PRICE_SCALE
        high = (trendbar.low + trendbar.deltaHigh) / CTRADER_PRICE_SCALE
        close = (trendbar.low + trendbar.deltaClose) / CTRADER_PRICE_SCALE
        if (
            low <= 0
            or open_price <= 0
            or high <= 0
            or close <= 0
            or low > min(open_price, close)
            or high < max(open_price, close)
        ):
            self._report_data_error(
                f"Ignoring a malformed {timeframe} candle from cTrader."
            )
            return None

        return Candle(
            symbol=self.symbol_name,
            timeframe=timeframe,
            time=datetime.fromtimestamp(
                trendbar.utcTimestampInMinutes * 60,
                tz=timezone.utc,
            ),
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=trendbar.volume,
        )

    def _update_candle(self, trendbar, timeframe: str) -> Optional[Candle]:
        candle = self._decode_candle(trendbar, timeframe)
        if candle is None:
            return None

        active_candle = self._active_candles.get(timeframe)
        if active_candle is None:
            self._active_candles[timeframe] = candle
            return None
        if candle.time < active_candle.time:
            self._report_data_error(
                f"Ignoring an out-of-order {timeframe} candle from cTrader."
            )
            return None
        if candle.time == active_candle.time:
            self._active_candles[timeframe] = candle
            return None

        candle_duration = timedelta(minutes=int(timeframe[1:]))
        if candle.time - active_candle.time > candle_duration:
            self._report_data_error(
                f"Missing one or more {timeframe} candles before "
                f"{candle.time.isoformat()}."
            )

        self._active_candles[timeframe] = candle
        return active_candle

    def start(self, install_signal_handlers: bool = True) -> None:
        if reactor.running:
            raise RuntimeError("The Twisted reactor is already running.")
        self._set_connection_state("connecting", f"Starting cTrader feed for {self.symbol_name}.")
        self.client.startService()
        reactor.run(installSignalHandlers=install_signal_handlers)