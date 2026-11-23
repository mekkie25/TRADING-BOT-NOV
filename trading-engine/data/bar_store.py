"""Local store for 1-minute candles, with a rolling window (default 3 years).

One parquet file per instrument: data/store/<SYMBOL>_M1.parquet. Every higher
timeframe is built from these 1-minute candles (see synthesizer.py), so there is
only one file per instrument to keep up to date.

The store folder is kept out of git automatically: it holds hundreds of
megabytes and changes every day. Back it up by copying the folder.

Columns: time (UTC, candle open), open, high, low, close, volume (tick volume).
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd

from . import synthesizer

DATA_DIR = Path(__file__).resolve().parent
STORE_DIR = DATA_DIR / "store"
RAW_DIR = DATA_DIR / "raw"
COLUMNS = list(synthesizer.COLUMNS)
DEFAULT_YEARS = 3
BACKTEST_TIMEFRAMES = ("M5", "H1", "H4", "D1")


@dataclass(frozen=True)
class MergeResult:
    symbol: str
    rows_before: int
    rows_received: int
    rows_after: int
    rows_trimmed: int
    rows_rejected: int
    first: Optional[pd.Timestamp]
    last: Optional[pd.Timestamp]


def ensure_dir(directory: Path, ignore_pattern: str = "*") -> Path:
    """Create the folder and a .gitignore inside it so git never uploads its contents."""
    directory.mkdir(parents=True, exist_ok=True)
    marker = directory / ".gitignore"
    if not marker.exists():
        marker.write_text(ignore_pattern + "\n", encoding="utf-8")
    return directory


def store_path(symbol: str, store_dir: Optional[Path] = None) -> Path:
    clean_symbol = "".join(ch for ch in symbol.upper() if ch.isalnum())
    if not clean_symbol:
        raise ValueError("Symbol name is empty.")
    return Path(store_dir or STORE_DIR) / f"{clean_symbol}_M1.parquet"


def clean_frame(frame: pd.DataFrame) -> "tuple[pd.DataFrame, int]":
    """Tidy new candles. Returns the clean frame and how many rows were rejected."""
    missing = [column for column in COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Candles are missing columns: {missing}.")
    data = frame[COLUMNS].copy()
    data["time"] = pd.to_datetime(data["time"], utc=True, errors="coerce")
    for column in COLUMNS[1:]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    before = len(data)
    data = data.dropna()
    prices = ["open", "high", "low", "close"]
    valid = (data[prices] > 0).all(axis=1)
    valid &= data["high"] >= data[["open", "close", "low"]].max(axis=1)
    valid &= data["low"] <= data[["open", "close", "high"]].min(axis=1)
    valid &= data["volume"] >= 0
    data = data[valid]
    rejected = before - len(data)
    data = data.drop_duplicates(subset="time", keep="last").sort_values("time")
    return data.reset_index(drop=True), rejected


def trim_window(frame: pd.DataFrame, years: float = DEFAULT_YEARS) -> pd.DataFrame:
    """Keep only the last `years` years, counted back from the newest candle."""
    if frame.empty:
        return frame
    newest = frame["time"].max()
    if float(years).is_integer():
        cutoff = newest - pd.DateOffset(years=int(years))
    else:
        cutoff = newest - pd.Timedelta(days=365.25 * float(years))
    return frame[frame["time"] >= cutoff].reset_index(drop=True)


def _utc(value) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")


def load_m1(symbol: str, store_dir: Optional[Path] = None) -> pd.DataFrame:
    """All stored 1-minute candles for an instrument. Empty if nothing is stored yet."""
    path = store_path(symbol, store_dir)
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS).astype({"time": "datetime64[ns, UTC]"})
    frame = pd.read_parquet(path)
    frame["time"] = pd.to_datetime(frame["time"], utc=True)
    return frame[COLUMNS]


def last_time(symbol: str, store_dir: Optional[Path] = None) -> Optional[pd.Timestamp]:
    """Time of the newest stored candle, or None if nothing is stored."""
    path = store_path(symbol, store_dir)
    if not path.exists():
        return None
    times = pd.read_parquet(path, columns=["time"])["time"]
    return pd.to_datetime(times, utc=True).max() if len(times) else None


def save_m1(symbol: str, frame: pd.DataFrame, store_dir: Optional[Path] = None) -> Path:
    """Write the file safely: a temporary file first, then swap it in."""
    path = store_path(symbol, store_dir)
    ensure_dir(path.parent)
    temporary = path.with_suffix(".tmp")
    frame[COLUMNS].to_parquet(temporary, index=False)
    os.replace(temporary, path)
    return path


def merge_m1(
    symbol: str,
    new_candles: pd.DataFrame,
    years: float = DEFAULT_YEARS,
    store_dir: Optional[Path] = None,
) -> MergeResult:
    """Add new candles, remove duplicates (new data wins), trim the window, save."""
    existing = load_m1(symbol, store_dir)
    fresh, rejected = clean_frame(new_candles) if len(new_candles) else (existing.iloc[0:0], 0)
    pieces = [piece for piece in (existing, fresh) if len(piece)]
    combined = pd.concat(pieces, ignore_index=True) if pieces else existing
    combined = combined.drop_duplicates(subset="time", keep="last").sort_values("time").reset_index(drop=True)
    trimmed = trim_window(combined, years)
    save_m1(symbol, trimmed, store_dir)
    return MergeResult(
        symbol=symbol.upper(),
        rows_before=len(existing),
        rows_received=len(fresh),
        rows_after=len(trimmed),
        rows_trimmed=len(combined) - len(trimmed),
        rows_rejected=rejected,
        first=trimmed["time"].iloc[0] if len(trimmed) else None,
        last=trimmed["time"].iloc[-1] if len(trimmed) else None,
    )


def load_candles(
    symbol: str,
    timeframe: str = "M1",
    store_dir: Optional[Path] = None,
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
    as_of: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """Candles for any supported timeframe, built from the stored 1-minute candles."""
    m1 = load_m1(symbol, store_dir)
    candles = synthesizer.build(m1, timeframe, as_of=as_of)
    if start is not None:
        candles = candles[candles["time"] >= _utc(start)]
    if end is not None:
        candles = candles[candles["time"] <= _utc(end)]
    return candles.reset_index(drop=True)


def status(symbol: str, store_dir: Optional[Path] = None) -> Dict[str, object]:
    """A short health report for one instrument."""
    frame = load_m1(symbol, store_dir)
    if frame.empty:
        return {"symbol": symbol.upper(), "rows": 0}
    gaps = frame["time"].diff().dropna()
    longest = gaps.max() if len(gaps) else pd.Timedelta(0)
    first, last = frame["time"].iloc[0], frame["time"].iloc[-1]
    return {
        "symbol": symbol.upper(),
        "rows": len(frame),
        "first": first,
        "last": last,
        "years_covered": round((last - first).days / 365.25, 2),
        "longest_gap_hours": round(longest.total_seconds() / 3600, 1),
        "gaps_over_3_days": int((gaps > pd.Timedelta(days=3)).sum()),
    }


def export_for_backtester(
    symbol: str,
    timeframes: Iterable[str] = BACKTEST_TIMEFRAMES,
    store_dir: Optional[Path] = None,
    raw_dir: Optional[Path] = None,
) -> List[Path]:
    """Write the CSV files the existing backtest loader reads (data/raw/<SYMBOL>_<TF>.csv)."""
    target = ensure_dir(Path(raw_dir or RAW_DIR), ignore_pattern="*.csv")
    m1 = load_m1(symbol, store_dir)
    clean_symbol = store_path(symbol, store_dir).name.replace("_M1.parquet", "")
    written = []
    for timeframe in timeframes:
        candles = synthesizer.build(m1, timeframe)
        path = target / f"{clean_symbol}_{timeframe.upper()}.csv"
        candles.to_csv(path, index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
        written.append(path)
    return written