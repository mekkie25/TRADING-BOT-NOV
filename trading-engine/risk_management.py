"""Apply explicitly supplied account-risk limits before execution.

Risk per trade and daily loss now come from account-size TIERS. A small account
gets different limits from a large one, and every tier number is a setting.
This module only reports PASS, FAIL or UNKNOWN. It never places orders.
"""

import math
from dataclasses import dataclass
from typing import List, Literal, Optional, Sequence, Tuple


RiskStatus = Literal["PASS", "FAIL", "UNKNOWN"]


@dataclass(frozen=True)
class RiskLimits:
    max_risk_per_trade_percent: float
    max_daily_loss_percent: float
    max_daily_trades: int
    max_open_positions: int


@dataclass(frozen=True)
class AccountRiskState:
    equity: float
    daily_start_equity: float
    trades_today: int
    open_positions: int


@dataclass(frozen=True)
class ProposedTradeRisk:
    planned_loss_cash: float


@dataclass(frozen=True)
class RiskCheck:
    name: str
    status: RiskStatus
    reason: str


@dataclass(frozen=True)
class RiskAssessment:
    status: RiskStatus
    checks: List[RiskCheck]
    summary: str


@dataclass(frozen=True)
class RiskTier:
    """One account-size band. min_balance is in account currency (dollars)."""

    name: str
    min_balance: float
    max_risk_per_trade_percent: float
    max_daily_loss_percent: float


# PLACEHOLDER VALUES. These are starting points for the owner to change, not
# recommendations. Balances are in account currency (dollars).
DEFAULT_RISK_TIERS: Tuple[RiskTier, ...] = (
    RiskTier("micro", 0.0, 10.0, 20.0),
    RiskTier("small", 100.0, 5.0, 10.0),
    RiskTier("medium", 1000.0, 2.0, 5.0),
    RiskTier("large", 10000.0, 1.0, 3.0),
)


def _validate_percent(name: str, value: float) -> None:
    if not math.isfinite(value) or not 0 < value <= 100:
        raise ValueError(f"{name} must be greater than 0 and no more than 100.")


def _validate_limits(limits: RiskLimits) -> None:
    _validate_percent("max_risk_per_trade_percent", limits.max_risk_per_trade_percent)
    _validate_percent("max_daily_loss_percent", limits.max_daily_loss_percent)
    if (
        not isinstance(limits.max_daily_trades, int)
        or isinstance(limits.max_daily_trades, bool)
        or limits.max_daily_trades < 1
    ):
        raise ValueError("max_daily_trades must be a positive integer.")
    if limits.max_daily_trades > 2:
        raise ValueError(
            "max_daily_trades must not exceed the master-strategy maximum of 2."
        )
    if (
        not isinstance(limits.max_open_positions, int)
        or isinstance(limits.max_open_positions, bool)
        or limits.max_open_positions < 1
    ):
        raise ValueError("max_open_positions must be a positive integer.")


def validate_tiers(tiers: Sequence[RiskTier]) -> None:
    """Raise ValueError unless the tiers are a usable ladder starting at zero."""
    if not tiers:
        raise ValueError("At least one risk tier is required.")
    names = set()
    previous_minimum = None
    for tier in tiers:
        if not isinstance(tier.name, str) or not tier.name.strip():
            raise ValueError("Every risk tier needs a name.")
        if tier.name in names:
            raise ValueError(f"Duplicate risk tier name: {tier.name}.")
        names.add(tier.name)
        if not math.isfinite(tier.min_balance) or tier.min_balance < 0:
            raise ValueError(f"Tier {tier.name}: min_balance must be zero or more.")
        _validate_percent(
            f"Tier {tier.name} max_risk_per_trade_percent",
            tier.max_risk_per_trade_percent,
        )
        _validate_percent(
            f"Tier {tier.name} max_daily_loss_percent",
            tier.max_daily_loss_percent,
        )
        if previous_minimum is None:
            if tier.min_balance != 0:
                raise ValueError("The first risk tier must start at a balance of 0.")
        elif tier.min_balance <= previous_minimum:
            raise ValueError("Risk tiers must go up in balance, smallest first.")
        previous_minimum = tier.min_balance


def tier_for_balance(
    balance: float,
    tiers: Sequence[RiskTier] = DEFAULT_RISK_TIERS,
) -> RiskTier:
    """Return the tier whose band contains this balance (in account currency)."""
    if not math.isfinite(balance) or balance <= 0:
        raise ValueError("balance must be a positive finite amount.")
    validate_tiers(tiers)
    chosen = tiers[0]
    for tier in tiers:
        if balance >= tier.min_balance:
            chosen = tier
    return chosen


def limits_for_balance(
    balance: float,
    tiers: Sequence[RiskTier] = DEFAULT_RISK_TIERS,
    max_daily_trades: int = 2,
    max_open_positions: int = 1,
) -> RiskLimits:
    """Build the risk limits for an account of this size."""
    tier = tier_for_balance(balance, tiers)
    limits = RiskLimits(
        max_risk_per_trade_percent=tier.max_risk_per_trade_percent,
        max_daily_loss_percent=tier.max_daily_loss_percent,
        max_daily_trades=max_daily_trades,
        max_open_positions=max_open_positions,
    )
    _validate_limits(limits)
    return limits


