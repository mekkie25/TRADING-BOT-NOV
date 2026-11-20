import unittest

from risk_management import (
    AccountRiskState,
    ProposedTradeRisk,
    RiskLimits,
    assess_trade_risk,
)


class RiskManagementTests(unittest.TestCase):
    def setUp(self):
        self.limits = RiskLimits(
            max_risk_per_trade_percent=2.0,
            max_daily_loss_percent=5.0,
            max_daily_trades=2,
            max_open_positions=2,
        )
        self.account = AccountRiskState(
            equity=10000.0,
            daily_start_equity=10000.0,
            trades_today=1,
            open_positions=0,
        )

    def test_passes_only_when_all_explicit_limits_are_met(self):
        result = assess_trade_risk(
            self.limits,
            self.account,
            ProposedTradeRisk(planned_loss_cash=100.0),
        )

        self.assertEqual(result.status, "PASS")
        self.assertEqual(len(result.checks), 4)
        self.assertIn("does not place", result.summary)

    def test_fails_when_trade_risk_or_projected_daily_loss_exceeds_limits(self):
        account = AccountRiskState(
            equity=10000.0,
            daily_start_equity=10000.0,
            trades_today=1,
            open_positions=0,
        )

        result = assess_trade_risk(
            self.limits,
            account,
            ProposedTradeRisk(planned_loss_cash=600.0),
        )

        self.assertEqual(result.status, "FAIL")
        failed_checks = [check.name for check in result.checks if check.status == "FAIL"]
        self.assertEqual(failed_checks, ["Risk per trade", "Daily loss"])

    def test_returns_unknown_when_broker_account_state_is_missing(self):
        result = assess_trade_risk(
            self.limits,
            None,
            ProposedTradeRisk(planned_loss_cash=100.0),
        )

        self.assertEqual(result.status, "UNKNOWN")
        self.assertIn("account risk state", result.summary)

    def test_rejects_when_daily_trade_or_open_position_limit_is_reached(self):
        account = AccountRiskState(
            equity=10000.0,
            daily_start_equity=10000.0,
            trades_today=2,
            open_positions=2,
        )

        result = assess_trade_risk(
            self.limits,
            account,
            ProposedTradeRisk(planned_loss_cash=100.0),
        )

        self.assertEqual(result.status, "FAIL")
        failed_checks = [check.name for check in result.checks if check.status == "FAIL"]
        self.assertEqual(failed_checks, ["Daily trade count", "Open positions"])

    def test_rejects_risk_limits_above_master_strategy_maxima(self):
        with self.assertRaisesRegex(ValueError, "must not exceed.*maximum of 2"):
            assess_trade_risk(
                RiskLimits(
                    max_risk_per_trade_percent=2.01,
                    max_daily_loss_percent=5.0,
                    max_daily_trades=2,
                    max_open_positions=2,
                ),
                self.account,
                ProposedTradeRisk(planned_loss_cash=100.0),
            )

        with self.assertRaisesRegex(ValueError, "max_daily_trades.*maximum of 2"):
            assess_trade_risk(
                RiskLimits(
                    max_risk_per_trade_percent=2.0,
                    max_daily_loss_percent=5.0,
                    max_daily_trades=3,
                    max_open_positions=2,
                ),
                self.account,
                ProposedTradeRisk(planned_loss_cash=100.0),
            )


if __name__ == "__main__":
    unittest.main()
