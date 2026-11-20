"""Replaceable session volume-profile providers and a labeled OHLC approximation."""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Literal, Optional, Protocol, Sequence

import pandas as pd

from data.timeframes import TIMEFRAME_LENGTHS


ProfileSource = Literal["true", "tick_approx", "time_approx"]


@dataclass(frozen=True)
class VolumeProfileReport:
    poc: Optional[float]
    vah: Optional[float]
    val: Optional[float]
    bin_size: Optional[float]
    value_area_fraction: float
    source: ProfileSource
    approximate: bool
    candle_count: int
    summary: str


class VolumeProfileProvider(Protocol):
    def calculate(
        self,
        candles: pd.DataFrame,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        as_of: datetime,
        average_candle_size: float,
        tick_size: Optional[float] = None,
    ) -> VolumeProfileReport:
        """Calculate a profile from closed session candles."""
        ...


class ApproximateVolumeProfileProvider:
    """Spread each candle's volume evenly over its intersecting price bins."""

    def __init__(
        self,
        value_area_fraction: float = 0.70,
        bin_size_acs_multiple: float = 0.10,
        fixed_bin_size: Optional[float] = None,
    ) -> None:
        if not 0 < value_area_fraction <= 1:
            raise ValueError("value_area_fraction must be in (0, 1].")
        if not math.isfinite(bin_size_acs_multiple) or bin_size_acs_multiple <= 0:
            raise ValueError("bin_size_acs_multiple must be positive and finite.")
        if fixed_bin_size is not None and (
            not math.isfinite(fixed_bin_size) or fixed_bin_size <= 0
        ):
            raise ValueError("fixed_bin_size must be positive and finite.")
        self.value_area_fraction = value_area_fraction
        self.bin_size_acs_multiple = bin_size_acs_multiple
        self.fixed_bin_size = fixed_bin_size

    def calculate(
        self,
        candles: pd.DataFrame,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        as_of: datetime,
        average_candle_size: float,
        tick_size: Optional[float] = None,
    ) -> VolumeProfileReport:
        _validate_utc_times(start_time, end_time, as_of)
        normalized_timeframe = timeframe.strip().upper()
        if normalized_timeframe not in TIMEFRAME_LENGTHS:
            raise ValueError(f"Unsupported timeframe: {timeframe}.")
        if end_time <= start_time:
            raise ValueError("end_time must be after start_time.")
        if not math.isfinite(average_candle_size) or average_candle_size <= 0:
            raise ValueError("average_candle_size must be positive and finite.")
        if tick_size is not None and (not math.isfinite(tick_size) or tick_size <= 0):
            raise ValueError("tick_size must be positive and finite.")
        if not isinstance(candles, pd.DataFrame):
            raise ValueError("candles must be a DataFrame.")
        required = {"time", "high", "low"}
        missing = required.difference(candles.columns)
        if missing:
            raise ValueError(f"Candles are missing columns: {', '.join(sorted(missing))}.")
        if candles.empty:
            return self._unavailable("No session candles were supplied.")
        times = pd.to_datetime(candles["time"], utc=True, errors="coerce")
        if times.isna().any() or not times.is_monotonic_increasing or times.duplicated().any():
            raise ValueError("Candle times must be valid, unique, and chronological.")
        duration = pd.Timedelta(TIMEFRAME_LENGTHS[normalized_timeframe])
        selected_mask = (
            (times >= pd.Timestamp(start_time))
            & (times < pd.Timestamp(end_time))
            & (times + duration <= pd.Timestamp(as_of))
            & (times + duration <= pd.Timestamp(end_time))
        )
        selected = candles.loc[selected_mask]
        if selected.empty:
            return self._unavailable("No usable candles were available in the session window.")

        prices = selected[["high", "low"]].apply(pd.to_numeric, errors="coerce")
        values = prices.to_numpy(dtype=float)
        if not all(math.isfinite(value) for value in values.flat):
            raise ValueError("Candle highs and lows must be finite.")
        if (prices["high"] < prices["low"]).any():
            raise ValueError("Candle highs must not be below candle lows.")

        bin_size = self.fixed_bin_size or average_candle_size * self.bin_size_acs_multiple
        if tick_size is not None:
            bin_size = max(bin_size, tick_size)
        bins: Dict[int, float] = {}
        volume_column = next(
            (name for name in ("tick_volume", "volume") if name in selected.columns),
            None,
        )
        source: ProfileSource = "tick_approx" if volume_column else "time_approx"
        if volume_column:
            volumes = pd.to_numeric(selected[volume_column], errors="coerce")
            if volumes.isna().any() or (volumes < 0).any():
                raise ValueError(f"{volume_column} values must be finite and non-negative.")
            weights: Sequence[float] = tuple(float(value) for value in volumes)
            if not any(weight > 0 for weight in weights):
                source = "time_approx"
                weights = tuple(1.0 for _ in range(len(selected)))
        else:
            weights = tuple(1.0 for _ in range(len(selected)))

        for (_, candle), weight in zip(selected.iterrows(), weights):
            low = float(candle["low"])
            high = float(candle["high"])
            first_bin = math.floor(low / bin_size)
            last_bin = math.floor(high / bin_size)
            covered_bins = list(range(first_bin, last_bin + 1))
            share = weight / len(covered_bins)
            for bin_index in covered_bins:
                bins[bin_index] = bins.get(bin_index, 0.0) + share

        total = math.fsum(bins.values())
        if total <= 0:
            return self._unavailable(
                "Session candles were present but had no positive volume or time weight."
            )
        poc_index = max(bins, key=lambda index: (bins[index], -index))
        included = {poc_index}
        accumulated = bins[poc_index]
        lower = poc_index - 1
        upper = poc_index + 1
        while accumulated / total < self.value_area_fraction:
            lower_weight = bins.get(lower, -1.0)
            upper_weight = bins.get(upper, -1.0)
            if lower_weight < 0 and upper_weight < 0:
                break
            if upper_weight > lower_weight:
                included.add(upper)
                accumulated += upper_weight
                upper += 1
            else:
                included.add(lower)
                accumulated += lower_weight
                lower -= 1
        minimum_bin = min(included)
        maximum_bin = max(included)
        poc = (poc_index + 0.5) * bin_size
        val = minimum_bin * bin_size
        vah = (maximum_bin + 1) * bin_size
        return VolumeProfileReport(
            poc=poc,
            vah=vah,
            val=val,
            bin_size=bin_size,
            value_area_fraction=self.value_area_fraction,
            source=source,
            approximate=True,
            candle_count=len(selected),
            summary=(
                f"Approximate session profile ({source}): POC {poc:g}, "
                f"VAH {vah:g}, VAL {val:g}, value area "
                f"{self.value_area_fraction:.0%} from {len(selected)} candles."
            ),
        )

    def _unavailable(self, reason: str) -> VolumeProfileReport:
        return VolumeProfileReport(
            poc=None,
            vah=None,
            val=None,
            bin_size=None,
            value_area_fraction=self.value_area_fraction,
            source="time_approx",
            approximate=True,
            candle_count=0,
            summary=f"POC, VAH, and VAL are unavailable: {reason}",
        )


def _validate_utc_times(*values: datetime) -> None:
    for value in values:
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("Profile times must be timezone-aware UTC.")
