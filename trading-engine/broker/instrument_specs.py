"""Price-distance and quote specifications for supported instruments."""

from dataclasses import dataclass
import math
from typing import Dict, Literal, Optional


DistanceUnit = Literal["price", "pips", "points", "ticks"]


@dataclass(frozen=True)
class InstrumentSpec:
    symbol: str
    pip_size: Optional[float] = None
    point_size: Optional[float] = None
    tick_size: Optional[float] = None
    pip_value_per_lot: Optional[float] = None
    point_value_per_lot: Optional[float] = None

    def price_distance(self, distance: float, unit: DistanceUnit) -> float:
        if isinstance(distance, bool) or not math.isfinite(float(distance)) or distance < 0:
            raise ValueError("distance must be finite and non-negative.")
        if unit == "price":
            return float(distance)
        size = {
            "pips": self.pip_size,
            "points": self.point_size,
            "ticks": self.tick_size,
        }.get(unit)
        if size is None:
            raise ValueError(f"{unit} size is not configured for {self.symbol}.")
        if not math.isfinite(size) or size <= 0:
            raise ValueError(f"Configured {unit} size must be positive and finite.")
        return float(distance) * size


DEFAULT_INSTRUMENT_SPECS: Dict[str, InstrumentSpec] = {
    "EURUSD": InstrumentSpec("EURUSD", pip_size=0.0001),
    "XAUUSD": InstrumentSpec("XAUUSD", pip_size=0.10),
    "US30": InstrumentSpec("US30", point_size=1.0),
    "NAS100": InstrumentSpec("NAS100", point_size=1.0),
    "NASDAQ": InstrumentSpec("NASDAQ", point_size=1.0),
    "DAX": InstrumentSpec("DAX", point_size=1.0),
}


def get_instrument_spec(
    symbol: str,
    overrides: Optional[Dict[str, InstrumentSpec]] = None,
) -> InstrumentSpec:
    """Return a configured spec; unknown symbols require explicit units."""
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise ValueError("symbol must not be empty.")
    if overrides:
        override = overrides.get(normalized_symbol)
        if override is not None:
            return override
    spec = DEFAULT_INSTRUMENT_SPECS.get(normalized_symbol)
    if spec is not None:
        return spec
    return InstrumentSpec(normalized_symbol)
