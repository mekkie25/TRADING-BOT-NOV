from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class TradeResult:
    """A single completed trade, matching the planned Trade Record."""
    result: str  # "WIN", "LOSS", or "BREAKEVEN"
    money_pnl: float
    r_multiple: float

@dataclass(frozen=True)
class BacktestMetrics:
    """The mathematical summary of a backtest run."""
    total_trades: int
    win_rate: float
    profit_factor: Optional[float]
    expectancy: float
    average_r: float
    max_drawdown: float
    summary: str

def calculate_metrics(trades: List[TradeResult], initial_balance: float = 10000.0) -> BacktestMetrics:
    """Calculates the performance grid required by Master Strategy Section 12.2."""
    if not trades:
        return BacktestMetrics(
            total_trades=0, win_rate=0.0, profit_factor=None, 
            expectancy=0.0, average_r=0.0, max_drawdown=0.0, 
            summary="No trades to analyze."
        )

    total = len(trades)
    wins = [t for t in trades if t.result == "WIN"]
    losses = [t for t in trades if t.result == "LOSS"]
    
    win_rate = (len(wins) / total) * 100.0
    
    gross_profit = sum(t.money_pnl for t in wins)
    gross_loss = abs(sum(t.money_pnl for t in losses))
    
    profit_factor = None
    if gross_loss > 0:
        profit_factor = round(gross_profit / gross_loss, 2)
    elif gross_profit > 0:
        profit_factor = float('inf') # No losses, infinite profit factor
        
    total_pnl = sum(t.money_pnl for t in trades)
    expectancy = round(total_pnl / total, 2)
    average_r = round(sum(t.r_multiple for t in trades) / total, 2)
    
    # Calculate Max Drawdown based on the closing balance of each trade
    current_equity = initial_balance
    peak_equity = initial_balance
    max_dd = 0.0
    
    for t in trades:
        current_equity += t.money_pnl
        if current_equity > peak_equity:
            peak_equity = current_equity
        dd = peak_equity - current_equity
        if dd > max_dd:
            max_dd = dd
            
    summary = (
        f"Analyzed {total} trades. Win rate: {win_rate:.1f}%. "
        f"Profit Factor: {profit_factor}. Expectancy: ${expectancy}. "
        f"Average R: {average_r}. Max Drawdown: ${max_dd:.2f}."
    )
    
    return BacktestMetrics(
        total_trades=total,
        win_rate=win_rate,
        profit_factor=profit_factor,
        expectancy=expectancy,
        average_r=average_r,
        max_drawdown=max_dd,
        summary=summary
    )