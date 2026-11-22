import unittest
from analytics.metrics import TradeResult, calculate_metrics

class MetricsTests(unittest.TestCase):
    def test_calculates_win_rate_profit_factor_and_expectancy(self):
        trades = [
            TradeResult("WIN", 200.0, 2.0),
            TradeResult("LOSS", -100.0, -1.0),
            TradeResult("WIN", 100.0, 1.0),
        ]
        metrics = calculate_metrics(trades)
        
        self.assertEqual(metrics.total_trades, 3)
        self.assertAlmostEqual(metrics.win_rate, 66.67, places=2)
        self.assertAlmostEqual(metrics.profit_factor, 3.0, places=2)
        self.assertAlmostEqual(metrics.expectancy, 66.67, places=2)
        self.assertAlmostEqual(metrics.average_r, 0.67, places=2)
        self.assertIn("Analyzed 3 trades", metrics.summary)

    def test_calculates_max_drawdown_from_initial_balance(self):
        trades = [
            TradeResult("WIN", 100.0, 1.0),
            TradeResult("LOSS", -200.0, -2.0),
            TradeResult("WIN", 50.0, 0.5),
        ]
        metrics = calculate_metrics(trades, initial_balance=10000.0)
        
        # Balance goes: 10000 -> 10100 (peak) -> 9900 (trough) -> 9950
        self.assertAlmostEqual(metrics.max_drawdown, 200.0)

    def test_handles_empty_trades_without_guessing(self):
        metrics = calculate_metrics([])
        self.assertEqual(metrics.total_trades, 0)
        self.assertIsNone(metrics.profit_factor)
        self.assertIn("No trades to analyze", metrics.summary)

if __name__ == "__main__":
    unittest.main()