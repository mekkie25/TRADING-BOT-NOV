from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from broker.ctrader_symbol_specs import build_ctrader_forex_spec
from broker.lot_sizing import calculate_lot_size
from data.data_quality import inspect_candle_data
from data.live_feed_manager import live_feed_manager
from engine.simulator import BacktestConfig as SimulatorConfig
from engine.simulator import BacktestSimulator
from strategies.validation_trivial import ValidationTrivial
from pydantic import BaseModel, Field
import uuid


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.live_feed_manager = live_feed_manager
    live_feed_manager.start()
    try:
        yield
    finally:
        live_feed_manager.stop()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKTESTS = {}
JOBS = {}


class BacktestCostRequest(BaseModel):
    spreadPips: float = Field(default=1.0, ge=0)
    commissionPerLot: float = Field(default=7.0, ge=0)
    slippagePips: float = Field(default=0.0, ge=0)
    swapPerNight: float = Field(default=0.0, ge=0)


class BacktestRequest(BaseModel):
    strategyId: str
    pairs: List[str] = Field(default_factory=lambda: ["EURUSD"])
    timeframe: str = "H1"
    historyLength: str = "Max available"
    startingBalance: float = Field(default=10000.0, gt=0)
    currency: str = "USD"
    leverage: int = 100
    riskPerTradePercent: float = Field(gt=0, le=100)
    brokerAccountType: str = "Standard"
    costs: BacktestCostRequest = Field(default_factory=BacktestCostRequest)


class LotSizingRequest(BaseModel):
    entryPrice: float = Field(gt=0)
    stopLossPrice: float = Field(gt=0)
    riskPercent: float = Field(gt=0, le=100)


# ==============================================================================
# DASHBOARD ENDPOINTS
# ==============================================================================
@app.get("/api/bot/status")
def get_bot_status():
    return {
        "state": "Stopped", 
        "uptimeSeconds": 0, 
        "activeStrategiesCount": 1, 
        "lastHeartbeat": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/account/summary")
def get_account_summary():
    raise HTTPException(
        status_code=503,
        detail="Broker account data is not connected; account values are unavailable.",
    )

@app.get("/api/account/facts")
def get_account_facts():
    facts = live_feed_manager.get_account_facts()
    if facts is None:
        raise HTTPException(
            status_code=503,
            detail="Broker account facts are not yet available or have become stale.",
        )
    return facts

@app.post("/api/broker/lot-size")
def get_live_lot_size(request: LotSizingRequest):
    if request.entryPrice == request.stopLossPrice:
        raise HTTPException(
            status_code=422,
            detail="Entry price and stop-loss price must be different.",
        )

    account_facts = live_feed_manager.get_account_facts()
    symbol_info = live_feed_manager.get_symbol_info()
    if account_facts is None or symbol_info is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Fresh broker account facts and complete symbol specifications "
                "are required for lot sizing."
            ),
        )

    try:
        instrument = build_ctrader_forex_spec(
            symbol_info,
            account_facts["depositAssetId"],
        )
        report = calculate_lot_size(
            account_equity=account_facts["equity"],
            risk_percent=request.riskPercent,
            entry_price=request.entryPrice,
            stop_loss_price=request.stopLossPrice,
            instrument=instrument,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Broker lot sizing is unavailable: {error}",
        ) from error

    return asdict(report)

@app.get("/api/account/equity-curve")
def get_equity_curve(range: str = "1M"):
    raise HTTPException(
        status_code=503,
        detail="Broker equity history is not connected; account values are unavailable.",
    )

@app.get("/api/positions/open")
def get_open_positions():
    raise HTTPException(
        status_code=503,
        detail="Broker position data is not connected; open positions are unavailable.",
    )

@app.get("/api/bot/activity")
def get_activity_log(limit: int = 50):
    return []

@app.get("/api/settings")
def get_settings():
    feed_status = live_feed_manager.get_snapshot()
    return {
        "broker": {"connectionState": feed_status["connectionState"]},
        "tradingMode": "Demo",
        "security": {"username": "operator@desk"},
    }

@app.get("/api/market/pairs")
def get_pairs():
    return [{"symbol": "EURUSD", "displayName": "EUR/USD"}]

@app.get("/api/market/live")
def get_live_market_data():
    return live_feed_manager.get_snapshot()

@app.get("/api/market/snapshot")
def get_market_snapshot():
    snapshot = live_feed_manager.get_market_snapshot()
    if snapshot is None:
        snapshot_error = live_feed_manager.get_market_snapshot_error()
        if snapshot_error is not None:
            raise HTTPException(
                status_code=503,
                detail=f"The one-minute market snapshot could not be generated: {snapshot_error}",
            )
        raise HTTPException(
            status_code=503,
            detail=(
                "The one-minute market snapshot is unavailable until the "
                "first completed report is generated from an M1 candle."
            ),
        )
    return jsonable_encoder(snapshot)

@app.get("/api/strategies")
def get_strategies():
    return [{"id": "validation_trivial", "name": "Validation Trivial", "isActive": True, "currentVersion": "v1.0.0", "versions": [], "indicatorIds": [], "assignedPairs": ["EURUSD"], "fileName": "", "codeSnippet": "", "updatedAt": "", "parameters": [], "gradingRules": {}, "description": ""}]

