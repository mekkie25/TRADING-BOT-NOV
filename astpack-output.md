# CODE

> Packed by astpack v0.2.0 · mode: skeleton · 113 files
>
> Source files are shown in skeleton form: function and method bodies were replaced with `...` placeholders, while imports, types, signatures and class members are intact, as are comments. Files marked [truncated] were cut at a size limit.

## Directory structure

```text
.
├── .gitignore
├── trading-bot-control-center/
│   ├── .env.example
│   ├── .gitignore
│   ├── README.md  [truncated]
│   ├── index.html
│   ├── metadata.json
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── index.css
│       ├── main.tsx
│       ├── components/
│       │   ├── AppContext.tsx
│       │   ├── BacktestResultsView.tsx
│       │   ├── ConfirmDialog.tsx
│       │   ├── DataState.tsx
│       │   ├── GradeBadge.tsx
│       │   ├── JournalDrawer.tsx
│       │   └── Layout.tsx
│       ├── mock/
│       │   ├── backtests.ts
│       │   ├── dashboardAndSettings.ts
│       │   ├── indicatorsAndStrategies.ts
│       │   ├── knowledgeBase.ts
│       │   ├── operations.ts
│       │   └── trades.ts
│       ├── pages/
│       │   ├── BacktesterPage.tsx
│       │   ├── DashboardPage.tsx
│       │   ├── DataManagerPage.tsx
│       │   ├── IndicatorsPage.tsx
│       │   ├── JournalPage.tsx
│       │   ├── LiveVsBacktestPage.tsx
│       │   ├── LoginPage.tsx
│       │   ├── LogsPage.tsx
│       │   ├── PortfolioPage.tsx
│       │   ├── RiskManagementPage.tsx
│       │   ├── SettingsPage.tsx
│       │   ├── StrategiesPage.tsx
│       │   ├── StrategyDetailPage.tsx
│       │   └── SystemStatusPage.tsx
│       ├── services/
│       │   └── api.ts
│       ├── types/
│       │   └── index.ts
│       └── utils/
│           └── formatters.ts
└── trading-engine/
    ├── .gitignore
    ├── api.py
    ├── main.py
    ├── requirements.txt
    ├── run_news.bat
    ├── setup.py
    ├── test_fvg_pro.py
    ├── analytics/
    │   └── metrics.py
    ├── broker/
    │   ├── costs.py
    │   └── fill.py
    ├── data/
    │   ├── bar_store.py
    │   ├── clock.py
    │   └── ctrader_client.py
    ├── engine/
    │   ├── models.py
    │   └── simulator.py
    ├── knowledge/
    │   ├── candlestick_anatomy.py
    │   ├── common.py
    │   ├── equilibrium.py
    │   ├── fair_value_gap.py
    │   ├── inverse_fvg.py
    │   ├── liquidity.py
    │   ├── market_strucure.py
    │   ├── news.py
    │   └── sessions.py
    ├── news_feed/
    │   ├── .env.example
    │   ├── .gitignore
    │   ├── Dockerfile
    │   ├── LICENSE
    │   ├── README.md  [truncated]
    │   ├── config.yaml
    │   ├── docker-compose.yml
    │   ├── local_api.py
    │   ├── requirements.txt
    │   ├── scraper.py
    │   ├── utils.py
    │   ├── docker/
    │   │   └── entrypoint.sh
    │   ├── ff_calendar_toolkit/
    │   │   ├── __init__.py
    │   │   ├── cli.py
    │   │   ├── config.py
    │   │   ├── console.py
    │   │   ├── cron_runtime.py
    │   │   ├── models.py
    │   │   ├── normalize.py
    │   │   ├── runtime.py
    │   │   ├── scheduler.py
    │   │   ├── scraper.py
    │   │   ├── service.py
    │   │   ├── storage.py
    │   │   ├── viewer.py
    │   │   └── alerts/
    │   │       ├── __init__.py
    │   │       ├── events.py
    │   │       ├── matcher.py
    │   │       ├── models.py
    │   │       ├── notifiers.py
    │   │       ├── rules.py
    │   │       ├── service.py
    │   │       └── state.py
    │   ├── rules/
    │   │   └── usd_high_impact_example.yaml
    │   ├── scripts/
    │   │   ├── refresh_docker.sh
    │   │   ├── run.sh
    │   │   └── setup_env.sh
    │   └── tests/
    │       ├── test_alert_matching.py
    │       ├── test_alert_notifiers.py
    │       ├── test_alert_rules.py
    │       ├── test_alert_state.py
    │       ├── test_cron_runtime.py
    │       ├── test_normalize.py
    │       ├── test_runtime.py
    │       └── test_storage.py
    └── strategies/
        ├── base.py
        └── validation_trivial.py
```

## Files

### `.gitignore`

```text
.env
venv/
__pycache__/
*.pyc
node_modules/
.vscode/
dist/
repomix-output.xml
```

### `trading-bot-control-center/.env.example`

```dotenv
# FastAPI Backend Base URL (used when VITE_USE_MOCK is set to "false")
VITE_API_BASE_URL="http://localhost:8000"

# Set to "false" to connect the UI to the live Python FastAPI backend instead of /src/mock
VITE_USE_MOCK="true"
```

### `trading-bot-control-center/.gitignore`

```text
node_modules/
build/
dist/
coverage/
.DS_Store
*.log
.env*
!.env.example
```

### `trading-bot-control-center/README.md` [truncated]

````markdown
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
... [truncated: 265 more lines, 8774 chars]
````

### `trading-bot-control-center/index.html`

```html
<!doctype html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Trading Bot Control Center</title>
    <meta
      name="description"
      content="Automated forex trading bot control center for monitoring live execution, trade journaling, backtesting analytics, strategy grading rules, and cTrader broker configuration."
    />
    <meta property="og:title" content="Trading Bot Control Center" />
    <meta
      property="og:description"
      content="Automated forex trading bot control center for monitoring live execution, trade journaling, backtesting analytics, strategy grading rules, and cTrader broker configuration."
    />
    <meta property="og:type" content="website" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap"
      rel="stylesheet"
    />
    <script>
      (function () {
        try {
          var saved = localStorage.getItem('tbcc_theme');
          if (saved === 'light') {
            document.documentElement.classList.remove('dark');
          } else {
            document.documentElement.classList.add('dark');
          }
        } catch (e) {}
      })();
    </script>
  </head>
  <body class="bg-slate-50 text-slate-900 dark:bg-[#0B0F17] dark:text-slate-100 antialiased selection:bg-blue-500/30 selection:text-blue-700 dark:selection:text-blue-200 transition-colors duration-150">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### `trading-bot-control-center/metadata.json`

```json
{
  "name": "Trading Bot Control Center",
  "description": "Automated forex trading bot control center for monitoring live execution, trade journaling, backtesting analytics, strategy grading rules, and cTrader broker configuration.",
  "requestFramePermissions": [],
  "majorCapabilities": []
}
```

### `trading-bot-control-center/package.json`

```json
{
  "name": "react-example",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite --port=3000 --host=0.0.0.0",
    "build": "vite build",
    "preview": "vite preview",
    "clean": "rm -rf dist server.js",
    "lint": "tsc --noEmit"
  },
  "dependencies": {
    "@google/genai": "^2.4.0",
    "@tailwindcss/vite": "^4.3.3",
    "@vitejs/plugin-react": "^6.1.1",
    "dotenv": "^17.2.3",
    "express": "^4.21.2",
    "lucide-react": "^0.546.0",
    "motion": "^12.23.24",
    "react": "^19.0.1",
    "react-dom": "^19.0.1",
    "react-is": "^19.3.1",
    "react-router-dom": "^7.18.5",
    "recharts": "^3.10.1",
    "vite": "^8.3.0"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/node": "^22.14.0",
    "@types/react": "^19.3.0",
    "@types/react-dom": "^19.3.0",
    "autoprefixer": "^10.4.21",
    "esbuild": "^0.25.0",
    "tailwindcss": "^4.3.3",
    "tsx": "^4.21.0",
    "typescript": "^7.0.2"
  }
}
```

### `trading-bot-control-center/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "experimentalDecorators": true,
    "useDefineForClassFields": false,
    "module": "ESNext",
    "types": ["vite/client"],
    "lib": [
      "ES2022",
      "DOM",
      "DOM.Iterable"
    ],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "isolatedModules": true,
    "moduleDetection": "force",
    "allowJs": true,
    "jsx": "react-jsx",
    "paths": {
      "@/*": [
        "./*"
      ]
    },
    "allowImportingTsExtensions": true,
    "noEmit": true
  },
  "exclude": ["dist"]
}
```

### `trading-bot-control-center/vite.config.ts`

```ts
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import fs from 'fs';
import path from 'path';
import {defineConfig} from 'vite';

export default defineConfig(() => { /* ... */ });
```

### `trading-bot-control-center/src/App.tsx`

```tsx
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppProvider, useAppContext } from './components/AppContext';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { JournalPage } from './pages/JournalPage';
import { BacktesterPage } from './pages/BacktesterPage';
import { LiveVsBacktestPage } from './pages/LiveVsBacktestPage';
import { StrategiesPage } from './pages/StrategiesPage';
import { StrategyDetailPage } from './pages/StrategyDetailPage';
import { IndicatorsPage } from './pages/IndicatorsPage';
import { PortfolioPage } from './pages/PortfolioPage';
import { RiskManagementPage } from './pages/RiskManagementPage';
import { DataManagerPage } from './pages/DataManagerPage';
import { LogsPage } from './pages/LogsPage';
import { SystemStatusPage } from './pages/SystemStatusPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';

function AppRoutes() { /* ... */ }

export default function App() { /* ... */ }
```

### `trading-bot-control-center/src/index.css`

```css
@import "tailwindcss";
@custom-variant dark (&:where(.dark, .dark *));

@theme {
  --font-display: "Archivo", ui-sans-serif, system-ui, sans-serif;
  --font-sans: "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, monospace;
}

@layer base {
  html {
    font-family: var(--font-sans);
    color-scheme: light;
  }

  html.dark {
    color-scheme: dark;
  }

  h1, h2, h3, h4 {
    font-family: var(--font-display);
  }
}

/* Theme-aware scrollbars */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f5f9;
}

html.dark ::-webkit-scrollbar-track {
  background: #0b0f17;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

html.dark ::-webkit-scrollbar-thumb {
  background: #1e293b;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

html.dark ::-webkit-scrollbar-thumb:hover {
  background: #334155;
}
```

### `trading-bot-control-center/src/main.tsx`

```tsx
import {createRoot} from 'react-dom/client';
import App from './App.tsx';
import './index.css';

createRoot(document.getElementById('root')!).render(<App />);
```

### `trading-bot-control-center/src/components/AppContext.tsx`

```tsx
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { api, USE_MOCK } from '../services/api';
import { convertCurrencyAmount, formatCurrency } from '../utils/formatters';
import type {
  AccountSummary,
  BotStatusInfo,
  ConnectionState,
  CurrencyCode,
  DisplayCurrency,
  KillSwitchResult,
  TradingMode,
} from '../types';

export type ThemeMode = 'dark' | 'light';

interface AppContextValue {
  theme: ThemeMode;
  toggleTheme: () => void;
  displayCurrency: DisplayCurrency;
  setDisplayCurrency: (currency: DisplayCurrency) => Promise<void>;
  formatDisplayAmount: (
    amount: number,
    sourceCurrency?: CurrencyCode,
    options?: { signed?: boolean; decimals?: number }
  ) => string;
  botStatus: BotStatusInfo | null;
  account: AccountSummary | null;
  connectionState: ConnectionState;
  tradingMode: TradingMode;
  useMock: boolean;
  isLoadingHeader: boolean;
  headerError: string | null;
  dataVersion: number;
  isAuthenticated: boolean;
  operatorUsername: string;
  lockSession: () => void;
  loginSession: (username: string) => void;
  refreshGlobalState: () => Promise<void>;
  setBotStatusDirect: (status: BotStatusInfo) => void;
  setConnectionDirect: (state: ConnectionState, mode?: TradingMode) => void;
  triggerKillSwitch: () => Promise<KillSwitchResult>;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

const THEME_STORAGE_KEY = 'tbcc_theme';
const CURRENCY_STORAGE_KEY = 'tbcc_display_currency';
const LOCK_STORAGE_KEY = 'tbcc_session_locked';

function getInitialTheme(): ThemeMode { /* ... */ }

function getInitialDisplayCurrency(): DisplayCurrency { /* ... */ }

function getInitialAuth(): boolean { /* ... */ }

export function AppProvider({ children }: { children: ReactNode }) { /* ... */ }

export function useAppContext() { /* ... */ }
```

### `trading-bot-control-center/src/components/BacktestResultsView.tsx`

```tsx
import { useState } from 'react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts';
import { AlertTriangle, Download } from 'lucide-react';
import type { BacktestResult, ConditionBreakdownItem } from '../types';
import { GradeBadge } from './GradeBadge';
import { useAppContext } from './AppContext';
import {
  exportTradesToCsv,
  formatCurrency,
  formatDateTime,
  formatDuration,
  formatPairPrice,
} from '../utils/formatters';

type ResultsTab =
  | 'overview'
  | 'conditions'
  | 'sltp'
  | 'maemfe'
  | 'grades'
  | 'robustness'
  | 'trades';

type ConditionDimension =
  | 'byVolatility'
  | 'byStructure'
  | 'bySession'
  | 'byDayOfWeek'
  | 'byTimeOfDay'
  | 'byWeek'
  | 'byMonth';

const TABS: Array<{ id: ResultsTab; label: string }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'conditions', label: 'Market Conditions' },
  { id: 'sltp', label: 'SL/TP Optimizer' },
  { id: 'maemfe', label: 'MAE/MFE' },
  { id: 'grades', label: 'Setup Grades' },
  { id: 'robustness', label: 'Robustness' },
  { id: 'trades', label: 'Trades' },
];

const CONDITION_DIMENSIONS: Array<{ key: ConditionDimension; label: string }> = [
  { key: 'byVolatility', label: 'Volatility Regime' },
  { key: 'byStructure', label: 'Trend vs Range' },
  { key: 'bySession', label: 'Session' },
  { key: 'byDayOfWeek', label: 'Day of Week' },
  { key: 'byTimeOfDay', label: 'Time of Day' },
  { key: 'byWeek', label: 'Week of Month' },
  { key: 'byMonth', label: 'Month' },
];

export function BacktestResultsView({ result }: { result: BacktestResult }) { /* ... */ }

function MarketConditionsTab({
  items,
  dimension,
  onChangeDimension,
  currency,
  chartPalette,
}: {
  items: ConditionBreakdownItem[];
  dimension: ConditionDimension;
  onChangeDimension: (d: ConditionDimension) => void;
  currency: BacktestResult['config']['currency'];
  chartPalette: {
    grid: string;
    axisStroke: string;
    tickFill: string;
    tooltipBg: string;
    tooltipBorder: string;
    tooltipText: string;
  };
}) { /* ... */ }

function MetricBox({
  label,
  value,
  subtext,
  tone = 'neutral',
}: {
  label: string;
  value: string;
  subtext?: string;
  tone?: 'neutral' | 'profit' | 'loss';
}) { /* ... */ }
```

### `trading-bot-control-center/src/components/ConfirmDialog.tsx`

```tsx
import { AlertTriangle, X } from 'lucide-react';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'primary';
  isProcessing?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel = 'Cancel',
  variant = 'primary',
  isProcessing = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) { /* ... */ }
```

### `trading-bot-control-center/src/components/DataState.tsx`

```tsx
import type { ReactNode } from 'react';
import { AlertCircle, Inbox, RefreshCw } from 'lucide-react';

interface PanelSkeletonProps {
  rows?: number;
  heightClass?: string;
}

export function PanelSkeleton({ rows = 4, heightClass }: PanelSkeletonProps) { /* ... */ }

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: ReactNode;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon,
}: EmptyStateProps) { /* ... */ }

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) { /* ... */ }

interface PanelShellProps {
  title: string;
  subtitle?: string;
  headerRight?: ReactNode;
  isLoading: boolean;
  error: string | null;
  isEmpty?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyActionLabel?: string;
  onEmptyAction?: () => void;
  onRetry?: () => void;
  skeletonHeightClass?: string;
  skeletonRows?: number;
  children: ReactNode;
  className?: string;
}

export function PanelShell({
  title,
  subtitle,
  headerRight,
  isLoading,
  error,
  isEmpty = false,
  emptyTitle = 'No records available',
  emptyDescription = 'Adjust your filters or wait for new data from the backend.',
  emptyActionLabel,
  onEmptyAction,
  onRetry,
  skeletonHeightClass,
  skeletonRows = 4,
  children,
  className = '',
}: PanelShellProps) { /* ... */ }
```

### `trading-bot-control-center/src/components/GradeBadge.tsx`

```tsx
import type { SetupGrade } from '../types';

const GRADE_STYLES: Record<SetupGrade, string> = {
  'A++': 'border-emerald-500/40 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
  'A+': 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
  'A': 'border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-300',
  'B': 'border-amber-500/35 bg-amber-500/12 text-amber-700 dark:text-amber-300',
  'Bad': 'border-red-500/35 bg-red-500/15 text-red-700 dark:text-red-300',
};

export function GradeBadge({ grade }: { grade: SetupGrade }) { /* ... */ }
```

### `trading-bot-control-center/src/components/JournalDrawer.tsx`

```tsx
import { useEffect, useState, type ChangeEvent } from 'react';
import { Check, ImagePlus, Plus, Save, Trash2, X } from 'lucide-react';
import type { JournalTrade } from '../types';
import { GradeBadge } from './GradeBadge';
import { useAppContext } from './AppContext';
import {
  formatDateTime,
  formatDuration,
  formatPairPrice,
} from '../utils/formatters';

interface JournalDrawerProps {
  trade: JournalTrade | null;
  onClose: () => void;
  onSaveMeta: (
    tradeId: string,
    patch: { notes?: string; tags?: string[]; screenshotUrl?: string }
  ) => Promise<void>;
}

export function JournalDrawer({
  trade,
  onClose,
  onSaveMeta,
}: JournalDrawerProps) { /* ... */ }

function DetailItem({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) { /* ... */ }
```

### `trading-bot-control-center/src/components/Layout.tsx`

```tsx
import { useState, type ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import {
  Activity,
  BookOpen,
  Cpu,
  Database,
  FileText,
  FlaskConical,
  GitCompare,
  Layers,
  Lock,
  Menu,
  Moon,
  OctagonAlert,
  PieChart,
  ServerCog,
  Settings,
  ShieldAlert,
  Sun,
  Wifi,
  WifiOff,
  X,
} from 'lucide-react';
import { useAppContext } from './AppContext';
import { ConfirmDialog } from './ConfirmDialog';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: Activity, end: true },
  { to: '/journal', label: 'Journal', icon: BookOpen, end: false },
  { to: '/backtester', label: 'Backtester', icon: FlaskConical, end: false },
  { to: '/live-vs-backtest', label: 'Live vs Backtest', icon: GitCompare, end: false },
  { to: '/strategies', label: 'Strategies', icon: Layers, end: false },
  { to: '/indicators', label: 'Indicators', icon: Cpu, end: false },
  { to: '/portfolio', label: 'Portfolio', icon: PieChart, end: false },
  { to: '/risk', label: 'Risk & Safety', icon: ShieldAlert, end: false },
  { to: '/data-manager', label: 'Data Manager', icon: Database, end: false },
  { to: '/logs', label: 'Logs & Audit', icon: FileText, end: false },
  { to: '/system-status', label: 'System Status', icon: ServerCog, end: false },
  { to: '/settings', label: 'Settings', icon: Settings, end: false },
];

export function Layout({ children }: { children: ReactNode }) { /* ... */ }
```

### `trading-bot-control-center/src/mock/backtests.ts`

```ts
import type {
  BacktestConfig,
  BacktestEquityPoint,
  BacktestResult,
  ConditionBreakdownItem,
  JournalTrade,
  MaeMfePoint,
  MonteCarloStep,
  SavedBacktestSummary,
  SetupGrade,
  SetupGradeBreakdown,
  SlTpHeatmapCell,
  VolatilityRegime,
} from '../types';
import { generateMockJournalTrades } from './trades';

function buildConditionBuckets(
  trades: JournalTrade[],
  selector: (t: JournalTrade) => string,
  orderedKeys?: string[]
): ConditionBreakdownItem[] { /* ... */ }

function buildBacktestFromConfig(
  id: string,
  name: string,
  createdAt: string,
  strategyName: string,
  config: BacktestConfig,
  seed: number,
  returnScale = 1
): BacktestResult { /* ... */ }

