"""Calculate a broker-valid position size from explicit risk and symbol data."""

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Optional


LotSizingStatus = Literal["sized", "below_minimum", "capped_at_maximum"]


@dataclass(frozen=True)
class BrokerInstrumentSpec:
    symbol: str
    tick_size: Optional[float]
    tick_value_per_lot: Optional[float]
    units_per_lot: int
    minimum_volume_units: int
    volume_step_units: int
    maximum_volume_units: int
    price_value_per_lot: Optional[float] = None


@dataclass(frozen=True)
class LotSizingReport:
    symbol: str
    status: LotSizingStatus
    risk_budget_cash: float
    planned_loss_cash: float
    stop_distance: float
    stop_distance_ticks: Optional[float]
    volume_units: int
    lots: float
    summary: str


def calculate_lot_size(
    account_equity: float,
    risk_percent: float,
    entry_price: float,
    stop_loss_price: float,
    instrument: BrokerInstrumentSpec,
) -> LotSizingReport:
    """Round down to broker volume steps; never round up past the risk budget."""
    if not instrument.symbol.strip():
        raise ValueError("instrument symbol must not be empty.")
    if not math.isfinite(account_equity) or account_equity <= 0:
        raise ValueError("account_equity must be a positive finite amount.")
    if not math.isfinite(risk_percent) or not 0 < risk_percent <= 100:
        raise ValueError("risk_percent must be greater than 0 and no more than 100.")
    if not all(
        math.isfinite(price) and price > 0
        for price in (entry_price, stop_loss_price)
    ):
        raise ValueError("Entry and stop-loss prices must be positive and finite.")
    has_tick_value = (
        instrument.tick_size is not None
        or instrument.tick_value_per_lot is not None
    )
    if instrument.price_value_per_lot is not None:
        if has_tick_value:
            raise ValueError(
                "Provide either tick values or price_value_per_lot, not both."
            )
        if (
            not math.isfinite(instrument.price_value_per_lot)
            or instrument.price_value_per_lot <= 0
        ):
            raise ValueError(
                "price_value_per_lot must be a positive finite amount."
            )
    else:
        if instrument.tick_size is None or instrument.tick_size <= 0:
            raise ValueError("tick_size must be a positive finite price size.")
        if (
            instrument.tick_value_per_lot is None
            or not math.isfinite(instrument.tick_value_per_lot)
            or instrument.tick_value_per_lot <= 0
        ):
            raise ValueError("tick_value_per_lot must be a positive finite amount.")
        if not math.isfinite(instrument.tick_size):
            raise ValueError("tick_size must be a positive finite price size.")

    volume_values = (
        instrument.units_per_lot,
        instrument.minimum_volume_units,
        instrument.volume_step_units,
        instrument.maximum_volume_units,
    )
    if any(not isinstance(value, int) or isinstance(value, bool) for value in volume_values):
        raise ValueError("Broker volume specifications must be integers.")
    if (
        instrument.units_per_lot <= 0
        or instrument.minimum_volume_units <= 0
        or instrument.volume_step_units <= 0
        or instrument.maximum_volume_units < instrument.minimum_volume_units
    ):
        raise ValueError("Broker volume specifications are inconsistent.")

    entry = Decimal(str(entry_price))
    stop = Decimal(str(stop_loss_price))
    distance = abs(entry - stop)
    if distance <= 0:
        raise ValueError("Entry and stop-loss prices must be different.")

    risk_budget_cash = account_equity * risk_percent / 100
    if instrument.price_value_per_lot is not None:
        stop_distance_ticks = None
        risk_per_lot = float(distance) * instrument.price_value_per_lot
    else:
        tick_size = Decimal(str(instrument.tick_size))
        ticks = distance / tick_size
        if ticks != ticks.to_integral_value():
            raise ValueError("Stop distance must be a whole number of broker ticks.")
        stop_distance_ticks = float(ticks)
        risk_per_lot = float(ticks) * instrument.tick_value_per_lot
    raw_volume_units = (
        Decimal(str(risk_budget_cash))
        / Decimal(str(risk_per_lot))
        * Decimal(instrument.units_per_lot)
    )
    minimum = Decimal(instrument.minimum_volume_units)
    step = Decimal(instrument.volume_step_units)
    maximum = Decimal(instrument.maximum_volume_units)

    if raw_volume_units < minimum:
        return LotSizingReport(
            symbol=instrument.symbol,
            status="below_minimum",
            risk_budget_cash=risk_budget_cash,
            planned_loss_cash=0.0,
            stop_distance=float(distance),
            stop_distance_ticks=stop_distance_ticks,
            volume_units=0,
            lots=0.0,
            summary=(
                f"No broker-valid size for {instrument.symbol} fits the "
                f"{risk_budget_cash:g} risk budget; the minimum volume "
                "would exceed it."
            ),
        )

    maximum_valid = minimum + (
        (maximum - minimum) // step
    ) * step
    if raw_volume_units > maximum_valid:
        volume_units = int(maximum_valid)
        status: LotSizingStatus = "capped_at_maximum"
    else:
        steps = (raw_volume_units - minimum) // step
        volume_units = int(minimum + steps * step)
        status = "sized"

    lots = volume_units / instrument.units_per_lot
    planned_loss_cash = lots * risk_per_lot
    summary = (
        f"{instrument.symbol} size is {lots:g} lots ({volume_units} units), "
        f"with a planned stop loss of {planned_loss_cash:g} against a "
        f"{risk_budget_cash:g} risk budget."
    )
    if status == "capped_at_maximum":
        summary += " The broker maximum volume limits the size."

    return LotSizingReport(
        symbol=instrument.symbol,
        status=status,
        risk_budget_cash=risk_budget_cash,
        planned_loss_cash=planned_loss_cash,
        stop_distance=float(distance),
        stop_distance_ticks=stop_distance_ticks,
        volume_units=volume_units,
        lots=lots,
        summary=summary,
    )
