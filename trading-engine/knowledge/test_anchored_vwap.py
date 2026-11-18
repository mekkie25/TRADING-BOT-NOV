import unittest

from knowledge.anchored_vwap import calculate_anchored_vwap


class AnchoredVwapTests(unittest.TestCase):
    def test_calculates_cumulative_price_weighted_by_supplied_volume(self):
        value = calculate_anchored_vwap([10, 20], [1, 3])

        self.assertEqual(value, 17.5)

    def test_ignores_zero_volume_bars_but_requires_positive_total_volume(self):
        value = calculate_anchored_vwap([10, 20], [0, 2])

        self.assertEqual(value, 20.0)
        with self.assertRaisesRegex(ValueError, "positive volume"):
            calculate_anchored_vwap([10, 20], [0, 0])

    def test_rejects_missing_or_invalid_price_and_volume_values(self):
        with self.assertRaisesRegex(ValueError, "same nonzero number"):
            calculate_anchored_vwap([10], [1, 2])
        with self.assertRaisesRegex(ValueError, "must not be negative"):
            calculate_anchored_vwap([10], [-1])
        with self.assertRaisesRegex(ValueError, "finite number"):
            calculate_anchored_vwap([float("nan")], [1])


if __name__ == "__main__":
    unittest.main()
