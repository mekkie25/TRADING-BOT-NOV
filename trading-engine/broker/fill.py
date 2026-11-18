import math

from engine.models import Direction


def market_fill_price(
    reference_mid_price: float,
    order_side: Direction,
    pip_size: float,
    spread_pips: float,
    slippage_pips: float,
) -> float:
    """Fill a market order at ask for buys or bid for sells, including slippage."""
    values = (reference_mid_price, pip_size, spread_pips, slippage_pips)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Fill inputs must be finite numbers")
    if reference_mid_price <= 0 or pip_size <= 0:
        raise ValueError("Reference price and pip_size must be positive")
    if spread_pips < 0 or slippage_pips < 0:
        raise ValueError("Spread and slippage must be non-negative")

    adjustment = (spread_pips / 2 + slippage_pips) * pip_size
    if order_side == Direction.BUY:
        return reference_mid_price + adjustment
    if order_side == Direction.SELL:
        return reference_mid_price - adjustment
    raise ValueError(f"Unsupported order side: {order_side}")