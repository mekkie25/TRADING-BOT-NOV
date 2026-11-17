# Trading Bot Control Center (Frontend UI Skeleton)

A React + TypeScript + Vite control center UI for an automated forex trading bot, designed to connect to a separate Python FastAPI backend.

## Architecture Overview

- **Single Service Layer (`/src/services/api.ts`)**: All UI pages and components communicate exclusively through `api.ts`. No component imports mock data or calls `fetch` directly.
- **Mock Toggle (`USE_MOCK` & `VITE_API_BASE_URL`)**:
  - Set `VITE_USE_MOCK=true` (default) to serve realistic in-memory mock data from `/src/mock`.
  - Set `VITE_USE_MOCK=false` and `VITE_API_BASE_URL=http://localhost:8000` to connect to the Python FastAPI server.
- **Strict Type Contracts (`/src/types/index.ts`)**: Every request and response shape is defined in TypeScript so FastAPI Pydantic models can mirror them 1:1.

## Running Locally

```bash
npm install
npm run dev
```

---

## Expected FastAPI Backend Endpoints

All endpoints below are relative to `VITE_API_BASE_URL` (e.g., `http://localhost:8000`).

### 1. Market Reference
#### `GET /api/market/pairs`
Returns supported forex instruments.
- **Response (`200 OK`)**:
```json
["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "USDZAR", "AUDUSD"]
```

---

### 2. Bot Control & Dashboard

#### `GET /api/bot/status`
Returns current bot execution status and uptime.
- **Response (`200 OK`)**:
```json
{
  "state": "Running",
  "uptimeSeconds": 18426,
  "startedAt": "2026-11-16T04:56:07Z",
  "activeStrategiesCount": 2,
  "lastHeartbeat": "2026-11-16T10:03:11Z"
}
```

#### `POST /api/bot/start`
Arms active strategies and starts the execution loop.
- **Response (`200 OK`)**: Same `BotStatusInfo` schema as `GET /api/bot/status`.

#### `POST /api/bot/stop`
Halts the execution loop cleanly.
- **Response (`200 OK`)**: Same `BotStatusInfo` schema as `GET /api/bot/status`.

#### `GET /api/account/summary`
Returns account balance, equity, margin, and intraday P/L.
- **Response (`200 OK`)**:
```json
{
  "currency": "ZAR",
  "balance": 254820.5,
  "equity": 257412.8,
  "openPnl": 2592.3,
  "todayPnl": 4185.6,
  "todayPnlPercent": 1.67,
  "openTradesCount": 4,
  "marginUsed": 18420.0,
  "freeMargin": 238992.8,
  "marginLevelPercent": 1397.46,
  "leverage": 100
}
```

#### `GET /api/account/equity-curve?range=1M`
Query param `range`: `1D | 1W | 1M | ALL`.
- **Response (`200 OK`)**:
```json
[
  {
    "timestamp": "2026-11-15T00:00:00Z",
    "label": "Nov 15",
    "equity": 254820.5,
    "balance": 254820.5
  }
]
```

#### `GET /api/positions/open`
Returns all currently open broker positions.
- **Response (`200 OK`)**:
```json
[
  {
    "id": "pos-9041",
    "pair": "EURUSD",
    "direction": "BUY",
    "entryPrice": 1.08425,
    "currentPrice": 1.08612,
    "stopLoss": 1.08195,
    "takeProfit": 1.09025,
    "sizeLots": 0.45,
    "floatingPnl": 1514.7,
    "floatingPnlPips": 18.7,
    "strategyId": "strat-london-breakout",
    "strategyName": "London Breakout Momentum",
    "setupGrade": "A++",
    "openedAt": "2026-11-16T08:14:22Z",
    "swap": 0,
    "commission": -56.7
  }
]
```

#### `GET /api/bot/activity?limit=35`
Returns recent scanner, setup grading, and order events.
- **Response (`200 OK`)**:
```json
[
  {
    "id": "log-108",
    "timestamp": "2026-11-16T08:14:22Z",
    "level": "order",
    "pair": "EURUSD",
    "strategyName": "London Breakout Momentum",
    "message": "Order placed: BUY 0.45 lots EURUSD @ 1.08425",
    "details": "SL 1.08195 · TP 1.09025 · Grade A++"
  }
]
```

