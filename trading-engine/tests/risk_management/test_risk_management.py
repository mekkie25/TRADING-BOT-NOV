import unittest

from risk_management import (
    DEFAULT_RISK_TIERS,
    AccountRiskState,
    ProposedTradeRisk,
    RiskLimits,
    RiskTier,
    assess_trade_risk,
    check_minimum_lot_affordable,
    limits_for_balance,
    rand_to_dollars,
    tier_for_balance,
    validate_tiers,
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

    def test_risk_per_trade_above_two_percent_is_now_allowed(self):
        # The old 2 percent cap is gone. Tiers set the limit instead.
        limits = RiskLimits(
            max_risk_per_trade_percent=10.0,
            max_daily_loss_percent=20.0,
            max_daily_trades=2,
            max_open_positions=2,
        )
        result = assess_trade_risk(
            limits,
            self.account,
            ProposedTradeRisk(planned_loss_cash=400.0),
        )
        self.assertEqual(result.status, "PASS")

    def test_risk_percent_must_still_be_between_zero_and_one_hundred(self):
        for bad_value in (0.0, -1.0, 100.01, float("nan")):
            with self.assertRaisesRegex(ValueError, "max_risk_per_trade_percent"):
                assess_trade_risk(
                    RiskLimits(
                        max_risk_per_trade_percent=bad_value,
                        max_daily_loss_percent=5.0,
                        max_daily_trades=2,
                        max_open_positions=2,
                    ),
                    self.account,
                    ProposedTradeRisk(planned_loss_cash=100.0),
                )

    def test_daily_trades_above_master_strategy_maximum_still_rejected(self):
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


class RiskTierTests(unittest.TestCase):
    def test_balance_picks_the_matching_tier(self):
        expected = {
            5.0: "micro",
            99.99: "micro",
            100.0: "small",
            999.99: "small",
            1000.0: "medium",
            9999.99: "medium",
            10000.0: "large",
            1000000.0: "large",
        }
        for balance, name in expected.items():
            self.assertEqual(tier_for_balance(balance).name, name, balance)

    def test_bad_balance_is_rejected(self):
        for balance in (0.0, -5.0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                tier_for_balance(balance)

    def test_limits_follow_the_tier_of_the_balance(self):
        small = limits_for_balance(50.0)
        self.assertEqual(small.max_risk_per_trade_percent, 10.0)
        self.assertEqual(small.max_daily_loss_percent, 20.0)
        self.assertEqual(small.max_daily_trades, 2)
        self.assertEqual(small.max_open_positions, 1)
        large = limits_for_balance(20000.0)
        self.assertEqual(large.max_risk_per_trade_percent, 1.0)
        self.assertEqual(large.max_daily_loss_percent, 3.0)

    def test_risk_drops_as_the_account_grows(self):
        balances = [50.0, 500.0, 5000.0, 50000.0]
        risks = [limits_for_balance(b).max_risk_per_trade_percent for b in balances]
        self.assertEqual(risks, sorted(risks, reverse=True))
        self.assertEqual(len(set(risks)), 4)

    def test_custom_tiers_can_be_supplied(self):
        tiers = (
            RiskTier("tiny", 0.0, 15.0, 30.0),
            RiskTier("bigger", 50.0, 3.0, 6.0),
        )
        self.assertEqual(tier_for_balance(49.0, tiers).name, "tiny")
        self.assertEqual(limits_for_balance(50.0, tiers).max_risk_per_trade_percent, 3.0)

    def test_default_tiers_are_valid(self):
        validate_tiers(DEFAULT_RISK_TIERS)

    def test_bad_tier_ladders_are_rejected(self):
        bad_ladders = {
            "empty": (),
            "first tier not at zero": (RiskTier("a", 10.0, 5.0, 10.0),),
            "not going up": (
                RiskTier("a", 0.0, 5.0, 10.0),
                RiskTier("b", 100.0, 4.0, 8.0),
                RiskTier("c", 100.0, 3.0, 6.0),
            ),
            "duplicate name": (
                RiskTier("a", 0.0, 5.0, 10.0),
                RiskTier("a", 100.0, 4.0, 8.0),
            ),
            "risk too high": (RiskTier("a", 0.0, 101.0, 10.0),),
            "risk zero": (RiskTier("a", 0.0, 0.0, 10.0),),
        }
        for label, ladder in bad_ladders.items():
            with self.assertRaises(ValueError, msg=label):
                validate_tiers(ladder)

    def test_small_account_trade_checked_against_its_own_tier(self):
        # 50 dollar account is in the micro tier: limit 10 percent per trade.
        limits = limits_for_balance(50.0)
        account = AccountRiskState(
            equity=50.0,
            daily_start_equity=50.0,
            trades_today=0,
            open_positions=0,
        )
        passes = assess_trade_risk(limits, account, ProposedTradeRisk(planned_loss_cash=4.0))
        self.assertEqual(passes.status, "PASS")
        fails = assess_trade_risk(limits, account, ProposedTradeRisk(planned_loss_cash=6.0))
        self.assertEqual(fails.status, "FAIL")
        failed = [c.name for c in fails.checks if c.status == "FAIL"]
        self.assertEqual(failed, ["Risk per trade"])


class MinimumLotTests(unittest.TestCase):
    def test_skips_when_smallest_trade_costs_too_much(self):
        check = check_minimum_lot_affordable(50.0, 10.0, 10.0)
        self.assertEqual(check.status, "FAIL")
        self.assertIn("smallest allowed trade", check.reason)
        self.assertIn("20.00%", check.reason)

    def test_passes_when_smallest_trade_fits(self):
        check = check_minimum_lot_affordable(50.0, 4.0, 10.0)
        self.assertEqual(check.status, "PASS")

    def test_exactly_at_the_limit_passes(self):
        self.assertEqual(check_minimum_lot_affordable(100.0, 10.0, 10.0).status, "PASS")

    def test_bad_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            check_minimum_lot_affordable(0.0, 1.0, 10.0)
        with self.assertRaises(ValueError):
            check_minimum_lot_affordable(50.0, -1.0, 10.0)
        with self.assertRaises(ValueError):
            check_minimum_lot_affordable(50.0, 1.0, 0.0)


class RandConversionTests(unittest.TestCase):
    def test_converts_rand_to_dollars_with_a_supplied_rate(self):
        self.assertAlmostEqual(rand_to_dollars(1800.0, 18.0), 100.0)

    def test_needs_a_real_rate(self):
        for rate in (0.0, -18.0, float("nan")):
            with self.assertRaises(ValueError):
                rand_to_dollars(100.0, rate)
        with self.assertRaises(ValueError):
            rand_to_dollars(-1.0, 18.0)


if __name__ == "__main__":
    unittest.main()