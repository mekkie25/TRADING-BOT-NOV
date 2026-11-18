"""Supported candle timeframe lengths shared by data and simulation code."""

from datetime import timedelta


TIMEFRAME_LENGTHS = {
    "M1": timedelta(minutes=1),
    "M5": timedelta(minutes=5),
    "M15": timedelta(minutes=15),
    "M30": timedelta(minutes=30),
    "H1": timedelta(hours=1),
    "H2": timedelta(hours=2),
    "H4": timedelta(hours=4),
    "D1": timedelta(days=1),
}