---

### 3. Trade Journal

#### `GET /api/journal/trades`
Query parameters: `start_date`, `end_date`, `pair`, `strategy_id`, `setup_grade`, `outcome` (`win | loss`), `search`.
- **Response (`200 OK`)**:
```json
{
  "trades": [
    {
      "id": "trd-1204",
      "openedAt": "2026-11-15T08:15:00Z",
      "closedAt": "2026-11-15T11:42:00Z",
      "pair": "EURUSD",
      "direction": "BUY",
      "strategyId": "strat-london-breakout",
      "strategyName": "London Breakout Momentum",
      "setupGrade": "A++",
      "entryPrice": 1.0841,
      "exitPrice": 1.0889,
      "stopLoss": 1.0821,
      "takeProfit": 1.0889,
      "sizeLots": 0.42,
      "pnl": 5120.4,
      "currency": "ZAR",
      "rMultiple": 2.4,
      "durationMinutes": 207,
      "marketConditions": {
        "volatilityRegime": "Normal",
        "marketStructure": "Trending",
        "session": "London",
        "newsNearby": false,
        "spreadPips": 0.5,
        "atrPips": 18,
        "htfBias": "Bullish"
      },
      "notes": "Clean London open displacement.",
      "maeR": 0.22,
      "mfeR": 2.65,
      "commission": -52.5,
      "swap": 0
    }
  ],
  "stats": {
    "totalTrades": 204,
    "wins": 112,
    "losses": 92,
    "winRate": 54.9,
    "netProfit": 148290.4,
    "expectancyR": 0.38,
    "profitFactor": 1.72,
    "avgWin": 4210.5,
    "avgLoss": -2380.2
  },
  "totalCount": 204
}
```

#### `PATCH /api/journal/trades/{tradeId}/notes`
- **Request**:
```json
{
  "notes": "Moved stop to breakeven after +1.5R impulse."
}
```
- **Response (`200 OK`)**: Updated `JournalTrade` object.

---

### 4. Backtester

#### `GET /api/backtests`
Returns list of `SavedBacktestSummary` objects.

#### `GET /api/backtests/{backtestId}`
Returns full `BacktestResult` covering `overview`, `marketConditions`, `slTpOptimizer`, `maeMfe`, `setupGrades`, `robustness`, and `trades`.

#### `POST /api/backtests/run`
Starts an asynchronous simulation job (must strictly evaluate bars causally without future lookahead).
- **Request**:
```json
{
  "name": "London Breakout · 2Y ZAR",
  "strategyId": "strat-london-breakout",
  "pairs": ["EURUSD", "GBPUSD", "USDZAR"],
  "timeframe": "M15",
  "historyLength": "2y",
  "startingBalance": 200000,
  "currency": "ZAR",
  "leverage": 100,
  "riskPerTradePercent": 1.0,
  "brokerAccountType": "Raw Spread / ECN",
  "costs": {
    "spreadPips": 0.8,
    "commissionPerLot": 110,
    "slippagePips": 0.2,
    "swapPerNight": -35
  }
}
```
- **Response (`200 OK`)**:
```json
{
  "jobId": "job-1763310000",
  "status": "running",
  "progressPercent": 12,
  "currentStep": "Loading historical OHLCV bars...",
  "startedAt": "2026-11-16T10:05:00Z"
}
```

#### `GET /api/backtests/jobs/{jobId}`
Returns `BacktestJobStatus` (`resultId` populated when `status === "completed"`).

#### `POST /api/backtests/jobs/{jobId}/cancel`
Cancels an active backtest job and returns updated `BacktestJobStatus`.

#### `DELETE /api/backtests/{backtestId}`
Deletes a saved backtest run (`204` or `200`).

---

### 5. Strategies & Indicators

#### `GET /api/strategies`
Returns `Strategy[]`.

#### `GET /api/strategies/{strategyId}`
Returns single `Strategy` with `parameters` and `gradingRules` (`A++`, `A+`, `A`, `B`, `Bad`).

