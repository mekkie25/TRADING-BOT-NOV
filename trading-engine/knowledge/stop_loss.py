"""Report a supplied stop-loss level against the current market quote."""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal


PositionSide = Literal["LONG", "SHORT"]
StopLossStatus = Literal["reached", "not_reached"]


@dataclass(frozen=True)
class StopLossObservation:
    position_side: PositionSide
    status: StopLossStatus
    stop_loss_price: float
    reference_price: float
    time: datetime
    description: str


def analyze_stop_loss(
    position_side: PositionSide,
    stop_loss_price: float,
    bid: float,
    ask: float,
    quote_time: datetime,
) -> StopLossObservation:
    """Report whether the quote has reached a supplied stop-loss level."""
    if position_side not in ("LONG", "SHORT"):
        raise ValueError("position_side must be either 'LONG' or 'SHORT'.")
    if not all(math.isfinite(price) and price > 0 for price in (stop_loss_price, bid, ask)):
        raise ValueError("stop_loss_price, bid, and ask must be positive finite prices.")
    if bid > ask:
        raise ValueError("bid must not be greater than ask.")
    if quote_time.tzinfo is None or quote_time.utcoffset() != timedelta(0):
        raise ValueError("quote_time must be timezone-aware UTC.")

    reference_price = bid if position_side == "LONG" else ask
    reached = (
        reference_price <= stop_loss_price
        if position_side == "LONG"
        else reference_price >= stop_loss_price
    )
    status: StopLossStatus = "reached" if reached else "not_reached"
    level_state = "has reached or passed" if reached else "has not reached"
    side_label = position_side.lower()
    price_name = "bid" if position_side == "LONG" else "ask"
    description = (
        f"The {side_label} stop-loss level at {stop_loss_price} {level_state}; "
        f"the current {price_name} is {reference_price}."
    )

    return StopLossObservation(
        position_side=position_side,
        status=status,
        stop_loss_price=stop_loss_price,
        reference_price=reference_price,
        time=quote_time,
        description=description,
    )
