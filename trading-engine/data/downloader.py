"""Downloads 1-minute candles from cTrader and keeps the local store up to date.

Run these from the trading-engine folder (with the venv active):

  python -m data.downloader symbols            list the broker's symbol names
  python -m data.downloader sync               first download, and the daily update
  python -m data.downloader status             what is stored for each instrument
  python -m data.downloader export             write the CSV files the backtester reads

Options for sync:
  --only XAUUSD US30       only these instruments
  --years 3                size of the rolling window
  --map DAX=GER40          use this broker symbol name for an instrument
  --chunk-days 3           how many days to ask for in one request

sync is safe to run again at any time: it continues from the newest stored candle
(going back one day to close any gap), removes duplicates, and drops candles older
than the window. Progress is saved as it goes, so a stopped run loses nothing.

Settings come from a .env file: CTRADER_CLIENT_ID, CTRADER_SECRET,
CTRADER_ACCESS_TOKEN, CTRADER_ACCOUNT_ID. Never share or commit that file.
"""

import argparse
import os
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from . import bar_store

PRICE_SCALE = 100000.0
WANTED = ("BTCUSD", "XAUUSD", "DAX", "EURUSD", "USDJPY", "GBPUSD", "US30", "NAS100")
# Brokers name instruments differently. Names are compared ignoring case, dots, slashes and spaces.
ALIASES = {
    "BTCUSD": ["BTCUSD", "BTCUSDT", "BITCOIN"],
    "XAUUSD": ["XAUUSD", "GOLD"],
    "DAX": ["GER40", "DE40", "DE30", "GER30", "DAX40", "DAX30", "DAX", "GERMANY40", "GERMANY30"],
    "EURUSD": ["EURUSD"],
    "USDJPY": ["USDJPY"],
    "GBPUSD": ["GBPUSD"],
    "US30": ["US30", "DJ30", "DJI30", "WS30", "DOW30", "USA30", "US30CASH", "DOWJONES"],
    "NAS100": ["NAS100", "US100", "USTEC", "NDX100", "NASDAQ100", "USTECH", "NAS100CASH", "USA100", "NASDAQ"],
}
SEARCH_HINTS = ("BTC", "XAU", "GOLD", "GER", "DE30", "DE40", "DAX", "EURUSD", "USDJPY", "GBPUSD",
                "US30", "DJ", "WS30", "NAS", "US100", "USTEC", "NDX")
REQUEST_DELAY_SECONDS = 0.25   # cTrader allows about 5 history requests per second
CHUNK_DAYS = 3.0
FLUSH_EVERY_CHUNKS = 50
STALL_SECONDS = 60


def normalize_name(name: str) -> str:
    return "".join(ch for ch in name.upper() if ch.isalnum())


def resolve_symbols(
    broker_symbols: Dict[str, int],
    wanted: Sequence[str] = WANTED,
    overrides: Optional[Dict[str, str]] = None,
) -> Tuple[Dict[str, Tuple[str, int]], List[str]]:
    """Match our instrument names to the broker's names. Returns (matches, missing)."""
    lookup: Dict[str, Tuple[str, int]] = {}
    for name, symbol_id in broker_symbols.items():
        lookup.setdefault(normalize_name(name), (name, symbol_id))
    overrides = {key.upper(): value for key, value in (overrides or {}).items()}
    resolved: Dict[str, Tuple[str, int]] = {}
    missing: List[str] = []
    for canonical in wanted:
        candidates = [overrides[canonical]] if canonical in overrides else ALIASES.get(canonical, [canonical])
        for candidate in candidates:
            hit = lookup.get(normalize_name(candidate))
            if hit:
                resolved[canonical] = hit
                break
        else:
            missing.append(canonical)
    return resolved, missing


def plan_chunks(start: datetime, end: datetime, chunk_days: float = CHUNK_DAYS) -> List[Tuple[int, int]]:
    """Split a time range into consecutive requests, as (from, to) in milliseconds."""
    if chunk_days <= 0:
        raise ValueError("chunk_days must be above zero.")
    chunks: List[Tuple[int, int]] = []
    step = timedelta(days=chunk_days)
    cursor = start
    while cursor < end:
        following = min(cursor + step, end)
        chunks.append((int(cursor.timestamp() * 1000), int(following.timestamp() * 1000)))
        cursor = following
    return chunks


def sync_start(existing_last: Optional[pd.Timestamp], now: datetime, years: float) -> datetime:
    """Where to start downloading: the window start, or one day before the newest stored candle."""
    window_start = now - timedelta(days=365.25 * years)
    if existing_last is None:
        return window_start
    return max(window_start, existing_last.to_pydatetime() - timedelta(days=1))


