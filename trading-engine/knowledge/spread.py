"""Report the bid/ask spread without judging whether it is tradable."""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass(frozen=True)
class SpreadReport:
    symbol: str
    time: datetime
    bid: float
    ask: float
    spread_price: float
    spread_pips: Optional[float]
    spread_ticks: Optional[float]
    summary: str


def analyze_spread(
    symbol: str,
    time: datetime,
    bid: float,
    ask: float,
    pip_size: Optional[float] = None,
    tick_size: Optional[float] = None,
) -> SpreadReport:
    """Report ask minus bid, converting units only when their sizes are supplied."""
    if not symbol.strip():
        raise ValueError("symbol must not be empty.")
    if time.tzinfo is None or time.utcoffset() != timedelta(0):
        raise ValueError("time must be timezone-aware UTC.")
    if not all(math.isfinite(price) and price > 0 for price in (bid, ask)):
        raise ValueError("bid and ask must be positive finite prices.")
    if ask < bid:
        raise ValueError("ask must not be less than bid.")
    if pip_size is not None and (not math.isfinite(pip_size) or pip_size <= 0):
        raise ValueError("pip_size must be a positive finite price size.")
    if tick_size is not None and (not math.isfinite(tick_size) or tick_size <= 0):
        raise ValueError("tick_size must be a positive finite price size.")

    spread_price = ask - bid
    spread_pips = spread_price / pip_size if pip_size is not None else None
    spread_ticks = spread_price / tick_size if tick_size is not None else None

    measurements = [f"{spread_price:g} price units"]
    if spread_pips is not None:
        measurements.append(f"{spread_pips:g} pips")
    if spread_ticks is not None:
        measurements.append(f"{spread_ticks:g} ticks")
    summary = (
        f"{symbol} spread was {'; '.join(measurements)} at "
        f"{time.isoformat()}."
    )
    if spread_pips is None:
        summary += " Pip size was not supplied, so no pip conversion was made."

    return SpreadReport(
        symbol=symbol,
        time=time,
        bid=bid,
        ask=ask,
        spread_price=spread_price,
        spread_pips=spread_pips,
        spread_ticks=spread_ticks,
        summary=summary,
    )
