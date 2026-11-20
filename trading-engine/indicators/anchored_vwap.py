"""Calculate an anchored VWAP from caller-supplied price and volume values."""

import math
from numbers import Real
from typing import Iterable


def calculate_anchored_vwap(
    prices_since_anchor: Iterable[float],
    volumes_since_anchor: Iterable[float],
) -> float:
    """Return cumulative price-volume divided by cumulative volume.

    Inputs must be chronological and start at the selected anchor candle. The
    caller chooses the price source and provides volume values; this function
    does not select an anchor or infer volume from candle ranges.
    """
    prices = tuple(
        _positive_price("price", price) for price in prices_since_anchor
    )
    volumes = tuple(
        _nonnegative_volume(volume) for volume in volumes_since_anchor
    )
    if not prices or len(prices) != len(volumes):
        raise ValueError(
            "Prices and volumes must have the same nonzero number of values."
        )

    weighted_prices = [price * volume for price, volume in zip(prices, volumes)]
    if not all(math.isfinite(value) for value in weighted_prices):
        raise ValueError("Price-volume products must be finite.")
    try:
        total_volume = math.fsum(volumes)
        total_weighted_price = math.fsum(weighted_prices)
    except OverflowError as error:
        raise ValueError("The supplied values produce a non-finite VWAP.") from error
    if not math.isfinite(total_volume) or total_volume <= 0:
        raise ValueError("At least one positive volume value is required.")

    anchored_vwap = total_weighted_price / total_volume
    if not math.isfinite(anchored_vwap):
        raise ValueError("The supplied values produce a non-finite VWAP.")
    return anchored_vwap


def _positive_price(name: str, value: float) -> float:
    number = _finite_number(name, value)
    if number <= 0:
        raise ValueError(f"{name} must be positive.")
    return number


def _nonnegative_volume(value: float) -> float:
    number = _finite_number("volume", value)
    if number < 0:
        raise ValueError("volume must not be negative.")
    return number


def _finite_number(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number.")
    return number
