"""One replaceable interface for historical or in-memory OHLC candle data."""

from datetime import datetime
from typing import Dict, Optional, Protocol, Tuple, runtime_checkable

import pandas as pd


@runtime_checkable
class CandleDataSource(Protocol):
    def load_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Return ordered OHLC candles for one symbol and timeframe."""
        ...


class InMemoryCandleDataSource:
    """Adapt supplied candle frames to the common backtest data interface."""

    def __init__(self, candles: Dict[Tuple[str, str], pd.DataFrame]) -> None:
        self._candles: Dict[Tuple[str, str], pd.DataFrame] = {}
        for (symbol, timeframe), frame in candles.items():
            key = (symbol.strip().upper(), timeframe.strip().upper())
            if not key[0] or not key[1]:
                raise ValueError("symbol and timeframe keys must not be empty.")
            if not isinstance(frame, pd.DataFrame):
                raise ValueError(f"Candles for {key[0]} {key[1]} must be a DataFrame.")
            self._candles[key] = frame.copy()

    def load_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> pd.DataFrame:
        key = (symbol.strip().upper(), timeframe.strip().upper())
        if key not in self._candles:
            raise KeyError(f"No candle data is registered for {key[0]} {key[1]}.")
        frame = self._candles[key].copy()
        if "time" not in frame.columns:
            raise ValueError("Candle data must include a 'time' column.")
        times = pd.to_datetime(frame["time"], utc=True, errors="coerce")
        if times.isna().any() or not times.is_monotonic_increasing or times.duplicated().any():
            raise ValueError("Candle times must be valid, unique, and chronological.")
        if start_time is not None:
            _validate_utc_datetime(start_time, "start_time")
            frame = frame.loc[times >= pd.Timestamp(start_time)]
            times = times.loc[frame.index]
        if end_time is not None:
            _validate_utc_datetime(end_time, "end_time")
            frame = frame.loc[times <= pd.Timestamp(end_time)]
        return frame.reset_index(drop=True)


def _validate_utc_datetime(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset().total_seconds() != 0:
        raise ValueError(f"{name} must be timezone-aware UTC.")