#### `POST /api/strategies`
Creates/uploads a new strategy.
- **Request**:
```json
{
  "name": "Tokyo Range Fade",
  "description": "Mean reversion on Asian session range extremes.",
  "indicatorIds": ["ind-bb", "ind-rsi"],
  "assignedPairs": ["USDJPY", "AUDUSD"],
  "fileName": "tokyo_range_fade.py",
  "codeSnippet": "class TokyoRangeFade(BaseStrategy): ..."
}
```

#### `PATCH /api/strategies/{strategyId}`
Updates `isActive`, `assignedPairs`, `indicatorIds`, `parameters`, `gradingRules`, or `codeSnippet`.

#### `GET /api/indicators`
Returns `Indicator[]`.

#### `POST /api/indicators`
Creates a custom indicator entry (`CreateIndicatorPayload`).

#### `PATCH /api/indicators/{indicatorId}`
Updates default parameters or description for an indicator.

---

### 6. Risk, Safety & News Filter

#### `PUT /api/risk/settings` / `GET /api/risk/settings`
Returns and updates `RiskSettings` (`positionSizingModel`, `maxRiskPerTradePercent`, `maxDailyLossPercent`, `maxDrawdownPercent`, `maxOpenTrades`, `maxCorrelatedExposurePercent`, `haltOnNewsMinutes`).

#### `POST /api/bot/kill-switch`
Immediately closes all open positions at market and stops the bot.
- **Response (`200 OK`)**:
```json
{
  "botStatus": {
    "state": "Stopped",
    "uptimeSeconds": 0,
    "startedAt": null,
    "activeStrategiesCount": 2,
    "lastHeartbeat": "2026-11-16T10:12:00Z",
    "version": "2.4.1"
  },
  "closedPositionsCount": 4,
  "triggeredAt": "2026-11-16T10:12:00Z"
}
```

#### `GET /api/safety/pairs`
Returns per-pair enable/disable flags (`PairToggleSetting[]`).

#### `PATCH /api/safety/pairs/{pair}`
- **Request**: `{ "enabled": false }`
- **Response (`200 OK`)**: Updated `PairToggleSetting`.

#### `GET /api/safety/auto-pause` & `PUT /api/safety/auto-pause`
Reads or updates `AutoPauseRules`:
```json
{
  "dailyLossLimit": { "enabled": true, "threshold": 3.0, "unit": "%", "description": "..." },
  "maxDrawdown": { "enabled": true, "threshold": 10.0, "unit": "%", "description": "..." },
  "connectionLost": { "enabled": true, "graceSeconds": 30, "description": "..." },
  "consecutiveLosses": { "enabled": true, "threshold": 4, "unit": "trades", "description": "..." }
}
```

#### `GET /api/news/upcoming`
Returns upcoming `NewsEventItem[]` (`timestamp`, `currency`, `title`, `impact`, `forecast`, `previous`, `affectedPairs`).

#### `GET /api/news/filter` & `PUT /api/news/filter`
Reads or updates blackout window (`{ "enabled": true, "minutesBefore": 30, "minutesAfter": 15 }`).

---

### 7. Manual Trade Controls

#### `POST /api/positions/{positionId}/close`
Manually closes an open broker position.
- **Response (`200 OK`)**: `{ "closedPositionId": "pos-9041", "realizedPnl": 1514.7 }`

#### `PATCH /api/positions/{positionId}/sl-tp`
- **Request**: `{ "stopLoss": 1.0835, "takeProfit": 1.0915 }`
- **Response (`200 OK`)**: Updated `OpenPosition`.

#### `POST /api/positions/manual`
Submits an operator-authorized manual market order.
- **Request**:
```json
{
  "pair": "EURUSD",
  "direction": "BUY",
  "sizeLots": 0.1,
  "stopLoss": 1.081,
  "takeProfit": 1.091,
  "comment": "Manual breakout entry"
}
```
- **Response (`200 OK`)**: Created `OpenPosition`.

---

### 8. System Status & Logs

#### `GET /api/system/status`
- **Response (`200 OK`)**:
```json
{
  "serverUptimeSeconds": 412890,
  "cpuPercent": 18.4,
  "ramUsedGb": 2.8,
  "ramTotalGb": 8.0,
  "diskUsedGb": 34.2,
  "diskTotalGb": 100.0,
  "lastHeartbeat": "2026-11-16T10:03:11Z",
  "ctraderStatus": "Connected",
  "dataFeedStatus": "Connected",
  "dataFeedProvider": "cTrader Open API Tick Stream (London LD4)",
  "lastError": { "timestamp": "2026-11-16T06:14:09Z", "component": "DataFeedWorker", "message": "Transient tick delay..." },
  "botVersion": "2.4.1",
  "pythonVersion": "3.12.4"
}
```