export const MOCK_BACKTEST_RESULTS: Record<string, BacktestResult> = {
  'bt-run-01': buildBacktestFromConfig(
    'bt-run-01',
    'London Breakout · 2Y Multi-Pair ZAR',
    '2026-11-10T16:40:00Z',
    'London Breakout Momentum',
    {
      id: 'bt-run-01',
      name: 'London Breakout · 2Y Multi-Pair ZAR',
      strategyId: 'strat-london-breakout',
      pairs: ['EURUSD', 'GBPUSD', 'USDZAR', 'XAUUSD'],
      timeframe: 'M15',
      historyLength: '2y',
      startingBalance: 200000,
      currency: 'ZAR',
      leverage: 100,
      riskPerTradePercent: 1.0,
      brokerAccountType: 'Raw Spread / ECN',
      costs: {
        spreadPips: 0.8,
        commissionPerLot: 110,
        slippagePips: 0.2,
        swapPerNight: -35,
      },
    },
    88412,
    1.0
  ),
  'bt-run-02': buildBacktestFromConfig(
    'bt-run-02',
    'NY Mean Reversion · 5Y Majors',
    '2026-11-08T11:15:00Z',
    'NY Session Mean Reversion',
    {
      id: 'bt-run-02',
      name: 'NY Mean Reversion · 5Y Majors',
      strategyId: 'strat-ny-reversion',
      pairs: ['EURUSD', 'AUDUSD', 'USDJPY'],
      timeframe: 'M15',
      historyLength: '5y',
      startingBalance: 200000,
      currency: 'ZAR',
      leverage: 100,
      riskPerTradePercent: 0.75,
      brokerAccountType: 'Raw Spread / ECN',
      costs: {
        spreadPips: 0.6,
        commissionPerLot: 110,
        slippagePips: 0.15,
        swapPerNight: -28,
      },
    },
    44910,
    0.78
  ),
  'bt-run-03': buildBacktestFromConfig(
    'bt-run-03',
    'Liquidity Sweep · 1Y Gold & GBP',
    '2026-10-29T19:05:00Z',
    'Multi-TF Liquidity Sweep',
    {
      id: 'bt-run-03',
      name: 'Liquidity Sweep · 1Y Gold & GBP',
      strategyId: 'strat-liquidity-sweep',
      pairs: ['XAUUSD', 'GBPUSD'],
      timeframe: 'H1',
      historyLength: '1y',
      startingBalance: 200000,
      currency: 'ZAR',
      leverage: 100,
      riskPerTradePercent: 1.25,
      brokerAccountType: 'Standard',
      costs: {
        spreadPips: 1.4,
        commissionPerLot: 0,
        slippagePips: 0.3,
        swapPerNight: -45,
      },
    },
    99103,
    1.18
  ),
};

export function toSavedSummary(r: BacktestResult): SavedBacktestSummary { /* ... */ }

export function generateBacktestResultFromConfig(config: BacktestConfig, strategyName: string): BacktestResult { /* ... */ }
```

### `trading-bot-control-center/src/mock/dashboardAndSettings.ts`

```ts
import type {
  AccountSummary,
  ActivityLogEntry,
  AppSettings,
  BotStatusInfo,
  EquityPoint,
  OpenPosition,
  RiskSettings,
} from '../types';

export const MOCK_BOT_STATUS: BotStatusInfo = {
  state: 'Running',
  uptimeSeconds: 18426,
  startedAt: '2026-11-16T04:56:07Z',
  activeStrategiesCount: 2,
  lastHeartbeat: '2026-11-16T10:03:11Z',
  version: '2.4.1',
};

export const MOCK_ACCOUNT_SUMMARY: AccountSummary = {
  currency: 'ZAR',
  balance: 254820.5,
  equity: 257412.8,
  openPnl: 2592.3,
  todayPnl: 4185.6,
  todayPnlPercent: 1.67,
  openTradesCount: 4,
  marginUsed: 18420.0,
  freeMargin: 238992.8,
  marginLevelPercent: 1397.46,
  leverage: 100,
};

export const MOCK_EQUITY_CURVE: EquityPoint[] = [
  { timestamp: '2026-10-18T00:00:00Z', label: 'Oct 18', equity: 215000, balance: 215000 },
  { timestamp: '2026-10-20T00:00:00Z', label: 'Oct 20', equity: 217840, balance: 217200 },
  { timestamp: '2026-10-22T00:00:00Z', label: 'Oct 22', equity: 216120, balance: 216120 },
  { timestamp: '2026-10-24T00:00:00Z', label: 'Oct 24', equity: 221450, balance: 220800 },
  { timestamp: '2026-10-26T00:00:00Z', label: 'Oct 26', equity: 224900, balance: 224900 },
  { timestamp: '2026-10-28T00:00:00Z', label: 'Oct 28', equity: 223100, balance: 223600 },
  { timestamp: '2026-10-30T00:00:00Z', label: 'Oct 30', equity: 228760, balance: 228200 },
  { timestamp: '2026-11-01T00:00:00Z', label: 'Nov 01', equity: 231400, balance: 231400 },
  { timestamp: '2026-11-03T00:00:00Z', label: 'Nov 03', equity: 229850, balance: 230100 },
  { timestamp: '2026-11-05T00:00:00Z', label: 'Nov 05', equity: 235620, balance: 234900 },
  { timestamp: '2026-11-07T00:00:00Z', label: 'Nov 07', equity: 241200, balance: 240500 },
  { timestamp: '2026-11-09T00:00:00Z', label: 'Nov 09', equity: 239400, balance: 239400 },
  { timestamp: '2026-11-11T00:00:00Z', label: 'Nov 11', equity: 246180, balance: 245300 },
  { timestamp: '2026-11-13T00:00:00Z', label: 'Nov 13', equity: 251340, balance: 250600 },
  { timestamp: '2026-11-15T00:00:00Z', label: 'Nov 15', equity: 254820.5, balance: 254820.5 },
  { timestamp: '2026-11-16T10:00:00Z', label: 'Now', equity: 257412.8, balance: 254820.5 },
];

export const MOCK_OPEN_POSITIONS: OpenPosition[] = [
  {
    id: 'pos-9041',
    pair: 'EURUSD',
    direction: 'BUY',
    entryPrice: 1.08425,
    currentPrice: 1.08612,
    stopLoss: 1.08195,
    takeProfit: 1.09025,
    sizeLots: 0.45,
    floatingPnl: 1514.7,
    floatingPnlPips: 18.7,
    strategyId: 'strat-london-breakout',
    strategyName: 'London Breakout Momentum',
    setupGrade: 'A++',
    openedAt: '2026-11-16T08:14:22Z',
    swap: 0,
    commission: -56.7,
  },
  {
    id: 'pos-9042',
    pair: 'USDZAR',
    direction: 'SELL',
    entryPrice: 18.1425,
    currentPrice: 18.089,
    stopLoss: 18.215,
    takeProfit: 17.96,
    sizeLots: 0.3,
    floatingPnl: 1605.0,
    floatingPnlPips: 53.5,
    strategyId: 'strat-london-breakout',
    strategyName: 'London Breakout Momentum',
    setupGrade: 'A+',
    openedAt: '2026-11-16T08:32:09Z',
    swap: 0,
    commission: -38.4,
  },
  {
    id: 'pos-9043',
    pair: 'XAUUSD',
    direction: 'BUY',
    entryPrice: 2586.4,
    currentPrice: 2584.1,
    stopLoss: 2576.0,
    takeProfit: 2612.0,
    sizeLots: 0.08,
    floatingPnl: -331.2,
    floatingPnlPips: -23.0,
    strategyId: 'strat-london-breakout',
    strategyName: 'London Breakout Momentum',
    setupGrade: 'A',
    openedAt: '2026-11-16T09:05:44Z',
    swap: 0,
    commission: -28.8,
  },
  {
    id: 'pos-9044',
    pair: 'AUDUSD',
    direction: 'SELL',
    entryPrice: 0.6489,
    currentPrice: 0.64945,
    stopLoss: 0.6512,
    takeProfit: 0.6438,
    sizeLots: 0.2,
    floatingPnl: -196.2,
    floatingPnlPips: -5.5,
    strategyId: 'strat-ny-reversion',
    strategyName: 'NY Session Mean Reversion',
    setupGrade: 'B',
    openedAt: '2026-11-16T09:41:18Z',
    swap: 0,
    commission: -25.2,
  },
];

export const MOCK_ACTIVITY_LOG: ActivityLogEntry[] = [
  {
    id: 'log-101',
    timestamp: '2026-11-16T10:03:08Z',
    level: 'info',
    pair: 'GBPUSD',
    strategyName: 'London Breakout Momentum',
    message: 'Scanning GBPUSD M15 candle close',
    details: 'ADX(14)=19.4 below threshold 22.0; no entry.',
  },
  {
    id: 'log-102',
    timestamp: '2026-11-16T10:01:45Z',
    level: 'info',
    pair: 'USDJPY',
    strategyName: 'NY Session Mean Reversion',
    message: 'Scanning USDJPY — awaiting New York session window',
    details: 'Spread 0.6 pips · Volatility Normal',
  },
  {
    id: 'log-103',
    timestamp: '2026-11-16T09:41:18Z',
    level: 'order',
    pair: 'AUDUSD',
    strategyName: 'NY Session Mean Reversion',
    message: 'Order placed: SELL 0.20 lots AUDUSD @ 0.64890',
    details: 'SL 0.65120 · TP 0.64380 · Grade B',
  },
  {
    id: 'log-104',
    timestamp: '2026-11-16T09:41:16Z',
    level: 'signal',
    pair: 'AUDUSD',
    strategyName: 'NY Session Mean Reversion',
    message: 'Setup graded B on AUDUSD',
    details: 'BB 2.2σ touch confirmed; ADX 24.1 slightly elevated.',
  },
  {
    id: 'log-105',
    timestamp: '2026-11-16T09:05:44Z',
    level: 'order',
    pair: 'XAUUSD',
    strategyName: 'London Breakout Momentum',
    message: 'Order placed: BUY 0.08 lots XAUUSD @ 2586.40',
    details: 'SL 2576.00 · TP 2612.00 · Grade A',
  },
  {
    id: 'log-106',
    timestamp: '2026-11-16T08:48:12Z',
    level: 'warning',
    pair: 'GBPUSD',
    strategyName: 'London Breakout Momentum',
    message: 'Skipped GBPUSD candidate due to spread spike (2.4 pips)',
    details: 'Exceeds maxSpreadPips=1.8 limit.',
  },
  {
    id: 'log-107',
    timestamp: '2026-11-16T08:32:09Z',
    level: 'order',
    pair: 'USDZAR',
    strategyName: 'London Breakout Momentum',
    message: 'Order placed: SELL 0.30 lots USDZAR @ 18.1425',
    details: 'SL 18.2150 · TP 17.9600 · Grade A+',
  },
  {
    id: 'log-108',
    timestamp: '2026-11-16T08:14:22Z',
    level: 'order',
    pair: 'EURUSD',
    strategyName: 'London Breakout Momentum',
    message: 'Order placed: BUY 0.45 lots EURUSD @ 1.08425',
    details: 'SL 1.08195 · TP 1.09025 · Grade A++',
  },
  {
    id: 'log-109',
    timestamp: '2026-11-16T08:14:20Z',
    level: 'signal',
    pair: 'EURUSD',
    strategyName: 'London Breakout Momentum',
    message: 'Setup graded A++ on EURUSD',
    details: 'H4 & H1 EMAs aligned, ADX 28.6, ADR 31% consumed.',
  },
  {
    id: 'log-110',
    timestamp: '2026-11-16T07:59:58Z',
    level: 'info',
    message: 'London session scan cycle initialized across 6 pairs',
  },
];

export const MOCK_RISK_SETTINGS: RiskSettings = {
  positionSizingModel: 'fixed_fractional',
  fixedLotSize: 0.1,
  maxRiskPerTradePercent: 1.0,
  maxDailyLossPercent: 3.0,
  maxDrawdownPercent: 10.0,
  maxOpenTrades: 5,
  maxCorrelatedExposurePercent: 2.5,
  haltOnNewsMinutes: 15,
};

export const MOCK_APP_SETTINGS: AppSettings = {
  apiBaseUrl: 'http://localhost:8000',
  useMock: true,
  tradingMode: 'Demo',
  defaultCurrency: 'ZAR',
  displayCurrency: 'ZAR',
  broker: {
    provider: 'cTrader',
    clientId: 'ctr_demo_8849201a',
    hasClientSecret: true,
    clientSecretMasked: '••••••••••••••••••••••••',
    accountId: '49201847',
    environment: 'Demo',
    connectionState: 'Connected',
    lastTestedAt: '2026-11-16T09:50:00Z',
    statusMessage: 'Authenticated to cTrader Open API (Demo Server)',
  },
  notifications: {
    tradeOpened: true,
    tradeClosed: true,
    error: true,
    botStopped: true,
    connectionLost: true,
    dailySummary: true,
    emailEnabled: true,
    emailAddress: 'trader@example.com',
    telegramEnabled: true,
    telegramBotTokenMasked: '••••••••••••••••••••',
    hasTelegramToken: true,
    telegramChatId: '-1002491820412',
  },
  security: {
    username: 'mcneill.isaaks@gmail.com',
    twoFactorEnabled: false,
    sessionTimeoutMinutes: 60,
    lastLoginAt: '2026-11-16T04:55:10Z',
  },
};
```

### `trading-bot-control-center/src/mock/indicatorsAndStrategies.ts`

```ts
import type { Indicator, Strategy, ForexPair } from '../types';

export const AVAILABLE_PAIRS: ForexPair[] = [
  'EURUSD',
  'GBPUSD',
  'USDJPY',
  'XAUUSD',
  'USDZAR',
  'AUDUSD',
];

export const MOCK_INDICATORS: Indicator[] = [
  {
    id: 'ind-atr',
    name: 'Average True Range',
    shortCode: 'ATR',
    category: 'Volatility',
    description:
      'Measures market volatility over a rolling lookback window for dynamic stop-loss, take-profit, and regime classification.',
    isCustom: false,
    parameters: [
      { key: 'period', label: 'Lookback Period', type: 'number', defaultValue: 14, min: 5, max: 50, step: 1 },
      { key: 'smoothing', label: 'Smoothing Method', type: 'select', defaultValue: 'RMA', options: ['RMA', 'EMA', 'SMA'] },
    ],
  },
  {
    id: 'ind-ema',
    name: 'Exponential Moving Average',
    shortCode: 'EMA',
    category: 'Trend',
    description:
      'Weighted moving average used for higher-timeframe directional bias and dynamic pullback zones.',
    isCustom: false,
    parameters: [
      { key: 'fastPeriod', label: 'Fast Period', type: 'number', defaultValue: 20, min: 5, max: 100, step: 1 },
      { key: 'slowPeriod', label: 'Slow Period', type: 'number', defaultValue: 50, min: 20, max: 250, step: 5 },
      { key: 'source', label: 'Price Source', type: 'select', defaultValue: 'Close', options: ['Close', 'HL2', 'OHLC4'] },
    ],
  },
  {
    id: 'ind-rsi',
    name: 'Relative Strength Index',
    shortCode: 'RSI',
    category: 'Momentum',
    description:
      'Momentum oscillator measuring speed and magnitude of recent price movements to detect exhaustion and divergence.',
    isCustom: false,
    parameters: [
      { key: 'period', label: 'RSI Period', type: 'number', defaultValue: 14, min: 5, max: 30, step: 1 },
      { key: 'overbought', label: 'Overbought Level', type: 'number', defaultValue: 70, min: 60, max: 85, step: 1 },
      { key: 'oversold', label: 'Oversold Level', type: 'number', defaultValue: 30, min: 15, max: 40, step: 1 },
    ],
  },
  {
    id: 'ind-adx',
    name: 'Average Directional Index',
    shortCode: 'ADX',
    category: 'Trend',
    description:
      'Quantifies trend strength independent of direction; separates trending vs ranging market conditions.',
    isCustom: false,
    parameters: [
      { key: 'period', label: 'ADX Period', type: 'number', defaultValue: 14, min: 7, max: 30, step: 1 },
      { key: 'trendThreshold', label: 'Trend Threshold', type: 'number', defaultValue: 25, min: 15, max: 40, step: 1 },
    ],
  },
  {
    id: 'ind-bb',
    name: 'Bollinger Bands',
    shortCode: 'BB',
    category: 'Volatility',
    description:
      'Standard-deviation envelope around a simple moving average for mean-reversion extremes and volatility squeezes.',
    isCustom: false,
    parameters: [
      { key: 'period', label: 'SMA Period', type: 'number', defaultValue: 20, min: 10, max: 50, step: 1 },
      { key: 'stdDev', label: 'Std Deviation', type: 'number', defaultValue: 2.0, min: 1.0, max: 3.5, step: 0.1 },
    ],
  },
  {
    id: 'ind-vwap',
    name: 'Session Anchored VWAP',
    shortCode: 'AVWAP',
    category: 'Volume',
    description:
      'Tick-volume weighted average price anchored to London or New York session open for institutional fair-value tracking.',
    isCustom: false,
    parameters: [
      { key: 'anchorSession', label: 'Anchor Session', type: 'select', defaultValue: 'London', options: ['Asian', 'London', 'New York'] },
      { key: 'bandMultiplier', label: 'Deviation Band', type: 'number', defaultValue: 1.5, min: 0.5, max: 3.0, step: 0.25 },
    ],
  },
  {
    id: 'ind-swing',
    name: 'Market Structure & Liquidity Pools',
    shortCode: 'MSLP',
    category: 'Structure',
    description:
      'Identifies fractal swing highs/lows, break-of-structure (BOS), and equal high/low liquidity sweeps.',
    isCustom: true,
    parameters: [
      { key: 'swingLeft', label: 'Swing Left Bars', type: 'number', defaultValue: 5, min: 2, max: 15, step: 1 },
      { key: 'swingRight', label: 'Swing Right Bars', type: 'number', defaultValue: 3, min: 1, max: 10, step: 1 },
    ],
  },
  {
    id: 'ind-adr',
    name: 'Average Daily Range',
    shortCode: 'ADR',
    category: 'Volatility',
    description:
      'Tracks rolling daily pip range consumption to avoid chasing exhausted moves late in a session.',
    isCustom: false,
    parameters: [
      { key: 'days', label: 'Lookback Days', type: 'number', defaultValue: 10, min: 5, max: 30, step: 1 },
      { key: 'exhaustionPct', label: 'Exhaustion %', type: 'number', defaultValue: 85, min: 60, max: 120, step: 5 },
    ],
  },
];

