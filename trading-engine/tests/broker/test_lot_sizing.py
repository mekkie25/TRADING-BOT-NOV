import unittest

from broker.lot_sizing import BrokerInstrumentSpec, calculate_lot_size


class LotSizingTests(unittest.TestCase):
    def setUp(self):
        self.instrument = BrokerInstrumentSpec(
            symbol="EURUSD",
            tick_size=0.001,
            tick_value_per_lot=10.0,
            units_per_lot=100000,
            minimum_volume_units=1000,
            volume_step_units=1000,
            maximum_volume_units=500000,
        )

    def test_rounds_volume_down_to_broker_step_without_exceeding_risk_budget(self):
        report = calculate_lot_size(
            account_equity=10000.0,
            risk_percent=1.499,
            entry_price=1.10,
            stop_loss_price=1.09,
            instrument=self.instrument,
        )

        self.assertEqual(report.volume_units, 149000)
        self.assertEqual(report.lots, 1.49)
        self.assertLessEqual(report.planned_loss_cash, report.risk_budget_cash)

    def test_does_not_force_a_size_when_minimum_volume_exceeds_budget(self):
        instrument = BrokerInstrumentSpec(
            symbol="EURUSD",
            tick_size=0.001,
            tick_value_per_lot=10.0,
            units_per_lot=100000,
            minimum_volume_units=10000,
            volume_step_units=1000,
            maximum_volume_units=500000,
        )

        report = calculate_lot_size(
            account_equity=10000.0,
            risk_percent=0.1,
            entry_price=1.10,
            stop_loss_price=1.00,
            instrument=instrument,
        )

        self.assertEqual(report.status, "below_minimum")
        self.assertEqual(report.volume_units, 0)

    def test_caps_volume_at_broker_maximum(self):
        report = calculate_lot_size(
            account_equity=100000.0,
            risk_percent=10.0,
            entry_price=1.10,
            stop_loss_price=1.09,
            instrument=self.instrument,
        )

        self.assertEqual(report.status, "capped_at_maximum")
        self.assertEqual(report.volume_units, self.instrument.maximum_volume_units)
        self.assertLessEqual(report.planned_loss_cash, report.risk_budget_cash)

    def test_price_value_sizing_does_not_infer_a_tick_size(self):
        instrument = BrokerInstrumentSpec(
            symbol="EURUSD",
            tick_size=None,
            tick_value_per_lot=None,
            units_per_lot=100000,
            minimum_volume_units=1000,
            volume_step_units=1000,
            maximum_volume_units=500000,
            price_value_per_lot=100000.0,
        )

        report = calculate_lot_size(
            account_equity=10000.0,
            risk_percent=1.0,
            entry_price=1.1,
            stop_loss_price=1.09495,
            instrument=instrument,
        )

        self.assertEqual(report.stop_distance_ticks, None)
        self.assertEqual(report.volume_units, 19000)
        self.assertAlmostEqual(report.planned_loss_cash, 95.95)
        self.assertLessEqual(report.planned_loss_cash, report.risk_budget_cash)


if __name__ == "__main__":
    unittest.main()
