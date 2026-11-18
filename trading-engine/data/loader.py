"""
Module: Data Loader
Purpose: Loads historical CSVs and converts them into the DataFeed object.
"""
import os
import pandas as pd
from .feed import DataFeed, FeedConfig

DATA_DIR = os.path.join(os.path.dirname(__file__), "raw")

def load_symbol(symbol: str) -> DataFeed:
    """
    Loads M5, H1, H4, D1 CSVs for a symbol and returns a DataFeed.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    
    def _read(tf):
        path = os.path.join(DATA_DIR, f"{symbol}_{tf}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing data file: {path}. Run downloader.py first.")
            
        df = pd.read_csv(path)
        # Ensure time is properly parsed
        df['time'] = pd.to_datetime(df['time'], utc=True)
        # Ensure correct types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.dropna().reset_index(drop=True)

    print(f"[*] Loading {symbol}...")
    m5 = _read("M5")
    h1 = _read("H1")
    h4 = _read("H4")
    d1 = _read("D1")
    print(f"[+] Loaded {len(m5):,} M5 bars, {len(h1):,} H1 bars, {len(d1):,} D1 bars.")
    
    return DataFeed(m5, h1, h4, d1, FeedConfig(symbol=symbol))