"""Evaluate the master-file daily pivot break-and-retest trigger."""

import math
from datetime import timedelta
from typing import Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from engine.models import Direction
from strategies.evaluation import StrategyCheck, StrategyEvaluation


STRATEGY_NAME = "pivot_break_retest"


def evaluate_pivot_break_retest(
    candles: pd.DataFrame,
    daily_r1: float,
    daily_s1: float,
    daily_r2: float,
    daily_s2: float,
    confluence_conditions: Optional[Mapping[str, Optional[bool]]],
    narrow_range_day: Optional[bool],
    stop_loss_price: Optional[float],
    minimum_confluence_count: int = 1,
) -> StrategyEvaluation:
    """Report a daily S1/R1 break-and-retest candidate without placing an order.

    The caller supplies already-computed pivot levels, other confluence facts,
    the narrow-range observation, and a stop price. Missing decisions or data
    block the candidate rather than selecting a default.
    """
    _validate_candles(candles)
    _validate_pivots(daily_r1, daily_s1, daily_r2, daily_s2)
    if stop_loss_price is not None and (
        not math.isfinite(stop_loss_price) or stop_loss_price <= 0
    ):
        raise ValueError("stop_loss_price must be a positive finite price.")
    if (
        isinstance(minimum_confluence_count, bool)
        or not isinstance(minimum_confluence_count, int)
        or minimum_confluence_count < 1
    ):
        raise ValueError("minimum_confluence_count must be a positive integer.")
    if confluence_conditions is not None:
        if any(not name.strip() for name in confluence_conditions):
            raise ValueError("confluence condition names must not be empty.")
        if any(
            value is not None and not isinstance(value, bool)
            for value in confluence_conditions.values()
        ):
            raise ValueError("confluence condition values must be true, false, or unknown.")

    closes = candles["close"].to_numpy(dtype=float)
    highs = candles["high"].to_numpy(dtype=float)
    lows = candles["low"].to_numpy(dtype=float)
    latest_close = float(closes[-1])
    latest_time = pd.Timestamp(candles["time"].iloc[-1])

    bearish_break = _latest_retest(closes, highs, lows, daily_s1, Direction.SELL)
    bullish_break = _latest_retest(closes, highs, lows, daily_r1, Direction.BUY)
    if bearish_break:
        direction = Direction.SELL
        pivot_level = daily_s1
        target_price = daily_s2
        trigger_reason = "Price broke below daily S1 and retested it from below."
    elif bullish_break:
        direction = Direction.BUY
        pivot_level = daily_r1
        target_price = daily_r2
        trigger_reason = "Price broke above daily R1 and retested it from above."
    else:
        return StrategyEvaluation(
            strategy_name=STRATEGY_NAME,
            variant="daily_s1_r1",
            status="NOT_TRIGGERED",
            direction=None,
            trigger_time=None,
            entry_reference_price=None,
            stop_loss_price=None,
            take_profit_prices=(),
            checks=(
                StrategyCheck(
                    "Pivot break and retest",
                    "FAIL",
                    "No closed-candle break followed by a retest holding the pivot was found.",
                ),
            ),
            summary="The daily pivot break-and-retest trigger was not found.",
        )

    checks = [
        StrategyCheck("Pivot break and retest", "PASS", trigger_reason),
    ]
    if narrow_range_day is None:
        checks.append(
            StrategyCheck(
                "Narrow-range filter",
                "UNKNOWN",
                "The caller did not supply whether this is a narrow, range-bound day.",
            )
        )
    elif narrow_range_day:
        checks.append(
            StrategyCheck(
                "Narrow-range filter",
                "FAIL",
                "The master file says to avoid narrow, range-bound days around the central pivot.",
            )
        )
    else:
        checks.append(
            StrategyCheck(
                "Narrow-range filter",
                "PASS",
                "The caller reports this is not a narrow, range-bound day.",
            )
        )

    confluences = confluence_conditions or {}
    for name, condition_met in confluences.items():
        checks.append(
            StrategyCheck(
                name,
                "UNKNOWN" if condition_met is None else "PASS" if condition_met else "FAIL",
                (
                    "The caller did not supply this confluence result."
                    if condition_met is None
                    else "The caller reports this confluence is present."
                    if condition_met
                    else "The caller reports this confluence is absent."
                ),
            )
        )
    present_confluences = [
        name for name, condition_met in confluences.items() if condition_met is True
    ]
    if len(present_confluences) < minimum_confluence_count:
        checks.append(
            StrategyCheck(
                "Required additional confluence",
                "UNKNOWN" if not confluences or all(
                    value is None for value in confluences.values()
                ) else "FAIL",
                (
                    "The pivot trigger requires "
                    f"{minimum_confluence_count} additional confluence reason(s); "
                    f"{len(present_confluences)} were present."
                ),
            )
        )

    if stop_loss_price is None:
        checks.append(
            StrategyCheck(
                "Stop loss",
                "UNKNOWN",
                "The master file requires a stop beyond the retested pivot or swing; no stop was supplied.",
            )
        )
    else:
        stop_is_beyond_pivot = (
            stop_loss_price > pivot_level
            if direction == Direction.SELL
            else stop_loss_price < pivot_level
        )
        checks.append(
            StrategyCheck(
                "Stop loss",
                "PASS" if stop_is_beyond_pivot else "FAIL",
                (
                    "The supplied stop is beyond the pivot on the risk side."
                    if stop_is_beyond_pivot
                    else "The supplied stop is not beyond the pivot on the risk side."
                ),
            )
        )

    target_is_ahead = (
        target_price < latest_close
        if direction == Direction.SELL
        else target_price > latest_close
    )
    checks.append(
        StrategyCheck(
            "Next daily pivot target",
            "PASS" if target_is_ahead else "FAIL",
            (
                "The next daily pivot level is ahead of the entry reference."
                if target_is_ahead
                else "The next daily pivot level is not ahead of the entry reference."
            ),
        )
    )

    if any(check.status != "PASS" for check in checks):
        return StrategyEvaluation(
            strategy_name=STRATEGY_NAME,
            variant="daily_s1_r1",
            status="BLOCKED",
            direction=direction,
            trigger_time=latest_time,
            entry_reference_price=latest_close,
            stop_loss_price=stop_loss_price,
            take_profit_prices=(target_price,),
            checks=tuple(checks),
            summary=(
                "The pivot break-and-retest pattern was observed, but required "
                "confluence or risk inputs did not pass."
            ),
        )

    return StrategyEvaluation(
        strategy_name=STRATEGY_NAME,
        variant="daily_s1_r1",
        status="TRIGGERED",
        direction=direction,
        trigger_time=latest_time,
        entry_reference_price=latest_close,
        stop_loss_price=stop_loss_price,
        take_profit_prices=(target_price,),
        checks=tuple(checks),
        summary=(
            "The daily pivot break-and-retest trigger and its required "
            "confluence and supplied risk inputs passed. This is not an order."
        ),
    )


