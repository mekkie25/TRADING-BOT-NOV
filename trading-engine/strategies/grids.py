"""$5 Grids for Gold (spec Section 3.19).

Grid lines sit every grid_size dollars (default 5.0, so 2400, 2405, 2410 ...).
Price approaches a line, rejects it and holds it:
  * Long when the line holds as support (candles close above it, lows stay near it).
  * Short when the line holds as resistance (candles close below it, highs stay near it).

"Rejection and hold" is not defined in the spec. It uses the shared hold
definition from Section 11 (hold_candles closes beyond the line, wicks inside the
tolerance, at least one candle touching the line). Entry is on the confirming
candle close, never a pending order.

Stop: past the midpoint of the grid interval on the far side of the line
(stop_grid_fraction 0.5 = $2.50 on a $5 grid), plus the usual structural buffer.
Target: the next grid line in the trade direction.

Spec conflict (kept as written): the spec says a 25 to 35 pip stop and a 50 pip
target, and also "1:1". Those do not match. stop_grid_fraction 1.0 gives 1:1.

Stops and targets default to structural (the grid maths). Fixed and
volatility-scaled modes stay selectable through sl_mode and tp_mode.
"""

import math
from typing import Dict, Optional

import pandas as pd

from broker.instrument_specs import InstrumentSpec
from engine.models import Direction, Signal
from knowledge.operational_definitions import level_holds
from strategies.common import instrument_default_distance_unit, make_signal
from strategies.context import MarketFacts


def _nearest_line(price: float, grid_size: float) -> float:
    return math.floor(price / grid_size + 0.5) * grid_size


def evaluate(
    candles: pd.DataFrame,
    facts: MarketFacts,
    instrument_spec: InstrumentSpec,
    parameters: Optional[Dict[str, object]] = None,
) -> Optional[Signal]:
    settings: Dict[str, object] = {"sl_mode": "structural", "tp_mode": "structural"}
    settings.update(parameters or {})

    grid_size = float(settings.get("grid_size", 5.0))
    if not math.isfinite(grid_size) or grid_size <= 0:
        raise ValueError("grid_size must be a positive number.")
    stop_fraction = float(settings.get("stop_grid_fraction", 0.5))
    if not math.isfinite(stop_fraction) or not 0 < stop_fraction <= 1:
        raise ValueError("stop_grid_fraction must be greater than 0 and at most 1.")
    hold_candles = settings.get("hold_candles", 2)
    if isinstance(hold_candles, bool) or not isinstance(hold_candles, int) or hold_candles < 1:
        raise ValueError("hold_candles must be a whole number of 1 or more.")

    acs = facts.average_candle_size
    if acs is None or not math.isfinite(acs) or acs <= 0:
        return None
    if len(candles) < hold_candles:
        return None

    tolerance_acs = float(settings.get("hold_wick_tolerance_acs", 0.25))
    break_acs = float(settings.get("break_distance_acs", 0.0))
    window = candles.tail(hold_candles)

    support = _nearest_line(float(window["low"].min()), grid_size)
    resistance = _nearest_line(float(window["high"].max()), grid_size)

    if support > 0 and level_holds(
        candles, support, "bullish", acs, hold_candles, tolerance_acs, break_acs
    ):
        direction = Direction.BUY
        stop = support - grid_size * stop_fraction
        target = support + grid_size
    elif resistance > 0 and level_holds(
        candles, resistance, "bearish", acs, hold_candles, tolerance_acs, break_acs
    ):
        direction = Direction.SELL
        stop = resistance + grid_size * stop_fraction
        target = resistance - grid_size
    else:
        return None

    return make_signal(
        name="grids",
        variant="grid_hold",
        direction=direction,
        candles=candles,
        facts=facts,
        instrument_spec=instrument_spec,
        parameters=settings,
        structural_stop_price=stop,
        structural_target_price=target,
        default_stop=25,
        default_target=50,
        default_distance_unit=instrument_default_distance_unit(instrument_spec),
    )