def trendbars_to_frame(bars: Iterable) -> pd.DataFrame:
    """Convert cTrader trendbars (prices stored as a low plus offsets) to candle rows."""
    rows = []
    for bar in bars:
        low = bar.low / PRICE_SCALE
        rows.append(
            {
                "time": datetime.fromtimestamp(bar.utcTimestampInMinutes * 60, timezone.utc),
                "open": round(low + bar.deltaOpen / PRICE_SCALE, 5),
                "high": round(low + bar.deltaHigh / PRICE_SCALE, 5),
                "low": round(low, 5),
                "close": round(low + bar.deltaClose / PRICE_SCALE, 5),
                "volume": float(bar.volume),
            }
        )
    return pd.DataFrame(rows, columns=bar_store.COLUMNS)


def parse_overrides(pairs: Optional[Sequence[str]]) -> Dict[str, str]:
    overrides: Dict[str, str] = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError(f"--map needs NAME=BROKERNAME, got {pair!r}.")
        key, value = pair.split("=", 1)
        overrides[key.strip().upper()] = value.strip()
    return overrides


def load_credentials() -> Tuple[Optional[Dict[str, str]], List[str]]:
    try:
        from dotenv import find_dotenv, load_dotenv
    except ImportError:  # python-dotenv is in requirements.txt
        find_dotenv = load_dotenv = None
    if load_dotenv is not None:
        load_dotenv(find_dotenv(usecwd=True) or find_dotenv())
    names = ("CTRADER_CLIENT_ID", "CTRADER_SECRET", "CTRADER_ACCESS_TOKEN", "CTRADER_ACCOUNT_ID")
    values = {name: os.getenv(name, "").strip() for name in names}
    missing = [name for name, value in values.items() if not value]
    return (None if missing else values), missing


