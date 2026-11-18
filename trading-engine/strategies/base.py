from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Optional

import pandas as pd

from engine.models import Signal


@dataclass(frozen=True)
class BarContext:
    df: pd.DataFrame
    current_time: datetime
    symbol: str


class Strategy(Protocol):
    name: str
    timeframe: str
    symbols: list[str]

    def on_bar(self, ctx: BarContext) -> Optional[Signal]:
        """
        Called once per closed bar, per symbol.
        ctx contains ONLY data available up to this bar's close.
        """
        ...