export const MOCK_STRATEGIES: Strategy[] = [
  {
    id: 'strat-london-breakout',
    name: 'London Breakout Momentum',
    description:
      'Captures directional expansion out of the Asian session consolidation box during London open when HTF EMA alignment and ADX confirm impulse.',
    isActive: true,
    currentVersion: 'v1.4',
    versions: [
      {
        version: 'v1.4',
        createdAt: '2026-11-12T08:45:00Z',
        notes: 'Tightened maxSpreadPips from 2.2 to 1.8 and added H4 EMA confluence for A++ grading.',
        tradeIds: ['trd-1204', 'trd-1201', 'trd-1198', 'trd-1194', 'trd-1190'],
        tradeCount: 38,
        isCurrent: true,
      },
      {
        version: 'v1.3',
        createdAt: '2026-10-18T10:15:00Z',
        notes: 'Adjusted ATR take-profit multiple from 2.5x to 3.0x based on Q3 walk-forward fold.',
        tradeIds: ['trd-1182', 'trd-1179', 'trd-1171', 'trd-1166'],
        tradeCount: 29,
        isCurrent: false,
      },
      {
        version: 'v1.2',
        createdAt: '2026-09-02T14:00:00Z',
        notes: 'Initial USDZAR and XAUUSD session box scaling deployment.',
        tradeIds: ['trd-1140', 'trd-1134', 'trd-1122'],
        tradeCount: 18,
        isCurrent: false,
      },
    ],
    indicatorIds: ['ind-atr', 'ind-ema', 'ind-adx', 'ind-adr'],
    assignedPairs: ['EURUSD', 'GBPUSD', 'USDZAR', 'XAUUSD'],
    updatedAt: '2026-11-12T08:45:00Z',
    fileName: 'london_breakout_momentum.py',
    codeSnippet: `class LondonBreakoutMomentum(BaseStrategy):
    def evaluate_signal(self, ctx: MarketContext) -> Optional[Signal]:
        # Evaluated server-side in Python FastAPI engine
        if not ctx.in_session("London") or ctx.spread_pips > self.params["max_spread_pips"]:
            return None
        return self.check_box_breakout(ctx)`,
    parameters: [
      { key: 'asianBoxHours', label: 'Asian Box Window (hrs)', type: 'number', value: 6, min: 3, max: 9, step: 1, description: 'Hours prior to London open used to form range.' },
      { key: 'atrSlMultiple', label: 'Stop Loss (ATR Multiple)', type: 'number', value: 1.5, min: 0.5, max: 4.0, step: 0.1 },
      { key: 'atrTpMultiple', label: 'Take Profit (ATR Multiple)', type: 'number', value: 3.0, min: 1.0, max: 8.0, step: 0.25 },
      { key: 'minAdx', label: 'Minimum ADX Filter', type: 'number', value: 22, min: 10, max: 40, step: 1 },
      { key: 'maxSpreadPips', label: 'Max Spread (pips)', type: 'number', value: 1.8, min: 0.5, max: 5.0, step: 0.1 },
      { key: 'avoidHighImpactNews', label: 'Pause Around Red News', type: 'boolean', value: true },
    ],
    gradingRules: {
      'A++': [
        { id: 'gr-lb-1', metric: 'HTF EMA Alignment', operator: '==', threshold: 'Aligned H4 & H1', description: 'Price above/below both H4 50 EMA and H1 20 EMA in breakout direction.' },
        { id: 'gr-lb-2', metric: 'ADX(14)', operator: '>=', threshold: '26', description: 'Strong emerging trend momentum at breakout.' },
        { id: 'gr-lb-3', metric: 'ADR Consumed', operator: '<=', threshold: '45%', description: 'Plenty of daily range expansion remaining.' },
      ],
      'A+': [
        { id: 'gr-lb-4', metric: 'HTF EMA Alignment', operator: '==', threshold: 'Aligned H1', description: 'H1 EMA aligned with breakout direction.' },
        { id: 'gr-lb-5', metric: 'ADX(14)', operator: '>=', threshold: '22', description: 'Moderate trend strength confirmed.' },
      ],
      'A': [
        { id: 'gr-lb-6', metric: 'Spread Ratio', operator: '<=', threshold: '1.5 pips', description: 'Clean liquidity execution with standard spread.' },
        { id: 'gr-lb-7', metric: 'ADR Consumed', operator: '<=', threshold: '65%', description: 'Moderate daily range remaining.' },
      ],
      'B': [
        { id: 'gr-lb-8', metric: 'ADX(14)', operator: '>=', threshold: '17', description: 'Borderline range expansion; reduced conviction.' },
      ],
      'Bad': [
        { id: 'gr-lb-9', metric: 'News Window', operator: '==', threshold: 'Within 15m', description: 'Signal occurs inside high-impact news spread spike.' },
        { id: 'gr-lb-10', metric: 'ADR Consumed', operator: '>=', threshold: '85%', description: 'Daily range exhausted before entry.' },
      ],
    },
    lastBacktestSummary: {
      date: '2026-11-10',
      winRate: 54.2,
      profitFactor: 1.84,
      netReturnPercent: 46.8,
      expectancyR: 0.42,
    },
  },
  {
    id: 'strat-ny-reversion',
    name: 'NY Session Mean Reversion',
    description:
      'Fades overextended Bollinger Band & AVWAP deviations back toward institutional fair value during low-to-normal volatility New York afternoon windows.',
    isActive: true,
    currentVersion: 'v2.1',
    versions: [
      {
        version: 'v2.1',
        createdAt: '2026-11-11T14:20:00Z',
        notes: 'Disabled entries during Extreme volatility regimes after FOMC whipsaw.',
        tradeIds: ['trd-1203', 'trd-1199', 'trd-1195'],
        tradeCount: 31,
        isCurrent: true,
      },
      {
        version: 'v2.0',
        createdAt: '2026-09-24T09:00:00Z',
        notes: 'Migrated mean target from SMA(20) to London/NY Anchored VWAP midpoint.',
        tradeIds: ['trd-1160', 'trd-1155', 'trd-1149'],
        tradeCount: 42,
        isCurrent: false,
      },
    ],
    indicatorIds: ['ind-bb', 'ind-rsi', 'ind-vwap', 'ind-atr'],
    assignedPairs: ['EURUSD', 'AUDUSD', 'USDJPY'],
    updatedAt: '2026-11-11T14:20:00Z',
    fileName: 'ny_mean_reversion.py',
    codeSnippet: `class NYMeanReversion(BaseStrategy):
    def evaluate_signal(self, ctx: MarketContext) -> Optional[Signal]:
        if ctx.volatility_regime == "Extreme":
            return None
        return self.check_avwap_band_rejection(ctx)`,
    parameters: [
      { key: 'bbStdDev', label: 'Bollinger Std Dev', type: 'number', value: 2.2, min: 1.5, max: 3.0, step: 0.1 },
      { key: 'rsiExtremeLow', label: 'RSI Oversold Trigger', type: 'number', value: 28, min: 15, max: 40, step: 1 },
      { key: 'rsiExtremeHigh', label: 'RSI Overbought Trigger', type: 'number', value: 72, min: 60, max: 85, step: 1 },
      { key: 'atrSlMultiple', label: 'Stop Loss (ATR Multiple)', type: 'number', value: 1.25, min: 0.5, max: 3.0, step: 0.05 },
      { key: 'targetMode', label: 'Take Profit Target', type: 'select', value: 'AVWAP_Mid', options: ['AVWAP_Mid', 'BB_Mid', 'Fixed_2R'] },
    ],
    gradingRules: {
      'A++': [
        { id: 'gr-ny-1', metric: 'ADX(14)', operator: '<=', threshold: '20', description: 'Clear non-trending range regime ideal for reversion.' },
        { id: 'gr-ny-2', metric: 'RSI Divergence', operator: '==', threshold: 'Confirmed', description: 'Momentum divergence on M15 at outer 2.2σ band.' },
      ],
      'A+': [
        { id: 'gr-ny-3', metric: 'Volatility Regime', operator: 'in', threshold: 'Low, Normal', description: 'Orderly liquidity without trend shock.' },
      ],
      'A': [
        { id: 'gr-ny-4', metric: 'Spread', operator: '<=', threshold: '1.2 pips', description: 'Tight spread during NY liquidity.' },
      ],
      'B': [
        { id: 'gr-ny-5', metric: 'ADX(14)', operator: '<=', threshold: '26', description: 'Slight directional drift present.' },
      ],
      'Bad': [
        { id: 'gr-ny-6', metric: 'Volatility Regime', operator: '==', threshold: 'Extreme', description: 'Fading parabolic expansion during macro shock.' },
      ],
    },
    lastBacktestSummary: {
      date: '2026-11-08',
      winRate: 61.5,
      profitFactor: 1.62,
      netReturnPercent: 31.4,
      expectancyR: 0.34,
    },
  },
  {
    id: 'strat-liquidity-sweep',
    name: 'Multi-TF Liquidity Sweep',
    description:
      'Monitors equal highs/lows on H1/H4 and executes counter-sweep displacement entries on M15 following a confirmed market structure shift.',
    isActive: false,
    currentVersion: 'v1.1',
    versions: [
      {
        version: 'v1.1',
        createdAt: '2026-11-04T19:10:00Z',
        notes: 'Raised displacement threshold from 0.9x ATR to 1.1x ATR to filter weak sweeps.',
        tradeIds: ['trd-1202', 'trd-1197'],
        tradeCount: 24,
        isCurrent: true,
      },
      {
        version: 'v1.0',
        createdAt: '2026-08-15T11:30:00Z',
        notes: 'Baseline Multi-TF liquidity sweep implementation.',
        tradeIds: ['trd-1115', 'trd-1108'],
        tradeCount: 22,
        isCurrent: false,
      },
    ],
    indicatorIds: ['ind-swing', 'ind-ema', 'ind-atr', 'ind-rsi'],
    assignedPairs: ['XAUUSD', 'GBPUSD', 'USDJPY', 'USDZAR'],
    updatedAt: '2026-11-04T19:10:00Z',
    fileName: 'mtf_liquidity_sweep.py',
    codeSnippet: `class MultiTFLiquiditySweep(BaseStrategy):
    def evaluate_signal(self, ctx: MarketContext) -> Optional[Signal]:
        sweep = ctx.detect_liquidity_sweep(lookback=self.params["swingLookback"])
        if sweep and ctx.confirm_mss():
            return self.build_limit_entry(sweep)`,
    parameters: [
      { key: 'swingLookback', label: 'Liquidity Swing Lookback', type: 'number', value: 24, min: 10, max: 60, step: 2 },
      { key: 'minDisplacementAtr', label: 'Min Displacement (ATR)', type: 'number', value: 1.1, min: 0.5, max: 2.5, step: 0.1 },
      { key: 'atrSlMultiple', label: 'Stop Loss (ATR Multiple)', type: 'number', value: 1.4, min: 0.6, max: 3.0, step: 0.1 },
      { key: 'atrTpMultiple', label: 'Take Profit (ATR Multiple)', type: 'number', value: 3.5, min: 1.5, max: 6.0, step: 0.25 },
    ],
    gradingRules: {
      'A++': [
        { id: 'gr-ls-1', metric: 'Session', operator: '==', threshold: 'London/NY Overlap', description: 'Peak institutional liquidity sweep window.' },
        { id: 'gr-ls-2', metric: 'Displacement Candle', operator: '>=', threshold: '1.5x ATR', description: 'Aggressive institutional orderflow shift after sweep.' },
      ],
      'A+': [
        { id: 'gr-ls-3', metric: 'HTF Bias', operator: '==', threshold: 'Aligned H4', description: 'Sweep occurs into H4 discount/premium zone.' },
      ],
      'A': [
        { id: 'gr-ls-4', metric: 'Retracement Entry', operator: '<=', threshold: '0.62 Fib', description: 'Clean FVG / order-block pullback fill.' },
      ],
      'B': [
        { id: 'gr-ls-5', metric: 'Session', operator: '==', threshold: 'Asian', description: 'Lower volume sweep outside peak sessions.' },
      ],
      'Bad': [
        { id: 'gr-ls-6', metric: 'Spread Spike', operator: '>=', threshold: '3.0 pips', description: 'Thin book execution distortion.' },
      ],
    },
    lastBacktestSummary: {
      date: '2026-10-29',
      winRate: 48.0,
      profitFactor: 1.95,
      netReturnPercent: 52.1,
      expectancyR: 0.51,
    },
  },
];
```

### `trading-bot-control-center/src/mock/knowledgeBase.ts`

```ts
```

### `trading-bot-control-center/src/mock/operations.ts`

```ts
import type {
  AutoPauseRules,
  CapitalTransaction,
  DataGap,
  ErrorLogEntry,
  HistoricalDataset,
  LiveVsBacktestComparison,
  NewsEventItem,
  NewsFilterSettings,
  PairToggleSetting,
  PortfolioExposureData,
  SystemStatusInfo,
  TradeAuditEntry,
} from '../types';

export const MOCK_PAIR_TOGGLES: PairToggleSetting[] = [
  { pair: 'EURUSD', enabled: true, spreadPips: 0.5, maxDailyTrades: 4, updatedAt: '2026-11-16T08:00:00Z' },
  { pair: 'GBPUSD', enabled: true, spreadPips: 0.8, maxDailyTrades: 4, updatedAt: '2026-11-16T08:00:00Z' },
  { pair: 'USDJPY', enabled: true, spreadPips: 0.7, maxDailyTrades: 3, updatedAt: '2026-11-16T08:00:00Z' },
  { pair: 'XAUUSD', enabled: true, spreadPips: 1.8, maxDailyTrades: 2, updatedAt: '2026-11-16T08:00:00Z' },
  { pair: 'USDZAR', enabled: true, spreadPips: 2.2, maxDailyTrades: 2, updatedAt: '2026-11-16T08:00:00Z' },
  { pair: 'AUDUSD', enabled: false, spreadPips: 0.6, maxDailyTrades: 3, updatedAt: '2026-11-15T19:30:00Z' },
];

export const MOCK_AUTO_PAUSE_RULES: AutoPauseRules = {
  dailyLossLimit: {
    enabled: true,
    threshold: 3.0,
    unit: '%',
    description: 'Automatically stop trading for the UTC day if realized + floating loss exceeds threshold.',
  },
  maxDrawdown: {
    enabled: true,
    threshold: 10.0,
    unit: '%',
    description: 'Pause the bot if peak-to-trough account equity drawdown breaches limit.',
  },
  connectionLost: {
    enabled: true,
    graceSeconds: 30,
    description: 'Pause new signal evaluation if cTrader or market data feed disconnects beyond grace window.',
  },
  consecutiveLosses: {
    enabled: true,
    threshold: 4,
    unit: 'trades',
    description: 'Halt new entries after consecutive stopped-out trades until manually resumed.',
  },
};

export const MOCK_SYSTEM_STATUS: SystemStatusInfo = {
  serverUptimeSeconds: 412890, // 4d 18h 41m
  cpuPercent: 18.4,
  ramUsedGb: 2.8,
  ramTotalGb: 8.0,
  diskUsedGb: 34.2,
  diskTotalGb: 100.0,
  lastHeartbeat: '2026-11-16T10:03:11Z',
  ctraderStatus: 'Connected',
  dataFeedStatus: 'Connected',
  dataFeedProvider: 'cTrader Open API Tick Stream (London LD4)',
  lastError: {
    timestamp: '2026-11-16T06:14:09Z',
    component: 'DataFeedWorker',
    message: 'Transient tick delay > 1200ms on USDZAR; reconnected automatically in 1.8s.',
  },
  botVersion: '2.4.1',
  pythonVersion: '3.12.4',
};

export const MOCK_ERROR_LOGS: ErrorLogEntry[] = [
  {
    id: 'err-01',
    timestamp: '2026-11-16T06:14:09Z',
    severity: 'WARNING',
    component: 'DataFeedWorker',
    message: 'Tick stream latency spike (1,240 ms) on USDZAR.',
    stackSummary: 'feed_client.py:182 in _on_heartbeat_check -> auto_resync()',
    resolved: true,
  },
  {
    id: 'err-02',
    timestamp: '2026-11-15T14:30:02Z',
    severity: 'ERROR',
    component: 'OrderRouter',
    message: 'Order #ORD-88219 rejected by broker: Off quotes during US CPI spike.',
    stackSummary: 'ctrader_adapter.py:412 in submit_market_order -> BrokerReject(OFF_QUOTES)',
    resolved: true,
  },
  {
    id: 'err-03',
    timestamp: '2026-11-14T22:00:05Z',
    severity: 'WARNING',
    component: 'RolloverGuard',
    message: 'Spread exceeded 4.5 pips on USDZAR during NY close rollover; paused pair for 15m.',
    resolved: true,
  },
  {
    id: 'err-04',
    timestamp: '2026-11-12T03:18:44Z',
    severity: 'CRITICAL',
    component: 'cTraderSession',
    message: 'WebSocket connection dropped unexpectedly (EOF). Bot entered safe pause and reconnected after 14s.',
    stackSummary: 'ws_transport.py:94 in recv_loop -> ConnectionClosedError(1006)',
    resolved: true,
  },
  {
    id: 'err-05',
    timestamp: '2026-11-10T09:12:33Z',
    severity: 'ERROR',
    component: 'HistorySync',
    message: 'Missing 3 M15 bars on XAUUSD 2026-11-09; backfilled from secondary cache.',
    resolved: true,
  },
];

export const MOCK_TRADE_AUDIT_LOGS: TradeAuditEntry[] = [
  {
    id: 'aud-509',
    timestamp: '2026-11-16T09:41:18Z',
    orderId: 'ORD-9044',
    pair: 'AUDUSD',
    direction: 'SELL',
    action: 'OPEN',
    requestedPrice: 0.6489,
    executedPrice: 0.6489,
    sizeLots: 0.2,
    brokerResponse: 'FILLED',
    brokerMessage: 'Market order filled @ 0.64890',
    latencyMs: 38,
    strategyName: 'NY Session Mean Reversion',
  },
  {
    id: 'aud-508',
    timestamp: '2026-11-16T09:05:44Z',
    orderId: 'ORD-9043',
    pair: 'XAUUSD',
    direction: 'BUY',
    action: 'OPEN',
    requestedPrice: 2586.3,
    executedPrice: 2586.4,
    sizeLots: 0.08,
    brokerResponse: 'REQUOTED',
    brokerMessage: 'Filled with +0.10 slippage within maxSlippage tolerance',
    latencyMs: 64,
    strategyName: 'London Breakout Momentum',
  },
  {
    id: 'aud-507',
    timestamp: '2026-11-16T08:32:09Z',
    orderId: 'ORD-9042',
    pair: 'USDZAR',
    direction: 'SELL',
    action: 'OPEN',
    requestedPrice: 18.1425,
    executedPrice: 18.1425,
    sizeLots: 0.3,
    brokerResponse: 'FILLED',
    brokerMessage: 'Market order filled @ 18.1425',
    latencyMs: 41,
    strategyName: 'London Breakout Momentum',
  },
  {
    id: 'aud-506',
    timestamp: '2026-11-16T08:14:22Z',
    orderId: 'ORD-9041',
    pair: 'EURUSD',
    direction: 'BUY',
    action: 'OPEN',
    requestedPrice: 1.08425,
    executedPrice: 1.08425,
    sizeLots: 0.45,
    brokerResponse: 'FILLED',
    brokerMessage: 'Market order filled @ 1.08425',
    latencyMs: 29,
    strategyName: 'London Breakout Momentum',
  },
  {
    id: 'aud-505',
    timestamp: '2026-11-15T14:30:02Z',
    orderId: 'ORD-88219',
    pair: 'GBPUSD',
    direction: 'BUY',
    action: 'OPEN',
    requestedPrice: 1.2691,
    executedPrice: null,
    sizeLots: 0.25,
    brokerResponse: 'REJECTED',
    brokerMessage: 'OFF_QUOTES — liquidity gap during CPI release',
    latencyMs: 142,
    strategyName: 'London Breakout Momentum',
  },
  {
    id: 'aud-504',
    timestamp: '2026-11-15T11:42:00Z',
    orderId: 'ORD-88190',
    pair: 'EURUSD',
    direction: 'BUY',
    action: 'MODIFY_SLTP',
    requestedPrice: 1.0865,
    executedPrice: 1.0865,
    sizeLots: 0.42,
    brokerResponse: 'MODIFIED',
    brokerMessage: 'Trailing stop moved to 1.08650 (+1.5R lock)',
    latencyMs: 24,
    strategyName: 'London Breakout Momentum',
  },
];

export const MOCK_LIVE_VS_BACKTEST: Record<string, LiveVsBacktestComparison> = {
  'strat-london-breakout': {
    strategyId: 'strat-london-breakout',
    strategyName: 'London Breakout Momentum',
    backtestName: 'London Breakout · 2Y Multi-Pair ZAR',
    diverging: false,
    divergenceReasons: [],
    live: {
      winRate: 52.9,
      expectancyR: 0.39,
      maxDrawdownPercent: 5.4,
      avgTradePnl: 1210.4,
      profitFactor: 1.76,
      totalTrades: 68,
      netReturnPercent: 18.6,
    },
    backtest: {
      winRate: 54.2,
      expectancyR: 0.42,
      maxDrawdownPercent: 6.1,
      avgTradePnl: 1295.0,
      profitFactor: 1.84,
      totalTrades: 180,
      netReturnPercent: 46.8,
    },
    equityComparison: [
      { tradeIndex: 0, label: 'T0', liveReturnPercent: 0, backtestReturnPercent: 0 },
      { tradeIndex: 10, label: 'T10', liveReturnPercent: 2.8, backtestReturnPercent: 3.1 },
      { tradeIndex: 20, label: 'T20', liveReturnPercent: 5.1, backtestReturnPercent: 6.4 },
      { tradeIndex: 30, label: 'T30', liveReturnPercent: 8.4, backtestReturnPercent: 9.0 },
      { tradeIndex: 40, label: 'T40', liveReturnPercent: 10.2, backtestReturnPercent: 12.1 },
      { tradeIndex: 50, label: 'T50', liveReturnPercent: 14.5, backtestReturnPercent: 15.8 },
      { tradeIndex: 60, label: 'T60', liveReturnPercent: 16.9, backtestReturnPercent: 18.2 },
      { tradeIndex: 68, label: 'T68', liveReturnPercent: 18.6, backtestReturnPercent: 20.1 },
    ],
  },
  'strat-ny-reversion': {
    strategyId: 'strat-ny-reversion',
    strategyName: 'NY Session Mean Reversion',
    backtestName: 'NY Mean Reversion · 5Y Majors',
    diverging: true,
    divergenceReasons: [
      'Live Win Rate (48.2%) is 13.3% below backtest baseline (61.5%).',
      'Live Expectancy (+0.11R) is > 0.20R below backtest expectation (+0.34R).',
      'Live Max Drawdown (-9.6%) exceeds backtest expected drawdown (-5.8%).',
    ],
    live: {
      winRate: 48.2,
      expectancyR: 0.11,
      maxDrawdownPercent: 9.6,
      avgTradePnl: 318.5,
      profitFactor: 1.14,
      totalTrades: 56,
      netReturnPercent: 4.2,
    },
    backtest: {
      winRate: 61.5,
      expectancyR: 0.34,
      maxDrawdownPercent: 5.8,
      avgTradePnl: 980.0,
      profitFactor: 1.62,
      totalTrades: 180,
      netReturnPercent: 31.4,
    },
    equityComparison: [
      { tradeIndex: 0, label: 'T0', liveReturnPercent: 0, backtestReturnPercent: 0 },
      { tradeIndex: 10, label: 'T10', liveReturnPercent: 1.9, backtestReturnPercent: 2.6 },
      { tradeIndex: 20, label: 'T20', liveReturnPercent: 3.1, backtestReturnPercent: 5.2 },
      { tradeIndex: 30, label: 'T30', liveReturnPercent: -1.4, backtestReturnPercent: 7.4 },
      { tradeIndex: 40, label: 'T40', liveReturnPercent: 0.8, backtestReturnPercent: 10.1 },
      { tradeIndex: 50, label: 'T50', liveReturnPercent: 2.7, backtestReturnPercent: 12.9 },
      { tradeIndex: 56, label: 'T56', liveReturnPercent: 4.2, backtestReturnPercent: 14.4 },
    ],
  },
  'strat-liquidity-sweep': {
    strategyId: 'strat-liquidity-sweep',
    strategyName: 'Multi-TF Liquidity Sweep',
    backtestName: 'Liquidity Sweep · 1Y Gold & GBP',
    diverging: false,
    divergenceReasons: [],
    live: {
      winRate: 47.8,
      expectancyR: 0.46,
      maxDrawdownPercent: 6.8,
      avgTradePnl: 1410.0,
      profitFactor: 1.88,
      totalTrades: 46,
      netReturnPercent: 16.2,
    },
    backtest: {
      winRate: 48.0,
      expectancyR: 0.51,
      maxDrawdownPercent: 7.2,
      avgTradePnl: 1520.0,
      profitFactor: 1.95,
      totalTrades: 180,
      netReturnPercent: 52.1,
    },
    equityComparison: [
      { tradeIndex: 0, label: 'T0', liveReturnPercent: 0, backtestReturnPercent: 0 },
      { tradeIndex: 10, label: 'T10', liveReturnPercent: 3.4, backtestReturnPercent: 3.9 },
      { tradeIndex: 20, label: 'T20', liveReturnPercent: 7.2, backtestReturnPercent: 7.8 },
      { tradeIndex: 30, label: 'T30', liveReturnPercent: 11.5, backtestReturnPercent: 12.1 },
      { tradeIndex: 40, label: 'T40', liveReturnPercent: 14.1, backtestReturnPercent: 15.6 },
      { tradeIndex: 46, label: 'T46', liveReturnPercent: 16.2, backtestReturnPercent: 17.8 },
    ],
  },
};

