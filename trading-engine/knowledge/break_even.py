"""Report whether a supplied stop is at entry and where the quote is."""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal


PositionSide = Literal["LONG", "SHORT"]


@dataclass(frozen=True)
class BreakEvenObservation:
    position_side: PositionSide
    stop_is_at_entry: bool
    quote_is_at_entry: bool
    entry_price: float
    stop_loss_price: float
    reference_price: float
    time: datetime
    description: str


def _price_tick(price: float, tick_size: float) -> int:
    return int(
        (Decimal(str(price)) / Decimal(str(tick_size))).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


def analyze_break_even(
    position_side: PositionSide,
    entry_price: float,
    stop_loss_price: float,
    tick_size: float,
    bid: float,
    ask: float,
    quote_time: datetime,
) -> BreakEvenObservation:
    """Report stop-at-entry and quote-at-entry facts without moving a stop."""
    if position_side not in ("LONG", "SHORT"):
        raise ValueError("position_side must be either 'LONG' or 'SHORT'.")
    prices = (entry_price, stop_loss_price, tick_size, bid, ask)
    if not all(math.isfinite(price) and price > 0 for price in prices):
        raise ValueError("All prices and tick_size must be positive finite numbers.")
    if bid > ask:
        raise ValueError("bid must not be greater than ask.")
    if quote_time.tzinfo is None or quote_time.utcoffset() != timedelta(0):
        raise ValueError("quote_time must be timezone-aware UTC.")

    reference_price = bid if position_side == "LONG" else ask
    stop_is_at_entry = _price_tick(stop_loss_price, tick_size) == _price_tick(
        entry_price,
        tick_size,
    )
    quote_is_at_entry = _price_tick(reference_price, tick_size) == _price_tick(
        entry_price,
        tick_size,
    )
    side_label = position_side.lower()
    stop_state = (
        "is at the entry price tick"
        if stop_is_at_entry
        else "is not at the entry price tick"
    )
    quote_state = (
        "is at the entry price tick"
        if quote_is_at_entry
        else "is not at the entry price tick"
    )
    description = (
        f"The {side_label} stop-loss {stop_state}; the current quote "
        f"({reference_price}) {quote_state}. Price comparison does not include "
        "spread, commission, or other trading costs."
    )

    return BreakEvenObservation(
        position_side=position_side,
        stop_is_at_entry=stop_is_at_entry,
        quote_is_at_entry=quote_is_at_entry,
        entry_price=entry_price,
        stop_loss_price=stop_loss_price,
        reference_price=reference_price,
        time=quote_time,
        description=description,
    )