def _latest_retest(
    closes: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    pivot_level: float,
    direction: Direction,
) -> bool:
    if len(closes) < 3:
        return False

    if direction == Direction.SELL:
        crossed = [
            index
            for index in range(1, len(closes) - 1)
            if closes[index - 1] >= pivot_level and closes[index] < pivot_level
        ]
        latest_break = crossed[-1] if crossed else None
        return bool(
            latest_break is not None
            and all(
                closes[index] < pivot_level
                for index in range(latest_break + 1, len(closes) - 1)
            )
            and highs[-1] >= pivot_level
            and lows[-1] <= pivot_level
            and closes[-1] < pivot_level
        )

    crossed = [
        index
        for index in range(1, len(closes) - 1)
        if closes[index - 1] <= pivot_level and closes[index] > pivot_level
    ]
    return bool(
        crossed
        and all(
            closes[index] > pivot_level
            for index in range(crossed[-1] + 1, len(closes) - 1)
        )
        and highs[-1] >= pivot_level
        and lows[-1] <= pivot_level
        and closes[-1] > pivot_level
    )


def _validate_candles(candles: pd.DataFrame) -> None:
    if not isinstance(candles, pd.DataFrame) or candles.empty:
        raise ValueError("candles must be a non-empty DataFrame.")
    required_columns = ("time", "open", "high", "low", "close")
    missing_columns = [name for name in required_columns if name not in candles]
    if missing_columns:
        raise ValueError(f"candles are missing columns: {', '.join(missing_columns)}.")
    prices = candles[["open", "high", "low", "close"]].to_numpy(dtype=float)
    if not np.isfinite(prices).all() or (prices <= 0).any():
        raise ValueError("candle prices must be positive finite numbers.")
    if (
        (candles["high"] < candles["low"]).any()
        or (candles["high"] < candles["open"]).any()
        or (candles["high"] < candles["close"]).any()
        or (candles["low"] > candles["open"]).any()
        or (candles["low"] > candles["close"]).any()
    ):
        raise ValueError("candle high and low values must contain open and close.")
    times = candles["time"]
    if not pd.api.types.is_datetime64_any_dtype(times) or times.dt.tz is None:
        raise ValueError("candle times must be timezone-aware UTC.")
    if not times.is_monotonic_increasing or times.duplicated().any():
        raise ValueError("candle times must be strictly increasing.")
    if any(timestamp.utcoffset() != timedelta(0) for timestamp in times):
        raise ValueError("candle times must be in UTC.")


def _validate_pivots(
    daily_r1: float,
    daily_s1: float,
    daily_r2: float,
    daily_s2: float,
) -> None:
    levels = (daily_r1, daily_s1, daily_r2, daily_s2)
    if not all(math.isfinite(level) and level > 0 for level in levels):
        raise ValueError("daily pivot levels must be positive finite prices.")
    if not (daily_r2 > daily_r1 > daily_s1 > daily_s2):
        raise ValueError("daily pivot levels must be ordered R2 > R1 > S1 > S2.")
