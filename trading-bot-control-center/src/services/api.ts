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
  LiveMarketDataInfo,
  MarketSnapshotInfo,
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

export function getActiveApiBaseUrl(): string {
  try {
    const saved = window.localStorage.getItem(STORAGE_BASE_URL_KEY);
    return saved && saved.trim() ? saved.trim() : API_BASE_URL;
  } catch {
    return API_BASE_URL;
  }
}

// ============================================================================
// In-Memory Mock Store (used ONLY when USE_MOCK === true)
// ============================================================================
function clone<T>(data: T): T {
  return JSON.parse(JSON.stringify(data)) as T;
}

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
): Promise<T> {
  const baseUrl = getActiveApiBaseUrl().replace(/\/+$/, '');
  const response = await fetch(`${baseUrl}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const errBody = await response.json();
      if (errBody?.detail) {
        detail = typeof errBody.detail === 'string' ? errBody.detail : JSON.stringify(errBody.detail);
      }
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

function computeJournalStats(trades: JournalTrade[]): JournalStats {
  const totalTrades = trades.length;
  if (totalTrades === 0) {
    return {
      totalTrades: 0,
      wins: 0,
      losses: 0,
      winRate: 0,
      netProfit: 0,
      expectancyR: 0,
      profitFactor: 0,
      avgWin: 0,
      avgLoss: 0,
    };
  }
  const winTrades = trades.filter((t) => t.pnl > 0);
  const lossTrades = trades.filter((t) => t.pnl <= 0);
  const grossWin = winTrades.reduce((s, t) => s + t.pnl, 0);
  const grossLoss = Math.abs(lossTrades.reduce((s, t) => s + t.pnl, 0));
  const netProfit = trades.reduce((s, t) => s + t.pnl, 0);
  const expectancyR = trades.reduce((s, t) => s + t.rMultiple, 0) / totalTrades;

  return {
    totalTrades,
    wins: winTrades.length,
    losses: lossTrades.length,
    winRate: Math.round((winTrades.length / totalTrades) * 1000) / 10,
    netProfit: Math.round(netProfit * 100) / 100,
    expectancyR: Math.round(expectancyR * 100) / 100,
    profitFactor: grossLoss > 0 ? Math.round((grossWin / grossLoss) * 100) / 100 : grossWin > 0 ? 9.99 : 0,
    avgWin: winTrades.length > 0 ? Math.round((grossWin / winTrades.length) * 100) / 100 : 0,
    avgLoss: lossTrades.length > 0 ? -Math.round((grossLoss / lossTrades.length) * 100) / 100 : 0,
  };
}

function recomputeMockAccountOpenStats() {
  const openPnl = mockStore.openPositions.reduce((sum, p) => sum + p.floatingPnl, 0);
  mockStore.account.openTradesCount = mockStore.openPositions.length;
  mockStore.account.openPnl = Math.round(openPnl * 100) / 100;
  mockStore.account.equity = Math.round((mockStore.account.balance + openPnl) * 100) / 100;
  mockStore.account.marginUsed = Math.round(
    mockStore.openPositions.reduce((sum, p) => sum + p.sizeLots * 16500, 0) * 100
  ) / 100;
  mockStore.account.freeMargin = Math.max(
    0,
    Math.round((mockStore.account.equity - mockStore.account.marginUsed) * 100) / 100
  );
  mockStore.account.marginLevelPercent =
    mockStore.account.marginUsed > 0
      ? Math.round((mockStore.account.equity / mockStore.account.marginUsed) * 10000) / 100
      : 0;
}

// ============================================================================
// Public Service Layer API
// ============================================================================
export const api = {
  // --- Reference metadata ---
  async getAvailablePairs(): Promise<ForexPair[]> {
    if (USE_MOCK) {
      return clone(AVAILABLE_PAIRS);
    }
    // Real FastAPI call replaces mock data
    return requestJson<ForexPair[]>('/api/market/pairs');
  },

  async getLiveMarketData(): Promise<LiveMarketDataInfo> {
    if (USE_MOCK) {
      await delay(50);
      return {
        connectionState: 'Disconnected',
        environment: 'Demo',
        symbol: 'EURUSD',
        message: 'Mock mode is enabled; no broker data is connected.',
        quote: null,
        lastClosedCandle: null,
      };
    }
    return requestJson<LiveMarketDataInfo>('/api/market/live');
  },

  async getMarketSnapshot(): Promise<MarketSnapshotInfo | null> {
    if (USE_MOCK) {
      return null;
    }
    return requestJson<MarketSnapshotInfo>('/api/market/snapshot');
  },

  // --- Dashboard & Bot Control ---
  async getBotStatus(): Promise<BotStatusInfo> {
    if (USE_MOCK) {
      await delay(90);
      mockStore.botStatus.activeStrategiesCount = mockStore.strategies.filter((s) => s.isActive).length;
      mockStore.botStatus.lastHeartbeat = new Date().toISOString();
      return clone(mockStore.botStatus);
    }
    // Real FastAPI call replaces mock data
    return requestJson<BotStatusInfo>('/api/bot/status');
  },

  async setBotRunning(run: boolean): Promise<BotStatusInfo> {
    if (USE_MOCK) {
      await delay(160);
      const now = new Date().toISOString();
      mockStore.botStatus = {
        ...mockStore.botStatus,
        state: run ? 'Running' : 'Stopped',
        startedAt: run ? now : null,
        uptimeSeconds: run ? 1 : 0,
        lastHeartbeat: now,
        errorMessage: undefined,
      };
      mockStore.activityLog.unshift({
        id: `log-${Date.now()}`,
        timestamp: now,
        level: run ? 'order' : 'warning',
        message: run ? 'Trading bot started by operator' : 'Trading bot stopped by operator',
        details: run
          ? `${mockStore.strategies.filter((s) => s.isActive).length} active strategies armed.`
          : 'Execution loop halted cleanly; existing positions remain monitored.',
      });
      return clone(mockStore.botStatus);
    }
    // Real FastAPI call replaces mock data
    return requestJson<BotStatusInfo>(run ? '/api/bot/start' : '/api/bot/stop', {
      method: 'POST',
    });
  },

  // --- Safety: Emergency Kill Switch ---
  async triggerKillSwitch(): Promise<KillSwitchResult> {
    if (USE_MOCK) {
      await delay(260);
      const now = new Date().toISOString();
      const closedCount = mockStore.openPositions.length;
      const realizedPnl = mockStore.openPositions.reduce((sum, p) => sum + p.floatingPnl, 0);

      for (const pos of mockStore.openPositions) {
        mockStore.tradeAuditLogs.unshift({
          id: `aud-${Date.now()}-${pos.id}`,
          timestamp: now,
          orderId: `KILL-${pos.id.toUpperCase()}`,
          pair: pos.pair,
          direction: pos.direction === 'BUY' ? 'SELL' : 'BUY',
          action: 'CLOSE',
          requestedPrice: pos.currentPrice,
          executedPrice: pos.currentPrice,
          sizeLots: pos.sizeLots,
          brokerResponse: 'FILLED',
          brokerMessage: `Emergency Kill Switch market close @ ${pos.currentPrice}`,
          latencyMs: 22,
          strategyName: pos.strategyName,
        });
      }

      mockStore.account.balance = Math.round((mockStore.account.balance + realizedPnl) * 100) / 100;
      mockStore.account.todayPnl = Math.round((mockStore.account.todayPnl + realizedPnl) * 100) / 100;
      mockStore.openPositions = [];
      recomputeMockAccountOpenStats();

      mockStore.botStatus = {
        ...mockStore.botStatus,
        state: 'Stopped',
        startedAt: null,
        uptimeSeconds: 0,
        lastHeartbeat: now,
        errorMessage: 'Emergency Kill Switch engaged — all positions closed and bot halted.',
      };

      mockStore.activityLog.unshift({
        id: `log-kill-${Date.now()}`,
        timestamp: now,
        level: 'error',
        message: `KILL SWITCH ENGAGED: Closed ${closedCount} open position(s) and stopped bot`,
        details: `Realized P/L on emergency flatten: ${realizedPnl >= 0 ? '+' : ''}${realizedPnl.toFixed(2)} ${mockStore.account.currency}`,
      });

      return {
        botStatus: clone(mockStore.botStatus),
        closedPositionsCount: closedCount,
        triggeredAt: now,
      };
    }
    // Real FastAPI call replaces mock data
    return requestJson<KillSwitchResult>('/api/bot/kill-switch', {
      method: 'POST',
    });
  },

  async getAccountSummary(): Promise<AccountSummary> {
    if (USE_MOCK) {
      await delay(90);
      return clone(mockStore.account);
    }
    // Real FastAPI call replaces mock data
    return requestJson<AccountSummary>('/api/account/summary');
  },

  async getEquityCurve(range: '1D' | '1W' | '1M' | 'ALL' = '1M'): Promise<EquityPoint[]> {
    if (USE_MOCK) {
      await delay(110);
      const pts = mockStore.equityCurve;
      if (range === '1D') return clone(pts.slice(-4));
      if (range === '1W') return clone(pts.slice(-8));
      return clone(pts);
    }
    // Real FastAPI call replaces mock data
    return requestJson<EquityPoint[]>(`/api/account/equity-curve?range=${encodeURIComponent(range)}`);
  },

  async getOpenPositions(): Promise<OpenPosition[]> {
    if (USE_MOCK) {
      await delay(100);
      return clone(mockStore.openPositions);
    }
    // Real FastAPI call replaces mock data
    return requestJson<OpenPosition[]>('/api/positions/open');
  },

  // --- Manual Trade Controls ---
  async closePosition(positionId: string): Promise<{ closedPositionId: string; realizedPnl: number }> {
    if (USE_MOCK) {
      await delay(180);
      const idx = mockStore.openPositions.findIndex((p) => p.id === positionId);
      if (idx === -1) throw new Error(`Position ${positionId} not found`);
      const pos = mockStore.openPositions[idx];
      const now = new Date().toISOString();

      mockStore.openPositions.splice(idx, 1);
      mockStore.account.balance = Math.round((mockStore.account.balance + pos.floatingPnl) * 100) / 100;
      mockStore.account.todayPnl = Math.round((mockStore.account.todayPnl + pos.floatingPnl) * 100) / 100;
      recomputeMockAccountOpenStats();

      mockStore.activityLog.unshift({
        id: `log-close-${Date.now()}`,
        timestamp: now,
        level: 'order',
        pair: pos.pair,
        strategyName: pos.strategyName,
        message: `Manual close executed on ${pos.pair} ${pos.direction} (${pos.sizeLots} lots)`,
        details: `Realized P/L: ${pos.floatingPnl >= 0 ? '+' : ''}${pos.floatingPnl.toFixed(2)} ${mockStore.account.currency}`,
      });
      mockStore.tradeAuditLogs.unshift({
        id: `aud-${Date.now()}`,
        timestamp: now,
        orderId: `MAN-CLS-${Date.now().toString().slice(-4)}`,
        pair: pos.pair,
        direction: pos.direction === 'BUY' ? 'SELL' : 'BUY',
        action: 'CLOSE',
        requestedPrice: pos.currentPrice,
        executedPrice: pos.currentPrice,
        sizeLots: pos.sizeLots,
        brokerResponse: 'FILLED',
        brokerMessage: `Manual operator close @ ${pos.currentPrice}`,
        latencyMs: 31,
        strategyName: 'Manual Override',
      });

      return { closedPositionId: positionId, realizedPnl: pos.floatingPnl };
    }
    // Real FastAPI call replaces mock data
    return requestJson<{ closedPositionId: string; realizedPnl: number }>(
      `/api/positions/${encodeURIComponent(positionId)}/close`,
      { method: 'POST' }
    );
  },

  async modifyPositionSlTp(
    positionId: string,
    payload: ModifyPositionSlTpPayload
  ): Promise<OpenPosition> {
    if (USE_MOCK) {
      await delay(140);
      const idx = mockStore.openPositions.findIndex((p) => p.id === positionId);
      if (idx === -1) throw new Error(`Position ${positionId} not found`);
      const now = new Date().toISOString();
      mockStore.openPositions[idx] = {
        ...mockStore.openPositions[idx],
        stopLoss: payload.stopLoss,
        takeProfit: payload.takeProfit,
      };
      const updated = mockStore.openPositions[idx];
      mockStore.activityLog.unshift({
        id: `log-mod-${Date.now()}`,
        timestamp: now,
        level: 'order',
        pair: updated.pair,
        message: `Modified SL/TP on ${updated.pair} (${updated.id})`,
        details: `New SL: ${payload.stopLoss}, New TP: ${payload.takeProfit}`,
      });
      mockStore.tradeAuditLogs.unshift({
        id: `aud-${Date.now()}`,
        timestamp: now,
        orderId: `MOD-${Date.now().toString().slice(-4)}`,
        pair: updated.pair,
        direction: updated.direction,
        action: 'MODIFY_SLTP',
        requestedPrice: updated.currentPrice,
        executedPrice: updated.currentPrice,
        sizeLots: updated.sizeLots,
        brokerResponse: 'MODIFIED',
        brokerMessage: `SL set to ${payload.stopLoss}, TP set to ${payload.takeProfit}`,
        latencyMs: 26,
        strategyName: 'Manual Override',
      });
      return clone(updated);
    }
    // Real FastAPI call replaces mock data
    return requestJson<OpenPosition>(
      `/api/positions/${encodeURIComponent(positionId)}/sl-tp`,
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }
    );
  },

  async placeManualOrder(payload: ManualOrderPayload): Promise<OpenPosition> {
    if (USE_MOCK) {
      await delay(200);
      const now = new Date().toISOString();
      const basePrices: Record<ForexPair, number> = {
        EURUSD: 1.0846,
        GBPUSD: 1.2684,
        USDJPY: 154.35,
        XAUUSD: 2588.2,
        USDZAR: 18.125,
        AUDUSD: 0.6485,
      };
      const entry = basePrices[payload.pair] ?? 1.0;
      const pos: OpenPosition = {
        id: `pos-man-${Date.now().toString().slice(-4)}`,
        pair: payload.pair,
        direction: payload.direction,
        entryPrice: entry,
        currentPrice: entry,
        stopLoss: payload.stopLoss,
        takeProfit: payload.takeProfit,
        sizeLots: payload.sizeLots,
        floatingPnl: -Math.round(payload.sizeLots * 45 * 100) / 100,
        floatingPnlPips: -0.6,
        strategyId: 'manual-override',
        strategyName: 'Manual Override',
        setupGrade: 'A',
        openedAt: now,
        swap: 0,
        commission: -Math.round(payload.sizeLots * 65 * 100) / 100,
      };
      mockStore.openPositions.unshift(pos);
      recomputeMockAccountOpenStats();

      mockStore.activityLog.unshift({
        id: `log-man-${Date.now()}`,
        timestamp: now,
        level: 'order',
        pair: pos.pair,
        strategyName: 'Manual Override',
        message: `Manual ${pos.direction} order opened on ${pos.pair} (${pos.sizeLots.toFixed(2)} lots @ ${entry})`,
        details: payload.comment || `SL ${payload.stopLoss} · TP ${payload.takeProfit}`,
      });
      mockStore.tradeAuditLogs.unshift({
        id: `aud-${Date.now()}`,
        timestamp: now,
        orderId: `MAN-${Date.now().toString().slice(-4)}`,
        pair: pos.pair,
        direction: pos.direction,
        action: 'OPEN',
        requestedPrice: entry,
        executedPrice: entry,
        sizeLots: pos.sizeLots,
        brokerResponse: 'FILLED',
        brokerMessage: `Manual market order filled @ ${entry}`,
        latencyMs: 34,
        strategyName: 'Manual Override',
      });
      return clone(pos);
    }
    // Real FastAPI call replaces mock data
    return requestJson<OpenPosition>('/api/positions/manual', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // --- Logs & Audit ---
  async getActivityLog(limit = 50): Promise<ActivityLogEntry[]> {
    if (USE_MOCK) {
      await delay(90);
      return clone(mockStore.activityLog.slice(0, limit));
    }
    // Real FastAPI call replaces mock data
    return requestJson<ActivityLogEntry[]>(`/api/bot/activity?limit=${limit}`);
  },

  async getErrorLogs(): Promise<ErrorLogEntry[]> {
    if (USE_MOCK) {
      await delay(100);
      return clone(mockStore.errorLogs);
    }
    // Real FastAPI call replaces mock data
    return requestJson<ErrorLogEntry[]>('/api/logs/errors');
  },

  async getTradeAuditLogs(): Promise<TradeAuditEntry[]> {
    if (USE_MOCK) {
      await delay(100);
      return clone(mockStore.tradeAuditLogs);
    }
    // Real FastAPI call replaces mock data
    return requestJson<TradeAuditEntry[]>('/api/logs/trade-audit');
  },

  // --- System Status ---
  async getSystemStatus(): Promise<SystemStatusInfo> {
    if (USE_MOCK) {
      await delay(90);
      mockStore.systemStatus.lastHeartbeat = new Date().toISOString();
      mockStore.systemStatus.ctraderStatus = mockStore.appSettings.broker.connectionState;
      mockStore.systemStatus.botVersion = mockStore.botStatus.version;
      return clone(mockStore.systemStatus);
    }
    // Real FastAPI call replaces mock data
    return requestJson<SystemStatusInfo>('/api/system/status');
  },

  // --- Trade Journal & Capital Ledger ---
  async getJournalTrades(filters: JournalFilters = {}): Promise<JournalResponse> {
    if (USE_MOCK) {
      await delay(130);
      let list = [...mockStore.trades];

      if (filters.startDate) {
        const startMs = new Date(filters.startDate).getTime();
        list = list.filter((t) => new Date(t.openedAt).getTime() >= startMs);
      }
      if (filters.endDate) {
        const endMs = new Date(filters.endDate).getTime() + 86400000;
        list = list.filter((t) => new Date(t.openedAt).getTime() <= endMs);
      }
      if (filters.pair && filters.pair !== 'ALL') {
        list = list.filter((t) => t.pair === filters.pair);
      }
      if (filters.strategyId && filters.strategyId !== 'ALL') {
        list = list.filter((t) => t.strategyId === filters.strategyId);
      }
      if (filters.setupGrade) {
        list = list.filter((t) => t.setupGrade === filters.setupGrade);
      }
      if (filters.outcome === 'win') {
        list = list.filter((t) => t.pnl > 0);
      } else if (filters.outcome === 'loss') {
        list = list.filter((t) => t.pnl <= 0);
      }
      if (filters.tag && filters.tag !== 'ALL') {
        list = list.filter((t) => (t.tags ?? []).includes(filters.tag!));
      }
      if (filters.search && filters.search.trim()) {
        const q = filters.search.trim().toLowerCase();
        list = list.filter(
          (t) =>
            t.pair.toLowerCase().includes(q) ||
            t.strategyName.toLowerCase().includes(q) ||
            t.notes.toLowerCase().includes(q) ||
            t.id.toLowerCase().includes(q) ||
            (t.tags ?? []).some((tg) => tg.toLowerCase().includes(q))
        );
      }

      return {
        trades: clone(list),
        stats: computeJournalStats(list),
        totalCount: list.length,
      };
    }

    // Real FastAPI call replaces mock data
    const params = new URLSearchParams();
    if (filters.startDate) params.set('start_date', filters.startDate);
    if (filters.endDate) params.set('end_date', filters.endDate);
    if (filters.pair && filters.pair !== 'ALL') params.set('pair', filters.pair);
    if (filters.strategyId && filters.strategyId !== 'ALL') params.set('strategy_id', filters.strategyId);
    if (filters.setupGrade) params.set('setup_grade', filters.setupGrade);
    if (filters.outcome && filters.outcome !== 'all') params.set('outcome', filters.outcome);
    if (filters.tag && filters.tag !== 'ALL') params.set('tag', filters.tag);
    if (filters.search) params.set('search', filters.search);
    return requestJson<JournalResponse>(`/api/journal/trades?${params.toString()}`);
  },

  async updateTradeNotes(tradeId: string, notes: string): Promise<JournalTrade> {
    return this.updateTradeMeta(tradeId, { notes });
  },

  async updateTradeMeta(
    tradeId: string,
    patch: { notes?: string; tags?: string[]; screenshotUrl?: string }
  ): Promise<JournalTrade> {
    if (USE_MOCK) {
      await delay(100);
      const idx = mockStore.trades.findIndex((t) => t.id === tradeId);
      if (idx === -1) throw new Error(`Trade ${tradeId} not found`);
      mockStore.trades[idx] = {
        ...mockStore.trades[idx],
        ...(patch.notes !== undefined ? { notes: patch.notes } : {}),
        ...(patch.tags !== undefined ? { tags: patch.tags } : {}),
        ...(patch.screenshotUrl !== undefined ? { screenshotUrl: patch.screenshotUrl } : {}),
      };
      return clone(mockStore.trades[idx]);
    }
    // Real FastAPI call replaces mock data
    return requestJson<JournalTrade>(`/api/journal/trades/${encodeURIComponent(tradeId)}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    });
  },

  async getCapitalTransactions(): Promise<CapitalTransaction[]> {
    if (USE_MOCK) {
      await delay(90);
      return clone(mockStore.capitalTransactions);
    }
    // Real FastAPI call replaces mock data
    return requestJson<CapitalTransaction[]>('/api/journal/capital-transactions');
  },

  async addCapitalTransaction(
    payload: Omit<CapitalTransaction, 'id'>
  ): Promise<CapitalTransaction> {
    if (USE_MOCK) {
      await delay(120);
      const created: CapitalTransaction = {
        id: `cap-${Date.now()}`,
        ...payload,
      };
      mockStore.capitalTransactions.unshift(created);
      return clone(created);
    }
    // Real FastAPI call replaces mock data
    return requestJson<CapitalTransaction>('/api/journal/capital-transactions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // --- Backtester ---
  async getSavedBacktests(): Promise<SavedBacktestSummary[]> {
    if (USE_MOCK) {
      await delay(110);
      return Object.values(mockStore.backtests)
        .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
        .map(toSavedSummary);
    }
    // Real FastAPI call replaces mock data
    return requestJson<SavedBacktestSummary[]>('/api/backtests');
  },

  async getBacktestResult(backtestId: string): Promise<BacktestResult> {
    if (USE_MOCK) {
      await delay(130);
      const found = mockStore.backtests[backtestId];
      if (!found) throw new Error(`Backtest ${backtestId} not found`);
      return clone(found);
    }
    // Real FastAPI call replaces mock data
    return requestJson<BacktestResult>(`/api/backtests/${encodeURIComponent(backtestId)}`);
  },

  async startBacktest(config: BacktestConfig): Promise<BacktestJobStatus> {
    if (USE_MOCK) {
      await delay(120);
      const jobId = `job-${Date.now()}`;
      const job: BacktestJobStatus = {
        jobId,
        status: 'running',
        progressPercent: 12,
        currentStep: 'Loading historical OHLCV bars (strictly causal index)...',
        startedAt: new Date().toISOString(),
      };
      mockStore.backtestJobs.set(jobId, { job, config: clone(config), pollCount: 0 });
      return clone(job);
    }
    // Real FastAPI call replaces mock data
    return requestJson<BacktestJobStatus>('/api/backtests/run', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  },

  async getBacktestJobStatus(jobId: string): Promise<BacktestJobStatus> {
    if (USE_MOCK) {
      await delay(100);
      const entry = mockStore.backtestJobs.get(jobId);
      if (!entry) throw new Error(`Backtest job ${jobId} not found`);
      if (entry.job.status === 'cancelled' || entry.job.status === 'completed') {
        return clone(entry.job);
      }

      entry.pollCount += 1;
      const steps = [
        { pct: 32, label: 'Computing indicator windows without lookahead...' },
        { pct: 58, label: 'Simulating fills with spread, commission & slippage...' },
        { pct: 82, label: 'Running SL/TP ATR grid & walk-forward folds...' },
        { pct: 95, label: 'Running 1,000-path Monte Carlo resampling...' },
      ];

      if (entry.pollCount <= steps.length) {
        const s = steps[entry.pollCount - 1];
        entry.job = { ...entry.job, progressPercent: s.pct, currentStep: s.label };
      } else {
        const strat = mockStore.strategies.find((s) => s.id === entry.config.strategyId);
        const result = generateBacktestResultFromConfig(
          entry.config,
          strat?.name || 'Selected Strategy'
        );
        mockStore.backtests[result.id] = result;
        entry.job = {
          ...entry.job,
          status: 'completed',
          progressPercent: 100,
          currentStep: 'Simulation complete',
          resultId: result.id,
        };
      }
      return clone(entry.job);
    }
    // Real FastAPI call replaces mock data
    return requestJson<BacktestJobStatus>(`/api/backtests/jobs/${encodeURIComponent(jobId)}`);
  },

  async cancelBacktestJob(jobId: string): Promise<BacktestJobStatus> {
    if (USE_MOCK) {
      await delay(80);
      const entry = mockStore.backtestJobs.get(jobId);
      if (!entry) throw new Error(`Backtest job ${jobId} not found`);
      entry.job = {
        ...entry.job,
        status: 'cancelled',
        currentStep: 'Cancelled by user',
      };
      return clone(entry.job);
    }
    // Real FastAPI call replaces mock data
    return requestJson<BacktestJobStatus>(`/api/backtests/jobs/${encodeURIComponent(jobId)}/cancel`, {
      method: 'POST',
    });
  },

  async deleteBacktest(backtestId: string): Promise<void> {
    if (USE_MOCK) {
      await delay(90);
      delete mockStore.backtests[backtestId];
      return;
    }
    // Real FastAPI call replaces mock data
    await requestJson<void>(`/api/backtests/${encodeURIComponent(backtestId)}`, {
      method: 'DELETE',
    });
  },

  // --- Live vs Backtest Comparison ---
  async getLiveVsBacktest(strategyId: string): Promise<LiveVsBacktestComparison> {
    if (USE_MOCK) {
      await delay(120);
      const found = mockStore.liveVsBacktest[strategyId];
      if (found) return clone(found);
      const strat = mockStore.strategies.find((s) => s.id === strategyId);
      return {
        strategyId,
        strategyName: strat?.name ?? 'Custom Strategy',
        backtestName: `${strat?.name ?? 'Strategy'} · Baseline`,
        diverging: false,
        divergenceReasons: [],
        live: {
          winRate: 51.0,
          expectancyR: 0.28,
          maxDrawdownPercent: 5.1,
          avgTradePnl: 780,
          profitFactor: 1.48,
          totalTrades: 18,
          netReturnPercent: 8.4,
        },
        backtest: {
          winRate: 53.2,
          expectancyR: 0.31,
          maxDrawdownPercent: 5.5,
          avgTradePnl: 840,
          profitFactor: 1.56,
          totalTrades: 120,
          netReturnPercent: 28.5,
        },
        equityComparison: [
          { tradeIndex: 0, label: 'T0', liveReturnPercent: 0, backtestReturnPercent: 0 },
          { tradeIndex: 6, label: 'T6', liveReturnPercent: 2.9, backtestReturnPercent: 3.1 },
          { tradeIndex: 12, label: 'T12', liveReturnPercent: 5.8, backtestReturnPercent: 6.0 },
          { tradeIndex: 18, label: 'T18', liveReturnPercent: 8.4, backtestReturnPercent: 9.2 },
        ],
      };
    }
    // Real FastAPI call replaces mock data
    return requestJson<LiveVsBacktestComparison>(
      `/api/analytics/live-vs-backtest?strategy_id=${encodeURIComponent(strategyId)}`
    );
  },

  // --- Strategies (incl. Versioning & Cloning) ---
  async getStrategies(): Promise<Strategy[]> {
    if (USE_MOCK) {
      await delay(100);
      return clone(mockStore.strategies);
    }
    // Real FastAPI call replaces mock data
    return requestJson<Strategy[]>('/api/strategies');
  },

  async getStrategy(strategyId: string): Promise<Strategy> {
    if (USE_MOCK) {
      await delay(90);
      const s = mockStore.strategies.find((x) => x.id === strategyId);
      if (!s) throw new Error(`Strategy ${strategyId} not found`);
      return clone(s);
    }
    // Real FastAPI call replaces mock data
    return requestJson<Strategy>(`/api/strategies/${encodeURIComponent(strategyId)}`);
  },

  async createStrategy(payload: CreateStrategyPayload): Promise<Strategy> {
    if (USE_MOCK) {
      await delay(140);
      const now = new Date().toISOString();
      const newStrat: Strategy = {
        id: `strat-${Date.now()}`,
        name: payload.name,
        description: payload.description,
        isActive: false,
        currentVersion: 'v1.0.0',
        versions: [
          {
            version: 'v1.0.0',
            createdAt: now,
            notes: 'Initial strategy registration.',
            tradeIds: [],
            tradeCount: 0,
            isCurrent: true,
          },
        ],
        indicatorIds: payload.indicatorIds,
        assignedPairs: payload.assignedPairs,
        fileName: payload.fileName,
        codeSnippet: payload.codeSnippet,
        updatedAt: now,
        parameters: [
          { key: 'atrSlMultiple', label: 'Stop Loss (ATR Multiple)', type: 'number', value: 1.5, min: 0.5, max: 4.0, step: 0.1 },
          { key: 'atrTpMultiple', label: 'Take Profit (ATR Multiple)', type: 'number', value: 3.0, min: 1.0, max: 6.0, step: 0.25 },
        ],
        gradingRules: {
          'A++': [],
          'A+': [],
          'A': [],
          'B': [],
          'Bad': [],
        },
      };
      mockStore.strategies.unshift(newStrat);
      return clone(newStrat);
    }
    // Real FastAPI call replaces mock data
    return requestJson<Strategy>('/api/strategies', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async cloneStrategy(strategyId: string): Promise<Strategy> {
    if (USE_MOCK) {
      await delay(140);
      const source = mockStore.strategies.find((s) => s.id === strategyId);
      if (!source) throw new Error(`Strategy ${strategyId} not found`);
      const now = new Date().toISOString();
      const cloned: Strategy = {
        ...clone(source),
        id: `strat-${Date.now()}`,
        name: `${source.name} (Copy)`,
        isActive: false,
        currentVersion: 'v1.0.0',
        updatedAt: now,
        versions: [
          {
            version: 'v1.0.0',
            createdAt: now,
            notes: `Cloned from ${source.name} (${source.currentVersion}).`,
            tradeIds: [],
            tradeCount: 0,
            isCurrent: true,
          },
        ],
      };
      mockStore.strategies.unshift(cloned);
      return clone(cloned);
    }
    // Real FastAPI call replaces mock data
    return requestJson<Strategy>(`/api/strategies/${encodeURIComponent(strategyId)}/clone`, {
      method: 'POST',
    });
  },

  async rollbackStrategyVersion(strategyId: string, version: string): Promise<Strategy> {
    if (USE_MOCK) {
      await delay(150);
      const idx = mockStore.strategies.findIndex((s) => s.id === strategyId);
      if (idx === -1) throw new Error(`Strategy ${strategyId} not found`);
      const strat = mockStore.strategies[idx];
      const now = new Date().toISOString();
      mockStore.strategies[idx] = {
        ...strat,
        currentVersion: version,
        updatedAt: now,
        versions: strat.versions.map((v) => ({
          ...v,
          isCurrent: v.version === version,
        })),
      };
      mockStore.activityLog.unshift({
        id: `log-rb-${Date.now()}`,
        timestamp: now,
        level: 'warning',
        strategyName: strat.name,
        message: `Rolled back ${strat.name} to version ${version}`,
      });
      return clone(mockStore.strategies[idx]);
    }
    // Real FastAPI call replaces mock data
    return requestJson<Strategy>(
      `/api/strategies/${encodeURIComponent(strategyId)}/rollback`,
      {
        method: 'POST',
        body: JSON.stringify({ version }),
      }
    );
  },

  async updateStrategy(strategyId: string, patch: Partial<Strategy>): Promise<Strategy> {
    if (USE_MOCK) {
      await delay(120);
      const idx = mockStore.strategies.findIndex((s) => s.id === strategyId);
      if (idx === -1) throw new Error(`Strategy ${strategyId} not found`);
      mockStore.strategies[idx] = {
        ...mockStore.strategies[idx],
        ...patch,
        updatedAt: new Date().toISOString(),
      };
      return clone(mockStore.strategies[idx]);
    }
    // Real FastAPI call replaces mock data
    return requestJson<Strategy>(`/api/strategies/${encodeURIComponent(strategyId)}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    });
  },

  async toggleStrategyActive(strategyId: string, isActive: boolean): Promise<Strategy> {
    return this.updateStrategy(strategyId, { isActive });
  },

  // --- Indicators ---
  async getIndicators(): Promise<Indicator[]> {
    if (USE_MOCK) {
      await delay(100);
      return clone(mockStore.indicators);
    }
    // Real FastAPI call replaces mock data
    return requestJson<Indicator[]>('/api/indicators');
  },

  async createIndicator(payload: CreateIndicatorPayload): Promise<Indicator> {
    if (USE_MOCK) {
      await delay(140);
      const created: Indicator = {
        id: `ind-${Date.now()}`,
        ...payload,
        isCustom: true,
      };
      mockStore.indicators.push(created);
      return clone(created);
    }
    // Real FastAPI call replaces mock data
    return requestJson<Indicator>('/api/indicators', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateIndicator(indicatorId: string, patch: Partial<Indicator>): Promise<Indicator> {
    if (USE_MOCK) {
      await delay(110);
      const idx = mockStore.indicators.findIndex((i) => i.id === indicatorId);
      if (idx === -1) throw new Error(`Indicator ${indicatorId} not found`);
      mockStore.indicators[idx] = { ...mockStore.indicators[idx], ...patch };
      return clone(mockStore.indicators[idx]);
    }
    // Real FastAPI call replaces mock data
    return requestJson<Indicator>(`/api/indicators/${encodeURIComponent(indicatorId)}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    });
  },

  // --- Data Manager ---
  async getDatasets(): Promise<HistoricalDataset[]> {
    if (USE_MOCK) {
      await delay(110);
      return clone(mockStore.datasets);
    }
    // Real FastAPI call replaces mock data
    return requestJson<HistoricalDataset[]>('/api/data/datasets');
  },

  async downloadDataset(datasetId: string): Promise<HistoricalDataset> {
    if (USE_MOCK) {
      await delay(350);
      const idx = mockStore.datasets.findIndex((d) => d.id === datasetId);
      if (idx === -1) throw new Error(`Dataset ${datasetId} not found`);
      const now = new Date().toISOString();
      mockStore.datasets[idx] = {
        ...mockStore.datasets[idx],
        endDate: now.slice(0, 10),
        candleCount: mockStore.datasets[idx].candleCount + 128,
        lastUpdated: now,
        status: 'Up to date',
      };
      return clone(mockStore.datasets[idx]);
    }
    // Real FastAPI call replaces mock data
    return requestJson<HistoricalDataset>(
      `/api/data/datasets/${encodeURIComponent(datasetId)}/download`,
      { method: 'POST' }
    );
  },

  async validateDataset(datasetId: string): Promise<HistoricalDataset> {
    if (USE_MOCK) {
      await delay(300);
      const idx = mockStore.datasets.findIndex((d) => d.id === datasetId);
      if (idx === -1) throw new Error(`Dataset ${datasetId} not found`);
      mockStore.datasets[idx] = {
        ...mockStore.datasets[idx],
        lastUpdated: new Date().toISOString(),
        status: 'Up to date',
      };
      return clone(mockStore.datasets[idx]);
    }
    // Real FastAPI call replaces mock data
    return requestJson<HistoricalDataset>(
      `/api/data/datasets/${encodeURIComponent(datasetId)}/validate`,
      { method: 'POST' }
    );
  },

  async getDatasetGaps(datasetId: string): Promise<DataGap[]> {
    if (USE_MOCK) {
      await delay(100);
      return clone(mockStore.dataGaps[datasetId] ?? []);
    }
    // Real FastAPI call replaces mock data
    return requestJson<DataGap[]>(
      `/api/data/datasets/${encodeURIComponent(datasetId)}/gaps`
    );
  },

  // --- Portfolio & Exposure ---
  async getPortfolioExposure(): Promise<PortfolioExposureData> {
    if (USE_MOCK) {
      await delay(110);
      return clone(mockStore.portfolio);
    }
    // Real FastAPI call replaces mock data
    return requestJson<PortfolioExposureData>('/api/portfolio/exposure');
  },

  // --- News Calendar & Blackout ---
  async getNewsEvents(): Promise<NewsEventItem[]> {
    if (USE_MOCK) {
      await delay(100);
      return clone(mockStore.newsEvents);
    }
    // Real FastAPI call replaces mock data
    return requestJson<NewsEventItem[]>('/api/news/upcoming');
  },

  async getNewsFilterSettings(): Promise<NewsFilterSettings> {
    if (USE_MOCK) {
      await delay(80);
      return clone(mockStore.newsFilter);
    }
    // Real FastAPI call replaces mock data
    return requestJson<NewsFilterSettings>('/api/news/filter');
  },

  async updateNewsFilterSettings(settings: NewsFilterSettings): Promise<NewsFilterSettings> {
    if (USE_MOCK) {
      await delay(110);
      mockStore.newsFilter = clone(settings);
      return clone(mockStore.newsFilter);
    }
    // Real FastAPI call replaces mock data
    return requestJson<NewsFilterSettings>('/api/news/filter', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  },

  // --- Safety: Pair Toggles & Auto-Pause Rules & Risk ---
  async getPairToggles(): Promise<PairToggleSetting[]> {
    if (USE_MOCK) {
      await delay(90);
      return clone(mockStore.pairToggles);
    }
    // Real FastAPI call replaces mock data
    return requestJson<PairToggleSetting[]>('/api/safety/pairs');
  },

  async togglePairEnabled(pair: ForexPair, enabled: boolean): Promise<PairToggleSetting> {
    if (USE_MOCK) {
      await delay(110);
      const idx = mockStore.pairToggles.findIndex((p) => p.pair === pair);
      if (idx === -1) throw new Error(`Pair ${pair} not found`);
      const now = new Date().toISOString();
      mockStore.pairToggles[idx] = {
        ...mockStore.pairToggles[idx],
        enabled,
        updatedAt: now,
      };
      mockStore.activityLog.unshift({
        id: `log-pair-${Date.now()}`,
        timestamp: now,
        level: 'warning',
        pair,
        message: `${pair} automated trading ${enabled ? 'enabled' : 'disabled'}`,
      });
      return clone(mockStore.pairToggles[idx]);
    }
    // Real FastAPI call replaces mock data
    return requestJson<PairToggleSetting>(`/api/safety/pairs/${encodeURIComponent(pair)}`, {
      method: 'PATCH',
      body: JSON.stringify({ enabled }),
    });
  },

  async getAutoPauseRules(): Promise<AutoPauseRules> {
    if (USE_MOCK) {
      await delay(90);
      return clone(mockStore.autoPauseRules);
    }
    // Real FastAPI call replaces mock data
    return requestJson<AutoPauseRules>('/api/safety/auto-pause');
  },

  async updateAutoPauseRules(rules: AutoPauseRules): Promise<AutoPauseRules> {
    if (USE_MOCK) {
      await delay(130);
      mockStore.autoPauseRules = clone(rules);
      return clone(mockStore.autoPauseRules);
    }
    // Real FastAPI call replaces mock data
    return requestJson<AutoPauseRules>('/api/safety/auto-pause', {
      method: 'PUT',
      body: JSON.stringify(rules),
    });
  },

  async getRiskSettings(): Promise<RiskSettings> {
    if (USE_MOCK) {
      await delay(90);
      return clone(mockStore.riskSettings);
    }
    // Real FastAPI call replaces mock data
    return requestJson<RiskSettings>('/api/risk/settings');
  },

  async updateRiskSettings(settings: RiskSettings): Promise<RiskSettings> {
    if (USE_MOCK) {
      await delay(120);
      mockStore.riskSettings = clone(settings);
      return clone(mockStore.riskSettings);
    }
    // Real FastAPI call replaces mock data
    return requestJson<RiskSettings>('/api/risk/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  },

  // --- Settings, Broker, Alerts, Security & Backup ---
  async getSettings(): Promise<AppSettings> {
    if (USE_MOCK) {
      await delay(100);
      return clone(mockStore.appSettings);
    }
    // Real FastAPI call replaces mock data
    return requestJson<AppSettings>('/api/settings');
  },

  async updateBrokerSettings(payload: BrokerUpdatePayload): Promise<BrokerSettings> {
    if (USE_MOCK) {
      await delay(150);
      const hasSecret = Boolean(payload.clientSecret?.trim()) || mockStore.appSettings.broker.hasClientSecret;
      mockStore.appSettings.broker = {
        ...mockStore.appSettings.broker,
        clientId: payload.clientId,
        accountId: payload.accountId,
        environment: payload.environment,
        hasClientSecret: hasSecret,
        clientSecretMasked: hasSecret ? '••••••••••••••••••••••••' : '',
        statusMessage: 'Credentials saved server-side. Test connection to verify.',
      };
      return clone(mockStore.appSettings.broker);
    }
    // Real FastAPI call replaces mock data (never returns plaintext secret)
    return requestJson<BrokerSettings>('/api/settings/broker', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  async testBrokerConnection(): Promise<BrokerSettings> {
    if (USE_MOCK) {
      await delay(380);
      const ok = Boolean(
        mockStore.appSettings.broker.clientId.trim() &&
          mockStore.appSettings.broker.accountId.trim() &&
          mockStore.appSettings.broker.hasClientSecret
      );
      mockStore.appSettings.broker = {
        ...mockStore.appSettings.broker,
        connectionState: ok ? 'Connected' : 'Error',
        lastTestedAt: new Date().toISOString(),
        statusMessage: ok
          ? `Authenticated to cTrader Open API (${mockStore.appSettings.broker.environment} Server)`
          : 'Missing Client ID, Client Secret, or Account ID.',
      };
      return clone(mockStore.appSettings.broker);
    }
    // Real FastAPI call replaces mock data
    return requestJson<BrokerSettings>('/api/settings/broker/test', {
      method: 'POST',
    });
  },

  async updateApiBaseUrl(apiBaseUrl: string): Promise<AppSettings> {
    try {
      window.localStorage.setItem(STORAGE_BASE_URL_KEY, apiBaseUrl.trim());
    } catch {
      // ignore storage errors
    }
    if (USE_MOCK) {
      await delay(80);
      mockStore.appSettings.apiBaseUrl = apiBaseUrl.trim();
      return clone(mockStore.appSettings);
    }
    return this.getSettings();
  },

  async setTradingMode(mode: TradingMode): Promise<AppSettings> {
    if (USE_MOCK) {
      await delay(140);
      mockStore.appSettings.tradingMode = mode;
      mockStore.appSettings.broker.environment = mode;
      mockStore.appSettings.broker.statusMessage = `Switched environment to ${mode}. Verify broker credentials.`;
      return clone(mockStore.appSettings);
    }
    // Real FastAPI call replaces mock data
    return requestJson<AppSettings>('/api/settings/trading-mode', {
      method: 'PUT',
      body: JSON.stringify({ tradingMode: mode }),
    });
  },

  async updateDisplayCurrency(displayCurrency: DisplayCurrency): Promise<AppSettings> {
    if (USE_MOCK) {
      await delay(60);
      mockStore.appSettings.displayCurrency = displayCurrency;
      return clone(mockStore.appSettings);
    }
    // Real FastAPI call replaces mock data
    return requestJson<AppSettings>('/api/settings/display-currency', {
      method: 'PUT',
      body: JSON.stringify({ displayCurrency }),
    });
  },

  async updateNotificationPreferences(
    prefs: NotificationPreferences,
    telegramBotToken?: string
  ): Promise<NotificationPreferences> {
    if (USE_MOCK) {
      await delay(110);
      const hasToken = Boolean(telegramBotToken?.trim()) || prefs.hasTelegramToken;
      mockStore.appSettings.notifications = clone({
        ...prefs,
        hasTelegramToken: hasToken,
        telegramBotTokenMasked: hasToken ? '••••••••••:••••••••••••••••••••' : '',
      });
      return clone(mockStore.appSettings.notifications);
    }
    // Real FastAPI call replaces mock data
    return requestJson<NotificationPreferences>('/api/settings/notifications', {
      method: 'PUT',
      body: JSON.stringify({ ...prefs, telegramBotToken }),
    });
  },

  async sendTestAlert(channel: 'email' | 'telegram'): Promise<TestAlertResult> {
    if (USE_MOCK) {
      await delay(280);
      const now = new Date().toISOString();
      const target =
        channel === 'telegram'
          ? mockStore.appSettings.notifications.telegramChatId || 'configured chat'
          : mockStore.appSettings.notifications.emailAddress || 'configured email';
      return {
        channel,
        success: true,
        message: `Test ${channel === 'telegram' ? 'Telegram' : 'Email'} alert dispatched to ${target}.`,
        sentAt: now,
      };
    }
    // Real FastAPI call replaces mock data
    return requestJson<TestAlertResult>('/api/settings/notifications/test', {
      method: 'POST',
      body: JSON.stringify({ channel }),
    });
  },

  // --- Security & Authentication ---
  async getSecuritySettings(): Promise<SecuritySettings> {
    if (USE_MOCK) {
      await delay(80);
      return clone(mockStore.appSettings.security);
    }
    // Real FastAPI call replaces mock data
    return requestJson<SecuritySettings>('/api/security/settings');
  },

  async setupTwoFactor(): Promise<TwoFactorSetupInfo> {
    if (USE_MOCK) {
      await delay(140);
      const secret = 'JBSWY3DPEHPK3PXP7K4M';
      return {
        secret,
        otpauthUrl: `otpauth://totp/TradingBotControlCenter:${mockStore.appSettings.security.username}?secret=${secret}&issuer=TradingBotControlCenter`,
      };
    }
    // Real FastAPI call replaces mock data
    return requestJson<TwoFactorSetupInfo>('/api/security/2fa/setup', {
      method: 'POST',
    });
  },

  async verifyTwoFactor(code: string): Promise<SecuritySettings> {
    if (USE_MOCK) {
      await delay(160);
      if (code.trim().length !== 6) {
        throw new Error('Enter a valid 6-digit authenticator verification code.');
      }
      mockStore.appSettings.security.twoFactorEnabled = true;
      return clone(mockStore.appSettings.security);
    }
    // Real FastAPI call replaces mock data
    return requestJson<SecuritySettings>('/api/security/2fa/verify', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
  },

  async disableTwoFactor(): Promise<SecuritySettings> {
    if (USE_MOCK) {
      await delay(120);
      mockStore.appSettings.security.twoFactorEnabled = false;
      return clone(mockStore.appSettings.security);
    }
    // Real FastAPI call replaces mock data
    return requestJson<SecuritySettings>('/api/security/2fa/disable', {
      method: 'POST',
    });
  },

  async updateSessionTimeout(
    sessionTimeoutMinutes: SecuritySettings['sessionTimeoutMinutes']
  ): Promise<SecuritySettings> {
    if (USE_MOCK) {
      await delay(90);
      mockStore.appSettings.security.sessionTimeoutMinutes = sessionTimeoutMinutes;
      return clone(mockStore.appSettings.security);
    }
    // Real FastAPI call replaces mock data
    return requestJson<SecuritySettings>('/api/security/session-timeout', {
      method: 'PUT',
      body: JSON.stringify({ sessionTimeoutMinutes }),
    });
  },

  async login(
    username: string,
    password: string,
    otpCode?: string
  ): Promise<{ authenticated: boolean; requiresTwoFactor: boolean; username: string }> {
    if (USE_MOCK) {
      await delay(200);
      if (!username.trim() || !password.trim()) {
        throw new Error('Username and password are required.');
      }
      if (mockStore.appSettings.security.twoFactorEnabled && !otpCode?.trim()) {
        return { authenticated: false, requiresTwoFactor: true, username };
      }
      if (mockStore.appSettings.security.twoFactorEnabled && (otpCode?.trim().length ?? 0) !== 6) {
        throw new Error('Invalid 6-digit 2FA verification code.');
      }
      mockStore.appSettings.security.username = username.trim();
      mockStore.appSettings.security.lastLoginAt = new Date().toISOString();
      return { authenticated: true, requiresTwoFactor: false, username: username.trim() };
    }
    // Real FastAPI call replaces mock data
    return requestJson<{ authenticated: boolean; requiresTwoFactor: boolean; username: string }>(
      '/api/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ username, password, otpCode }),
      }
    );
  },

  // --- Export & Import Backup ---
  async exportBackupSection(section: 'journal' | 'strategies' | 'settings'): Promise<unknown> {
    if (USE_MOCK) {
      await delay(120);
      if (section === 'journal') {
        return {
          exportedAt: new Date().toISOString(),
          section: 'journal',
          trades: clone(mockStore.trades),
          capitalTransactions: clone(mockStore.capitalTransactions),
        };
      }
      if (section === 'strategies') {
        return {
          exportedAt: new Date().toISOString(),
          section: 'strategies',
          strategies: clone(mockStore.strategies),
          indicators: clone(mockStore.indicators),
        };
      }
      return {
        exportedAt: new Date().toISOString(),
        section: 'settings',
        appSettings: clone(mockStore.appSettings),
        riskSettings: clone(mockStore.riskSettings),
        autoPauseRules: clone(mockStore.autoPauseRules),
        pairToggles: clone(mockStore.pairToggles),
        newsFilter: clone(mockStore.newsFilter),
      };
    }
    // Real FastAPI call replaces mock data
    return requestJson<unknown>(`/api/backup/export/${section}`);
  },

  async importBackupSection(
    section: 'journal' | 'strategies' | 'settings',
    payload: Record<string, unknown>
  ): Promise<{ restoredCount: number; message: string }> {
    if (USE_MOCK) {
      await delay(180);
      if (section === 'journal' && Array.isArray(payload.trades)) {
        mockStore.trades = clone(payload.trades as JournalTrade[]);
        if (Array.isArray(payload.capitalTransactions)) {
          mockStore.capitalTransactions = clone(payload.capitalTransactions as CapitalTransaction[]);
        }
        return {
          restoredCount: mockStore.trades.length,
          message: `Imported ${mockStore.trades.length} trade journal records.`,
        };
      }
      if (section === 'strategies' && Array.isArray(payload.strategies)) {
        mockStore.strategies = clone(payload.strategies as Strategy[]);
        return {
          restoredCount: mockStore.strategies.length,
          message: `Imported ${mockStore.strategies.length} strategy definitions.`,
        };
      }
      if (section === 'settings' && payload.appSettings) {
        mockStore.appSettings = clone(payload.appSettings as AppSettings);
        if (payload.riskSettings) mockStore.riskSettings = clone(payload.riskSettings as RiskSettings);
        if (payload.autoPauseRules) mockStore.autoPauseRules = clone(payload.autoPauseRules as AutoPauseRules);
        return {
          restoredCount: 1,
          message: 'Restored settings, risk rules, and notification preferences.',
        };
      }
      throw new Error(`Invalid backup JSON format for "${section}".`);
    }
    // Real FastAPI call replaces mock data
    return requestJson<{ restoredCount: number; message: string }>(
      `/api/backup/import/${section}`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },
};
