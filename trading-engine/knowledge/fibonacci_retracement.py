"""Calculate Fibonacci levels between two caller-supplied price points."""

import math
from dataclasses import dataclass
from numbers import Real
from typing import Iterable, List


DEFAULT_FIBONACCI_RATIOS = (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0)


@dataclass(frozen=True)
class FibonacciLevel:
    ratio: float
    price: float


def calculate_fibonacci_levels(
    price_point_1: float,
    price_point_2: float,
    ratios: Iterable[float] = DEFAULT_FIBONACCI_RATIOS,
    logarithmic: bool = False,
) -> List[FibonacciLevel]:
    """Calculate levels in point order without choosing or labeling trade zones.

    Ratios below zero and above one are accepted for extensions. Logarithmic
    interpolation is available only when explicitly requested.
    """
    first_price = _positive_price("price_point_1", price_point_1)
    second_price = _positive_price("price_point_2", price_point_2)
    if not isinstance(logarithmic, bool):
        raise ValueError("logarithmic must be a boolean.")

    supplied_ratios = tuple(_finite_number("ratio", ratio) for ratio in ratios)
    if not supplied_ratios:
        raise ValueError("At least one Fibonacci ratio must be supplied.")
    if len(set(supplied_ratios)) != len(supplied_ratios):
        raise ValueError("Fibonacci ratios must be unique.")

    levels = []
    for ratio in supplied_ratios:
        if logarithmic:
            log_price = math.log(first_price) + (
                math.log(second_price) - math.log(first_price)
            ) * ratio
            try:
                price = math.exp(log_price)
            except OverflowError as error:
                raise ValueError(
                    "The ratio produces a non-finite logarithmic price."
                ) from error
        else:
            price = first_price + (second_price - first_price) * ratio
        if not math.isfinite(price):
            raise ValueError("The ratio produces a non-finite Fibonacci price.")
        levels.append(FibonacciLevel(ratio=ratio, price=price))
    return levels


def _positive_price(name: str, value: float) -> float:
    price = _finite_number(name, value)
    if price <= 0:
        raise ValueError(f"{name} must be positive.")
    return price


def _finite_number(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number.")
    return number