export const MOCK_HISTORICAL_DATASETS: HistoricalDataset[] = [
  { id: 'ds-eurusd-m15', pair: 'EURUSD', timeframe: 'M15', startDate: '2019-01-02', endDate: '2026-11-16', candleCount: 194820, gapsFound: 0, lastUpdated: '2026-11-16T09:45:00Z', status: 'Up to date' },
  { id: 'ds-eurusd-h1', pair: 'EURUSD', timeframe: 'H1', startDate: '2016-01-04', endDate: '2026-11-16', candleCount: 68420, gapsFound: 0, lastUpdated: '2026-11-16T09:45:00Z', status: 'Up to date' },
  { id: 'ds-gbpusd-m15', pair: 'GBPUSD', timeframe: 'M15', startDate: '2019-01-02', endDate: '2026-11-16', candleCount: 194790, gapsFound: 2, lastUpdated: '2026-11-16T08:30:00Z', status: 'Up to date' },
  { id: 'ds-usdjpy-m15', pair: 'USDJPY', timeframe: 'M15', startDate: '2019-01-02', endDate: '2026-11-15', candleCount: 194510, gapsFound: 1, lastUpdated: '2026-11-15T21:00:00Z', status: 'Outdated' },
  { id: 'ds-xauusd-m15', pair: 'XAUUSD', timeframe: 'M15', startDate: '2020-01-02', endDate: '2026-11-16', candleCount: 161280, gapsFound: 3, lastUpdated: '2026-11-16T09:30:00Z', status: 'Up to date' },
  { id: 'ds-usdzar-m15', pair: 'USDZAR', timeframe: 'M15', startDate: '2020-01-02', endDate: '2026-11-14', candleCount: 158420, gapsFound: 4, lastUpdated: '2026-11-14T18:20:00Z', status: 'Outdated' },
  { id: 'ds-audusd-m15', pair: 'AUDUSD', timeframe: 'M15', startDate: '2019-01-02', endDate: '2026-11-16', candleCount: 194810, gapsFound: 0, lastUpdated: '2026-11-16T09:45:00Z', status: 'Up to date' },
];

export const MOCK_DATA_GAPS: Record<string, DataGap[]> = {
  'ds-gbpusd-m15': [
    { id: 'gap-1', datasetId: 'ds-gbpusd-m15', gapStart: '2024-03-11T00:00:00Z', gapEnd: '2024-03-11T00:45:00Z', missingCandles: 3, reason: 'Broker DST transition feed pause' },
    { id: 'gap-2', datasetId: 'ds-gbpusd-m15', gapStart: '2025-08-04T13:15:00Z', gapEnd: '2025-08-04T13:30:00Z', missingCandles: 1, reason: 'Dropped M15 bar during server maintenance' },
  ],
  'ds-usdjpy-m15': [
    { id: 'gap-3', datasetId: 'ds-usdjpy-m15', gapStart: '2025-12-26T01:00:00Z', gapEnd: '2025-12-26T02:15:00Z', missingCandles: 5, reason: 'Post-holiday illiquid session' },
  ],
  'ds-xauusd-m15': [
    { id: 'gap-4', datasetId: 'ds-xauusd-m15', gapStart: '2024-11-05T23:00:00Z', gapEnd: '2024-11-05T23:45:00Z', missingCandles: 3, reason: 'Daily XAU market break extension' },
    { id: 'gap-5', datasetId: 'ds-xauusd-m15', gapStart: '2025-04-18T12:00:00Z', gapEnd: '2025-04-18T16:00:00Z', missingCandles: 16, reason: 'Good Friday partial market holiday' },
    { id: 'gap-6', datasetId: 'ds-xauusd-m15', gapStart: '2026-11-09T09:00:00Z', gapEnd: '2026-11-09T09:45:00Z', missingCandles: 3, reason: 'Feed reconnect window' },
  ],
  'ds-usdzar-m15': [
    { id: 'gap-7', datasetId: 'ds-usdzar-m15', gapStart: '2024-07-19T06:30:00Z', gapEnd: '2024-07-19T07:15:00Z', missingCandles: 3, reason: 'Global CrowdStrike outage liquidity halt' },
    { id: 'gap-8', datasetId: 'ds-usdzar-m15', gapStart: '2025-01-02T00:00:00Z', gapEnd: '2025-01-02T01:00:00Z', missingCandles: 4, reason: 'New Year thin book' },
    { id: 'gap-9', datasetId: 'ds-usdzar-m15', gapStart: '2025-10-12T22:00:00Z', gapEnd: '2025-10-12T22:30:00Z', missingCandles: 2, reason: 'Sunday open rollover gap' },
    { id: 'gap-10', datasetId: 'ds-usdzar-m15', gapStart: '2026-06-16T07:00:00Z', gapEnd: '2026-11-16T07:30:00Z', missingCandles: 2, reason: 'Youth Day local bank thin liquidity' },
  ],
};

export const MOCK_PORTFOLIO_EXPOSURE: PortfolioExposureData = {
  accountEquity: 257412.8,
  currency: 'ZAR',
  totalOpenRiskAmount: 7420.5,
  totalOpenRiskPercent: 2.88,
  marginUsed: 18420.0,
  freeMargin: 238992.8,
  marginLevelPercent: 1397.46,
  currencyExposures: [
    { currency: 'EUR', netLots: 0.45, netNotionalZar: 882900, direction: 'LONG', percentOfEquity: 34.3 },
    { currency: 'USD', netLots: -0.55, netNotionalZar: -995500, direction: 'SHORT', percentOfEquity: -38.7 },
    { currency: 'ZAR', netLots: 0.3, netNotionalZar: 543000, direction: 'LONG', percentOfEquity: 21.1 },
    { currency: 'XAU', netLots: 0.08, netNotionalZar: 374100, direction: 'LONG', percentOfEquity: 14.5 },
    { currency: 'AUD', netLots: -0.2, netNotionalZar: -235400, direction: 'SHORT', percentOfEquity: -9.1 },
    { currency: 'GBP', netLots: 0.0, netNotionalZar: 0, direction: 'FLAT', percentOfEquity: 0.0 },
    { currency: 'JPY', netLots: 0.0, netNotionalZar: 0, direction: 'FLAT', percentOfEquity: 0.0 },
  ],
  correlationMatrix: {
    pairs: ['EURUSD', 'USDZAR', 'XAUUSD', 'AUDUSD'],
    matrix: [
      [1.0, -0.72, 0.58, 0.81],
      [-0.72, 1.0, -0.49, -0.66],
      [0.58, -0.49, 1.0, 0.52],
      [0.81, -0.66, 0.52, 1.0],
    ],
  },
};

export const MOCK_CAPITAL_TRANSACTIONS: CapitalTransaction[] = [
  { id: 'cap-01', date: '2026-05-01', type: 'DEPOSIT', amount: 150000, currency: 'ZAR', reference: 'EFT-994012', notes: 'Initial live/paper seed capital' },
  { id: 'cap-02', date: '2026-07-15', type: 'DEPOSIT', amount: 50000, currency: 'ZAR', reference: 'EFT-102844', notes: 'Q3 allocation top-up' },
  { id: 'cap-03', date: '2026-09-30', type: 'WITHDRAWAL', amount: 25000, currency: 'ZAR', reference: 'WDR-44102', notes: 'Quarterly profit sweep' },
];

export const MOCK_NEWS_EVENTS: NewsEventItem[] = [
  {
    id: 'news-1',
    timestamp: '2026-11-16T13:30:00Z',
    currency: 'USD',
    title: 'NY Empire State Manufacturing Index',
    impact: 'Medium',
    forecast: '1.4',
    previous: '-11.9',
    affectedPairs: ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'USDZAR', 'AUDUSD'],
  },
  {
    id: 'news-2',
    timestamp: '2026-11-17T07:00:00Z',
    currency: 'GBP',
    title: 'UK Claimant Count Change & Average Earnings',
    impact: 'High',
    forecast: '18.2K',
    previous: '27.9K',
    affectedPairs: ['GBPUSD'],
  },
  {
    id: 'news-3',
    timestamp: '2026-11-18T13:30:00Z',
    currency: 'USD',
    title: 'US Core Retail Sales m/m',
    impact: 'High',
    forecast: '0.3%',
    previous: '0.5%',
    affectedPairs: ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'USDZAR', 'AUDUSD'],
  },
  {
    id: 'news-4',
    timestamp: '2026-11-19T12:00:00Z',
    currency: 'ZAR',
    title: 'SARB Interest Rate Decision',
    impact: 'High',
    forecast: '7.50%',
    previous: '7.75%',
    affectedPairs: ['USDZAR'],
  },
  {
    id: 'news-5',
    timestamp: '2026-11-20T19:00:00Z',
    currency: 'USD',
    title: 'FOMC Meeting Minutes',
    impact: 'High',
    affectedPairs: ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'USDZAR', 'AUDUSD'],
  },
];

export const MOCK_NEWS_FILTER_SETTINGS: NewsFilterSettings = {
  enabled: true,
  minutesBefore: 30,
  minutesAfter: 15,
};
```

### `trading-bot-control-center/src/mock/trades.ts`

```ts
import type {
  ForexPair,
  JournalTrade,
  MarketStructure,
  SetupGrade,
  TradeDirection,
  TradingSession,
  VolatilityRegime,
} from '../types';

function createSeededRng(seed: number) { /* ... */ }

interface PairSpec {
  pair: ForexPair;
  basePrice: number;
  pipSize: number;
  decimals: number;
  typicalAtrPips: number;
  typicalSpread: number;
}

const PAIR_SPECS: PairSpec[] = [
  { pair: 'EURUSD', basePrice: 1.084, pipSize: 0.0001, decimals: 5, typicalAtrPips: 18, typicalSpread: 0.5 },
  { pair: 'GBPUSD', basePrice: 1.268, pipSize: 0.0001, decimals: 5, typicalAtrPips: 24, typicalSpread: 0.8 },
  { pair: 'USDJPY', basePrice: 153.4, pipSize: 0.01, decimals: 3, typicalAtrPips: 28, typicalSpread: 0.7 },
  { pair: 'XAUUSD', basePrice: 2565.0, pipSize: 0.1, decimals: 2, typicalAtrPips: 75, typicalSpread: 1.8 },
  { pair: 'USDZAR', basePrice: 18.05, pipSize: 0.001, decimals: 4, typicalAtrPips: 42, typicalSpread: 2.2 },
  { pair: 'AUDUSD', basePrice: 0.652, pipSize: 0.0001, decimals: 5, typicalAtrPips: 15, typicalSpread: 0.6 },
];

const STRATEGIES = [
  { id: 'strat-london-breakout', name: 'London Breakout Momentum', version: 'v1.4' },
  { id: 'strat-ny-reversion', name: 'NY Session Mean Reversion', version: 'v2.1' },
  { id: 'strat-liquidity-sweep', name: 'Multi-TF Liquidity Sweep', version: 'v1.1' },
];

const GRADE_PROFILES: Array<{
  grade: SetupGrade;
  weight: number;
  winProb: number;
  avgWinR: number;
  avgLossR: number;
}> = [
  { grade: 'A++', weight: 0.14, winProb: 0.72, avgWinR: 2.55, avgLossR: -0.95 },
  { grade: 'A+', weight: 0.24, winProb: 0.61, avgWinR: 2.15, avgLossR: -0.98 },
  { grade: 'A', weight: 0.34, winProb: 0.53, avgWinR: 1.85, avgLossR: -1.0 },
  { grade: 'B', weight: 0.2, winProb: 0.42, avgWinR: 1.45, avgLossR: -1.02 },
  { grade: 'Bad', weight: 0.08, winProb: 0.26, avgWinR: 1.15, avgLossR: -1.12 },
];

const VOLATILITIES: VolatilityRegime[] = ['Low', 'Normal', 'High', 'Extreme'];
const STRUCTURES: MarketStructure[] = ['Trending', 'Ranging', 'Breakout'];
const SESSIONS: TradingSession[] = ['Asian', 'London', 'New York', 'London/NY Overlap'];
const NEWS_EVENTS = ['US CPI m/m', 'FOMC Rate Decision', 'NFP Payrolls', 'ECB Press Conf', 'UK GDP q/q'];
const SAMPLE_NOTES = [
  'Clean London open displacement with tight spread and H4 EMA alignment.',
  'Partial scale-out triggered at +1.5R; remainder trailed behind M15 swing.',
  'Entered slightly late after pullback; spread widened briefly at NY open.',
  'Stopped out cleanly on reversal candle; respected daily risk limit.',
  'High-conviction liquidity sweep below equal lows; held to full TP.',
  '',
  '',
  '',
];
const TAG_POOL = [
  'htf-aligned',
  'clean-displacement',
  'london-open',
  'spread-spike',
  'partial-tp',
  'retest-entry',
  'news-avoided',
  'trend-continuation',
];

function roundPrice(val: number, decimals: number): number { /* ... */ }

export function generateMockJournalTrades(count = 204, seed = 20261116): JournalTrade[] { /* ... */ }

export const MOCK_JOURNAL_TRADES: JournalTrade[] = generateMockJournalTrades(204, 20261116);
```

### `trading-bot-control-center/src/pages/BacktesterPage.tsx`

```tsx
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  Columns2,
  FolderOpen,
  Play,
  ShieldCheck,
  Square,
  Trash2,
  X,
} from 'lucide-react';
import { api } from '../services/api';
import type {
  BacktestConfig,
  BacktestJobStatus,
  BacktestResult,
  BrokerAccountType,
  CurrencyCode,
  ForexPair,
  HistoryLength,
  SavedBacktestSummary,
  Strategy,
  Timeframe,
} from '../types';
import { BacktestResultsView } from '../components/BacktestResultsView';
import { PanelShell } from '../components/DataState';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { useAppContext } from '../components/AppContext';
import { formatCurrency, formatDateTime } from '../utils/formatters';

const TIMEFRAMES: Timeframe[] = ['M5', 'M15', 'M30', 'H1', 'H4', 'D1'];
const HISTORY_LENGTHS: HistoryLength[] = ['1y', '2y', '5y', '10y', 'Max available'];
const CURRENCIES: CurrencyCode[] = ['ZAR', 'USD', 'EUR', 'GBP'];
const LEVERAGES = [10, 30, 50, 100, 200, 500];
const ACCOUNT_TYPES: BrokerAccountType[] = [
  'Raw Spread / ECN',
  'Standard',
  'Zero Commission',
];

export function BacktesterPage() { /* ... */ }

function ComparisonPanel({
  runs,
  onClose,
}: {
  runs: [BacktestResult, BacktestResult];
  onClose: () => void;
}) { /* ... */ }
```

### `trading-bot-control-center/src/pages/DashboardPage.tsx`

```tsx
import { useCallback, useEffect, useState, type FormEvent } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  AlertTriangle,
  CalendarClock,
  Edit3,
  Power,
  RefreshCw,
  Send,
  X,
  XCircle,
} from 'lucide-react';
import { api } from '../services/api';
import type {
  AccountSummary,
  ActivityLogEntry,
  EquityPoint,
  ForexPair,
  NewsEventItem,
  NewsFilterSettings,
  OpenPosition,
  TradeDirection,
} from '../types';
import { useAppContext } from '../components/AppContext';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { GradeBadge } from '../components/GradeBadge';
import { ErrorState, PanelShell } from '../components/DataState';
import {
  convertCurrencyAmount,
  formatCurrency,
  formatDateTime,
  formatPairPrice,
  formatUptime,
} from '../utils/formatters';

type EquityRange = '1D' | '1W' | '1M' | 'ALL';

export function DashboardPage() { /* ... */ }

function KpiCard({
  label,
  value,
  subtext,
  valueTone = 'neutral',
}: {
  label: string;
  value: string;
  subtext: string;
  valueTone?: 'neutral' | 'profit' | 'loss';
}) { /* ... */ }
```

### `trading-bot-control-center/src/pages/DataManagerPage.tsx`

```tsx
import { useCallback, useEffect, useState } from 'react';
import {
  CheckCircle2,
  DownloadCloud,
  Eye,
  RefreshCw,
  ShieldCheck,
  X,
} from 'lucide-react';
import { api } from '../services/api';
import type { DataGap, HistoricalDataset } from '../types';
import { PanelShell } from '../components/DataState';
import { formatDateTime } from '../utils/formatters';

export function DataManagerPage() { /* ... */ }
```

### `trading-bot-control-center/src/pages/IndicatorsPage.tsx`

```tsx
import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Check, Pencil, Plus, Save, X } from 'lucide-react';
import { api } from '../services/api';
import type { Indicator, IndicatorParameter } from '../types';
import { PanelShell } from '../components/DataState';

const CATEGORIES: Indicator['category'][] = [
  'Trend',
  'Momentum',
  'Volatility',
  'Volume',
  'Structure',
];

export function IndicatorsPage() { /* ... */ }
```

### `trading-bot-control-center/src/pages/JournalPage.tsx`

```tsx
import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import {
  BarChart3,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Download,
  Landmark,
  Plus,
  RotateCcw,
  Search,
  Table2,
} from 'lucide-react';
import { api } from '../services/api';
import type {
  CapitalTransaction,
  ForexPair,
  JournalFilters,
  JournalStats,
  JournalTrade,
  SetupGrade,
  Strategy,
} from '../types';
import { PanelShell } from '../components/DataState';
import { GradeBadge } from '../components/GradeBadge';
import { JournalDrawer } from '../components/JournalDrawer';
import { useAppContext } from '../components/AppContext';
import {
  exportTradesToCsv,
  formatDateTime,
  formatDuration,
  formatPairPrice,
} from '../utils/formatters';

const GRADES: SetupGrade[] = ['A++', 'A+', 'A', 'B', 'Bad'];
const PAGE_SIZE = 25;

type JournalTab = 'ledger' | 'calendar' | 'summary' | 'capital';

interface BreakdownBucket {
  label: string;
  trades: number;
  wins: number;
  pnl: number;
  avgR: number;
}

function buildBreakdown(
  trades: JournalTrade[],
  keyFn: (t: JournalTrade) => string
): BreakdownBucket[] { /* ... */ }

export function JournalPage() { /* ... */ }

function BreakdownCard({
  title,
  rows,
  formatAmount,
}: {
  title: string;
  rows: BreakdownBucket[];
  formatAmount: (amount: number) => string;
}) { /* ... */ }

