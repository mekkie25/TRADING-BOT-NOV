"""Apply explicitly supplied account-risk limits before execution."""

import math
from dataclasses import dataclass
from typing import List, Literal, Optional


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


def _validate_limits(limits: RiskLimits) -> None:
    percent_limits = {
        "max_risk_per_trade_percent": limits.max_risk_per_trade_percent,
        "max_daily_loss_percent": limits.max_daily_loss_percent,
    }
    for name, value in percent_limits.items():
        if not math.isfinite(value) or not 0 < value <= 100:
            raise ValueError(f"{name} must be greater than 0 and no more than 100.")
    if (
        not isinstance(limits.max_daily_trades, int)
        or isinstance(limits.max_daily_trades, bool)
        or limits.max_daily_trades < 1
    ):
        raise ValueError("max_daily_trades must be a positive integer.")
    if (
        not isinstance(limits.max_open_positions, int)
        or isinstance(limits.max_open_positions, bool)
        or limits.max_open_positions < 1
    ):
        raise ValueError("max_open_positions must be a positive integer.")


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