class HistoryDownloader:
    """Talks to cTrader one request at a time. Reply handling follows the working EURUSD script."""

    def __init__(
        self,
        mode: str,
        wanted: Sequence[str] = WANTED,
        years: float = bar_store.DEFAULT_YEARS,
        overrides: Optional[Dict[str, str]] = None,
        chunk_days: float = CHUNK_DAYS,
        show_all: bool = False,
        store_dir=None,
    ):
        self.mode = mode
        self.wanted = [name.upper() for name in wanted]
        self.years = years
        self.overrides = overrides or {}
        self.chunk_days = chunk_days
        self.show_all = show_all
        self.store_dir = store_dir
        self.exit_code = 0
        self.jobs: List[Dict[str, object]] = []
        self.current: Optional[Dict[str, object]] = None
        self.buffers: Dict[str, List[pd.DataFrame]] = {}
        self.results: List[bar_store.MergeResult] = []
        self.chunks_done = 0
        self.last_message = time.time()
        self.api = None
        self.reactor = None
        self.client = None
        self.credentials: Dict[str, str] = {}

    # ----- start and stop -----

    def run(self) -> int:
        credentials, missing = load_credentials()
        if credentials is None:
            print("Missing settings in your .env file: " + ", ".join(missing))
            return 2
        self.credentials = credentials
        try:
            self._load_api()
        except ImportError as error:
            print(f"Could not load the cTrader library: {error}")
            return 2
        self.client = self.api.Client(self.api.EndPoints.PROTOBUF_LIVE_HOST, self.api.EndPoints.PROTOBUF_PORT, self.api.TcpProtocol)
        self.client.setConnectedCallback(self.on_connected)
        self.client.setMessageReceivedCallback(self.on_message)
        self.reactor.callLater(10, self._watchdog)
        self.client.startService()
        self.reactor.run()
        return self.exit_code

    def _load_api(self) -> None:
        from ctrader_open_api import Client, EndPoints, Protobuf, TcpProtocol
        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOAAccountAuthReq,
            ProtoOAApplicationAuthReq,
            ProtoOAGetTrendbarsReq,
            ProtoOASymbolsListReq,
        )
        from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOAPayloadType, ProtoOATrendbarPeriod
        from twisted.internet import reactor

        self.api = SimpleNamespace(
            Client=Client, EndPoints=EndPoints, Protobuf=Protobuf, TcpProtocol=TcpProtocol,
            AppAuthReq=ProtoOAApplicationAuthReq, AccountAuthReq=ProtoOAAccountAuthReq,
            SymbolsListReq=ProtoOASymbolsListReq, TrendbarsReq=ProtoOAGetTrendbarsReq,
            PayloadType=ProtoOAPayloadType, Period=ProtoOATrendbarPeriod,
        )
        self.reactor = reactor

    def finish(self, code: int = 0) -> None:
        self._flush_all()
        self.exit_code = code
        self._print_summary()
        if self.reactor is not None and self.reactor.running:
            self.reactor.stop()

    def _watchdog(self) -> None:
        if time.time() - self.last_message > STALL_SECONDS:
            print(f"\nNo reply from cTrader for {STALL_SECONDS} seconds. Stopping. Progress so far is saved.")
            self.finish(1)
            return
        self.reactor.callLater(10, self._watchdog)

    # ----- messages -----

    def on_connected(self, client) -> None:
        print("Connected to cTrader LIVE API...")
        request = self.api.AppAuthReq()
        request.clientId = self.credentials["CTRADER_CLIENT_ID"]
        request.clientSecret = self.credentials["CTRADER_SECRET"]
        client.send(request)

    def on_message(self, client, message) -> None:
        self.last_message = time.time()
        kind = self.api.PayloadType
        if message.payloadType == kind.PROTO_OA_ERROR_RES:
            error = self.api.Protobuf.extract(message)
            where = ""
            if self.current:
                where = f" (while asking for {self.current['symbol']} chunk {self.current['index']} of {self.current['total']})"
            print(f"\n!!! cTrader error{where}: {error.description}")
            self.finish(1)
        elif message.payloadType == kind.PROTO_OA_APPLICATION_AUTH_RES:
            print("App authenticated. Authenticating account...")
            request = self.api.AccountAuthReq()
            request.ctidTraderAccountId = int(self.credentials["CTRADER_ACCOUNT_ID"])
            request.accessToken = self.credentials["CTRADER_ACCESS_TOKEN"]
            client.send(request)
        elif message.payloadType == kind.PROTO_OA_ACCOUNT_AUTH_RES:
            print("Account authenticated. Fetching the symbol list...")
            request = self.api.SymbolsListReq()
            request.ctidTraderAccountId = int(self.credentials["CTRADER_ACCOUNT_ID"])
            client.send(request)
        elif message.payloadType == kind.PROTO_OA_SYMBOLS_LIST_RES:
            response = self.api.Protobuf.extract(message)
            self._on_symbols({item.symbolName: item.symbolId for item in response.symbol})
        elif message.payloadType == kind.PROTO_OA_GET_TRENDBARS_RES:
            response = self.api.Protobuf.extract(message)
            self._on_trendbars(response)

    def _on_symbols(self, broker_symbols: Dict[str, int]) -> None:
        resolved, missing = resolve_symbols(broker_symbols, self.wanted, self.overrides)
        print("\nInstrument matches:")
        for canonical in self.wanted:
            if canonical in resolved:
                print(f"  {canonical:8s} -> {resolved[canonical][0]} (id {resolved[canonical][1]})")
            else:
                print(f"  {canonical:8s} -> NOT FOUND (use --map {canonical}=BROKERNAME)")
        if self.mode == "symbols":
            hints = [name for name in sorted(broker_symbols) if self.show_all or any(h in normalize_name(name) for h in SEARCH_HINTS)]
            print(f"\nBroker symbols{' (all)' if self.show_all else ' that look relevant'}: {len(hints)}")
            for name in hints:
                print(f"  {name}")
            self.finish(0)
            return
        if not resolved:
            print("\nNo instruments could be matched, nothing to download.")
            self.finish(1)
            return
        now = datetime.now(timezone.utc)
        for canonical in self.wanted:
            if canonical not in resolved:
                continue
            _name, symbol_id = resolved[canonical]
            start = sync_start(bar_store.last_time(canonical, self.store_dir), now, self.years)
            chunks = plan_chunks(start, now, self.chunk_days)
            print(f"  {canonical}: {len(chunks)} requests from {start:%Y-%m-%d}")
            for number, (from_ms, to_ms) in enumerate(chunks, 1):
                self.jobs.append({"symbol": canonical, "id": symbol_id, "from": from_ms, "to": to_ms,
                                  "index": number, "total": len(chunks), "last": number == len(chunks)})
        print(f"\nStarting download: {len(self.jobs)} requests, about {len(self.jobs) * REQUEST_DELAY_SECONDS / 60:.0f} minutes.\n")
        self._send_next()

    # ----- download loop -----

    def _send_next(self) -> None:
        if not self.jobs:
            self.finish(0)
            return
        job = self.jobs.pop(0)
        self.current = job
        request = self.api.TrendbarsReq()
        request.ctidTraderAccountId = int(self.credentials["CTRADER_ACCOUNT_ID"])
        request.symbolId = int(job["id"])
        request.period = self.api.Period.M1
        request.fromTimestamp = int(job["from"])
        request.toTimestamp = int(job["to"])
        self.client.send(request)

    def _on_trendbars(self, response) -> None:
        job = self.current
        frame = trendbars_to_frame(response.trendbar)
        symbol = str(job["symbol"])
        if len(frame):
            self.buffers.setdefault(symbol, []).append(frame)
            if getattr(response, "hasMore", False):
                resume_ms = int(frame["time"].max().timestamp() * 1000) + 60000
                if resume_ms < int(job["to"]) and resume_ms > int(job["from"]):
                    self.jobs.insert(0, dict(job, **{"from": resume_ms, "last": job["last"]}))
                    job = dict(job, last=False)
        self.chunks_done += 1
        if job["last"] or self.chunks_done % FLUSH_EVERY_CHUNKS == 0:
            self._flush(symbol)
        if self.chunks_done % 25 == 0 or job["last"]:
            when = datetime.fromtimestamp(int(job["to"]) / 1000, timezone.utc)
            print(f"  {symbol}: request {job['index']}/{job['total']} (up to {when:%Y-%m-%d})")
        self.reactor.callLater(REQUEST_DELAY_SECONDS, self._send_next)

    # ----- saving -----

    def _flush(self, symbol: str) -> None:
        pieces = self.buffers.pop(symbol, [])
        if not pieces:
            return
        result = bar_store.merge_m1(symbol, pd.concat(pieces, ignore_index=True), self.years, self.store_dir)
        self.results = [r for r in self.results if r.symbol != result.symbol] + [result]

    def _flush_all(self) -> None:
        for symbol in list(self.buffers):
            self._flush(symbol)

    def _print_summary(self) -> None:
        if not self.results:
            return
        print("\nStored 1-minute candles:")
        for result in self.results:
            first = f"{result.first:%Y-%m-%d}" if result.first is not None else "-"
            last = f"{result.last:%Y-%m-%d %H:%M}" if result.last is not None else "-"
            print(f"  {result.symbol:8s} {result.rows_after:>9,} rows  {first} to {last}  "
                  f"(new {result.rows_received:,}, dropped as old {result.rows_trimmed:,}, rejected {result.rows_rejected:,})")