function StatTile({
  label,
  value,
  tone = 'neutral',
}: {
  label: string;
  value: string;
  tone?: 'neutral' | 'profit' | 'loss';
}) { /* ... */ }
```

### `trading-bot-control-center/src/pages/LiveVsBacktestPage.tsx`

```tsx
import { useCallback, useEffect, useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import type { LiveVsBacktestComparison, Strategy } from '../types';
import { PanelShell } from '../components/DataState';
import { useAppContext } from '../components/AppContext';

export function LiveVsBacktestPage() { /* ... */ }
```

### `trading-bot-control-center/src/pages/LoginPage.tsx`

```tsx
import { useState, type FormEvent } from 'react';
import { Lock, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import { useAppContext } from '../components/AppContext';

export function LoginPage() { /* ... */ }
```

### `trading-bot-control-center/src/pages/LogsPage.tsx`

```tsx
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Download, RefreshCw, Search } from 'lucide-react';
import { api } from '../services/api';
import type {
  ActivityLogEntry,
  ErrorLogEntry,
  ErrorSeverity,
  TradeAuditEntry,
} from '../types';
import { PanelShell } from '../components/DataState';
import { exportRowsToCsv, formatDateTime } from '../utils/formatters';

type LogTab = 'activity' | 'errors' | 'audit';

export function LogsPage() { /* ... */ }
```

### `trading-bot-control-center/src/pages/PortfolioPage.tsx`

```tsx
import { useCallback, useEffect, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import type { PortfolioExposureData } from '../types';
import { PanelShell } from '../components/DataState';
import { useAppContext } from '../components/AppContext';

export function PortfolioPage() { /* ... */ }
```

### `trading-bot-control-center/src/pages/RiskManagementPage.tsx`

```tsx
import { useCallback, useEffect, useState } from 'react';
import { Check, Save, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import type {
  AutoPauseRules,
  NewsFilterSettings,
  PairToggleSetting,
  RiskSettings,
  Strategy,
} from '../types';
import { PanelShell } from '../components/DataState';
import { useAppContext } from '../components/AppContext';

export function RiskManagementPage() { /* ... */ }

function SwitchButton({
  checked,
  disabled,
  label,
  onToggle,
}: {
  checked: boolean;
  disabled?: boolean;
  label: string;
  onToggle: () => void;
}) { /* ... */ }
```

### `trading-bot-control-center/src/pages/SettingsPage.tsx`

```tsx
import { useCallback, useEffect, useState, type ChangeEvent, type FormEvent } from 'react';
import {
  AlertTriangle,
  Bell,
  Check,
  Download,
  KeyRound,
  Lock,
  PlugZap,
  Save,
  Send,
  Server,
  ShieldCheck,
  Upload,
} from 'lucide-react';
import { api, USE_MOCK } from '../services/api';
import type {
  AppSettings,
  DisplayCurrency,
  NotificationPreferences,
  SecuritySettings,
  TradingMode,
  TwoFactorSetupInfo,
} from '../types';
import { PanelShell } from '../components/DataState';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { useAppContext } from '../components/AppContext';
import { downloadJsonFile, formatDateTime } from '../utils/formatters';

export function SettingsPage() { /* ... */ }
```

### `trading-bot-control-center/src/pages/StrategiesPage.tsx`

```tsx
import { useCallback, useEffect, useState, type ChangeEvent, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Columns3, Copy, Plus, Upload, X } from 'lucide-react';
import { api } from '../services/api';
import type { ForexPair, Indicator, Strategy } from '../types';
import { PanelShell } from '../components/DataState';
import { useAppContext } from '../components/AppContext';

export function StrategiesPage() { /* ... */ }
```

### `trading-bot-control-center/src/pages/StrategyDetailPage.tsx`

```tsx
import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Check, History, Plus, RotateCcw, Save, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import type {
  ForexPair,
  GradingCondition,
  Indicator,
  SetupGrade,
  Strategy,
} from '../types';
import { PanelShell } from '../components/DataState';
import { GradeBadge } from '../components/GradeBadge';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { useAppContext } from '../components/AppContext';
import { formatDateTime } from '../utils/formatters';

const GRADES: SetupGrade[] = ['A++', 'A+', 'A', 'B', 'Bad'];
const OPERATORS: GradingCondition['operator'][] = ['>=', '<=', '==', '!=', 'in'];

export function StrategyDetailPage() { /* ... */ }
```

### `trading-bot-control-center/src/pages/SystemStatusPage.tsx`

```tsx
import { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Cpu,
  HardDrive,
  RefreshCw,
  Server,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { api } from '../services/api';
import type { ConnectionState, SystemStatusInfo } from '../types';
import { PanelShell } from '../components/DataState';
import { formatDateTime } from '../utils/formatters';

function formatServerUptime(totalSeconds: number): string { /* ... */ }

export function SystemStatusPage() { /* ... */ }

function ConnectionCard({
  title,
  status,
  detail,
}: {
  title: string;
  status: ConnectionState;
  detail: string;
}) { /* ... */ }
```

### `trading-bot-control-center/src/services/api.ts`

```ts
import type {
  AccountSummary,
  ActivityLogEntry,
  AppSettings,
  AutoPauseRules,
  BacktestConfig,
  BacktestJobStatus,
  BacktestResult,
  BotStatusInfo,
  BrokerSettings,
  BrokerUpdatePayload,
  CapitalTransaction,
  CreateIndicatorPayload,
  CreateStrategyPayload,
  DataGap,
  DisplayCurrency,
  EquityPoint,
  ErrorLogEntry,
  ForexPair,
  HistoricalDataset,
  Indicator,
  JournalFilters,
  JournalResponse,
  JournalStats,
  JournalTrade,
  KillSwitchResult,
  LiveVsBacktestComparison,
  ManualOrderPayload,
  ModifyPositionSlTpPayload,
  NewsEventItem,
  NewsFilterSettings,
  NotificationPreferences,
  OpenPosition,
  PairToggleSetting,
  PortfolioExposureData,
  RiskSettings,
  SavedBacktestSummary,
  SecuritySettings,
  Strategy,
  SystemStatusInfo,
  TestAlertResult,
  TradeAuditEntry,
  TradingMode,
  TwoFactorSetupInfo,
} from '../types';

import {
  AVAILABLE_PAIRS,
  MOCK_INDICATORS,
  MOCK_STRATEGIES,
} from '../mock/indicatorsAndStrategies';
import {
  MOCK_ACCOUNT_SUMMARY,
  MOCK_ACTIVITY_LOG,
  MOCK_APP_SETTINGS,
  MOCK_BOT_STATUS,
  MOCK_EQUITY_CURVE,
  MOCK_OPEN_POSITIONS,
  MOCK_RISK_SETTINGS,
} from '../mock/dashboardAndSettings';
import { MOCK_JOURNAL_TRADES } from '../mock/trades';
import {
  MOCK_BACKTEST_RESULTS,
  generateBacktestResultFromConfig,
  toSavedSummary,
} from '../mock/backtests';
import {
  MOCK_AUTO_PAUSE_RULES,
  MOCK_CAPITAL_TRANSACTIONS,
  MOCK_DATA_GAPS,
  MOCK_ERROR_LOGS,
  MOCK_HISTORICAL_DATASETS,
  MOCK_LIVE_VS_BACKTEST,
  MOCK_NEWS_EVENTS,
  MOCK_NEWS_FILTER_SETTINGS,
  MOCK_PAIR_TOGGLES,
  MOCK_PORTFOLIO_EXPOSURE,
  MOCK_SYSTEM_STATUS,
  MOCK_TRADE_AUDIT_LOGS,
} from '../mock/operations';

// ============================================================================
// Centralized API Configuration
// Set VITE_USE_MOCK=false and VITE_API_BASE_URL=http://localhost:8000 in .env
// to connect this frontend to the Python FastAPI backend.
// ============================================================================
export const USE_MOCK: boolean =
  (import.meta.env.VITE_USE_MOCK ?? 'false').toLowerCase() !== 'false';

export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const STORAGE_BASE_URL_KEY = 'tbcc_api_base_url';

export function getActiveApiBaseUrl(): string { /* ... */ }

// ============================================================================
// In-Memory Mock Store (used ONLY when USE_MOCK === true)
// ============================================================================
function clone<T>(data: T): T { /* ... */ }

const mockStore = {
  botStatus: clone(MOCK_BOT_STATUS) as BotStatusInfo,
  account: clone(MOCK_ACCOUNT_SUMMARY) as AccountSummary,
  equityCurve: clone(MOCK_EQUITY_CURVE) as EquityPoint[],
  openPositions: clone(MOCK_OPEN_POSITIONS) as OpenPosition[],
  activityLog: clone(MOCK_ACTIVITY_LOG) as ActivityLogEntry[],
  errorLogs: clone(MOCK_ERROR_LOGS) as ErrorLogEntry[],
  tradeAuditLogs: clone(MOCK_TRADE_AUDIT_LOGS) as TradeAuditEntry[],
  trades: clone(MOCK_JOURNAL_TRADES) as JournalTrade[],
  capitalTransactions: clone(MOCK_CAPITAL_TRANSACTIONS) as CapitalTransaction[],
  strategies: clone(MOCK_STRATEGIES) as Strategy[],
  indicators: clone(MOCK_INDICATORS) as Indicator[],
  backtests: clone(MOCK_BACKTEST_RESULTS) as Record<string, BacktestResult>,
  backtestJobs: new Map<
    string,
    {
      job: BacktestJobStatus;
      config: BacktestConfig;
      pollCount: number;
    }
  >(),
  riskSettings: clone(MOCK_RISK_SETTINGS) as RiskSettings,
  pairToggles: clone(MOCK_PAIR_TOGGLES) as PairToggleSetting[],
  autoPauseRules: clone(MOCK_AUTO_PAUSE_RULES) as AutoPauseRules,
  systemStatus: clone(MOCK_SYSTEM_STATUS) as SystemStatusInfo,
  liveVsBacktest: clone(MOCK_LIVE_VS_BACKTEST) as Record<string, LiveVsBacktestComparison>,
  datasets: clone(MOCK_HISTORICAL_DATASETS) as HistoricalDataset[],
  dataGaps: clone(MOCK_DATA_GAPS) as Record<string, DataGap[]>,
  portfolio: clone(MOCK_PORTFOLIO_EXPOSURE) as PortfolioExposureData,
  newsEvents: clone(MOCK_NEWS_EVENTS) as NewsEventItem[],
  newsFilter: clone(MOCK_NEWS_FILTER_SETTINGS) as NewsFilterSettings,
  appSettings: clone({
    ...MOCK_APP_SETTINGS,
    apiBaseUrl: getActiveApiBaseUrl(),
    useMock: USE_MOCK,
  }) as AppSettings,
};

const delay = (ms = 130) => new Promise((resolve) => setTimeout(resolve, ms));

async function requestJson<T>(
  path: string,
  options?: RequestInit
): Promise<T> { /* ... */ }

function computeJournalStats(trades: JournalTrade[]): JournalStats { /* ... */ }

function recomputeMockAccountOpenStats() { /* ... */ }

// ============================================================================
// Public Service Layer API
// ============================================================================
export const api = {
  // --- Reference metadata ---
  async getAvailablePairs(): Promise<ForexPair[]> { /* ... */ },

  // --- Dashboard & Bot Control ---
  async getBotStatus(): Promise<BotStatusInfo> { /* ... */ },

  async setBotRunning(run: boolean): Promise<BotStatusInfo> { /* ... */ },

  // --- Safety: Emergency Kill Switch ---
  async triggerKillSwitch(): Promise<KillSwitchResult> { /* ... */ },

  async getAccountSummary(): Promise<AccountSummary> { /* ... */ },

  async getEquityCurve(range: '1D' | '1W' | '1M' | 'ALL' = '1M'): Promise<EquityPoint[]> { /* ... */ },

  async getOpenPositions(): Promise<OpenPosition[]> { /* ... */ },

  // --- Manual Trade Controls ---
  async closePosition(positionId: string): Promise<{ closedPositionId: string; realizedPnl: number }> { /* ... */ },

  async modifyPositionSlTp(
    positionId: string,
    payload: ModifyPositionSlTpPayload
  ): Promise<OpenPosition> { /* ... */ },

  async placeManualOrder(payload: ManualOrderPayload): Promise<OpenPosition> { /* ... */ },

  // --- Logs & Audit ---
  async getActivityLog(limit = 50): Promise<ActivityLogEntry[]> { /* ... */ },

  async getErrorLogs(): Promise<ErrorLogEntry[]> { /* ... */ },

  async getTradeAuditLogs(): Promise<TradeAuditEntry[]> { /* ... */ },

  // --- System Status ---
  async getSystemStatus(): Promise<SystemStatusInfo> { /* ... */ },

  // --- Trade Journal & Capital Ledger ---
  async getJournalTrades(filters: JournalFilters = {}): Promise<JournalResponse> { /* ... */ },

  async updateTradeNotes(tradeId: string, notes: string): Promise<JournalTrade> { /* ... */ },

  async updateTradeMeta(
    tradeId: string,
    patch: { notes?: string; tags?: string[]; screenshotUrl?: string }
  ): Promise<JournalTrade> { /* ... */ },

  async getCapitalTransactions(): Promise<CapitalTransaction[]> { /* ... */ },

  async addCapitalTransaction(
    payload: Omit<CapitalTransaction, 'id'>
  ): Promise<CapitalTransaction> { /* ... */ },

  // --- Backtester ---
  async getSavedBacktests(): Promise<SavedBacktestSummary[]> { /* ... */ },

  async getBacktestResult(backtestId: string): Promise<BacktestResult> { /* ... */ },

  async startBacktest(config: BacktestConfig): Promise<BacktestJobStatus> { /* ... */ },

  async getBacktestJobStatus(jobId: string): Promise<BacktestJobStatus> { /* ... */ },

  async cancelBacktestJob(jobId: string): Promise<BacktestJobStatus> { /* ... */ },

  async deleteBacktest(backtestId: string): Promise<void> { /* ... */ },

  // --- Live vs Backtest Comparison ---
  async getLiveVsBacktest(strategyId: string): Promise<LiveVsBacktestComparison> { /* ... */ },

  // --- Strategies (incl. Versioning & Cloning) ---
  async getStrategies(): Promise<Strategy[]> { /* ... */ },

  async getStrategy(strategyId: string): Promise<Strategy> { /* ... */ },

  async createStrategy(payload: CreateStrategyPayload): Promise<Strategy> { /* ... */ },

  async cloneStrategy(strategyId: string): Promise<Strategy> { /* ... */ },

  async rollbackStrategyVersion(strategyId: string, version: string): Promise<Strategy> { /* ... */ },

  async updateStrategy(strategyId: string, patch: Partial<Strategy>): Promise<Strategy> { /* ... */ },

  async toggleStrategyActive(strategyId: string, isActive: boolean): Promise<Strategy> { /* ... */ },

  // --- Indicators ---
  async getIndicators(): Promise<Indicator[]> { /* ... */ },

  async createIndicator(payload: CreateIndicatorPayload): Promise<Indicator> { /* ... */ },

  async updateIndicator(indicatorId: string, patch: Partial<Indicator>): Promise<Indicator> { /* ... */ },

  // --- Data Manager ---
  async getDatasets(): Promise<HistoricalDataset[]> { /* ... */ },

  async downloadDataset(datasetId: string): Promise<HistoricalDataset> { /* ... */ },

  async validateDataset(datasetId: string): Promise<HistoricalDataset> { /* ... */ },

  async getDatasetGaps(datasetId: string): Promise<DataGap[]> { /* ... */ },

  // --- Portfolio & Exposure ---
  async getPortfolioExposure(): Promise<PortfolioExposureData> { /* ... */ },

  // --- News Calendar & Blackout ---
  async getNewsEvents(): Promise<NewsEventItem[]> { /* ... */ },

  async getNewsFilterSettings(): Promise<NewsFilterSettings> { /* ... */ },

  async updateNewsFilterSettings(settings: NewsFilterSettings): Promise<NewsFilterSettings> { /* ... */ },

  // --- Safety: Pair Toggles & Auto-Pause Rules & Risk ---
  async getPairToggles(): Promise<PairToggleSetting[]> { /* ... */ },

  async togglePairEnabled(pair: ForexPair, enabled: boolean): Promise<PairToggleSetting> { /* ... */ },

  async getAutoPauseRules(): Promise<AutoPauseRules> { /* ... */ },

  async updateAutoPauseRules(rules: AutoPauseRules): Promise<AutoPauseRules> { /* ... */ },

  async getRiskSettings(): Promise<RiskSettings> { /* ... */ },

  async updateRiskSettings(settings: RiskSettings): Promise<RiskSettings> { /* ... */ },

  // --- Settings, Broker, Alerts, Security & Backup ---
  async getSettings(): Promise<AppSettings> { /* ... */ },

  async updateBrokerSettings(payload: BrokerUpdatePayload): Promise<BrokerSettings> { /* ... */ },

  async testBrokerConnection(): Promise<BrokerSettings> { /* ... */ },

  async updateApiBaseUrl(apiBaseUrl: string): Promise<AppSettings> { /* ... */ },

  async setTradingMode(mode: TradingMode): Promise<AppSettings> { /* ... */ },

  async updateDisplayCurrency(displayCurrency: DisplayCurrency): Promise<AppSettings> { /* ... */ },

  async updateNotificationPreferences(
    prefs: NotificationPreferences,
    telegramBotToken?: string
  ): Promise<NotificationPreferences> { /* ... */ },

  async sendTestAlert(channel: 'email' | 'telegram'): Promise<TestAlertResult> { /* ... */ },

  // --- Security & Authentication ---
  async getSecuritySettings(): Promise<SecuritySettings> { /* ... */ },

  async setupTwoFactor(): Promise<TwoFactorSetupInfo> { /* ... */ },

  async verifyTwoFactor(code: string): Promise<SecuritySettings> { /* ... */ },

  async disableTwoFactor(): Promise<SecuritySettings> { /* ... */ },

  async updateSessionTimeout(
    sessionTimeoutMinutes: SecuritySettings['sessionTimeoutMinutes']
  ): Promise<SecuritySettings> { /* ... */ },

  async login(
    username: string,
    password: string,
    otpCode?: string
  ): Promise<{ authenticated: boolean; requiresTwoFactor: boolean; username: string }> { /* ... */ },

  // --- Export & Import Backup ---
  async exportBackupSection(section: 'journal' | 'strategies' | 'settings'): Promise<unknown> { /* ... */ },

  async importBackupSection(
    section: 'journal' | 'strategies' | 'settings',
    payload: Record<string, unknown>
  ): Promise<{ restoredCount: number; message: string }> { /* ... */ },
};
```

### `trading-bot-control-center/src/types/index.ts`

```ts
export type BotRunState = 'Running' | 'Stopped' | 'Error';
export type ConnectionState = 'Connected' | 'Disconnected' | 'Connecting' | 'Error';
export type TradingMode = 'Demo' | 'Live';
export type CurrencyCode = 'ZAR' | 'USD' | 'EUR' | 'GBP';
export type DisplayCurrency = 'ZAR' | 'USD';

export type ForexPair =
  | 'EURUSD'
  | 'GBPUSD'
  | 'USDJPY'
  | 'XAUUSD'
  | 'USDZAR'
  | 'AUDUSD';

export type TradeDirection = 'BUY' | 'SELL';
export type SetupGrade = 'A++' | 'A+' | 'A' | 'B' | 'Bad';
export type VolatilityRegime = 'Low' | 'Normal' | 'High' | 'Extreme';
export type MarketStructure = 'Trending' | 'Ranging' | 'Breakout';
export type TradingSession = 'Asian' | 'London' | 'New York' | 'London/NY Overlap';
export type Timeframe = 'M5' | 'M15' | 'M30' | 'H1' | 'H4' | 'D1';
export type HistoryLength = '1y' | '2y' | '5y' | '10y' | 'Max available';
export type BrokerAccountType = 'Raw Spread / ECN' | 'Standard' | 'Zero Commission';

export interface BotStatusInfo {
  state: BotRunState;
  uptimeSeconds: number;
  startedAt: string | null;
  activeStrategiesCount: number;
  lastHeartbeat: string;
  version: string;
  errorMessage?: string;
}

export interface KillSwitchResult {
  botStatus: BotStatusInfo;
  closedPositionsCount: number;
  triggeredAt: string;
}

export interface PairToggleSetting {
  pair: ForexPair;
  enabled: boolean;
  spreadPips: number;
  maxDailyTrades: number;
  updatedAt: string;
}

export interface AutoPauseRule {
  enabled: boolean;
  threshold: number;
  unit: string;
  description: string;
}

export interface AutoPauseRules {
  dailyLossLimit: AutoPauseRule;
  maxDrawdown: AutoPauseRule;
  connectionLost: {
    enabled: boolean;
    graceSeconds: number;
    description: string;
  };
  consecutiveLosses: AutoPauseRule;
}

export interface AccountSummary {
  currency: CurrencyCode;
  balance: number;
  equity: number;
  openPnl: number;
  todayPnl: number;
  todayPnlPercent: number;
  openTradesCount: number;
  marginUsed: number;
  freeMargin: number;
  marginLevelPercent: number;
  leverage: number;
}

export interface EquityPoint {
  timestamp: string;
  label: string;
  equity: number;
  balance: number;
}

export interface OpenPosition {
  id: string;
  pair: ForexPair;
  direction: TradeDirection;
  entryPrice: number;
  currentPrice: number;
  stopLoss: number;
  takeProfit: number;
  sizeLots: number;
  floatingPnl: number;
  floatingPnlPips: number;
  strategyId: string;
  strategyName: string;
  setupGrade: SetupGrade;
  openedAt: string;
  swap: number;
  commission: number;
}

export interface ManualOrderPayload {
  pair: ForexPair;
  direction: TradeDirection;
  sizeLots: number;
  stopLoss: number;
  takeProfit: number;
  comment?: string;
}

export interface ModifyPositionSlTpPayload {
  stopLoss: number;
  takeProfit: number;
}

export type ActivityLevel = 'info' | 'signal' | 'order' | 'warning' | 'error';

export interface ActivityLogEntry {
  id: string;
  timestamp: string;
  level: ActivityLevel;
  pair?: string;
  strategyName?: string;
  message: string;
  details?: string;
}

export type ErrorSeverity = 'WARNING' | 'ERROR' | 'CRITICAL';

export interface ErrorLogEntry {
  id: string;
  timestamp: string;
  severity: ErrorSeverity;
  component: string;
  message: string;
  stackSummary?: string;
  resolved: boolean;
}

export type BrokerOrderStatus = 'FILLED' | 'REJECTED' | 'REQUOTED' | 'CANCELLED' | 'MODIFIED';

export interface TradeAuditEntry {
  id: string;
  timestamp: string;
  orderId: string;
  pair: ForexPair;
  direction: TradeDirection;
  action: 'OPEN' | 'CLOSE' | 'MODIFY_SLTP';
  requestedPrice: number;
  executedPrice: number | null;
  sizeLots: number;
  brokerResponse: BrokerOrderStatus;
  brokerMessage: string;
  latencyMs: number;
  strategyName: string;
}

export interface SystemStatusInfo {
  serverUptimeSeconds: number;
  cpuPercent: number;
  ramUsedGb: number;
  ramTotalGb: number;
  diskUsedGb: number;
  diskTotalGb: number;
  lastHeartbeat: string;
  ctraderStatus: ConnectionState;
  dataFeedStatus: ConnectionState;
  dataFeedProvider: string;
  lastError: {
    timestamp: string;
    message: string;
    component: string;
  } | null;
  botVersion: string;
  pythonVersion: string;
}

export interface MarketConditionTags {
  volatilityRegime: VolatilityRegime;
  marketStructure: MarketStructure;
  session: TradingSession;
  newsNearby: boolean;
  newsEvent?: string;
  spreadPips: number;
  atrPips: number;
  htfBias: 'Bullish' | 'Bearish' | 'Neutral';
}

export interface JournalTrade {
  id: string;
  openedAt: string;
  closedAt: string;
  pair: ForexPair;
  direction: TradeDirection;
  strategyId: string;
  strategyName: string;
  strategyVersion?: string;
  setupGrade: SetupGrade;
  entryPrice: number;
  exitPrice: number;
  stopLoss: number;
  takeProfit: number;
  sizeLots: number;
  pnl: number;
  currency: CurrencyCode;
  rMultiple: number;
  durationMinutes: number;
  marketConditions: MarketConditionTags;
  notes: string;
  tags: string[];
  screenshotUrl?: string;
  maeR: number;
  mfeR: number;
  commission: number;
  swap: number;
}

export interface CapitalTransaction {
  id: string;
  date: string;
  type: 'DEPOSIT' | 'WITHDRAWAL';
  amount: number;
  currency: CurrencyCode;
  reference: string;
  notes?: string;
}

export interface JournalFilters {
  startDate?: string;
  endDate?: string;
  pair?: string;
  strategyId?: string;
  setupGrade?: SetupGrade | '';
  outcome?: 'all' | 'win' | 'loss';
  tag?: string;
  search?: string;
}

export interface JournalStats {
  totalTrades: number;
  wins: number;
  losses: number;
  winRate: number;
  netProfit: number;
  expectancyR: number;
  profitFactor: number;
  avgWin: number;
  avgLoss: number;
}

export interface JournalResponse {
  trades: JournalTrade[];
  stats: JournalStats;
  totalCount: number;
}

export interface BacktestCostSettings {
  spreadPips: number;
  commissionPerLot: number;
  slippagePips: number;
  swapPerNight: number;
}

export interface BacktestConfig {
  id?: string;
  name?: string;
  strategyId: string;
  pairs: ForexPair[];
  timeframe: Timeframe;
  historyLength: HistoryLength;
  startingBalance: number;
  currency: CurrencyCode;
  leverage: number;
  riskPerTradePercent: number;
  brokerAccountType: BrokerAccountType;
  costs: BacktestCostSettings;
}

export interface BacktestEquityPoint {
  date: string;
  equity: number;
  drawdownPercent: number;
}

export interface BacktestOverview {
  equityCurve: BacktestEquityPoint[];
  totalTrades: number;
  wins: number;
  losses: number;
  winRate: number;
  netProfit: number;
  netReturnPercent: number;
  expectancyR: number;
  profitFactor: number;
  avgWin: number;
  avgLoss: number;
  maxDrawdownPercent: number;
  maxDrawdownAmount: number;
  longestLosingStreak: number;
  recoveryTimeDays: number;
  sharpeRatio: number;
  finalBalance: number;
}

export interface ConditionBreakdownItem {
  bucket: string;
  trades: number;
  wins: number;
  winRate: number;
  netProfit: number;
  expectancyR: number;
  profitFactor: number;
  lowSampleWarning: boolean;
}

export interface MarketConditionsBreakdown {
  byVolatility: ConditionBreakdownItem[];
  byStructure: ConditionBreakdownItem[];
  bySession: ConditionBreakdownItem[];
  byDayOfWeek: ConditionBreakdownItem[];
  byTimeOfDay: ConditionBreakdownItem[];
  byWeek: ConditionBreakdownItem[];
  byMonth: ConditionBreakdownItem[];
}

export interface SlTpHeatmapCell {
  slAtrMultiple: number;
  tpAtrMultiple: number;
  expectancyR: number;
  netReturnPercent: number;
  winRate: number;
  profitFactor: number;
  trades: number;
}

export interface VolatilityOptimalSlTp {
  volatilityRegime: VolatilityRegime;
  bestSlAtr: number;
  bestTpAtr: number;
  expectancyR: number;
  winRate: number;
  netReturnPercent: number;
  trades: number;
}

export interface SlTpOptimizationResult {
  slMultiples: number[];
  tpMultiples: number[];
  cells: SlTpHeatmapCell[];
  optimalByVolatility: VolatilityOptimalSlTp[];
}

export interface MaeMfePoint {
  tradeId: string;
  pair: ForexPair;
  outcome: 'win' | 'loss';
  maeR: number;
  mfeR: number;
  rMultiple: number;
  setupGrade: SetupGrade;
}

export interface SetupGradeBreakdown {
  grade: SetupGrade;
  trades: number;
  wins: number;
  winRate: number;
  expectancyR: number;
  profitFactor: number;
  netProfit: number;
}

export interface WalkForwardFold {
  fold: string;
  inSamplePeriod: string;
  outOfSamplePeriod: string;
  inSampleReturnPercent: number;
  outOfSampleReturnPercent: number;
  inSampleExpectancyR: number;
  outOfSampleExpectancyR: number;
  efficiencyRatio: number;
}

export interface MonteCarloStep {
  tradeIndex: number;
  p5: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
  drawdownP50: number;
  drawdownP95: number;
}

export interface ParameterStabilityMetric {
  parameterName: string;
  stabilityScore: number;
  optimalRange: string;
  sensitivity: 'Low' | 'Moderate' | 'High';
}

export interface RobustnessAnalysis {
  walkForwardFolds: WalkForwardFold[];
  monteCarloDistribution: MonteCarloStep[];
  monteCarloMaxDd95Percent: number;
  monteCarloRuinProbabilityPercent: number;
  parameterStability: ParameterStabilityMetric[];
  overallStabilityLabel: 'Robust' | 'Moderate' | 'Fragile';
}

export interface BacktestJobStatus {
  jobId: string;
  status: 'queued' | 'running' | 'completed' | 'cancelled' | 'failed';
  progressPercent: number;
  currentStep: string;
  startedAt: string;
  resultId?: string;
}

export interface BacktestResult {
  id: string;
  name: string;
  createdAt: string;
  config: BacktestConfig;
  strategyName: string;
  overview: BacktestOverview;
  marketConditions: MarketConditionsBreakdown;
  slTpOptimizer: SlTpOptimizationResult;
  maeMfe: MaeMfePoint[];
  setupGrades: SetupGradeBreakdown[];
  robustness: RobustnessAnalysis;
  trades: JournalTrade[];
}

export interface SavedBacktestSummary {
  id: string;
  name: string;
  createdAt: string;
  strategyId: string;
  strategyName: string;
  pairs: ForexPair[];
  timeframe: Timeframe;
  historyLength: HistoryLength;
  currency: CurrencyCode;
  startingBalance: number;
  netProfit: number;
  netReturnPercent: number;
  winRate: number;
  profitFactor: number;
  maxDrawdownPercent: number;
  expectancyR: number;
  totalTrades: number;
}

export interface LiveVsBacktestPoint {
  tradeIndex: number;
  label: string;
  liveReturnPercent: number;
  backtestReturnPercent: number;
}

export interface LiveVsBacktestMetrics {
  winRate: number;
  expectancyR: number;
  maxDrawdownPercent: number;
  avgTradePnl: number;
  profitFactor: number;
  totalTrades: number;
  netReturnPercent: number;
}

export interface LiveVsBacktestComparison {
  strategyId: string;
  strategyName: string;
  backtestName: string;
  diverging: boolean;
  divergenceReasons: string[];
  live: LiveVsBacktestMetrics;
  backtest: LiveVsBacktestMetrics;
  equityComparison: LiveVsBacktestPoint[];
}

export interface StrategyParameter {
  key: string;
  label: string;
  type: 'number' | 'boolean' | 'string' | 'select';
  value: number | boolean | string;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  description?: string;
}

export interface GradingCondition {
  id: string;
  metric: string;
  operator: '>=' | '<=' | '==' | '!=' | 'in';
  threshold: string;
  description: string;
}

export type SetupGradingRules = Record<SetupGrade, GradingCondition[]>;

export interface StrategyVersion {
  version: string;
  createdAt: string;
  notes: string;
  tradeIds: string[];
  tradeCount: number;
  isCurrent: boolean;
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  isActive: boolean;
  currentVersion: string;
  versions: StrategyVersion[];
  indicatorIds: string[];
  assignedPairs: ForexPair[];
  parameters: StrategyParameter[];
  gradingRules: SetupGradingRules;
  fileName?: string;
  codeSnippet?: string;
  updatedAt: string;
  lastBacktestSummary?: {
    date: string;
    winRate: number;
    profitFactor: number;
    netReturnPercent: number;
    expectancyR: number;
  };
}

export interface CreateStrategyPayload {
  name: string;
  description: string;
  indicatorIds: string[];
  assignedPairs: ForexPair[];
  fileName?: string;
  codeSnippet?: string;
}

export interface IndicatorParameter {
  key: string;
  label: string;
  type: 'number' | 'select';
  defaultValue: number | string;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
}

export interface Indicator {
  id: string;
  name: string;
  shortCode: string;
  category: 'Trend' | 'Momentum' | 'Volatility' | 'Volume' | 'Structure';
  description: string;
  parameters: IndicatorParameter[];
  isCustom: boolean;
}

export interface CreateIndicatorPayload {
  name: string;
  shortCode: string;
  category: Indicator['category'];
  description: string;
  parameters: IndicatorParameter[];
}

export interface HistoricalDataset {
  id: string;
  pair: ForexPair;
  timeframe: Timeframe;
  startDate: string;
  endDate: string;
  candleCount: number;
  gapsFound: number;
  lastUpdated: string;
  status: 'Up to date' | 'Outdated' | 'Validating' | 'Error';
}

export interface DataGap {
  id: string;
  datasetId: string;
  gapStart: string;
  gapEnd: string;
  missingCandles: number;
  reason: string;
}

export interface CurrencyExposureItem {
  currency: string;
  netLots: number;
  netNotionalZar: number;
  direction: 'LONG' | 'SHORT' | 'FLAT';
  percentOfEquity: number;
}

export interface CorrelationMatrixData {
  pairs: ForexPair[];
  matrix: number[][];
}

export interface PortfolioExposureData {
  accountEquity: number;
  currency: CurrencyCode;
  totalOpenRiskAmount: number;
  totalOpenRiskPercent: number;
  marginUsed: number;
  freeMargin: number;
  marginLevelPercent: number;
  currencyExposures: CurrencyExposureItem[];
  correlationMatrix: CorrelationMatrixData;
}

export interface NewsEventItem {
  id: string;
  timestamp: string;
  currency: string;
  title: string;
  impact: 'High' | 'Medium';
  forecast?: string;
  previous?: string;
  affectedPairs: ForexPair[];
}

export interface NewsFilterSettings {
  enabled: boolean;
  minutesBefore: number;
  minutesAfter: number;
}

export interface RiskSettings {
  positionSizingModel: 'fixed_fractional' | 'volatility_adjusted' | 'fixed_lot';
  fixedLotSize: number;
  maxRiskPerTradePercent: number;
  maxDailyLossPercent: number;
  maxDrawdownPercent: number;
  maxOpenTrades: number;
  maxCorrelatedExposurePercent: number;
  haltOnNewsMinutes: number;
}

export interface BrokerSettings {
  provider: 'cTrader';
  clientId: string;
  hasClientSecret: boolean;
  clientSecretMasked: string;
  accountId: string;
  environment: TradingMode;
  connectionState: ConnectionState;
  lastTestedAt?: string;
  statusMessage?: string;
}

export interface BrokerUpdatePayload {
  clientId: string;
  clientSecret?: string;
  accountId: string;
  environment: TradingMode;
}

export interface NotificationPreferences {
  tradeOpened: boolean;
  tradeClosed: boolean;
  error: boolean;
  botStopped: boolean;
  connectionLost: boolean;
  dailySummary: boolean;
  emailEnabled: boolean;
  emailAddress: string;
  telegramEnabled: boolean;
  telegramBotTokenMasked: string;
  hasTelegramToken: boolean;
  telegramChatId: string;
}

export interface SecuritySettings {
  username: string;
  twoFactorEnabled: boolean;
  sessionTimeoutMinutes: 15 | 30 | 60 | 240 | 0;
  lastLoginAt: string;
}

export interface TwoFactorSetupInfo {
  secret: string;
  otpauthUrl: string;
}

export interface AppSettings {
  apiBaseUrl: string;
  useMock: boolean;
  tradingMode: TradingMode;
  defaultCurrency: CurrencyCode;
  displayCurrency: DisplayCurrency;
  broker: BrokerSettings;
  notifications: NotificationPreferences;
  security: SecuritySettings;
}

export interface TestAlertResult {
  channel: 'email' | 'telegram';
  success: boolean;
  message: string;
  sentAt: string;
}
```

### `trading-bot-control-center/src/utils/formatters.ts`

```ts
import type { CurrencyCode, DisplayCurrency, ForexPair, JournalTrade } from '../types';

const CURRENCY_SYMBOLS: Record<CurrencyCode, string> = {
  ZAR: 'R',
  USD: '$',
  EUR: '€',
  GBP: '£',
};

// Reference UI display conversion rate (ZAR per 1 USD)
export const FX_ZAR_PER_USD = 18.1;

export function convertCurrencyAmount(
  amount: number,
  fromCurrency: CurrencyCode = 'ZAR',
  toCurrency: DisplayCurrency = 'ZAR'
): number { /* ... */ }

export function formatCurrency(
  amount: number,
  currency: CurrencyCode = 'ZAR',
  options?: { signed?: boolean; decimals?: number }
): string { /* ... */ }

export function formatPairPrice(price: number, pair: ForexPair): string { /* ... */ }

export function formatDuration(minutes: number): string { /* ... */ }

export function formatUptime(totalSeconds: number): string { /* ... */ }

export function formatDateTime(iso: string): string { /* ... */ }

export function downloadJsonFile(data: unknown, filename: string): void { /* ... */ }

export function exportRowsToCsv(
  headers: string[],
  rows: Array<Array<string | number | boolean | null | undefined>>,
  filename: string
): void { /* ... */ }

export function exportTradesToCsv(trades: JournalTrade[], filename: string): void { /* ... */ }
```

### `trading-engine/.gitignore`

```text
.env
venv/
__pycache__/
*.pyc
```

### `trading-engine/api.py`

```python
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
    ...

@app.get("/api/account/summary")
def get_account_summary():
    ...

@app.get("/api/account/equity-curve")
def get_equity_curve(range: str = "1M"):
    # Return a dummy flat line for the dashboard chart
    ...

@app.get("/api/positions/open")
def get_open_positions():
    ...

@app.get("/api/bot/activity")
def get_activity_log(limit: int = 50):
    ...

@app.get("/api/settings")
def get_settings():
    ...

@app.get("/api/market/pairs")
def get_pairs():
    ...

@app.get("/api/strategies")
def get_strategies():
    ...

# ==============================================================================
# REAL BACKTESTER ENDPOINTS
# ==============================================================================
@app.get("/api/backtests")
def get_saved_backtests():
    ...

@app.post("/api/backtests/run")
def start_backtest(req: BacktestRequest):
    ...

@app.get("/api/backtests/jobs/{job_id}")
def get_job_status(job_id: str):
    ...

@app.get("/api/backtests/{backtest_id}")
def get_backtest_result(backtest_id: str):
    ...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### `trading-engine/main.py`

```python
import os
import pandas as pd
from data.ctrader_client import CTraderClient
from engine.simulator import BacktestSimulator
from strategies.validation_trivial import ValidationTrivial

def run_backtest():
    ...

if __name__ == "__main__":
    run_backtest()
```

### `trading-engine/requirements.txt`

```text
ctrader-open-api==0.9.0
pandas==2.2.1
pyarrow==15.0.0
duckdb==0.10.0
twisted==23.10.0
python-dotenv==1.0.1
requests==2.31.0
pyOpenSSL==23.2.0
service_identity==24.1.0
```

### `trading-engine/run_news.bat`

```batch
@echo off
cd /d "C:\Users\mcnei\Downloads\TB 2\CODE\trading-engine\news_feed"
python scraper.py
```

### `trading-engine/setup.py`

```python
import os
import requests
from urllib.parse import urlparse, parse_qs
from dotenv import set_key
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq, ProtoOAGetAccountListByAccessTokenReq
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOAPayloadType
from twisted.internet import reactor

print("\n--- SETUP SCRIPT ---")
CLIENT_ID = input("Paste your cTrader Client ID here and press Enter: ").strip()
SECRET = input("Paste your cTrader Secret here and press Enter: ").strip()

set_key(".env", "CTRADER_CLIENT_ID", CLIENT_ID)
set_key(".env", "CTRADER_SECRET", SECRET)

REDIRECT_URI = "http://localhost"

print("\n--- STEP 1: GET AUTH CODE ---")
url = f"https://id.ctrader.com/my/settings/openapi/grantingaccess/?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=accounts"
print(f"1. Open this link in your browser:\n\n{url}\n")
print("2. Click 'Allow'.")
print("3. You will land on an error page (this is normal). COPY the entire URL from the address bar.")
pasted_url = input("\n4. Paste the URL here and press Enter: ").strip()

code = parse_qs(urlparse(pasted_url).query).get('code', [''])[0]
if not code:
    print("Could not find code in URL. Please try again.")
    exit()

print("\n--- STEP 2: GET TOKEN ---")
res = requests.post("https://openapi.ctrader.com/apps/token", data={
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": REDIRECT_URI,
    "client_id": CLIENT_ID,
    "client_secret": SECRET
}).json()

token = res.get("accessToken")
if not token:
    print("Error getting token:", res)
    exit()
    
print("Token received!")
set_key(".env", "CTRADER_ACCESS_TOKEN", token)

print("\n--- STEP 3: FIND ACCOUNT ID ---")
def on_connected(client):
    ...

def on_message(client, message):
    ...

client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
client.setConnectedCallback(on_connected)
client.setMessageReceivedCallback(on_message)
client.startService()
reactor.run()
print("\nSetup complete! You can now run: python main.py")
```

### `trading-engine/test_fvg_pro.py`

```python
from knowledge.fair_value_gap import check_fvg, is_price_in_fvg, is_fvg_invalidated

print("--- TESTING BULLISH FVG ---")
# Fake candles for a Bullish FVG
c1 = {"open": 1.0850, "high": 1.0860, "low": 1.0840, "close": 1.0855}
c2 = {"open": 1.0855, "high": 1.0900, "low": 1.0855, "close": 1.0895} # Massive green push
c3 = {"open": 1.0895, "high": 1.0910, "low": 1.0880, "close": 1.0905} # Low is 1.0880

fvg = check_fvg(c1, c2, c3)
print(f"FVG Found: {fvg['type']}")
print(f"Gap Bottom: {fvg['gap_bottom']}")
print(f"Gap Top: {fvg['gap_top']}")

print("\n--- TESTING ENTRY ---")
current_price = 1.0870 # Price pulls back into the gap
print(f"Price at {current_price}. In gap? {is_price_in_fvg(current_price, fvg)}")

print("\n--- TESTING INVALIDATION ---")
bad_price = 1.0850 # Price crashes below the gap
print(f"Price closes at {bad_price}. Invalidated? {is_fvg_invalidated(bad_price, fvg)}")
```

### `trading-engine/analytics/metrics.py`

```python
```

### `trading-engine/broker/costs.py`

```python
```

### `trading-engine/broker/fill.py`

```python
```

### `trading-engine/data/bar_store.py`

```python
```

### `trading-engine/data/clock.py`

```python
import pandas as pd

class DataClock:
    def __init__(self, full_df: pd.DataFrame):
        ...

    def step_forward(self) -> bool:
        """Moves the clock forward by one bar. Returns False if out of data."""
        ...

    def get_visible_bars(self) -> pd.DataFrame:
        """Returns ONLY the bars up to the current tick. The future is hidden."""
        ...

    def get_current_time(self):
        ...
```

### `trading-engine/data/ctrader_client.py`

```python
import os
import datetime
import pandas as pd
from dotenv import load_dotenv
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq, ProtoOAAccountAuthReq, ProtoOASymbolsListReq,
    ProtoOAGetTrendbarsReq
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import (
    ProtoOATrendbarPeriod,
    ProtoOAPayloadType
)
from twisted.internet import reactor

load_dotenv()

class CTraderClient:
    def __init__(self):
        ...

    def on_connected(self, client):
        ...

    def on_message(self, client, message):
        ...

    def fetch(self):
        ...

if __name__ == "__main__":
    client = CTraderClient()
    client.fetch()
```

### `trading-engine/engine/models.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict

class Direction(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class Signal:
    direction: Direction
    sl_atr_multiple: float
    tp_atr_multiple: float
    max_spread_pips: float = 2.0

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
    
    max_adverse_excursion: float = 0.0
    max_favorable_excursion: float = 0.0
    conditions: Dict[str, str] = field(default_factory=dict)

@dataclass
class AccountState:
    balance: float
    equity: float
    margin_used: float = 0.0
```

### `trading-engine/engine/simulator.py`

```python
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from engine.models import Signal, Trade, Direction
from data.clock import DataClock

class BacktestSimulator:
    def __init__(self, df: pd.DataFrame, strategy, starting_balance: float = 10000.0, risk_percent: float = 1.0):
        ...

    def run(self):
        ...

    def _open_trade(self, bar, signal: Signal):
        ...

    def _check_exits(self, bar):
        ...

    def _close_trade(self, bar, reason, fill_price=None):
        ...

    def _print_results(self):
        ...
```

### `trading-engine/knowledge/candlestick_anatomy.py`

```python
# trading-engine/knowledge/candlesticks.py
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any
from .common import validate_candles

@dataclass
class CandleConfig:
    rejection_wick_multiplier: float = 2.0
    doji_max_body_percent: float = 0.1

def describe() -> Dict[str, Any]:
    ...

def analyze(candles: pd.DataFrame, config: CandleConfig = CandleConfig()) -> pd.DataFrame:
    ...

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    
    df = pd.read_csv(args.csv)
    df['time'] = pd.to_datetime(df['time'])
    analyzed = analyze(df)
    print(analyzed.tail(50)[['time', 'open', 'close', 'control', 'is_doji', 'is_bullish_rejection', 'is_bearish_rejection']])
```

### `trading-engine/knowledge/common.py`

```python
# trading-engine/knowledge/common.py
import pandas as pd
from dataclasses import dataclass

@dataclass
class CandleValidation:
    is_valid: bool
    error_message: str = ""

def validate_candles(df: pd.DataFrame) -> CandleValidation:
    ...
```

### `trading-engine/knowledge/equilibrium.py`

```python
# trading-engine/knowledge/equilibrium.py

def calculate_equilibrium(swing_high, swing_low):
    """
    Calculates the 50% equilibrium level of a price swing.
    """
    ...

def check_market_zone(current_price, eq_data):
    """
    Tells the bot if the current price is in a Premium or Discount zone.
    """
    ...

def get_fib_levels(swing_high, swing_low):
    """
    Calculates the Premium (OTE) and Discount levels.
    Standard SMC uses the 61.8% and 79% for deep pullbacks.
    """
    ...
```

### `trading-engine/knowledge/fair_value_gap.py`

```python
# trading-engine/knowledge/fair_value_gap.py

def check_fvg(candle1, candle2, candle3):
    """
    Checks for a Fair Value Gap (FVG) over 3 consecutive candles.
    candle1 = oldest (2 bars ago)
    candle2 = middle (1 bar ago) - The explosive candle
    candle3 = newest (current bar)
    """
    ...

def is_price_in_fvg(current_price, fvg):
    """
    Checks if the current price has pulled back into the FVG zone.
    """
    ...

def is_fvg_invalidated(current_close, fvg):
    """
    Checks if the price has broken completely through the FVG.
    If a Bullish FVG is broken below the bottom, it is invalid.
    If a Bearish FVG is broken above the top, it is invalid.
    """
    ...
```

### `trading-engine/knowledge/inverse_fvg.py`

```python
# trading-engine/knowledge/inverse_fvg.py
from knowledge.fair_value_gap import check_fvg

def check_for_ifvg(candle1, candle2, candle3, current_candle):
    """
    Checks if a previously formed FVG has been broken (invalidated) 
    and is now acting as an Inverse FVG.
    """
    ...
```

### `trading-engine/knowledge/liquidity.py`

```python
# trading-engine/knowledge/liquidity.py
import pandas as pd

# ==========================================
# 1. SWING POINT LIQUIDITY (EQUAL HIGHS/LOWS)
# ==========================================
def find_equal_highs(highs, tolerance_pips=2.0):
    ...

def find_equal_lows(lows, tolerance_pips=2.0):
    ...

# ==========================================
# 2. PREVIOUS DAY LIQUIDITY (PDH / PDL)
# ==========================================
def get_previous_day_levels(df):
    """
    Finds the Previous Day High (PDH) and Previous Day Low (PDL).
    """
    ...

# ==========================================
# 3. ASIAN RANGE LIQUIDITY
# ==========================================
def get_asian_range(df):
    """
    Calculates the Asian Range High and Low based on SAST time.
    Assumes 'timestamp' is in SAST.
    """
    ...

# ==========================================
# 4. SWEEP DETECTORS
# ==========================================
def check_sweep(current_candle, level, direction):
    """
    Checks if a specific level was swept.
    direction: "HIGH" or "LOW"
    """
    ...
```

### `trading-engine/knowledge/market_strucure.py`

```python
# trading-engine/knowledge/market_structure.py
import pandas as pd

def find_swings(df, lookback=3):
    """
    Finds Swing Highs and Swing Lows using a fractal method.
    A Swing High must be higher than 'lookback' candles to its left AND right.
    """
    ...

def determine_market_structure(df, lookback=3):
    """
    Analyzes the swings to return the current market state: 
    BULLISH, BEARISH, RANGING, or CHOPPY.
    Also detects BOS (Break of Structure) and CHoCH (Change of Character).
    """
    ...

def check_for_choch(df, current_price, lookback=3):
    """
    Checks if the current price has just caused a Change of Character (CHoCH).
    A CHoCH happens when price breaks the most recent Swing Low in a Bullish trend, or Swing High in a Bearish trend.
    """
    ...
```

### `trading-engine/knowledge/news.py`

```python
# trading-engine/knowledge/news.py
import json
from datetime import datetime, timedelta
from pathlib import Path

CURRENT_FOLDER = Path(__file__).resolve().parent 
ENGINE_FOLDER = CURRENT_FOLDER.parent 
CALENDAR_PATH = ENGINE_FOLDER / "news_feed" / "news" / "last_run"

def load_news_events():
    ...

def is_news_blackout(current_time_sast: datetime, pair: str):
    ...
```

### `trading-engine/knowledge/sessions.py`

```python
# trading-engine/knowledge/sessions.py
from datetime import datetime, time

def get_session_sast(current_time_sast: datetime):
    """
    Takes the current SAST time (South Africa Standard Time, UTC+2).
    Returns the session name, killzone status, and bot action rules.
    """
    ...

def get_asian_range(asian_bars):
    """
    Takes all the candles from the Asian session (02:00 to 11:00 SAST)
    and returns the High and Low. London often sweeps these levels.
    """
    ...
```

### `trading-engine/news_feed/.env.example`

```dotenv
# Docker volume ownership — prevents files in news/ and state/ from becoming root-owned.
# Run `id -u` and `id -g` to get your values.
DOCKER_UID=1000
DOCKER_GID=1000

# Optional runtime overrides:
# FF_RUN_MODE=once
# FF_SCHEDULE_PRESET=weekly
# FF_ALERT_SCHEDULE_PRESET=every_5_minutes
# FF_ALERT_CRON_SCHEDULE=*/5 * * * *

# Connector secrets:
# DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
# TELEGRAM_BOT_TOKEN=123456:ABC-DEF
# TELEGRAM_CHAT_ID=-1001234567890
# ALERT_WEBHOOK_URL=https://example.com/webhook
# ALERT_WEBHOOK_AUTH=Bearer your-token

# Optional scrape cron override:
# CRON_SCHEDULE=0 6 * * *
```

### `trading-engine/news_feed/.gitignore`

```text
__pycache__/
*.pyc
.env
.pytest_cache/
.streamlit/
.venv/
venv/
env/
.conda-env/
.codex
news/
state/
```

### `trading-engine/news_feed/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV FF_CHROME_BIN=/usr/bin/chromium
ENV FF_CHROMEDRIVER_PATH=/usr/bin/chromedriver

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x scripts/setup_env.sh scripts/run_scraper.sh scripts/run_alerts.sh scripts/view_data.sh docker/entrypoint.sh

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD []
```

### `trading-engine/news_feed/LICENSE`

```text
MIT License

Copyright (c) 2023 Fizah Khalid

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### `trading-engine/news_feed/README.md` [truncated]

````markdown
# Forex Factory Calendar Scraper & Alert System

Python scraper for the [Forex Factory](https://www.forexfactory.com/calendar) economic calendar. Pulls monthly events into structured CSV/JSON, filters by currency and impact, converts timezones, and fires configurable pre-event alerts to Discord, Telegram, or any HTTP webhook.

## Features

- Scrapes the full FF economic calendar — currency, impact, time, event name, detail URL
- Filter by currency (USD, EUR, GBP, CAD, JPY, ...) and impact level (high/medium/low)
- Converts all event times to your local timezone
- Stores data in three tiers: last run, monthly canonical, and timestamped history
- Rule-based alerts: match events by currency, impact, keywords, exact name, or weekday
- Fires alerts N minutes before each matched event
- Delivers to Discord webhooks, Telegram bots, or any HTTPS endpoint
- Runs unattended via Docker Compose with built-in scheduling
- Optional Streamlit UI for browsing data and editing rules live

## Quickstart

**Docker (recommended)**

```bash
cp .env.example .env
# add connector secrets to .env, enable connectors in config.yaml
./scripts/refresh_docker.sh refresh
```

That builds the image, starts the scraper scheduler and the alert checker, and prints their status. Common management commands:

```bash
./scripts/refresh_docker.sh restart   # restart without rebuilding
./scripts/refresh_docker.sh down      # stop and remove containers
./scripts/refresh_docker.sh status    # show running containers
docker compose logs -f alerts         # tail alert logs
docker compose logs -f scraper        # tail scraper logs
```

**Local**

```bash
./scripts/setup_env.sh
cp .env.example .env
./scripts/run.sh scrape
```

## Commands

```bash
python -m ff_calendar_toolkit.cli scrape           # scrape now
python -m ff_calendar_toolkit.cli alerts-check     # check alerts now
python -m ff_calendar_toolkit.cli test-notify      # verify notification delivery
python -m ff_calendar_toolkit.cli view             # open the Streamlit UI
```

---

## Scraping

### What gets scraped

Each event row contains:

| Field | Example |
|---|---|
| `currency` | `USD` |
| `impact` | `red` |
| `date` | `2025-01-15` |
| `time` | `13:30` |
| `event` | `Core CPI m/m` |
| `detail` | `https://www.forexfactory.com/...` |
| `timezone` | `Asia/Karachi` |
| `scraped_at` | `2025-01-14T08:00:00` |

### Filtering

Control which events are stored via `config.yaml`:

```yaml
allowed_currencies:
  - USD
  - EUR
  - GBP
  - CAD

allowed_impacts:
  - red      # high impact
  - orange   # medium impact
  - gray     # low impact / holidays
```

Override at runtime with CLI flags:

```bash
python -m ff_calendar_toolkit.cli scrape --currencies USD EUR --impacts red orange
```

### Month selection

```yaml
months:
  - this     # current month
  - next     # next month
```

Or pass a specific month:

```bash
python -m ff_calendar_toolkit.cli scrape --months 2025-03
```

Multiple values are supported: `--months this next 2025-06`

### Output format and storage

```yaml
output_format: both   # csv | json | both
output_dir: news
```

Three storage tiers are written on every run:

```
news/last_run/     ← overwritten each run (easy to read latest)
news/monthly/      ← canonical file for each month (updated in place)
news/history/      ← timestamped snapshots, never overwritten
```

### Timezone conversion

```yaml
timezone: Asia/Karachi
```

All event times are converted from the Forex Factory source timezone to your configured timezone. Any [tz database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) works.

---

## Scheduling

Set `schedule_preset` in `config.yaml`:

**Scraper presets**

| Preset | Cron |
|---|---|
| `weekly` (default) | `0 0 * * 0` |
| `daily` | `0 0 * * *` |
| `monthly` | `0 0 1 * *` |
| `hourly` | `0 * * * *` |

**Alert check presets**

| Preset | Cron |
|---|---|
| `every_1_minute` | `* * * * *` |
| `every_5_minutes` | `*/5 * * * *` |
| `every_10_minutes` | `*/10 * * * *` |
| `hourly` | `0 * * * *` |

Use a custom cron expression instead of a preset via the `CRON_SCHEDULE` or `ALERT_CRON_SCHEDULE` env variables.

---

## Alert rules

One YAML file per rule in `rules/`. A rule fires when all `match` conditions are met.

```yaml
name: usd-cpi-alert
enabled: true
match:
  currencies: [USD]
  impacts: [red]
  event_keywords: [CPI]
  weekdays: [Wed]
trigger:
  minutes_before: 10
deliver:
  - discord_main
```

**Match fields** (all optional, combined with AND logic):

| Field | Type | Example |
|---|---|---|
| `currencies` | list | `[USD, EUR, GBP]` |
| `impacts` | list | `[red, orange]` |
| `event_names` | list | exact event name match |
| `event_keywords` | list | substring match on event name |
| `weekdays` | list | `[Mon, Tue, Wed, Thu, Fri]` |

Multiple rules can target the same connector. State is tracked so an alert fires only once per event.

---

## Notification setup

Enable connectors in `config.yaml` under `alerts.connectors`, then add secrets to `.env`.

**Discord**

... [truncated: 121 more lines, 3261 chars]
````

### `trading-engine/news_feed/config.yaml`

```yaml
months:
  - this
output_format: both
output_dir: news
timezone: Asia/Karachi
allowed_currencies:
  - CAD
  - EUR
  - GBP
  - USD
allowed_impacts:
  - red
  - orange
  - gray
headless: true
schedule_preset: weekly
viewer_host: 127.0.0.1
viewer_port: 8501

alerts:
  rules_dir: rules
  state_dir: state/alerts
  check_interval_minutes: 1
  schedule_preset: every_1_minute
  retry_attempts: 3
  retry_backoff_seconds: 1
  message_prefix: "Forex Factory Alert"
  connectors:
    - id: discord_main
      type: discord
      enabled: true
      webhook_url_env: DISCORD_WEBHOOK_URL

    - id: telegram_main
      type: telegram
      enabled: false
      bot_token_env: TELEGRAM_BOT_TOKEN
      chat_id_env: TELEGRAM_CHAT_ID

    - id: webhook_main
      type: webhook
      enabled: true
      url_env: ALERT_WEBHOOK_URL
      auth_header_name: Authorization
      auth_header_env: ALERT_WEBHOOK_AUTH
```

### `trading-engine/news_feed/docker-compose.yml`

```yaml
services:
  scraper:
    build:
      context: .
    image: forex-factory-toolkit
    container_name: forex-factory-scraper
    restart: unless-stopped
    user: "${DOCKER_UID:-1000}:${DOCKER_GID:-1000}"
    environment:
      FF_RUN_MODE: schedule
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./.env:/app/.env
      - ./news:/app/news
      - ./rules:/app/rules
      - ./state:/app/state

  alerts:
    build:
      context: .
    image: forex-factory-toolkit
    container_name: forex-factory-alerts
    restart: unless-stopped
    user: "${DOCKER_UID:-1000}:${DOCKER_GID:-1000}"
    environment:
      FF_RUN_MODE: alerts-schedule
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./.env:/app/.env
      - ./news:/app/news
      - ./rules:/app/rules
      - ./state:/app/state
```

### `trading-engine/news_feed/local_api.py`

```python
#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import uvicorn
from fastapi import FastAPI, Query, Request

from ff_calendar_toolkit.alerts.events import load_alert_events
from ff_calendar_toolkit.alerts.service import preview_alerts
from ff_calendar_toolkit.runtime import (
    build_alert_options,
    build_view_options,
    load_env_file,
    resolve_config_path,
)


def build_parser() -> argparse.ArgumentParser:
    ...


def build_context(config_value: str | None):
    ...


def build_app(config_value: str | None = None) -> FastAPI:
    ...


def _upcoming_events(output_dir: Path, limit: int) -> list[dict]:
    ...


def main():
    ...


if __name__ == "__main__":
    main()
```

### `trading-engine/news_feed/requirements.txt`

```text
fastapi==0.115.6
pandas==2.2.3
pytz==2024.2
PyYAML==6.0.2
rich==13.9.4
selenium==4.13.0
streamlit==1.40.2
uvicorn==0.34.0
webdriver_manager==4.0.2
```

### `trading-engine/news_feed/scraper.py`

```python
from ff_calendar_toolkit.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

### `trading-engine/news_feed/utils.py`

```python
from datetime import datetime

from ff_calendar_toolkit.config import DEFAULT_ALLOWED_CURRENCY_CODES, DEFAULT_ALLOWED_IMPACT_COLORS, DEFAULT_OUTPUT_DIR, DEFAULT_TARGET_TIMEZONE
from ff_calendar_toolkit.models import ScrapeContext
from ff_calendar_toolkit.normalize import convert_time_zone, extract_date_parts, filter_row, normalize_rows, read_json
from ff_calendar_toolkit.storage import FileOutputStore


def reformat_data(data: list, year: str) -> list:
    ...


def save_csv(data, month, year):
    ...


def find_location_timezone():
    ...
```

### `trading-engine/news_feed/docker/entrypoint.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

MODE="${FF_RUN_MODE:-once}"
LOG_DIR="/app/state/logs"
LOG_FILE="${LOG_DIR}/forex_factory_scrape.log"
ALERT_LOG_FILE="${LOG_DIR}/forex_factory_alerts.log"

resolve_schedule() { : '...'; }

resolve_alert_schedule() { : '...'; }

run_scheduler_loop() { : '...'; }

if [[ "${MODE}" == "schedule" ]]; then
  SCHEDULE="$(resolve_schedule)"
  run_scheduler_loop "${SCHEDULE}" "scrape" "${LOG_FILE}"
fi

if [[ "${MODE}" == "alerts-schedule" ]]; then
  ALERT_SCHEDULE="$(resolve_alert_schedule)"
  run_scheduler_loop "${ALERT_SCHEDULE}" "alerts-check" "${ALERT_LOG_FILE}"
fi

if [[ "${MODE}" == "alerts-once" ]]; then
  exec python3 -m ff_calendar_toolkit.cli alerts-check "$@"
fi

exec python3 -m ff_calendar_toolkit.cli scrape "$@"
```

### `trading-engine/news_feed/ff_calendar_toolkit/__init__.py`

```python
"""Local-first toolkit for scraping and browsing Forex Factory calendar data."""
```

### `trading-engine/news_feed/ff_calendar_toolkit/cli.py`

```python
import argparse
import os
import subprocess
import sys
from pathlib import Path

from .config import DEFAULT_VIEWER_HOST, DEFAULT_VIEWER_PORT
from .console import AppConsole
from .runtime import (
    build_alert_options,
    build_run_options,
    build_view_options,
    current_alert_schedule,
    current_schedule,
    load_env_file,
    resolve_config_path,
)
from .scheduler import resolve_alert_schedule, resolve_schedule


def build_parser() -> argparse.ArgumentParser:
    ...


def _prepare_args(argv: list[str] | None) -> list[str]:
    ...


def main(argv: list[str] | None = None) -> int:
    ...


def run_viewer(console: AppConsole, args) -> int:
    ...


if __name__ == "__main__":
    raise SystemExit(main())
```

### `trading-engine/news_feed/ff_calendar_toolkit/config.py`

```python
"""Internal defaults and schema definitions."""

from pathlib import Path

DEFAULT_CONFIG_PATH = Path("config.yaml")
DEFAULT_ENV_PATH = Path(".env")

ALLOWED_ELEMENT_TYPES = {
    "calendar__cell": "date",
    "calendar__cell calendar__date": "date",
    "calendar__cell calendar__time": "time",
    "calendar__cell calendar__currency": "currency",
    "calendar__cell calendar__impact": "impact",
    "calendar__cell calendar__detail": "detail",
    "calendar__cell calendar__event event": "event",
    "calendar__cell calendar__actual": "actual",
    "calendar__cell calendar__forecast": "forecast",
    "calendar__cell calendar__previous": "previous",
}

EXCLUDED_ELEMENT_TYPES = [
    "calendar__cell calendar__graph",
]

ICON_COLOR_MAP = {
    "icon icon--ff-impact-yel": "yellow",
    "icon icon--ff-impact-ora": "orange",
    "icon icon--ff-impact-red": "red",
    "icon icon--ff-impact-gra": "gray",
}

NORMALIZED_FIELDS = [
    "time",
    "timezone",
    "currency",
    "impact",
    "event",
    "detail",
    "actual",
    "forecast",
    "previous",
    "day",
    "date",
    "scraped_at",
]

DEFAULT_ALLOWED_CURRENCY_CODES = ["CAD", "EUR", "GBP", "USD"]
DEFAULT_ALLOWED_IMPACT_COLORS = ["red", "orange", "gray"]
DEFAULT_TARGET_TIMEZONE = "Asia/Karachi"
DEFAULT_OUTPUT_DIR = Path("news")
DEFAULT_OUTPUT_FORMAT = "both"
DEFAULT_MONTHS = ["this"]
DEFAULT_HEADLESS = True
DEFAULT_SCHEDULE_PRESET = "weekly"
DEFAULT_VIEWER_HOST = "127.0.0.1"
DEFAULT_VIEWER_PORT = 8501
DEFAULT_ALERT_RULES_DIR = Path("rules")
DEFAULT_ALERT_STATE_DIR = Path("state/alerts")
DEFAULT_ALERT_CHECK_INTERVAL_MINUTES = 5
DEFAULT_ALERT_SCHEDULE_PRESET = "every_5_minutes"
DEFAULT_ALERT_RETRY_ATTEMPTS = 3
DEFAULT_ALERT_RETRY_BACKOFF_SECONDS = 1
DEFAULT_ALERT_MESSAGE_PREFIX = "Forex Factory Alert"

ENV_KEYS = {
    "config_path": "FF_CONFIG_PATH",
    "env_path": "FF_ENV_PATH",
    "months": "FF_MONTHS",
    "timezone": "FF_TARGET_TIMEZONE",
    "currencies": "FF_ALLOWED_CURRENCIES",
    "impacts": "FF_ALLOWED_IMPACTS",
    "output_dir": "FF_OUTPUT_DIR",
    "output_format": "FF_OUTPUT_FORMAT",
    "headless": "FF_HEADLESS",
    "viewer_host": "FF_VIEWER_HOST",
    "viewer_port": "FF_VIEWER_PORT",
    "schedule_preset": "FF_SCHEDULE_PRESET",
    "cron_schedule": "CRON_SCHEDULE",
    "alert_rules_dir": "FF_ALERT_RULES_DIR",
    "alert_state_dir": "FF_ALERT_STATE_DIR",
    "alert_schedule_preset": "FF_ALERT_SCHEDULE_PRESET",
    "alert_cron_schedule": "FF_ALERT_CRON_SCHEDULE",
    "alert_check_interval": "FF_ALERT_CHECK_INTERVAL_MINUTES",
    "alert_retry_attempts": "FF_ALERT_RETRY_ATTEMPTS",
    "alert_retry_backoff": "FF_ALERT_RETRY_BACKOFF_SECONDS",
    "alert_message_prefix": "FF_ALERT_MESSAGE_PREFIX",
}
```

### `trading-engine/news_feed/ff_calendar_toolkit/console.py`

```python
from datetime import datetime

try:
    from rich.console import Console
except ModuleNotFoundError:
    Console = None


class AppConsole:
    def __init__(self) -> None:
        ...

    def _stamp(self) -> str:
        ...

    def _line(self, label: str, color: str, message: str) -> None:
        ...

    def step(self, message: str) -> None:
        ...

    def success(self, message: str) -> None:
        ...

    def warn(self, message: str) -> None:
        ...

    def error(self, message: str) -> None:
        ...
```

### `trading-engine/news_feed/ff_calendar_toolkit/cron_runtime.py`

```python
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class CronField:
    minimum: int
    maximum: int


FIELDS = (
    CronField(0, 59),
    CronField(0, 23),
    CronField(1, 31),
    CronField(1, 12),
    CronField(0, 6),
)


def cron_matches(expression: str, when: datetime | None = None) -> bool:
    ...


def seconds_until_next_minute(when: datetime | None = None) -> int:
    ...


def _cron_weekday(when: datetime) -> int:
    ...


def _field_matches(part: str, value: int, minimum: int, maximum: int) -> bool:
    ...


def _token_matches(token: str, value: int, minimum: int, maximum: int) -> bool:
    ...


def _expand_base(base: str, minimum: int, maximum: int) -> list[int]:
    ...


def _normalize_value(value: int, minimum: int, maximum: int) -> int:
    ...


def main(argv: list[str] | None = None) -> int:
    ...


if __name__ == "__main__":
    raise SystemExit(main())
```

### `trading-engine/news_feed/ff_calendar_toolkit/models.py`

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunOptions:
    config_path: Path
    months: list[str]
    output_format: str
    output_dir: Path
    target_timezone: str | None
    allowed_currencies: list[str]
    allowed_impacts: list[str]
    headless: bool


@dataclass(frozen=True)
class ViewOptions:
    config_path: Path
    output_dir: Path
    rules_dir: Path
    state_dir: Path
    host: str
    port: int


@dataclass(frozen=True)
class AlertConnector:
    connector_id: str
    connector_type: str
    enabled: bool
    settings: dict


@dataclass(frozen=True)
class AlertOptions:
    config_path: Path
    output_dir: Path
    rules_dir: Path
    state_dir: Path
    check_interval_minutes: int
    schedule_preset: str
    cron_schedule: str | None
    retry_attempts: int
    retry_backoff_seconds: int
    message_prefix: str
    connectors: list[AlertConnector]


@dataclass(frozen=True)
class ScrapeContext:
    month_param: str
    month_name: str
    month_slug: str
    year: str
    source_timezone: str | None
    target_timezone: str | None
    scraped_at: str


@dataclass(frozen=True)
class WriteResult:
    last_run_paths: list[Path]
    monthly_paths: list[Path]
    history_paths: list[Path]
```

### `trading-engine/news_feed/ff_calendar_toolkit/normalize.py`

```python
import json
import re
from datetime import datetime
from pathlib import Path

import pytz

from .config import NORMALIZED_FIELDS


def read_json(path: str | Path):
    ...


def extract_date_parts(text: str, year: str):
    ...


def convert_time_zone(
    date_str: str,
    time_str: str,
    from_zone_str: str | None,
    to_zone_str: str | None,
) -> tuple[str, str, str]:
    """Convert an event to the target timezone.

    Returns (time, date, day). The date and day shift too when the
    conversion crosses midnight.
    """
    ...


def filter_row(row: dict, allowed_currencies: list[str], allowed_impacts: list[str]):
    ...


def normalize_rows(
    data: list[dict],
    year: str,
    source_timezone: str | None,
    target_timezone: str | None,
    allowed_currencies: list[str],
    allowed_impacts: list[str],
    scraped_at: str | None = None,
) -> list[dict]:
    ...
```

### `trading-engine/news_feed/ff_calendar_toolkit/runtime.py`

```python
import os
from pathlib import Path

import yaml

from .config import (
    DEFAULT_ALERT_CHECK_INTERVAL_MINUTES,
    DEFAULT_ALERT_MESSAGE_PREFIX,
    DEFAULT_ALERT_RETRY_ATTEMPTS,
    DEFAULT_ALERT_RETRY_BACKOFF_SECONDS,
    DEFAULT_ALERT_RULES_DIR,
    DEFAULT_ALERT_SCHEDULE_PRESET,
    DEFAULT_ALERT_STATE_DIR,
    DEFAULT_ALLOWED_CURRENCY_CODES,
    DEFAULT_ALLOWED_IMPACT_COLORS,
    DEFAULT_CONFIG_PATH,
    DEFAULT_ENV_PATH,
    DEFAULT_HEADLESS,
    DEFAULT_MONTHS,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_SCHEDULE_PRESET,
    DEFAULT_TARGET_TIMEZONE,
    DEFAULT_VIEWER_HOST,
    DEFAULT_VIEWER_PORT,
    ENV_KEYS,
)
from .models import AlertConnector, AlertOptions, RunOptions, ViewOptions


def _csv_values(value: str | None, default: list[str]) -> list[str]:
    ...


def _space_values(value: str | None, default: list[str]) -> list[str]:
    ...


def _bool_value(value: str | None, default: bool) -> bool:
    ...


def _int_value(value: str | None, default: int) -> int:
    ...


def _config_relative_path(config_path: Path, value, default: Path) -> Path:
    ...


def resolve_config_path(path_value: str | None = None) -> Path:
    ...


def resolve_env_path(config_path: Path, env_path_value: str | None = None) -> Path:
    ...


def load_env_file(config_path: Path | None = None, env_path_value: str | None = None) -> Path:
    ...


def _load_yaml_config(path: Path) -> dict:
    ...


def _yaml_list(value, default: list[str]) -> list[str]:
    ...


def _alerts_config(yaml_config: dict) -> dict:
    ...


def _connector_configs(alerts_config: dict) -> list[AlertConnector]:
    ...


def build_run_options(args) -> RunOptions:
    ...


def build_view_options(args) -> ViewOptions:
    ...


def build_alert_options(args) -> AlertOptions:
    ...


def current_schedule(config_path: str | None = None) -> tuple[str | None, str]:
    ...


def current_alert_schedule(config_path: str | None = None) -> tuple[str | None, str]:
    ...
```

### `trading-engine/news_feed/ff_calendar_toolkit/scheduler.py`

```python
SCHEDULE_PRESETS = {
    "hourly": "0 * * * *",
    "daily": "0 0 * * *",
    "weekly": "0 0 * * 0",
    "monthly": "0 0 1 * *",
}

ALERT_SCHEDULE_PRESETS = {
    "every_1_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_10_minutes": "*/10 * * * *",
    "hourly": "0 * * * *",
}


def resolve_schedule(preset: str | None, cron_expression: str | None) -> str:
    ...


def resolve_alert_schedule(preset: str | None, cron_expression: str | None) -> str:
    ...
```

### `trading-engine/news_feed/ff_calendar_toolkit/scraper.py`

```python
import os
import time
from datetime import datetime, timezone

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .config import ALLOWED_ELEMENT_TYPES, ICON_COLOR_MAP
from .models import ScrapeContext


class ForexFactoryScraper:
    def __init__(self, console, headless: bool = True) -> None:
        ...

    def init_driver(self) -> webdriver.Chrome:
        ...

    def scroll_to_end(self, driver: webdriver.Chrome) -> None:
        ...

    def parse_table(self, driver: webdriver.Chrome, month_name: str) -> list[dict]:
        ...

    def resolve_month(self, month_param: str) -> tuple[str, str, int]:
        ...

    def scrape_month(
        self, month_param: str, target_timezone: str | None
    ) -> tuple[list[dict], ScrapeContext]:
        ...
```

### `trading-engine/news_feed/ff_calendar_toolkit/service.py`

```python
from .console import AppConsole
from .models import RunOptions
from .normalize import normalize_rows
from .scraper import ForexFactoryScraper
from .storage import FileOutputStore


class ScrapeService:
    def __init__(self, console: AppConsole | None = None) -> None:
        ...

    def run(self, options: RunOptions) -> int:
        ...
```

### `trading-engine/news_feed/ff_calendar_toolkit/storage.py`

```python
import csv
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from .config import NORMALIZED_FIELDS
from .models import ScrapeContext, WriteResult


class OutputStore(ABC):
    @abstractmethod
    def write(self, records: list[dict], context: ScrapeContext, output_format: str) -> WriteResult:
        ...


class FileOutputStore(OutputStore):
    def __init__(self, output_dir: Path) -> None:
        ...

    def begin_run(self, output_format: str) -> None:
        ...

    def write(self, records: list[dict], context: ScrapeContext, output_format: str) -> WriteResult:
        ...

    def _write_file(self, path: Path, file_format: str, records: list[dict]) -> None:
        ...

    def _write_csv(self, path: Path, records: list[dict]) -> None:
        ...

    def _write_json(self, path: Path, records: list[dict]) -> None:
        ...
```

### `trading-engine/news_feed/ff_calendar_toolkit/viewer.py`

```python
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import streamlit as st
import yaml

from ff_calendar_toolkit.alerts.rules import load_rule_document, load_rules, rule_template, save_rule
from ff_calendar_toolkit.alerts.service import preview_alerts
from ff_calendar_toolkit.alerts.state import AlertStateStore
from ff_calendar_toolkit.config import NORMALIZED_FIELDS
from ff_calendar_toolkit.runtime import (
    build_alert_options,
    build_view_options,
    load_env_file,
    resolve_config_path,
)


WEEKDAY_OPTIONS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _load_default_file(output_dir: Path) -> Path | None:
    ...


def _load_records(path: Path) -> list[dict]:
    ...


def _view_context():
    ...


def _rule_defaults(records: list[dict]) -> tuple[list[str], list[str]]:
    ...


def _save_config_text(config_path: Path, content: str) -> None:
    ...


def _render_data_browser(output_dir: Path) -> list[dict]:
    ...


def _render_rules_tab(alert_options, records: list[dict]) -> None:
    ...


def _render_config_tab(config_path: Path, alert_options) -> None:
    ...


def _render_preview_tab(alert_options) -> None:
    ...


def _render_state_tab(alert_options) -> None:
    ...


def _split_csv(text: str) -> list[str]:
    ...


def main() -> None:
    ...


if __name__ == "__main__":
    main()
```

### `trading-engine/news_feed/ff_calendar_toolkit/alerts/__init__.py`

```python
"""Alerts subsystem for stored calendar data."""
```

### `trading-engine/news_feed/ff_calendar_toolkit/alerts/events.py`

```python
import json
from datetime import datetime
from pathlib import Path

import pytz

from .models import AlertEvent


def event_identity(record: dict) -> str:
    ...


def load_alert_events(output_dir: Path) -> list[AlertEvent]:
    ...


def _events_from_file(path: Path) -> list[AlertEvent]:
    ...


def _parse_event_time(record: dict) -> datetime | None:
    ...
```

### `trading-engine/news_feed/ff_calendar_toolkit/alerts/matcher.py`

```python
from datetime import datetime, timedelta

from .models import AlertEvent, AlertPreview, AlertRule


def build_dedup_key(rule: AlertRule, event: AlertEvent) -> str:
    ...


def event_matches_rule(rule: AlertRule, event: AlertEvent) -> bool:
    ...


def event_should_trigger(
    rule: AlertRule, event: AlertEvent, now: datetime, check_interval_minutes: int
) -> bool:
    ...


def preview_match(
    rule: AlertRule,
    event: AlertEvent,
    connector_id: str,
    status: str,
) -> AlertPreview:
    ...


def _lower_list(value) -> list[str]:
    ...


def _weekday_list(value) -> list[str]:
    ...
```

### `trading-engine/news_feed/ff_calendar_toolkit/alerts/models.py`

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AlertRule:
    rule_id: str
    name: str
    enabled: bool
    match: dict
    trigger: dict
    deliver: list[str]
    path: str


@dataclass(frozen=True)
class AlertEvent:
    event_id: str
    event_time: datetime
    payload: dict


@dataclass(frozen=True)
class AlertPreview:
    dedup_key: str
    rule_id: str
    rule_name: str
    connector_id: str
    event_id: str
    event_name: str
    currency: str
    impact: str
    trigger_at: datetime
    event_time: datetime
    timezone: str
    status: str
```

### `trading-engine/news_feed/ff_calendar_toolkit/alerts/notifiers.py`

```python
import json
import os
import time
from urllib import parse, request
from urllib.error import HTTPError, URLError

from ff_calendar_toolkit.models import AlertConnector, AlertOptions

from .models import AlertEvent, AlertRule


class NotificationError(RuntimeError):
    pass


class NotifierFactory:
    def __init__(self, options: AlertOptions) -> None:
        ...

    def connector_ids(self) -> list[str]:
        ...

    def send_raw(self, connector_id: str, message: str) -> None:
        ...

    def send(self, connector_id: str, rule: AlertRule, event: AlertEvent) -> None:
        ...

    def _send_once(
        self, connector: AlertConnector, message: str, rule: AlertRule, event: AlertEvent
    ) -> None:
        ...

    def _send_discord(self, connector: AlertConnector, message: str) -> None:
        ...

    def _send_telegram(self, connector: AlertConnector, message: str) -> None:
        ...

    def _send_webhook(
        self, connector: AlertConnector, message: str, rule: AlertRule, event: AlertEvent
    ) -> None:
        ...


def render_message(prefix: str, rule: AlertRule, event: AlertEvent) -> str:
    ...


def _required_env(env_name) -> str:
    ...


def _post_json(url: str, payload: dict, headers: dict | None = None) -> None:
    ...


def _post_form(url: str, payload: bytes) -> None:
    ...


def _perform_request(url: str, payload: bytes, headers: dict) -> None:
    # Mask the URL for logging — keep the domain, hide the token
    ...
```

### `trading-engine/news_feed/ff_calendar_toolkit/alerts/rules.py`

```python
from pathlib import Path
from typing import Iterable

import yaml

from .models import AlertRule


RULE_TEMPLATE = {
    "name": "usd-high-impact",
    "enabled": True,
    "match": {
        "currencies": ["USD"],
        "impacts": ["red"],
        "event_names": [],
        "event_keywords": ["CPI", "Non-Farm"],
        "weekdays": [],
    },
    "trigger": {
        "minutes_before": 10,
    },
    "deliver": ["discord_main"],
}


def slugify_rule_name(name: str) -> str:
    ...


def rule_template() -> dict:
    ...


def load_rules(rules_dir: Path) -> list[AlertRule]:
    ...


def save_rule(rules_dir: Path, payload: dict, filename: str | None = None) -> Path:
    ...


def load_rule_document(path: Path) -> dict:
    ...


def _validate_rule(path: Path, payload: dict) -> AlertRule:
    ...


def connector_choices_from_rules(rules: Iterable[AlertRule]) -> list[str]:
    ...
```

### `trading-engine/news_feed/ff_calendar_toolkit/alerts/service.py`

```python
from datetime import datetime, timezone

from ff_calendar_toolkit.console import AppConsole
from ff_calendar_toolkit.models import AlertOptions

from .events import load_alert_events
from .matcher import build_dedup_key, event_matches_rule, event_should_trigger, preview_match
from .notifiers import NotificationError, NotifierFactory
from .rules import load_rules
from .state import AlertStateStore


class AlertService:
    def __init__(self, console: AppConsole | None = None) -> None:
        ...

    def run(self, options: AlertOptions) -> int:
        ...


def preview_alerts(options: AlertOptions) -> list[dict]:
    ...
```

### `trading-engine/news_feed/ff_calendar_toolkit/alerts/state.py`

```python
import json
from datetime import datetime, timezone
from pathlib import Path


class AlertStateStore:
    def __init__(self, state_dir: Path) -> None:
        ...

    def load(self) -> dict:
        ...

    def save(self, state: dict) -> None:
        ...

    def is_sent(self, state: dict, dedup_key: str, connector_id: str) -> bool:
        ...

    def mark_sent(self, state: dict, dedup_key: str, connector_id: str, preview: dict) -> None:
        ...

    def mark_failure(self, state: dict, dedup_key: str, connector_id: str, error_message: str) -> None:
        ...
```

### `trading-engine/news_feed/rules/usd_high_impact_example.yaml`

```yaml
name: usd-med-impact-example
enabled: true
match:
  currencies:
    - USD
  impacts:
    - orange
  event_names: []
  event_keywords:
    - President
  weekdays: []
trigger:
  minutes_before: 10
deliver:
  - webhook_main
```

### `trading-engine/news_feed/scripts/refresh_docker.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-forex-factory-toolkit}"
SCRAPER_CONTAINER="${SCRAPER_CONTAINER:-forex-factory-scraper}"
ALERTS_CONTAINER="${ALERTS_CONTAINER:-forex-factory-alerts}"
MODE="${1:-refresh}"
DOCKER_UID="${DOCKER_UID:-$(id -u)}"
DOCKER_GID="${DOCKER_GID:-$(id -g)}"

compose_available() { : '...'; }

build_image() { : '...'; }

stop_and_remove() { : '...'; }

down_raw() { : '...'; }

cleanup_compose_name_conflicts() { : '...'; }

up_raw() { : '...'; }

status_raw() { : '...'; }

down_compose() { : '...'; }

up_compose() { : '...'; }

build_compose() { : '...'; }

status_compose() { : '...'; }

down() { : '...'; }

up() { : '...'; }

build() { : '...'; }

status() { : '...'; }

usage() { : '...'; }

case "${MODE}" in
  refresh)
    if compose_available; then
      down_compose
      up_compose --build
      status_compose
    else
      down_raw
      build_image
      up_raw
      status_raw
    fi
    ;;
  restart)
    down
    up
    status
    ;;
  build)
    build
    ;;
  down)
    down
    ;;
  up)
    up
    status
    ;;
  status)
    status
    ;;
  *)
    usage
    exit 1
    ;;
