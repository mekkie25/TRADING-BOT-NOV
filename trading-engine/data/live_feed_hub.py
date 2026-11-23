"""Runs the live cTrader feed for several instruments on one shared Twisted engine.

The primary manager (EURUSD) runs the engine and is the only one that reads the
account balance. Every other instrument gets its own manager and its own
connection, started on the same engine. Each manager keeps its own quote,
candles and market snapshot, so the instruments never mix.
"""

from typing import Dict, Iterable, List

from data.live_feed_manager import LiveFeedManager

WATCHED_INSTRUMENTS = (
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "XAUUSD",
    "BTCUSD",
    "DAX",
    "US30",
    "NAS100",
)


class LiveFeedHub:
    def __init__(
        self,
        primary: LiveFeedManager,
        symbols: Iterable[str] = WATCHED_INSTRUMENTS,
    ) -> None:
        self.primary = primary
        self._managers: Dict[str, LiveFeedManager] = {primary.symbol_name: primary}
        for name in symbols:
            key = name.strip().upper()
            if key not in self._managers:
                self._managers[key] = LiveFeedManager(symbol_name=key, track_account=False)

    @property
    def symbols(self) -> List[str]:
        return list(self._managers)

    def get(self, symbol: str) -> LiveFeedManager:
        """The manager for one instrument. Raises KeyError for an unknown instrument."""
        return self._managers[symbol.strip().upper()]

    def start(self) -> None:
        self.primary.start()
        for manager in self._managers.values():
            if manager is not self.primary:
                manager.start_attached(self.primary)

    def stop(self) -> None:
        for manager in self._managers.values():
            if manager is not self.primary:
                manager.stop_attached()
        self.primary.stop()

    def get_all_snapshots(self) -> Dict[str, dict]:
        return {symbol: manager.get_snapshot() for symbol, manager in self._managers.items()}