def print_status(symbols: Sequence[str]) -> None:
    print(f"{'Instrument':10s} {'Rows':>10s}  {'First':10s}  {'Last':16s}  {'Years':>5s}  {'Longest gap (h)':>15s}")
    for symbol in symbols:
        info = bar_store.status(symbol)
        if not info["rows"]:
            print(f"{symbol:10s} {'nothing stored yet':>10s}")
            continue
        print(f"{symbol:10s} {info['rows']:>10,}  {info['first']:%Y-%m-%d}  {info['last']:%Y-%m-%d %H:%M}  "
              f"{info['years_covered']:>5}  {info['longest_gap_hours']:>15}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m data.downloader", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("symbols", help="list the broker's symbol names")
    listing.add_argument("--all", action="store_true", help="show every symbol, not only the likely ones")
    for name in ("sync", "download", "update"):
        sync = commands.add_parser(name, help="download new candles and trim the window")
        sync.add_argument("--only", nargs="+", help="only these instruments")
        sync.add_argument("--years", type=float, default=bar_store.DEFAULT_YEARS)
        sync.add_argument("--chunk-days", type=float, default=CHUNK_DAYS)
    for name in ("symbols", "sync", "download", "update"):
        commands.choices[name].add_argument("--map", nargs="+", metavar="NAME=BROKERNAME", help="broker symbol name for an instrument")
    for name in ("status", "export"):
        item = commands.add_parser(name, help=f"{name} the stored candles")
        item.add_argument("--only", nargs="+", help="only these instruments")
    args = parser.parse_args(argv)

    only = [name.upper() for name in args.only] if getattr(args, "only", None) else list(WANTED)
    if args.command == "status":
        print_status(only)
        return 0
    if args.command == "export":
        for symbol in only:
            if bar_store.last_time(symbol) is None:
                print(f"{symbol}: nothing stored, skipped.")
                continue
            files = bar_store.export_for_backtester(symbol)
            print(f"{symbol}: wrote " + ", ".join(path.name for path in files))
        return 0
    overrides = parse_overrides(getattr(args, "map", None))
    if args.command == "symbols":
        return HistoryDownloader("symbols", only, overrides=overrides, show_all=args.all).run()
    return HistoryDownloader("sync", only, args.years, overrides, args.chunk_days).run()


if __name__ == "__main__":
    raise SystemExit(main())