esac
```

### `trading-engine/news_feed/scripts/run.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: run.sh <scrape|alerts-check|view|test-notify> [args...]" >&2
  exit 1
fi

COMMAND="$1"
shift

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="${FF_PYTHON_BIN:-python3}"
fi

exec "${PYTHON_BIN}" -m ff_calendar_toolkit.cli "${COMMAND}" "$@"
```

### `trading-engine/news_feed/scripts/setup_env.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
CONDA_DIR="${ROOT_DIR}/.conda-env"
REQ_FILE="${ROOT_DIR}/requirements.txt"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=9

print_header() { : '...'; }

print_choice_menu() { : '...'; }

ensure_command() { : '...'; }

python_is_supported() { : '...'; }

pick_python_interpreter() { : '...'; }

setup_uv() { : '...'; }

setup_conda() { : '...'; }

setup_venv() { : '...'; }

main() { : '...'; }

main "$@"
```

### `trading-engine/news_feed/tests/test_alert_matching.py`

```python
import unittest
from datetime import datetime, timedelta

import pytz

from ff_calendar_toolkit.alerts.matcher import build_dedup_key, event_matches_rule, event_should_trigger
from ff_calendar_toolkit.alerts.models import AlertEvent, AlertRule


class AlertMatchingTests(unittest.TestCase):
    def setUp(self):
        ...

    def test_event_matches_rule(self):
        ...

    def test_event_should_trigger_in_window(self):
        ...

    def test_build_dedup_key_is_deterministic(self):
        ...


