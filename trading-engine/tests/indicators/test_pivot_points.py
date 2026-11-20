import unittest

from indicators.pivot_points import (
    calculate_pivot_points,
    get_pivot_period,
)


class PivotPointsTests(unittest.TestCase):
    def test_uses_the_requested_chart_to_pivot_period_mapping(self):
        expected_periods = {
            "M1": "daily",
            "M5": "daily",
            "M15": "daily",
            "M30": "daily",
            "H1": "daily",
            "H2": "daily",
            "H4": "weekly",
            "D1": "monthly",
            "W1": "yearly",
            "MONTHLY": "yearly",
        }

        for timeframe, expected in expected_periods.items():
            with self.subTest(timeframe=timeframe):
                self.assertEqual(get_pivot_period(timeframe), expected)

    def test_calculates_traditional_levels_from_previous_period_values(self):
        report = calculate_pivot_points(
            "H4",
            previous_high=110,
            previous_low=90,
            previous_close=100,
        )

        self.assertEqual(report.pivot_period, "weekly")
        self.assertEqual(
            report.levels,
            {
                "P": 100.0,
                "R1": 110.0,
                "S1": 90.0,
                "R2": 120.0,
                "S2": 80.0,
                "R3": 130.0,
                "S3": 70.0,
                "R4": 150.0,
                "S4": 50.0,
                "R5": 170.0,
                "S5": 30.0,
            },
        )

    def test_rejects_invalid_or_missing_previous_period_prices(self):
        with self.assertRaisesRegex(ValueError, "within the previous period range"):
            calculate_pivot_points("D1", 110, 90, 120)
        with self.assertRaisesRegex(ValueError, "finite positive number"):
            calculate_pivot_points("D1", float("nan"), 90, 100)
        with self.assertRaisesRegex(ValueError, "Unsupported chart timeframe"):
            calculate_pivot_points("M2", 110, 90, 100)


if __name__ == "__main__":
    unittest.main()
