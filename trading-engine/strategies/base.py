from typing import Protocol, Optional
from engine.models import Signal

class Strategy(Protocol):
    name: str
    timeframe: str
    symbols: list[str]

    def on_bar(self, ctx: "BarContext") -> Optional[Signal]:
        """
        Called once per closed bar, per symbol.
        ctx contains ONLY data available up to this bar's close.
        """
        ...