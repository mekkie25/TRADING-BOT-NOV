import pandas as pd

class DataClock:
    def __init__(self, full_df: pd.DataFrame):
        self.full_df = full_df
        self.current_index = 0
        self.total_bars = len(full_df)

    def step_forward(self) -> bool:
        """Moves the clock forward by one bar. Returns False if out of data."""
        if self.current_index >= self.total_bars - 1:
            return False
        self.current_index += 1
        return True

    def get_visible_bars(self) -> pd.DataFrame:
        """Returns ONLY the bars up to the current tick. The future is hidden."""
        # Slice up to and including current index
        return self.full_df.iloc[:self.current_index + 1].copy()

    def get_current_time(self):
        return self.full_df.iloc[self.current_index]['timestamp']