from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List

class Direction(Enum):
    BUY = "BUY"
    SELL = "SELL"

class PositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

@dataclass
class Signal:
    direction: Direction
    sl_atr_multiple: float = 1.5
    tp_atr_multiple: float = 3.0
    max_spread_pips: float = 2.0
    strategy_name: str = ""
    variant: str = "default"
    session: str = "unknown"
    sl_mode: str = "volatility_scaled"
    tp_mode: str = "volatility_scaled"
    time_limit_seconds: Optional[int] = None
    stop_distance: Optional[float] = None
    target_distance: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    structural_stop_price: Optional[float] = None
    structural_target_price: Optional[float] = None
    average_candle_size: Optional[float] = None
    confluence_reasons: List[str] = field(default_factory=list)
    confluence_count: int = 0
    definition_parameters: Dict[str, object] = field(default_factory=dict)
    poc_source: Optional[str] = None

@dataclass
class Trade:
    id: str
    symbol: str
    direction: Direction
    entry_time: datetime
    entry_price: float
    size_lots: float
    sl_price: float
    tp_price: float
    
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    r_multiple: float = 0.0
    exit_reason: str = "" 
    signal_time: Optional[datetime] = None
    entry_mid_price: float = 0.0
    exit_mid_price: Optional[float] = None
    gross_pnl: float = 0.0
    spread_cost: float = 0.0
    slippage_cost: float = 0.0
    commission: float = 0.0
    risk_cash: float = 0.0
    strategy_name: str = ""
    strategy_variant: str = "default"
    session: str = "unknown"
    sl_mode: str = "volatility_scaled"
    tp_mode: str = "volatility_scaled"
    time_limit_seconds: Optional[int] = None
    average_candle_size: Optional[float] = None
    confluence_reasons: List[str] = field(default_factory=list)
    confluence_count: int = 0
    definition_parameters: Dict[str, object] = field(default_factory=dict)
    poc_source: Optional[str] = None
    stop_distance: float = 0.0
    target_distance: float = 0.0
    
    max_adverse_excursion: float = 0.0
    max_favorable_excursion: float = 0.0
    conditions: Dict[str, str] = field(default_factory=dict)

    @property
    def position_side(self) -> PositionSide:
        """Describe this trade's position side, not the market's direction."""
        if self.direction == Direction.BUY:
            return PositionSide.LONG
        return PositionSide.SHORT

@dataclass
class AccountState:
    balance: float
    equity: float
    margin_used: float = 0.0