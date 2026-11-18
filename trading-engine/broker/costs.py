import math


def calculate_round_trip_commission(
    size_lots: float,
    commission_per_lot_per_side: float,
) -> float:
    """Return commission for opening and closing a position."""
    if not math.isfinite(size_lots) or size_lots < 0:
        raise ValueError("size_lots must be a finite non-negative number")
    if not math.isfinite(commission_per_lot_per_side) or commission_per_lot_per_side < 0:
        raise ValueError("commission must be a finite non-negative number")
    return size_lots * commission_per_lot_per_side * 2