#### `GET /api/logs/errors`
Returns `ErrorLogEntry[]` with `severity` (`WARNING | ERROR | CRITICAL`), `component`, `message`, `stackSummary`, `resolved`.

#### `GET /api/logs/trade-audit`
Returns `TradeAuditEntry[]` (`orderId`, `pair`, `direction`, `action`, `requestedPrice`, `executedPrice`, `brokerResponse`, `brokerMessage`, `latencyMs`).

---

### 9. Live vs Backtest, Portfolio Exposure & Data Manager

#### `GET /api/analytics/live-vs-backtest?strategy_id={id}`
Returns `LiveVsBacktestComparison` containing `diverging`, `divergenceReasons`, `live`, `backtest`, and `equityComparison`.

#### `GET /api/portfolio/exposure`
Returns `PortfolioExposureData`: net exposure per currency (`currencyExposures`), correlation matrix (`correlationMatrix`), `totalOpenRiskAmount`, `totalOpenRiskPercent`, `marginUsed`, `freeMargin`, `marginLevelPercent`.

#### `GET /api/data/datasets`
Returns `HistoricalDataset[]`.

#### `POST /api/data/datasets/{datasetId}/download`
Backfills latest candles and returns updated `HistoricalDataset`.

#### `POST /api/data/datasets/{datasetId}/validate`
Runs integrity check and returns updated `HistoricalDataset`.

#### `GET /api/data/datasets/{datasetId}/gaps`
Returns `DataGap[]` (`gapStart`, `gapEnd`, `missingCandles`, `reason`).

---

### 10. Strategy Versioning, Cloning & Journal Upgrades

#### `POST /api/strategies/{strategyId}/clone`
Clones an existing strategy and returns the new `Strategy` object.

#### `POST /api/strategies/{strategyId}/rollback`
- **Request**: `{ "version": "v2.0.0" }`
- **Response (`200 OK`)**: Updated `Strategy`.

#### `PATCH /api/journal/trades/{tradeId}`
Updates `notes`, `tags` (`string[]`), and/or `screenshotUrl`.

#### `GET /api/journal/capital-transactions` & `POST /api/journal/capital-transactions`
Tracks `DEPOSIT` and `WITHDRAWAL` entries separately from trading P/L.

---

### 11. Settings, Alerts, Security (2FA) & Backup

#### `GET /api/settings`
Returns `AppSettings`. Note: `broker.clientSecret` and `telegramBotToken` are **never** returned in plain text.

#### `PUT /api/settings/broker` & `POST /api/settings/broker/test`
Updates cTrader credentials server-side or tests connection.

#### `PUT /api/settings/trading-mode`
- **Request**: `{ "tradingMode": "Demo" | "Live" }`

#### `PUT /api/settings/display-currency`
- **Request**: `{ "displayCurrency": "ZAR" | "USD" }`

#### `PUT /api/settings/notifications`
Updates `NotificationPreferences` (`tradeOpened`, `tradeClosed`, `error`, `botStopped`, `connectionLost`, `dailySummary`, `emailEnabled`, `emailAddress`, `telegramEnabled`, `telegramChatId`, optional `telegramBotToken`).

#### `POST /api/settings/notifications/test`
- **Request**: `{ "channel": "email" | "telegram" }`
- **Response (`200 OK`)**: `{ "channel": "telegram", "success": true, "message": "Test Telegram alert dispatched.", "sentAt": "..." }`

#### `GET /api/security/settings`, `POST /api/security/2fa/setup`, `POST /api/security/2fa/verify`, `POST /api/security/2fa/disable`, `PUT /api/security/session-timeout`, `POST /api/auth/login`
Handles operator login, TOTP 2FA enrollment/verification, and idle session timeout configuration.

#### `GET /api/backup/export/{section}` & `POST /api/backup/import/{section}`
Exports/imports JSON backups where `section` is `journal | strategies | settings`.