# ==============================================================================
# REAL BACKTESTER ENDPOINTS
# ==============================================================================
@app.get("/api/backtests")
def get_saved_backtests():
    summaries = []
    for bid, res in BACKTESTS.items():
        summaries.append({
            "id": bid, "name": res["name"], "createdAt": res["createdAt"],
            "strategyId": res["config"]["strategyId"], "strategyName": res["strategyName"],
            "pairs": res["config"]["pairs"], "timeframe": res["config"]["timeframe"],
            "historyLength": res["config"]["historyLength"], "currency": res["config"]["currency"],
            "startingBalance": res["config"]["startingBalance"], "netProfit": res["overview"]["netProfit"],
            "netReturnPercent": res["overview"]["netReturnPercent"], "winRate": res["overview"]["winRate"],
            "profitFactor": res["overview"]["profitFactor"], "maxDrawdownPercent": res["overview"]["maxDrawdownPercent"],
            "expectancyR": res["overview"]["expectancyR"], "totalTrades": res["overview"]["totalTrades"],
        })
    return summaries

@app.post("/api/backtests/run")
def start_backtest(req: BacktestRequest):
    job_id = str(uuid.uuid4())
    result_id = f"bt-run-{uuid.uuid4()}"
    started_at = datetime.now(timezone.utc)

    if req.strategyId != "validation_trivial":
        raise HTTPException(status_code=400, detail="Only validation_trivial is implemented.")
    if [pair.upper() for pair in req.pairs] != ["EURUSD"]:
        raise HTTPException(status_code=400, detail="This prototype supports EURUSD only.")
    if req.timeframe.upper() != "H1":
        raise HTTPException(status_code=400, detail="This prototype supports H1 data only.")
    if req.currency.upper() != "USD":
        raise HTTPException(status_code=400, detail="This prototype reports account values in USD.")
    if req.costs.swapPerNight != 0:
        raise HTTPException(
            status_code=400,
            detail="Overnight swap is not modeled; set swapPerNight to 0.",
        )

    years = {
        "1y": 1,
        "2y": 2,
        "5y": 5,
        "10y": 10,
    }
    if req.historyLength != "Max available" and req.historyLength not in years:
        raise HTTPException(status_code=400, detail="Unsupported history length.")

    data_file = Path(__file__).parent / "data" / "EURUSD_H1.parquet"
    if not data_file.exists():
        raise HTTPException(status_code=404, detail=f"Local candle data not found: {data_file.name}")
    df = pd.read_parquet(data_file)
    if req.historyLength in years:
        time_column = "time" if "time" in df.columns else "timestamp"
        timestamps = pd.to_datetime(df[time_column], utc=True, errors="coerce")
        latest_time = timestamps.max()
        cutoff = latest_time - pd.Timedelta(days=365 * years[req.historyLength])
        if timestamps.min() > cutoff + pd.Timedelta(days=1):
            raise HTTPException(
                status_code=400,
                detail=f"The local data does not contain the requested {req.historyLength} history.",
            )
        df = df.loc[timestamps >= cutoff].reset_index(drop=True)

    data_quality = inspect_candle_data(df, req.timeframe)
    if data_quality.has_errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Candle data has structural quality errors; simulation was not run.",
                "dataQuality": data_quality.to_dict(),
            },
        )

    strategy = ValidationTrivial()
    config = SimulatorConfig(
        spread_pips=req.costs.spreadPips,
        commission_per_lot_per_side=req.costs.commissionPerLot,
        slippage_pips=req.costs.slippagePips,
    )
    sim = BacktestSimulator(
        df=df,
        strategy=strategy,
        starting_balance=req.startingBalance,
        risk_percent=req.riskPerTradePercent,
        config=config,
    )
    backtest = sim.run()

    formatted_trades = []
    for trade in backtest.trades:
        formatted_trades.append(
            {
                "id": trade.id,
                "pair": trade.symbol,
                "direction": trade.direction.value,
                "setupGrade": "N/A",
                "entryPrice": trade.entry_price,
                "exitPrice": trade.exit_price,
                "stopLoss": trade.sl_price,
                "takeProfit": trade.tp_price,
                "sizeLots": trade.size_lots,
                "pnl": round(trade.pnl, 2),
                "rMultiple": round(trade.r_multiple, 2),
                "openedAt": trade.entry_time.isoformat(),
                "closedAt": trade.exit_time.isoformat(),
                "durationMinutes": int((trade.exit_time - trade.entry_time).total_seconds() / 60),
                "currency": "USD",
                "strategyId": req.strategyId,
                "strategyName": strategy.name,
                "marketConditions": {},
                "notes": trade.exit_reason,
                "tags": [],
                "maeR": 0.0,
                "mfeR": 0.0,
                "commission": round(trade.commission, 2),
                "swap": 0.0,
            }
        )

    daily_returns = [point["return_percent"] for point in backtest.daily_equity]
    daily_std = float(pd.Series(daily_returns).std()) if len(daily_returns) > 1 else 0.0
    sharpe_ratio = (
        float(pd.Series(daily_returns).mean()) / daily_std * (252 ** 0.5)
        if daily_std > 0
        else 0.0
    )
    peak_equity = req.startingBalance
    peak_time = backtest.equity_curve[0]["time"]
    drawdown_start = None
    max_drawdown_amount = 0.0
    recovery_time_days = 0
    losing_streak = 0
    longest_losing_streak = 0
    for point in backtest.equity_curve:
        max_drawdown_amount = max(max_drawdown_amount, peak_equity - point["equity"])
        if point["equity"] >= peak_equity:
            if drawdown_start is not None:
                recovery_time_days = max(
                    recovery_time_days,
                    (point["time"] - drawdown_start).days,
                )
                drawdown_start = None
            peak_equity = point["equity"]
            peak_time = point["time"]
        elif drawdown_start is None:
            drawdown_start = peak_time
    if drawdown_start is not None:
        recovery_time_days = max(
            recovery_time_days,
            (backtest.equity_curve[-1]["time"] - drawdown_start).days,
        )
    for trade in backtest.trades:
        if trade.pnl < 0:
            losing_streak += 1
            longest_losing_streak = max(longest_losing_streak, losing_streak)
        else:
            losing_streak = 0

    wins = [trade for trade in backtest.trades if trade.pnl > 0]
    losses = [trade for trade in backtest.trades if trade.pnl < 0]
    result = {
        "id": result_id,
        "name": "Prototype Backtest",
        "strategyName": strategy.name,
        "createdAt": started_at.isoformat(),
        "prototypeStatus": "unverified",
        "assumptions": backtest.assumptions + [
            f"Data quality ({data_quality.status}): {data_quality.summary}"
        ],
        "dataQuality": data_quality.to_dict(),
        "config": {
            "id": result_id,
            "name": "Prototype Backtest",
            "strategyId": req.strategyId,
            "pairs": ["EURUSD"],
            "timeframe": "H1",
            "historyLength": req.historyLength,
            "startingBalance": req.startingBalance,
            "currency": "USD",
            "leverage": req.leverage,
            "riskPerTradePercent": req.riskPerTradePercent,
            "brokerAccountType": req.brokerAccountType,
            "costs": {
                "spreadPips": req.costs.spreadPips,
                "commissionPerLot": req.costs.commissionPerLot,
                "slippagePips": req.costs.slippagePips,
                "swapPerNight": 0,
            },
        },
        "overview": {
            "totalTrades": backtest.total_trades,
            "wins": backtest.wins,
            "losses": backtest.losses,
            "winRate": round(backtest.win_rate, 1),
            "netProfit": round(backtest.net_profit, 2),
            "netReturnPercent": round(backtest.return_percent, 2),
            "expectancyR": round(backtest.expectancy_r, 2),
            "profitFactor": round(backtest.profit_factor or 0, 2),
            "avgWin": round(sum(trade.pnl for trade in wins) / len(wins), 2) if wins else 0,
            "avgLoss": round(sum(trade.pnl for trade in losses) / len(losses), 2) if losses else 0,
            "maxDrawdownPercent": round(backtest.max_drawdown_percent, 2),
            "maxDrawdownAmount": round(max_drawdown_amount, 2),
            "longestLosingStreak": longest_losing_streak,
            "recoveryTimeDays": recovery_time_days,
            "sharpeRatio": round(sharpe_ratio, 2),
            "finalBalance": round(backtest.final_balance, 2),
            "equityCurve": [
                {
                    "date": point["time"].isoformat(),
                    "equity": round(point["equity"], 2),
                    "drawdownPercent": round(point["drawdown_percent"], 2),
                }
                for point in backtest.equity_curve
            ],
        },
        "trades": formatted_trades,
        "marketConditions": {
            "byVolatility": [],
            "byStructure": [],
            "bySession": [],
            "byDayOfWeek": [],
            "byTimeOfDay": [],
            "byWeek": [],
            "byMonth": [],
        },
        "slTpOptimizer": {"slMultiples": [], "tpMultiples": [], "cells": [], "optimalByVolatility": []},
        "maeMfe": [],
        "setupGrades": [],
        "robustness": {
            "walkForwardFolds": [],
            "monteCarloDistribution": [],
            "monteCarloMaxDd95Percent": 0,
            "monteCarloRuinProbabilityPercent": 0,
            "overallStabilityLabel": "N/A",
            "parameterStability": [],
        },
    }

    BACKTESTS[result_id] = result
    JOBS[job_id] = {
        "jobId": job_id,
        "status": "completed",
        "progressPercent": 100,
        "currentStep": "Prototype simulation complete; results are unverified",
        "startedAt": started_at.isoformat(),
        "resultId": result_id,
    }

    return JOBS[job_id]

@app.get("/api/backtests/jobs/{job_id}")
def get_job_status(job_id: str):
    return JOBS.get(job_id, {"status": "error"})

@app.get("/api/backtests/{backtest_id}")
def get_backtest_result(backtest_id: str):
    return BACKTESTS.get(backtest_id, {})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)