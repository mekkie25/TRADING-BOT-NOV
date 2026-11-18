import unittest
from types import SimpleNamespace

from broker.ctrader_symbol_specs import build_ctrader_forex_spec
from broker.lot_sizing import calculate_lot_size


class CTraderSymbolSpecsTests(unittest.TestCase):
    def setUp(self):
        self.symbol_info = SimpleNamespace(
            symbol="EURUSD",
            base_asset_id=1,
            quote_asset_id=2,
            digits=5,
            pip_position=4,
            lot_size_cents=10000000,
            minimum_volume_cents=100000,
            volume_step_cents=100000,
            maximum_volume_cents=50000000,
            maximum_exposure_cents=None,
        )

    def test_converts_cTrader_volume_cents_and_sizes_from_contract_units(self):
        instrument = build_ctrader_forex_spec(self.symbol_info, deposit_asset_id=2)
        report = calculate_lot_size(
            account_equity=10000.0,
            risk_percent=1.0,
            entry_price=1.1,
            stop_loss_price=1.09,
            instrument=instrument,
        )

        self.assertEqual(instrument.units_per_lot, 100000)
        self.assertEqual(instrument.minimum_volume_units, 1000)
        self.assertEqual(instrument.volume_step_units, 1000)
        self.assertEqual(instrument.maximum_volume_units, 500000)
        self.assertEqual(report.volume_units, 10000)
        self.assertEqual(report.lots, 0.1)
        self.assertEqual(report.planned_loss_cash, 100.0)

    def test_refuses_unavailable_quote_to_deposit_conversion(self):
        self.symbol_info.quote_asset_id = 3

        with self.assertRaisesRegex(ValueError, "currency conversion is not connected"):
            build_ctrader_forex_spec(self.symbol_info, deposit_asset_id=2)

    def test_refuses_volume_fields_that_do_not_convert_to_whole_units(self):
        self.symbol_info.minimum_volume_cents = 1

        with self.assertRaisesRegex(ValueError, "whole volume units"):
            build_ctrader_forex_spec(self.symbol_info, deposit_asset_id=2)

    def test_refuses_unaccounted_broker_maximum_exposure(self):
        self.symbol_info.maximum_exposure_cents = 100000000

        with self.assertRaisesRegex(ValueError, "maxExposure limit"):
            build_ctrader_forex_spec(self.symbol_info, deposit_asset_id=2)


if __name__ == "__main__":
    unittest.main()
