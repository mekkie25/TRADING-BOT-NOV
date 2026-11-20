import unittest

from broker.instrument_specs import get_instrument_spec


class InstrumentSpecTests(unittest.TestCase):
    def test_documented_price_distances_use_instrument_units(self):
        self.assertAlmostEqual(get_instrument_spec("EURUSD").price_distance(30, "pips"), 0.003)
        self.assertAlmostEqual(get_instrument_spec("XAUUSD").price_distance(50, "pips"), 5.0)
        self.assertEqual(get_instrument_spec("US30").price_distance(40, "points"), 40.0)
        self.assertEqual(get_instrument_spec("DAX").price_distance(1, "points"), 1.0)

    def test_unknown_units_are_not_guessed(self):
        with self.assertRaisesRegex(ValueError, "not configured"):
            get_instrument_spec("CUSTOM").price_distance(10, "pips")

    def test_explicit_specs_override_defaults(self):
        from broker.instrument_specs import InstrumentSpec

        spec = get_instrument_spec("EURUSD", {"EURUSD": InstrumentSpec("EURUSD", pip_size=0.01)})
        self.assertEqual(spec.price_distance(2, "pips"), 0.02)


if __name__ == "__main__":
    unittest.main()
