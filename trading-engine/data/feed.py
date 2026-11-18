"""
Module: Data Feed & Bar Aggregator
Depends on: common.py

Purpose: Manages historical data, reconstructs higher timeframes 
without look-ahead bias, and provides a clean interface for the simulator.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, Generator, Dict, Any
import bisect

from knowledge.common import validate_candles

# ==========================================
# 1. ZERO LOOK-AHEAD AGGREGATOR
# ==========================================
class ZeroLookAheadAggregator:
    """
    Reconstructs H1, H4, D1 from M5 data in O(1) time.
    Ensures that at any given timestamp, the HTF candles only reflect 
    data that would have been available in real-time.
    """
    def __init__(self, d1_history: pd.DataFrame, h4_history: pd.DataFrame, h1_history: pd.DataFrame):
        self.d1_all = d1_history.copy()
        self.h4_all = h4_history.copy()
        self.h1_all = h1_history.copy()

        for df in [self.d1_all, self.h4_all, self.h1_all]:
            if not isinstance(df.index, pd.DatetimeIndex):
                df['time'] = pd.to_datetime(df['time'], utc=True)
                df.set_index('time', inplace=True)
                df.sort_index(inplace=True)

        # Precompute close timestamps for fast binary search
        self._d1_close_epochs = [int((t + pd.Timedelta(hours=24)).timestamp()) for t in self.d1_all.index]
        self._h4_close_epochs = [int((t + pd.Timedelta(hours=4)).timestamp()) for t in self.h4_all.index]
        self._h1_close_epochs = [int((t + pd.Timedelta(hours=1)).timestamp()) for t in self.h1_all.index]

        # Pre-allocated buffers (150 for D1 is standard warmup)
        self._d1_buffer = self._init_buffer(self.d1_all, 150)
        self._h4_buffer = self._init_buffer(self.h4_all, 30)
        self._h1_buffer = self._init_buffer(self.h1_all, 30)

    def _init_buffer(self, source_df: pd.DataFrame, size: int) -> pd.DataFrame:
        cols = ['open', 'high', 'low', 'close', 'volume']
        sample = source_df[cols].tail(size).copy().reset_index()
        if len(sample) < size:
            pad = pd.DataFrame(index=range(size - len(sample)), columns=cols)
            sample = pd.concat([pad, sample], ignore_index=True)
        return sample

    def get_feeds_at_time(self, m5_history_up_to_t: pd.DataFrame, current_time_utc: datetime) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        curr_epoch = int(current_time_utc.timestamp())
        m5_times = pd.to_datetime(m5_history_up_to_t['time'], utc=True)

        # --- 1. DAILY ---
        d1_idx = bisect.bisect_right(self._d1_close_epochs, curr_epoch)
        last_d1_open_hour = self.d1_all.index[d1_idx - 1].hour if d1_idx > 0 else 21
        d1_start = current_time_utc.replace(hour=last_d1_open_hour, minute=0, second=0, microsecond=0)
        if current_time_utc < d1_start:
            d1_start -= timedelta(days=1)
            
        m5_today = m5_history_up_to_t[m5_times >= d1_start]
        if not m5_today.empty:
            self._d1_buffer.iloc[149] = [
                float(m5_today['open'].iloc[0]), float(m5_today['high'].max()),
                float(m5_today['low'].min()), float(m5_today['close'].iloc[-1]),
                int(m5_today['volume'].sum())
            ]
            active_d1 = self._d1_buffer.copy()
            active_d1['time'] = self.d1_all.index[max(0, d1_idx - 150):d1_idx].tolist() + [d1_start]
        else:
            active_d1 = self._d1_buffer.iloc[:149].copy()
            active_d1['time'] = self.d1_all.index[max(0, d1_idx - 149):d1_idx].tolist()

        # --- 2. H4 ---
        h4_idx = bisect.bisect_right(self._h4_close_epochs, curr_epoch)
        h4_start_hour = (current_time_utc.hour // 4) * 4
        h4_start = current_time_utc.replace(hour=h4_start_hour, minute=0, second=0, microsecond=0)
        
        m5_h4 = m5_history_up_to_t[m5_times >= h4_start]
        if not m5_h4.empty:
            self._h4_buffer.iloc[29] = [
                float(m5_h4['open'].iloc[0]), float(m5_h4['high'].max()),
                float(m5_h4['low'].min()), float(m5_h4['close'].iloc[-1]),
                int(m5_h4['volume'].sum())
            ]
            active_h4 = self._h4_buffer.copy()
            active_h4['time'] = self.h4_all.index[max(0, h4_idx - 30):h4_idx].tolist() + [h4_start]
        else:
            active_h4 = self._h4_buffer.iloc[:29].copy()
            active_h4['time'] = self.h4_all.index[max(0, h4_idx - 29):h4_idx].tolist()

        # --- 3. H1 ---
        h1_idx = bisect.bisect_right(self._h1_close_epochs, curr_epoch)
        h1_start = current_time_utc.replace(minute=0, second=0, microsecond=0)
        
        m5_h1 = m5_history_up_to_t[m5_times >= h1_start]
        if not m5_h1.empty:
            self._h1_buffer.iloc[29] = [
                float(m5_h1['open'].iloc[0]), float(m5_h1['high'].max()),
                float(m5_h1['low'].min()), float(m5_h1['close'].iloc[-1]),
                int(m5_h1['volume'].sum())
            ]
            active_h1 = self._h1_buffer.copy()
            active_h1['time'] = self.h1_all.index[max(0, h1_idx - 30):h1_idx].tolist() + [h1_start]
        else:
            active_h1 = self._h1_buffer.iloc[:29].copy()
            active_h1['time'] = self.h1_all.index[max(0, h1_idx - 29):h1_idx].tolist()

        return active_h1, active_h4, active_d1


# ==========================================
# 2. DATA FEED MANAGER
# ==========================================
@dataclass
class FeedConfig:
    symbol: str
    timeframe: str = "M5"
    warmup_bars: int = 120

class DataFeed:
    def __init__(self, m5_df: pd.DataFrame, h1_df: pd.DataFrame, h4_df: pd.DataFrame, d1_df: pd.DataFrame, config: FeedConfig):
        self.config = config
        
        # 1. Validate all DataFrames
        for name, df in [("M5", m5_df), ("H1", h1_df), ("H4", h4_df), ("D1", d1_df)]:
            val = validate_candles(df)
            if not val.is_valid:
                raise ValueError(f"Invalid {name} data: {val.error_message}")
                
        # 2. Sort and reset index
        self.m5 = m5_df.sort_values('time').reset_index(drop=True)
        self.h1 = h1_df.sort_values('time').reset_index(drop=True)
        self.h4 = h4_df.sort_values('time').reset_index(drop=True)
        self.d1 = d1_df.sort_values('time').reset_index(drop=True)
        
        # 3. Initialize Aggregator
        self.aggregator = ZeroLookAheadAggregator(self.d1, self.h4, self.h1)
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """
        Yields a context dictionary for each M5 bar. 
        The simulator will loop over this.
        """
        total_bars = len(self.m5)
        
        for i in range(self.config.warmup_bars, total_bars):
            current_candle = self.m5.iloc[i]
            current_time = current_candle['time'].to_pydatetime()
            
            # Get historical M5 slice up to current bar
            hist_m5 = self.m5.iloc[:i+1].copy()
            
            # Reconstruct HTF
            h1_view, h4_view, d1_view = self.aggregator.get_feeds_at_time(hist_m5, current_time)
            
            yield {
                "bar_index": i,
                "time": current_candle['time'],
                "m5_df": hist_m5,
                "h1_df": h1_view,
                "h4_df": h4_view,
                "d1_df": d1_view,
                "current_candle": current_candle,
            }

# ==========================================
# 3. LOADER (For CSV / Parquet)
# ==========================================
def load_feed_from_csv(symbol: str, data_dir: str = "data/") -> DataFeed:
    """Loads all 4 timeframes from CSV."""
    def read_csv(tf):
        path = f"{data_dir}{symbol}_{tf}.csv"
        df = pd.read_csv(path)
        df['time'] = pd.to_datetime(df['time'], utc=True)
        return df

    m5 = read_csv("M5")
    h1 = read_csv("H1")
    h4 = read_csv("H4")
    d1 = read_csv("D1")
    
    return DataFeed(m5, h1, h4, d1, FeedConfig(symbol=symbol))