if __name__ == "__main__":
    unittest.main()
```

### `trading-engine/news_feed/tests/test_alert_notifiers.py`

```python
import os
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytz

from ff_calendar_toolkit.alerts.models import AlertEvent, AlertRule
from ff_calendar_toolkit.alerts.notifiers import NotifierFactory, render_message
from ff_calendar_toolkit.models import AlertConnector, AlertOptions


class AlertNotifierTests(unittest.TestCase):
    def setUp(self):
        ...

    def test_render_message_contains_core_fields(self):
        ...

    @patch("ff_calendar_toolkit.alerts.notifiers._perform_request")
    def test_webhook_payload_is_sent(self, perform_request):
        ...


if __name__ == "__main__":
    unittest.main()
```

### `trading-engine/news_feed/tests/test_alert_rules.py`

```python
import tempfile
import unittest
from pathlib import Path

from ff_calendar_toolkit.alerts.rules import load_rules, save_rule


class AlertRuleTests(unittest.TestCase):
    def test_valid_rule_loads(self):
        ...

    def test_invalid_rule_raises(self):
        ...


if __name__ == "__main__":
    unittest.main()
```

### `trading-engine/news_feed/tests/test_alert_state.py`

```python
import tempfile
import unittest
from pathlib import Path

from ff_calendar_toolkit.alerts.state import AlertStateStore