def check_minimum_lot_affordable(
    equity: float,
    loss_at_minimum_lot_cash: float,
    max_risk_per_trade_percent: float,
) -> RiskCheck:
    """Can this account afford even the smallest trade the broker allows?

    loss_at_minimum_lot_cash is the cash lost if the stop is hit at the smallest
    allowed lot, in account currency. The caller works this out from the broker
    specs and the stop distance.
    """
    for name, value in (
        ("equity", equity),
        ("loss_at_minimum_lot_cash", loss_at_minimum_lot_cash),
    ):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a positive finite amount.")
    _validate_percent("max_risk_per_trade_percent", max_risk_per_trade_percent)
    risk_percent = loss_at_minimum_lot_cash / equity * 100
    if risk_percent > max_risk_per_trade_percent:
        return RiskCheck(
            "Minimum lot affordable",
            "FAIL",
            (
                f"The smallest allowed trade already risks {risk_percent:.2f}% of "
                f"equity; this account's limit is {max_risk_per_trade_percent:.2f}%. "
                "Skip this trade."
            ),
        )
    return RiskCheck(
        "Minimum lot affordable",
        "PASS",
        (
            f"The smallest allowed trade risks {risk_percent:.2f}% of equity; "
            f"limit is {max_risk_per_trade_percent:.2f}%."
        ),
    )


def rand_to_dollars(amount_rand: float, rand_per_dollar: float) -> float:
    """Convert rand to dollars. The caller supplies the current rate."""
    if not math.isfinite(amount_rand) or amount_rand < 0:
        raise ValueError("amount_rand must be zero or more.")
    if not math.isfinite(rand_per_dollar) or rand_per_dollar <= 0:
        raise ValueError("rand_per_dollar must be a positive finite rate.")
    return amount_rand / rand_per_dollar


def assess_trade_risk(
    limits: RiskLimits,
    account: Optional[AccountRiskState],
    proposed_trade: Optional[ProposedTradeRisk],
) -> RiskAssessment:
    """Return PASS only when all supplied account and planned-loss checks pass."""
    _validate_limits(limits)
    if account is None or proposed_trade is None:
        missing = []
        if account is None:
            missing.append("account risk state")
        if proposed_trade is None:
            missing.append("planned trade loss")
        reason = f"Missing required data: {', '.join(missing)}."
        return RiskAssessment(
            status="UNKNOWN",
            checks=[RiskCheck("Required data", "UNKNOWN", reason)],
            summary=f"Risk status is unknown. {reason}",
        )

    account_values = {
        "equity": account.equity,
        "daily_start_equity": account.daily_start_equity,
        "planned_loss_cash": proposed_trade.planned_loss_cash,
    }
    for name, value in account_values.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a positive finite amount.")
    counts = {
        "trades_today": account.trades_today,
        "open_positions": account.open_positions,
    }
    for name, value in counts.items():
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer.")

    risk_percent = proposed_trade.planned_loss_cash / account.equity * 100
    current_daily_loss_cash = max(
        account.daily_start_equity - account.equity,
        0.0,
    )
    projected_daily_loss_percent = (
        current_daily_loss_cash + proposed_trade.planned_loss_cash
    ) / account.daily_start_equity * 100

    risk_per_trade_status: RiskStatus = (
        "FAIL"
        if risk_percent > limits.max_risk_per_trade_percent
        else "PASS"
    )
    daily_loss_status: RiskStatus = (
        "FAIL"
        if projected_daily_loss_percent > limits.max_daily_loss_percent
        else "PASS"
    )
    trade_count_status: RiskStatus = (
        "FAIL"
        if account.trades_today >= limits.max_daily_trades
        else "PASS"
    )
    open_positions_status: RiskStatus = (
        "FAIL"
        if account.open_positions >= limits.max_open_positions
        else "PASS"
    )
    checks = [
        RiskCheck(
            "Risk per trade",
            risk_per_trade_status,
            (
                f"Planned loss is {risk_percent:.2f}% of equity; "
                f"limit is {limits.max_risk_per_trade_percent:.2f}%."
            ),
        ),
        RiskCheck(
            "Daily loss",
            daily_loss_status,
            (
                f"Current loss plus planned loss would be "
                f"{projected_daily_loss_percent:.2f}% of daily starting equity; "
                f"limit is {limits.max_daily_loss_percent:.2f}%."
            ),
        ),
        RiskCheck(
            "Daily trade count",
            trade_count_status,
            (
                f"{account.trades_today} trades have been taken today; "
                f"maximum is {limits.max_daily_trades}."
            ),
        ),
        RiskCheck(
            "Open positions",
            open_positions_status,
            (
                f"{account.open_positions} positions are open; "
                f"maximum is {limits.max_open_positions}."
            ),
        ),
    ]
    failures = sum(check.status == "FAIL" for check in checks)
    status: RiskStatus = "FAIL" if failures else "PASS"
    summary = (
        f"Risk checks rejected the proposed trade: {failures} limit(s) failed."
        if failures
        else "All supplied risk checks passed; this does not place or execute a trade."
    )
    return RiskAssessment(status=status, checks=checks, summary=summary)