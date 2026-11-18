"""Convert cTrader Forex symbol fields into the lot-sizing input."""

from typing import Optional, Protocol

from broker.lot_sizing import BrokerInstrumentSpec


class CTraderSymbolInfo(Protocol):
    symbol: str
    base_asset_id: int
    quote_asset_id: int
    digits: int
    pip_position: int
    lot_size_cents: int
    minimum_volume_cents: int
    volume_step_cents: int
    maximum_volume_cents: int
    maximum_exposure_cents: Optional[int]


def build_ctrader_forex_spec(
    symbol_info: CTraderSymbolInfo,
    deposit_asset_id: int,
) -> BrokerInstrumentSpec:
    """Build a Forex spec only when its quote asset matches the account currency."""
    if not symbol_info.symbol.strip():
        raise ValueError("cTrader symbol name must not be empty.")
    if (
        symbol_info.base_asset_id <= 0
        or symbol_info.quote_asset_id <= 0
        or deposit_asset_id <= 0
    ):
        raise ValueError("cTrader asset IDs must be positive.")
    if symbol_info.base_asset_id == symbol_info.quote_asset_id:
        raise ValueError("cTrader Forex base and quote assets must differ.")
    if symbol_info.quote_asset_id != deposit_asset_id:
        raise ValueError(
            "Lot sizing is unavailable because the symbol quote asset differs "
            "from the account deposit asset and currency conversion is not connected."
        )
    if symbol_info.maximum_exposure_cents is not None:
        raise ValueError(
            "Lot sizing is unavailable because the broker's maxExposure limit "
            "is not included in this calculation."
        )

    units_per_lot = _volume_units_from_cents(
        "lotSize",
        symbol_info.lot_size_cents,
    )
    minimum_volume_units = _volume_units_from_cents(
        "minVolume",
        symbol_info.minimum_volume_cents,
    )
    volume_step_units = _volume_units_from_cents(
        "stepVolume",
        symbol_info.volume_step_cents,
    )
    maximum_volume_units = _volume_units_from_cents(
        "maxVolume",
        symbol_info.maximum_volume_cents,
    )
    if maximum_volume_units < minimum_volume_units:
        raise ValueError("cTrader volume limits are inconsistent.")

    return BrokerInstrumentSpec(
        symbol=symbol_info.symbol,
        tick_size=None,
        tick_value_per_lot=None,
        units_per_lot=units_per_lot,
        minimum_volume_units=minimum_volume_units,
        volume_step_units=volume_step_units,
        maximum_volume_units=maximum_volume_units,
        price_value_per_lot=float(units_per_lot),
    )


def _volume_units_from_cents(field_name: str, value: int) -> int:
    if value <= 0 or value % 100 != 0:
        raise ValueError(
            f"cTrader {field_name} cannot be represented as whole volume units."
        )
    return value // 100
