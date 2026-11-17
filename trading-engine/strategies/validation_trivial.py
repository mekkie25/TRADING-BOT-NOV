from strategies.base import Strategy
from engine.models import Signal, Direction

class ValidationTrivial:
    name = "validation_trivial"
    timeframe = "H1"
    symbols = ["EURUSD"]

    def __init__(self):
        self.bar_count = 0

    def on_bar(self, ctx):
        self.bar_count += 1
        
        if self.bar_count % 10 == 0:
            return Signal(
                direction=Direction.BUY,
                sl_atr_multiple=1.5,
                tp_atr_multiple=3.0
            )
        return None