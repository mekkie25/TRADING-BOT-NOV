"""Runs the live cTrader feed for all watched instruments on ONE connection.

cTrader does not accept the same account logged in on several connections, so
EURUSD (the primary manager) opens the single connection and logs in once. The
other instruments ride on it: the feed asks cTrader for each instrument and hands
every quote and candle to the right manager. Each manager keeps its own quote,
candles and market snapshot, so the instruments never mix. Only EURUSD reads the
account balance.
"""

from typing import Dict, Iterable, List

from data.live_feed_manager import LiveFeedManager

# TEST ORDER: US30 and NAS100 come right after EURUSD, to see whether the last
# requests in the list are the ones cTrader does not answer.
WATCHED_INSTRUMENTS = (
    "EURUSD",
    "US30",
    "NAS100",
    "GBPUSD",
    "USDJPY",
    "XAUUSD",
    "BTCUSD",
    "DAX",
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
                manager = LiveFeedManager(symbol_name=key, track_account=False)
                self._managers[key] = manager
                primary.share_connection_with(manager)

    @property
    def symbols(self) -> List[str]:
        return list(self._managers)

    def get(self, symbol: str) -> LiveFeedManager:
        """The manager for one instrument. Raises KeyError for an unknown instrument."""
        return self._managers[symbol.strip().upper()]

    def start(self) -> None:
        self.primary.start()

    def stop(self) -> None:
        for manager in self._managers.values():
            if manager is not self.primary:
                manager.stop()
        self.primary.stop()

    def get_all_snapshots(self) -> Dict[str, dict]:
        return {symbol: manager.get_snapshot() for symbol, manager in self._managers.items()}