import os
import pandas as pd
from data.ctrader_client import CTraderClient
from engine.simulator import BacktestSimulator
from strategies.validation_trivial import ValidationTrivial

def run_backtest():
    data_file = "data/EURUSD_H1.parquet"
    
    # 1. If we don't have data yet, fetch it from Fusion/cTrader
    if not os.path.exists(data_file):
        print("No local data found. Fetching from cTrader...")
        client = CTraderClient()
        client.fetch()
    
    # 2. Make sure the file actually exists before trying to read it
    if not os.path.exists(data_file):
        print("\nERROR: Data fetch failed. Please check the error messages above.")
        return

    # 3. Load the data
    print(f"Loading data from {data_file}...")
    df = pd.read_parquet(data_file)
    
    # Cut down the data for a quick test (last 1000 bars)
    df = df.tail(1000).reset_index(drop=True)
    
    # 4. Setup the strategy and engine
    strategy = ValidationTrivial()
    sim = BacktestSimulator(
        df=df, 
        strategy=strategy, 
        starting_balance=10000.0, 
        risk_percent=1.0
    )
    
    # 5. Run it
    sim.run()

if __name__ == "__main__":
    run_backtest()