from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from engine.simulator import BacktestSimulator
from strategies.validation_trivial import ValidationTrivial
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKTESTS = {}
JOBS = {}

class BacktestRequest(BaseModel):
    strategyId: str
    startingBalance: float = 10000.0
    riskPerTradePercent: float = 1.0

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
    return {
        "currency": "ZAR", "balance": 181000.0, "equity": 181000.0, 
        "openPnl": 0.0, "todayPnl": 0.0, "todayPnlPercent": 0.0, 
        "openTradesCount": 0, "marginUsed": 0.0, "freeMargin": 181000.0, 
        "marginLevelPercent": 0.0, "leverage": 100
    }

@app.get("/api/account/equity-curve")
def get_equity_curve(range: str = "1M"):
    # Return a dummy flat line for the dashboard chart
    return [
        {"timestamp": datetime.now(timezone.utc).isoformat(), "label": "Start", "equity": 181000.0, "balance": 181000.0},
        {"timestamp": datetime.now(timezone.utc).isoformat(), "label": "Now", "equity": 181000.0, "balance": 181000.0}
    ]

@app.get("/api/positions/open")
def get_open_positions():
    return []

@app.get("/api/bot/activity")
def get_activity_log(limit: int = 50):
    return []

@app.get("/api/settings")
def get_settings():
    return {"broker": {"connectionState": "Connected"}, "tradingMode": "Demo", "security": {"username": "operator@desk"}}

@app.get("/api/market/pairs")
def get_pairs():
    return [{"symbol": "EURUSD", "displayName": "EUR/USD"}]

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
    result_id = f"bt-run-{int(datetime.now().timestamp())}"
    
    data_file = "data/EURUSD_H1.parquet"
    if not os.path.exists(data_file):
        return {"status": "error", "message": "No data found"}

    df = pd.read_parquet(data_file)
    df = df.tail(2000).reset_index(drop=True)
    
    strategy = ValidationTrivial()
    sim = BacktestSimulator(df=df, strategy=strategy, starting_balance=req.startingBalance, risk_percent=req.riskPerTradePercent)
    
    import io, contextlib
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        sim.run()
        
    formatted_trades = []
    for t in sim.closed_trades:
        r_mult = (t.exit_price - t.entry_price) / (t.entry_price - t.sl_price) if t.direction.value == "BUY" else (t.entry_price - t.exit_price) / (t.sl_price - t.entry_price)
        formatted_trades.append({
            "id": t.id, "pair": t.symbol, "direction": t.direction.value, "setupGrade": "A",
            "entryPrice": t.entry_price, "exitPrice": t.exit_price, "sizeLots": t.size_lots,
            "pnl": round(t.pnl, 2), "rMultiple": round(r_mult, 2),
            "openedAt": t.entry_time.isoformat(), "closedAt": t.exit_time.isoformat(),
            "durationMinutes": int((t.exit_time - t.entry_time).total_seconds() / 60), "currency": "USD"
        })

    wins = [t for t in sim.closed_trades if t.pnl > 0]
    losses = [t for t in sim.closed_trades if t.pnl <= 0]
    
    result = {
        "id": result_id, "name": "Live Engine Backtest", "strategyName": "Validation Trivial",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "config": {
            "id": result_id, "name": "Live Engine Backtest", "strategyId": req.strategyId,
            "pairs": ["EURUSD"], "timeframe": "H1", "historyLength": "1y",
            "startingBalance": req.startingBalance, "currency": "USD", "leverage": 100,
            "riskPerTradePercent": req.riskPerTradePercent, "brokerAccountType": "Demo",
            "costs": {"spreadPips": 0, "commissionPerLot": 0, "slippagePips": 0, "swapPerNight": 0}
        },
        "overview": {
            "totalTrades": len(sim.closed_trades), "wins": len(wins), "losses": len(losses),
            "winRate": round((len(wins) / len(sim.closed_trades)) * 100, 1) if sim.closed_trades else 0,
            "netProfit": round(sim.balance - req.startingBalance, 2),
            "netReturnPercent": round(((sim.balance - req.startingBalance) / req.startingBalance) * 100, 1),
            "expectancyR": round(sum(t["rMultiple"] for t in formatted_trades) / len(formatted_trades), 2) if formatted_trades else 0,
            "profitFactor": 0, "avgWin": 0, "avgLoss": 0, "maxDrawdownPercent": 0, "maxDrawdownAmount": 0,
            "longestLosingStreak": 0, "recoveryTimeDays": 0, "sharpeRatio": 0,
            "finalBalance": round(sim.balance, 2),
            "equityCurve": [{"date": "Start", "equity": req.startingBalance, "drawdownPercent": 0}, {"date": "End", "equity": round(sim.balance, 2), "drawdownPercent": 0}]
        },
        "trades": formatted_trades,
        "marketConditions": {"byVolatility": [], "byStructure": [], "bySession": [], "byDayOfWeek": [], "byTimeOfDay": [], "byWeek": [], "byMonth": []},
        "slTpOptimizer": {"slMultiples": [1.0], "tpMultiples": [2.0], "cells": [], "optimalByVolatility": []},
        "maeMfe": [], "setupGrades": [],
        "robustness": {"walkForwardFolds": [], "monteCarloDistribution": [], "monteCarloMaxDd95Percent": 0, "monteCarloRuinProbabilityPercent": 0, "overallStabilityLabel": "N/A", "parameterStability": []}
    }
    
    BACKTESTS[result_id] = result
    JOBS[job_id] = {"jobId": job_id, "status": "completed", "progressPercent": 100, "currentStep": "Simulation complete", "resultId": result_id}
    
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