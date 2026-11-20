import unittest

from indicators.fibonacci_retracement import (
    DEFAULT_FIBONACCI_RATIOS,
    calculate_fibonacci_levels,
)


class FibonacciRetracementTests(unittest.TestCase):
    def test_calculates_default_linear_levels_between_two_points(self):
        levels = calculate_fibonacci_levels(100, 200)

        self.assertEqual(
            [level.ratio for level in levels],
            list(DEFAULT_FIBONACCI_RATIOS),
        )
        expected_prices = [100.0, 123.6, 138.2, 150.0, 161.8, 178.6, 200.0]
        for level, expected_price in zip(levels, expected_prices):
            self.assertAlmostEqual(level.price, expected_price)

    def test_supports_custom_extension_ratios_and_reversed_points(self):
        levels = calculate_fibonacci_levels(
            200,
            100,
            ratios=(-0.5, 0.5, 1.5),
        )

        self.assertEqual(
            [level.price for level in levels],
            [250.0, 150.0, 50.0],
        )

    def test_supports_logarithmic_interpolation_when_requested(self):
        levels = calculate_fibonacci_levels(
            100,
            400,
            ratios=(0.5,),
            logarithmic=True,
        )

        self.assertAlmostEqual(levels[0].price, 200.0)

    def test_rejects_invalid_points_and_ratios(self):
        with self.assertRaisesRegex(ValueError, "price_point_1 must be positive"):
            calculate_fibonacci_levels(0, 100)
        with self.assertRaisesRegex(ValueError, "ratios must be unique"):
            calculate_fibonacci_levels(100, 200, ratios=(0.5, 0.5))
        with self.assertRaisesRegex(ValueError, "At least one"):
            calculate_fibonacci_levels(100, 200, ratios=())


if __name__ == "__main__":
    unittest.main()
