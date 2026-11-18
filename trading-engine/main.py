from pathlib import Path

import pandas as pd
from data.data_quality import inspect_candle_data
from engine.simulator import BacktestSimulator
from strategies.validation_trivial import ValidationTrivial


def run_backtest():
    data_file = Path(__file__).parent / "data" / "EURUSD_H1.parquet"
    if not data_file.exists():
        raise FileNotFoundError(f"Local candle data not found: {data_file}")

    print(f"Loading data from {data_file}...")
    df = pd.read_parquet(data_file)
    data_quality = inspect_candle_data(df, "H1")
    print(f"Data quality: {data_quality.status}")
    print(data_quality.summary)
    for gap in data_quality.gap_examples:
        print(
            f"- Gap: {gap['previousTime']} to {gap['nextTime']} "
            f"({gap['gapHours']:.1f} hours; {gap['category']})"
        )
    for candle in data_quality.largest_candle_ranges:
        print(
            f"- Large-candle review candidate: {candle['time']}, "
            f"{candle['rangePercent']:.3f}% of previous close"
        )
    if data_quality.has_errors:
        raise ValueError(f"Cannot backtest structurally invalid candle data: {data_quality.summary}")

    strategy = ValidationTrivial()
    sim = BacktestSimulator(
        df=df,
        strategy=strategy,
        starting_balance=10000.0,
        risk_percent=2.0,
    )
    result = sim.run()

    print("PROTOTYPE BACKTEST - results are unverified and must not be treated as facts.")
    print(f"Strategy: {strategy.name}")
    print(f"Bars: {len(df)}")
    print(f"Trades: {result.total_trades} (wins: {result.wins}, losses: {result.losses})")
    print(f"Starting balance: ${result.starting_balance:,.2f}")
    print(f"Final balance: ${result.final_balance:,.2f}")
    print(f"Net profit/loss: ${result.net_profit:,.2f}")
    print(f"Return: {result.return_percent:.2f}%")
    print(f"Maximum drawdown: {result.max_drawdown_percent:.2f}%")
    print("Assumptions:")
    for assumption in result.assumptions + [f"Data quality: {data_quality.summary}"]:
        print(f"- {assumption}")


if __name__ == "__main__":
    run_backtest()