class AlertStateTests(unittest.TestCase):
    def test_state_tracks_sent_and_failures(self):
        ...


if __name__ == "__main__":
    unittest.main()
```

### `trading-engine/news_feed/tests/test_cron_runtime.py`

```python
from datetime import datetime
import unittest

from ff_calendar_toolkit.cron_runtime import cron_matches, seconds_until_next_minute
from ff_calendar_toolkit.scheduler import resolve_alert_schedule, resolve_schedule


class CronRuntimeTests(unittest.TestCase):
    def test_matches_every_five_minutes(self):
        ...

    def test_matches_weekly_sunday_midnight(self):
        ...

    def test_seconds_until_next_minute(self):
        ...


class SchedulerTests(unittest.TestCase):
    def test_schedule_prefers_cron_expression(self):
        ...

    def test_schedule_uses_preset(self):
        ...

    def test_schedule_defaults_to_weekly(self):
        ...

    def test_alert_schedule_defaults_to_every_five_minutes(self):
        ...


if __name__ == "__main__":
    unittest.main()
```

### `trading-engine/news_feed/tests/test_normalize.py`

```python
import unittest

from ff_calendar_toolkit.normalize import convert_time_zone, normalize_rows


class NormalizeTests(unittest.TestCase):
    def test_normalize_rows_carries_dates_and_times(self):
        ...

    def test_convert_time_zone_handles_special_values(self):
        ...

    def test_convert_time_zone_shifts_date_back_over_midnight(self):
        ...

    def test_convert_time_zone_shifts_date_forward_over_midnight(self):
        ...

    def test_normalize_rows_shifts_day_and_date_over_midnight(self):
        ...


if __name__ == "__main__":
    unittest.main()
```

### `trading-engine/news_feed/tests/test_runtime.py`

```python
import os
import tempfile
import unittest
from pathlib import Path

from ff_calendar_toolkit.runtime import build_alert_options, build_run_options


class Args:
    config = None
    months = None
    output_format = None
    output_dir = None
    rules_dir = None
    state_dir = None
    timezone = None
    currencies = None
    impacts = None
    show_browser = False


class RuntimeTests(unittest.TestCase):
    def test_cli_options_override_environment(self):
        ...

    def test_yaml_config_is_used_when_env_and_cli_are_absent(self):
        ...

    def test_alert_options_load_from_yaml(self):
        ...


if __name__ == "__main__":
    unittest.main()
```

### `trading-engine/news_feed/tests/test_storage.py`

```python
import json
import tempfile
import unittest
from pathlib import Path

from ff_calendar_toolkit.models import ScrapeContext
from ff_calendar_toolkit.storage import FileOutputStore


class StorageTests(unittest.TestCase):
    def test_file_output_store_writes_last_run_monthly_and_history(self):
        ...


if __name__ == "__main__":
    unittest.main()
```

### `trading-engine/strategies/base.py`

```python
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
```

### `trading-engine/strategies/validation_trivial.py`

```python
from strategies.base import Strategy
from engine.models import Signal, Direction

class ValidationTrivial:
    name = "validation_trivial"
    timeframe = "H1"
    symbols = ["EURUSD"]

    def __init__(self):
        ...

    def on_bar(self, ctx):
        ...
```
