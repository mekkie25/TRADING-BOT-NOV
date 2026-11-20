"""Build a read-only market picture from completed live candles."""

from datetime import datetime, timedelta
from typing import Dict, Mapping, Optional, Sequence

import pandas as pd

from data.live_feed import Candle, LiveQuote
from data.timeframes import TIMEFRAME_LENGTHS
from indicators.exponential_moving_average import (
    analyze_exponential_moving_averages,
)
from knowledge.average_candle_range import analyze_average_candle_range
from knowledge.candlestick_anatomy import analyze as analyze_candlestick_anatomy
from knowledge.cisd import analyze as analyze_cisd
from knowledge.daily_profiles import analyze as analyze_daily_profiles
from knowledge.equilibrium import analyze as analyze_equilibrium
from knowledge.fair_value_gap import analyze as analyze_fair_value_gaps
from knowledge.inverse_fvg import analyze as analyze_inverse_fvgs
from knowledge.liquidity import analyze as analyze_liquidity
from knowledge.market_conditions import get_market_condition
from knowledge.market_structure import analyze as analyze_market_structure
from knowledge.multi_timeframe_alignment import (
    analyze_multi_timeframe_alignment,
)
from knowledge.previous_day_levels import analyze_previous_day_levels
from knowledge.previous_week_levels import analyze_previous_week_levels
from knowledge.sessions import get_current_session
from knowledge.spread import analyze_spread
from knowledge.supply_demand import analyze_supply_demand
from knowledge.support_resistance import analyze_support_resistance
from knowledge.time_structure import report_market_time
from knowledge.trend_lines import analyze_trend_lines


ANALYSIS_CANDLE_LIMIT = 1_000


UNAVAILABLE_REPORTS = {
    "daily_bias": "Completed D1 candles are not available in the live feed.",
    "weekly_bias": "Completed D1 and W1 candles are not available in the live feed.",
    "average_daily_range": "Completed D1 candles are not available in the live feed.",
    "judas_swing": (
        "Complete session-start candle coverage is not guaranteed, and the "
        "detection conventions are not mentor-verified."
    ),
    "liquidity_types": (
        "Its classification weights and round-number step require explicit "
        "instrument settings that the snapshot does not supply."
    ),
    "economic_calendar": "Calendar events are not supplied to the live market snapshot.",
    "news": "News events are not supplied to the live market snapshot.",
    "smt": "A second correlated symbol is not supplied.",
    "fibonacci_levels": "No two anchor prices were supplied.",
    "pivot_points": "Previous completed pivot-period prices were not supplied.",
    "anchored_vwap": "No anchor and verified volume source were supplied.",
    "round_numbers": "No instrument-specific price interval was supplied.",
    "break_retest": "No level and direction were supplied.",
    "stop_loss": "No open-position stop level was supplied.",
    "take_profit": "No open-position target was supplied.",
    "break_even": "No open-position entry and stop levels were supplied.",
    "drawdown": "Account equity history is not part of the market snapshot.",
}


def build_market_snapshot(
    symbol: str,
    as_of: datetime,
    quote: Optional[LiveQuote],
    candles_by_timeframe: Mapping[str, Sequence[Candle]],
) -> dict:
    """Report available observations without evaluating entry criteria."""
    if not symbol.strip():
        raise ValueError("symbol must not be empty.")
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise ValueError("as_of must be timezone-aware UTC.")
    if quote is not None:
        if quote.symbol.upper() != symbol.upper():
            raise ValueError("quote symbol must match the snapshot symbol.")
        if quote.time > as_of:
            raise ValueError("quote time must not be later than as_of.")

    retained_frames = {
        timeframe: _closed_candles_frame(
            candles_by_timeframe.get(timeframe, ()),
            timeframe,
            as_of,
        )
        for timeframe in ("M1", "M5")
    }
    frames = {
        timeframe: candles.tail(ANALYSIS_CANDLE_LIMIT).reset_index(drop=True)
        for timeframe, candles in retained_frames.items()
    }

    reports_by_timeframe = {}
    for timeframe, candles in frames.items():
        reports_by_timeframe[timeframe] = {
            "market_structure": analyze_market_structure(candles),
            "candlestick_anatomy": analyze_candlestick_anatomy(candles),
            "market_condition": get_market_condition(candles),
            "fair_value_gaps": analyze_fair_value_gaps(candles),
            "inverse_fair_value_gaps": analyze_inverse_fvgs(candles),
            "liquidity": analyze_liquidity(candles),
            "equilibrium": analyze_equilibrium(candles),
            "support_resistance": analyze_support_resistance(candles),
            "supply_demand": analyze_supply_demand(
                candles,
                timeframe,
                as_of,
            ),
            "change_in_state_of_delivery": analyze_cisd(candles),
            "average_candle_range": analyze_average_candle_range(
                candles,
                timeframe,
                20,
                as_of,
            ),
            "exponential_moving_averages": analyze_exponential_moving_averages(
                candles,
                timeframe,
                as_of,
            ),
        }

    quote_report = None
    spread_report = None
    if quote is not None:
        quote_report = {
            "time": quote.time,
            "bid": quote.bid,
            "ask": quote.ask,
        }
        spread_report = analyze_spread(
            symbol=quote.symbol,
            time=quote.time,
            bid=quote.bid,
            ask=quote.ask,
        )

    m1_times = retained_frames["M1"]["time"]
    m1_history = {
        "candle_count": len(retained_frames["M1"]),
        "analysis_candle_count": len(frames["M1"]),
        "analysis_candle_limit": ANALYSIS_CANDLE_LIMIT,
        "retained_candle_limit": 10_080,
        "first_candle_time": m1_times.iloc[0] if not m1_times.empty else None,
        "latest_candle_time": m1_times.iloc[-1] if not m1_times.empty else None,
    }

    return {
        "symbol": symbol,
        "as_of": as_of,
        "updated_by": "completed M1 candle",
        "entry_criteria_evaluated": False,
        "quote": quote_report,
        "market_time": report_market_time(as_of),
        "session": get_current_session(as_of),
        "spread": spread_report,
        "candles": m1_history,
        "reports": reports_by_timeframe,
        "multi_timeframe_alignment": analyze_multi_timeframe_alignment(
            frames,
            as_of,
        ),
        "trend_lines": analyze_trend_lines(frames),
        "previous_day_levels": analyze_previous_day_levels(
            retained_frames["M1"],
            "M1",
            as_of,
        ),
        "previous_week_levels": analyze_previous_week_levels(
            retained_frames["M1"],
            "M1",
            as_of,
        ),
        "daily_profiles": analyze_daily_profiles(
            frames["M1"],
            pd.Timestamp(as_of),
        ),
        "unavailable_reports": dict(UNAVAILABLE_REPORTS),
    }


def _closed_candles_frame(
    candles: Sequence[Candle],
    timeframe: str,
    as_of: datetime,
) -> pd.DataFrame:
    rows = []
    duration = TIMEFRAME_LENGTHS[timeframe]
    previous_time = None
    for candle in candles:
        if candle.timeframe != timeframe:
            raise ValueError(
                f"Expected {timeframe} candles, received {candle.timeframe}."
            )
        if previous_time is not None and candle.time <= previous_time:
            raise ValueError(
                f"{timeframe} candle times must be strictly increasing."
            )
        previous_time = candle.time
        if candle.time + duration > as_of:
            continue
        rows.append(
            {
                "time": candle.time,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume,
            }
        )
    return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
