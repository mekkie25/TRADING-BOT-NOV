# trading-engine/knowledge/common.py
import pandas as pd
from dataclasses import dataclass

@dataclass
class CandleValidation:
    is_valid: bool
    error_message: str = ""

def validate_candles(df: pd.DataFrame) -> CandleValidation:
    required_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            return CandleValidation(False, f"Missing required column: {col}")
    if df.empty:
        return CandleValidation(False, "DataFrame is empty")
    if not pd.api.types.is_datetime64_any_dtype(df['time']):
        return CandleValidation(False, "Column 'time' must be a datetime type")
    if (df['high'] < df['low']).any():
        return CandleValidation(False, "Found candles where High is less than Low")
    if (df['high'] < df['open']).any() or (df['high'] < df['close']).any():
        return CandleValidation(False, "Found candles where High is not the highest price")
    if (df['low'] > df['open']).any() or (df['low'] > df['close']).any():
        return CandleValidation(False, "Found candles where Low is not the lowest price")
    return CandleValidation(True)