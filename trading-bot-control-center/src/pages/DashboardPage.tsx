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

export function DashboardPage() {
  const {
    theme,
    displayCurrency,
    formatDisplayAmount,
    botStatus,
    setBotStatusDirect,
    refreshGlobalState,
    dataVersion,
  } = useAppContext();
  const isDark = theme === 'dark';

  // Bot control dialog state
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [isTogglingBot, setIsTogglingBot] = useState(false);
  const [botError, setBotError] = useState<string | null>(null);

  // Account KPIs
  const [account, setAccount] = useState<AccountSummary | null>(null);
  const [accountLoading, setAccountLoading] = useState(true);
  const [accountError, setAccountError] = useState<string | null>(null);

  // Equity curve
  const [equityRange, setEquityRange] = useState<EquityRange>('1M');
  const [equityData, setEquityData] = useState<EquityPoint[]>([]);
  const [equityLoading, setEquityLoading] = useState(true);
  const [equityError, setEquityError] = useState<string | null>(null);

  // Open positions & manual close/modify
  const [positions, setPositions] = useState<OpenPosition[]>([]);
  const [positionsLoading, setPositionsLoading] = useState(true);
  const [positionsError, setPositionsError] = useState<string | null>(null);
  const [closeTarget, setCloseTarget] = useState<OpenPosition | null>(null);
  const [closingPos, setClosingPos] = useState(false);

  const [modifyTarget, setModifyTarget] = useState<OpenPosition | null>(null);
  const [modifySl, setModifySl] = useState('');
  const [modifyTp, setModifyTp] = useState('');
  const [confirmModifyOpen, setConfirmModifyOpen] = useState(false);
  const [modifyingPos, setModifyingPos] = useState(false);

  // Manual trade override
  const [availablePairs, setAvailablePairs] = useState<ForexPair[]>([
    'EURUSD',
    'GBPUSD',
    'USDJPY',
    'XAUUSD',
    'USDZAR',
    'AUDUSD',
  ]);
  const [manualPair, setManualPair] = useState<ForexPair>('EURUSD');
  const [manualDir, setManualDir] = useState<TradeDirection>('BUY');
  const [manualLots, setManualLots] = useState('0.10');
  const [manualSl, setManualSl] = useState('1.0810');
  const [manualTp, setManualTp] = useState('1.0910');
  const [manualComment, setManualComment] = useState('');
  const [confirmManualOpen, setConfirmManualOpen] = useState(false);
  const [submittingManual, setSubmittingManual] = useState(false);
  const [manualFeedback, setManualFeedback] = useState<string | null>(null);

  // Activity log
  const [activity, setActivity] = useState<ActivityLogEntry[]>([]);
  const [activityLoading, setActivityLoading] = useState(true);
  const [activityError, setActivityError] = useState<string | null>(null);
  const [activityFilter, setActivityFilter] = useState<'all' | 'signal' | 'order'>('all');

  // News calendar panel
  const [newsEvents, setNewsEvents] = useState<NewsEventItem[]>([]);
  const [newsFilter, setNewsFilter] = useState<NewsFilterSettings | null>(null);
  const [newsLoading, setNewsLoading] = useState(true);
  const [newsError, setNewsError] = useState<string | null>(null);

  const fetchAccount = useCallback(async () => {
    setAccountLoading(true);
    setAccountError(null);
    try {
      const res = await api.getAccountSummary();
      setAccount(res);
    } catch (err) {
      setAccountError(err instanceof Error ? err.message : 'Failed to load account metrics');
    } finally {
      setAccountLoading(false);
    }
  }, []);

  const fetchEquity = useCallback(async (range: EquityRange) => {
    setEquityLoading(true);
    setEquityError(null);
    try {
      const res = await api.getEquityCurve(range);
      setEquityData(res);
    } catch (err) {
      setEquityError(err instanceof Error ? err.message : 'Failed to load equity curve');
    } finally {
      setEquityLoading(false);
    }
  }, []);

  const fetchPositions = useCallback(async () => {
    setPositionsLoading(true);
    setPositionsError(null);
    try {
      const res = await api.getOpenPositions();
      setPositions(res);
    } catch (err) {
      setPositionsError(err instanceof Error ? err.message : 'Failed to load open positions');
    } finally {
      setPositionsLoading(false);
    }
  }, []);

  const fetchActivity = useCallback(async () => {
    setActivityLoading(true);
    setActivityError(null);
    try {
      const res = await api.getActivityLog(35);
      setActivity(res);
    } catch (err) {
      setActivityError(err instanceof Error ? err.message : 'Failed to load activity feed');
    } finally {
      setActivityLoading(false);
    }
  }, []);

  const fetchNews = useCallback(async () => {
    setNewsLoading(true);
    setNewsError(null);
    try {
      const [events, filterCfg, pairs] = await Promise.all([
        api.getNewsEvents(),
        api.getNewsFilterSettings(),
        api.getAvailablePairs(),
      ]);
      setNewsEvents(events);
      setNewsFilter(filterCfg);
      setAvailablePairs(pairs);
    } catch (err) {
      setNewsError(err instanceof Error ? err.message : 'Failed to load news calendar');
    } finally {
      setNewsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchAccount();
    void fetchPositions();
    void fetchActivity();
    void fetchNews();
  }, [fetchAccount, fetchPositions, fetchActivity, fetchNews, dataVersion]);

  useEffect(() => {
    void fetchEquity(equityRange);
  }, [equityRange, fetchEquity]);

  const handleConfirmToggleBot = async () => {
    const targetRun = botStatus?.state !== 'Running';
    setIsTogglingBot(true);
    setBotError(null);
    try {
      const updated = await api.setBotRunning(targetRun);
      setBotStatusDirect(updated);
      setConfirmOpen(false);
      await fetchActivity();
    } catch (err) {
      setBotError(err instanceof Error ? err.message : 'Failed to toggle bot state');
    } finally {
      setIsTogglingBot(false);
    }
  };

  const handleConfirmClosePosition = async () => {
    if (!closeTarget) return;
    setClosingPos(true);
    try {
      await api.closePosition(closeTarget.id);
      setCloseTarget(null);
      await Promise.all([fetchPositions(), fetchAccount(), fetchActivity(), refreshGlobalState()]);
    } catch (err) {
      setPositionsError(err instanceof Error ? err.message : 'Failed to close position');
    } finally {
      setClosingPos(false);
    }
  };

  const openModifyModal = (pos: OpenPosition) => {
    setModifyTarget(pos);
    setModifySl(String(pos.stopLoss));
    setModifyTp(String(pos.takeProfit));
  };

  const handleConfirmModifySlTp = async () => {
    if (!modifyTarget) return;
    setModifyingPos(true);
    try {
      await api.modifyPositionSlTp(modifyTarget.id, {
        stopLoss: Number(modifySl),
        takeProfit: Number(modifyTp),
      });
      setConfirmModifyOpen(false);
      setModifyTarget(null);
      await Promise.all([fetchPositions(), fetchActivity()]);
    } catch (err) {
      setPositionsError(err instanceof Error ? err.message : 'Failed to modify SL/TP');
    } finally {
      setModifyingPos(false);
    }
  };

  const handleManualSubmitRequest = (e: FormEvent) => {
    e.preventDefault();
    setManualFeedback(null);
    setConfirmManualOpen(true);
  };

  const handleConfirmManualOrder = async () => {
    setSubmittingManual(true);
    try {
      const created = await api.placeManualOrder({
        pair: manualPair,
        direction: manualDir,
        sizeLots: Math.max(0.01, Number(manualLots) || 0.1),
        stopLoss: Number(manualSl) || 0,
        takeProfit: Number(manualTp) || 0,
        comment: manualComment.trim() || undefined,
      });
      setConfirmManualOpen(false);
      setManualComment('');
      setManualFeedback(
        `Submitted manual ${created.direction} ${created.pair} (${created.sizeLots.toFixed(2)} lots).`
      );
      await Promise.all([fetchPositions(), fetchAccount(), fetchActivity(), refreshGlobalState()]);
    } catch (err) {
      setManualFeedback(err instanceof Error ? err.message : 'Manual order failed');
      setConfirmManualOpen(false);
    } finally {
      setSubmittingManual(false);
    }
  };

  const isRunning = botStatus?.state === 'Running';
  const botState = botStatus?.state ?? 'Stopped';
  const sourceCurrency = account?.currency ?? 'ZAR';

  const chartEquityData = equityData.map((pt) => ({
    ...pt,
    displayEquity: convertCurrencyAmount(pt.equity, sourceCurrency, displayCurrency),
    displayBalance: convertCurrencyAmount(pt.balance, sourceCurrency, displayCurrency),
  }));

  const filteredActivity =
    activityFilter === 'all'
      ? activity
      : activity.filter((a) => a.level === activityFilter);

  return (
    <div className="space-y-6">
      {/* Page Title & Bot Master Control Strip */}
      <div className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-5 md:flex-row md:items-center md:justify-between">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Control Center
            </h1>
            <span
              className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-0.5 text-xs font-semibold ${
                botState === 'Running'
                  ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                  : botState === 'Error'
                  ? 'border-red-500/40 bg-red-500/15 text-red-700 dark:text-red-300'
                  : 'border-slate-300 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300'
              }`}
            >
              {botState === 'Error' && <AlertTriangle className="h-3.5 w-3.5" />}
              {botState}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
            <span>
              Uptime:{' '}
              <span className="font-mono font-medium text-slate-800 dark:text-slate-200 tabular-nums">
                {botStatus ? formatUptime(botStatus.uptimeSeconds) : '00:00:00'}
              </span>
            </span>
            <span aria-hidden="true">·</span>
            <span>
              Active strategies:{' '}
              <span className="font-mono font-medium text-slate-800 dark:text-slate-200 tabular-nums">
                {botStatus?.activeStrategiesCount ?? 0}
              </span>
            </span>
            {botStatus?.errorMessage && (
              <>
                <span aria-hidden="true">·</span>
                <span className="text-red-600 dark:text-red-400">{botStatus.errorMessage}</span>
              </>
            )}
          </div>
          {botError && (
            <p className="text-xs text-red-600 dark:text-red-400">{botError}</p>
          )}
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={() => {
              void refreshGlobalState();
              void fetchAccount();
              void fetchEquity(equityRange);
              void fetchPositions();
              void fetchActivity();
              void fetchNews();
            }}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-slate-100 px-3.5 py-2.5 text-xs font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700/80 dark:bg-slate-800/70 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors whitespace-nowrap"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>

          {/* Big ON / OFF Toggle */}
          <button
            type="button"
            onClick={() => setConfirmOpen(true)}
            className={`inline-flex items-center gap-2.5 rounded-lg px-5 py-2.5 text-sm font-semibold transition-colors whitespace-nowrap shadow-sm ${
              isRunning
                ? 'bg-red-600 hover:bg-red-500 text-white'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white'
            }`}
          >
            <Power className="h-4 w-4" />
            {isRunning ? 'Stop Bot (OFF)' : 'Start Bot (ON)'}
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      {accountLoading ? (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
          {Array.from({ length: 6 }).map((_, idx) => (
            <div
              key={idx}
              className="h-24 rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-4 animate-pulse"
            />
          ))}
        </div>
      ) : accountError ? (
        <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-4">
          <ErrorState message={accountError} onRetry={fetchAccount} />
        </div>
      ) : !account ? (
        <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-4">
          <ErrorState message="No account telemetry available." onRetry={fetchAccount} />
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
          <KpiCard
            label="Account Balance"
            value={formatDisplayAmount(account.balance, sourceCurrency)}
            subtext={`${displayCurrency} · 1:${account.leverage}`}
          />
          <KpiCard
            label="Equity"
            value={formatDisplayAmount(account.equity, sourceCurrency)}
            subtext={`Margin lvl ${account.marginLevelPercent.toFixed(0)}%`}
          />
          <KpiCard
            label="Open P/L"
            value={formatDisplayAmount(account.openPnl, sourceCurrency, { signed: true })}
            valueTone={account.openPnl >= 0 ? 'profit' : 'loss'}
            subtext={`${account.openTradesCount} open position${account.openTradesCount === 1 ? '' : 's'}`}
          />
          <KpiCard
            label="Today's P/L"
            value={formatDisplayAmount(account.todayPnl, sourceCurrency, { signed: true })}
            valueTone={account.todayPnl >= 0 ? 'profit' : 'loss'}
            subtext={`${account.todayPnlPercent >= 0 ? '+' : ''}${account.todayPnlPercent.toFixed(2)}% today`}
          />
          <KpiCard
            label="Open Trades"
            value={String(account.openTradesCount)}
            subtext="Active broker tickets"
          />
          <KpiCard
            label="Margin Used"
            value={formatDisplayAmount(account.marginUsed, sourceCurrency)}
            subtext={`Free ${formatDisplayAmount(account.freeMargin, sourceCurrency, { decimals: 0 })}`}
          />
        </div>
      )}

      {/* Equity Curve + Activity Log Split */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        {/* Equity Curve (8 cols) */}
        <PanelShell
          className="xl:col-span-8"
          title="Account Equity Curve"
          subtitle={`Closed balance vs live floating equity (${displayCurrency})`}
          isLoading={equityLoading}
          error={equityError}
          isEmpty={chartEquityData.length === 0}
          emptyTitle="No equity history yet"
          emptyDescription="Equity snapshots will render once the backend records balance checkpoints."
          onRetry={() => fetchEquity(equityRange)}
          skeletonHeightClass="h-72"
          headerRight={
            <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-100 dark:border-slate-800 dark:bg-[#0B0F17] p-1">
              {(['1D', '1W', '1M', 'ALL'] as EquityRange[]).map((rng) => (
                <button
                  key={rng}
                  type="button"
                  onClick={() => setEquityRange(rng)}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors whitespace-nowrap ${
                    equityRange === rng
                      ? 'bg-white text-slate-900 shadow-xs dark:bg-slate-800 dark:text-slate-100'
                      : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
                  }`}
                >
                  {rng}
                </button>
              ))}
            </div>
          }
        >
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartEquityData} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
                <defs>
                  <linearGradient id="dashEquityGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.28} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke={isDark ? '#1E293B' : '#E2E8F0'} strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="label"
                  stroke={isDark ? '#64748B' : '#94A3B8'}
                  tick={{ fill: isDark ? '#94A3B8' : '#475569', fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke={isDark ? '#64748B' : '#94A3B8'}
                  tick={{ fill: isDark ? '#94A3B8' : '#475569', fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  domain={['auto', 'auto']}
                  tickFormatter={(v) =>
                    displayCurrency === 'ZAR'
                      ? `${(Number(v) / 1000).toFixed(0)}k`
                      : `$${(Number(v) / 1000).toFixed(1)}k`
                  }
                  width={52}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: isDark ? '#0E141F' : '#FFFFFF',
                    borderColor: isDark ? '#334155' : '#CBD5E1',
                    color: isDark ? '#F1F5F9' : '#0F172A',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  formatter={(value, name) => [
                    formatCurrency(Number(value ?? 0), displayCurrency),
                    name === 'displayEquity' ? 'Equity' : 'Balance',
                  ]}
                />
                <Area
                  type="monotone"
                  dataKey="displayEquity"
                  stroke="#10B981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#dashEquityGrad)"
                />
                <Area
                  type="monotone"
                  dataKey="displayBalance"
                  stroke="#64748B"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  fill="none"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </PanelShell>

        {/* Live Activity Log (4 cols) */}
        <PanelShell
          className="xl:col-span-4"
          title="Live Activity Log"
          subtitle="Execution & scanner events"
          isLoading={activityLoading}
          error={activityError}
          isEmpty={filteredActivity.length === 0}
          emptyTitle="No activity events"
          emptyDescription="Bot scan ticks, setup grading, and order placements will stream here."
          onRetry={fetchActivity}
          skeletonRows={6}
          headerRight={
            <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-100 dark:border-slate-800 dark:bg-[#0B0F17] p-1">
              {(['all', 'signal', 'order'] as const).map((lvl) => (
                <button
                  key={lvl}
                  type="button"
                  onClick={() => setActivityFilter(lvl)}
                  className={`rounded-md px-2 py-1 text-[11px] font-medium capitalize transition-colors whitespace-nowrap ${
                    activityFilter === lvl
                      ? 'bg-white text-slate-900 shadow-xs dark:bg-slate-800 dark:text-slate-100'
                      : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>
          }
        >
          <div className="max-h-72 overflow-y-auto pr-1 space-y-2">
            {filteredActivity.map((entry) => {
              const levelBadge =
                entry.level === 'order'
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : entry.level === 'signal'
                  ? 'text-blue-600 dark:text-blue-400'
                  : entry.level === 'warning'
                  ? 'text-amber-600 dark:text-amber-400'
                  : entry.level === 'error'
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-slate-500 dark:text-slate-400';

              return (
                <div
                  key={entry.id}
                  className="rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800/70 dark:bg-[#0D131D] px-3 py-2 text-xs"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={`font-mono text-[11px] font-semibold uppercase ${levelBadge}`}>
                      {entry.level}
                      {entry.pair ? ` · ${entry.pair}` : ''}
                    </span>
                    <span className="font-mono text-[11px] text-slate-500 tabular-nums">
                      {new Date(entry.timestamp).toLocaleTimeString('en-GB', {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: false,
                      })}
                    </span>
                  </div>
                  <p className="mt-1 text-slate-800 dark:text-slate-200 leading-snug">{entry.message}</p>
                  {entry.details && (
                    <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">{entry.details}</p>
                  )}
                </div>
              );
            })}
          </div>
        </PanelShell>
      </div>

      {/* Currently Open Positions Table with Manual Controls */}
      <PanelShell
        title="Currently Open Positions"
        subtitle="Live broker positions · modify SL/TP or manually close any ticket"
        isLoading={positionsLoading}
        error={positionsError}
        isEmpty={positions.length === 0}
        emptyTitle="No open positions"
        emptyDescription="The bot currently has zero open market exposure. New positions appear here upon entry fill."
        onRetry={fetchPositions}
        skeletonRows={4}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 whitespace-nowrap">
                <th className="py-2.5 pr-4 font-medium">Pair</th>
                <th className="py-2.5 px-3 font-medium">Direction</th>
                <th className="py-2.5 px-3 font-medium text-right">Entry</th>
                <th className="py-2.5 px-3 font-medium text-right">Current</th>
                <th className="py-2.5 px-3 font-medium text-right">SL</th>
                <th className="py-2.5 px-3 font-medium text-right">TP</th>
                <th className="py-2.5 px-3 font-medium text-right">Lots</th>
                <th className="py-2.5 px-3 font-medium text-right">Floating P/L</th>
                <th className="py-2.5 px-3 font-medium">Strategy</th>
                <th className="py-2.5 px-3 font-medium text-right">Grade</th>
                <th className="py-2.5 pl-3 font-medium text-right">Manual Controls</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
              {positions.map((pos) => {
                const isProfit = pos.floatingPnl >= 0;
                return (
                  <tr key={pos.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/35 transition-colors">
                    <td className="py-2.5 pr-4 font-mono font-semibold text-slate-900 dark:text-slate-100 whitespace-nowrap">
                      <div>{pos.pair}</div>
                      <div className="text-[10px] font-normal text-slate-500">
                        {formatDateTime(pos.openedAt)}
                      </div>
                    </td>
                    <td className="py-2.5 px-3 whitespace-nowrap">
                      <span
                        className={`font-mono text-[11px] font-semibold ${
                          pos.direction === 'BUY'
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : 'text-red-600 dark:text-red-400'
                        }`}
                      >
                        {pos.direction}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200">
                      {formatPairPrice(pos.entryPrice, pos.pair)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-600 dark:text-slate-300">
                      {formatPairPrice(pos.currentPrice, pos.pair)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-500 dark:text-slate-400">
                      {formatPairPrice(pos.stopLoss, pos.pair)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-500 dark:text-slate-400">
                      {formatPairPrice(pos.takeProfit, pos.pair)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200">
                      {pos.sizeLots.toFixed(2)}
                    </td>
                    <td
                      className={`py-2.5 px-3 text-right font-mono font-semibold tabular-nums whitespace-nowrap ${
                        isProfit
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      <div>{formatDisplayAmount(pos.floatingPnl, sourceCurrency, { signed: true })}</div>
                      <div className="text-[10px] font-normal opacity-80">
                        {pos.floatingPnlPips >= 0 ? '+' : ''}
                        {pos.floatingPnlPips.toFixed(1)} pips
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-slate-700 dark:text-slate-300 whitespace-nowrap">
                      {pos.strategyName}
                    </td>
                    <td className="py-2.5 px-3 text-right whitespace-nowrap">
                      <GradeBadge grade={pos.setupGrade} />
                    </td>
                    <td className="py-2.5 pl-3 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => openModifyModal(pos)}
                          className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                        >
                          <Edit3 className="h-3 w-3" />
                          SL/TP
                        </button>
                        <button
                          type="button"
                          onClick={() => setCloseTarget(pos)}
                          className="inline-flex items-center gap-1 rounded-md border border-red-500/35 bg-red-500/10 px-2 py-1 text-[11px] font-semibold text-red-700 hover:bg-red-500/20 dark:text-red-300"
                        >
                          <XCircle className="h-3 w-3" />
                          Close
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </PanelShell>

      {/* Bottom Split: Manual Trade Override + Upcoming News Calendar */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        {/* Manual Trade Override Panel (5 cols) */}
        <PanelShell
          className="xl:col-span-5"
          title="Manual Trade Override"
          subtitle="Submit an operator-authorized market order directly via FastAPI"
          isLoading={false}
          error={null}
          isEmpty={false}
        >
          <form onSubmit={handleManualSubmitRequest} className="space-y-3.5">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Pair
                </label>
                <select
                  value={manualPair}
                  onChange={(e) => setManualPair(e.target.value as ForexPair)}
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-2 font-mono text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                >
                  {availablePairs.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Direction
                </label>
                <div className="grid grid-cols-2 gap-1.5">
                  {(['BUY', 'SELL'] as TradeDirection[]).map((dir) => (
                    <button
                      key={dir}
                      type="button"
                      onClick={() => setManualDir(dir)}
                      className={`rounded-lg border py-2 font-mono text-xs font-bold transition-colors ${
                        manualDir === dir
                          ? dir === 'BUY'
                            ? 'border-emerald-500 bg-emerald-600/20 text-emerald-700 dark:text-emerald-300'
                            : 'border-red-500 bg-red-600/20 text-red-700 dark:text-red-300'
                          : 'border-slate-300 bg-slate-50 text-slate-500 dark:border-slate-700 dark:bg-[#0B0F17] dark:text-slate-400'
                      }`}
                    >
                      {dir}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Lots
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={manualLots}
                  onChange={(e) => setManualLots(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-2 font-mono text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Stop Loss
                </label>
                <input
                  type="number"
                  step="any"
                  required
                  value={manualSl}
                  onChange={(e) => setManualSl(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-2 font-mono text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Take Profit
                </label>
                <input
                  type="number"
                  step="any"
                  required
                  value={manualTp}
                  onChange={(e) => setManualTp(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-2 font-mono text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                Operator Note (Optional)
              </label>
              <input
                type="text"
                value={manualComment}
                onChange={(e) => setManualComment(e.target.value)}
                placeholder="Reason for manual intervention..."
                className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
              />
            </div>

            {manualFeedback && (
              <p className="text-xs text-emerald-600 dark:text-emerald-400">{manualFeedback}</p>
            )}

            <button
              type="submit"
              className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-blue-500 transition-colors"
            >
              <Send className="h-3.5 w-3.5" />
              Review &amp; Submit Manual Order
            </button>
          </form>
        </PanelShell>

        {/* Upcoming News Calendar Panel (7 cols) */}
        <PanelShell
          className="xl:col-span-7"
          title="Upcoming Economic News Calendar"
          subtitle={
            newsFilter?.enabled
              ? `News blackout active: ${newsFilter.minutesBefore}m before / ${newsFilter.minutesAfter}m after High-Impact events`
              : 'News blackout filter is currently disabled (configure in Risk & Safety)'
          }
          isLoading={newsLoading}
          error={newsError}
          isEmpty={newsEvents.length === 0}
          emptyTitle="No upcoming scheduled releases"
          emptyDescription="Economic calendar events will appear here when synced."
          onRetry={fetchNews}
          skeletonRows={4}
          headerRight={
            <CalendarClock className="h-4 w-4 text-slate-400" />
          }
        >
          <div className="space-y-2.5">
            {newsEvents.map((ev) => (
              <div
                key={ev.id}
                className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800/80 dark:bg-[#0B0F17] p-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded border px-1.5 py-0.5 font-mono text-[10px] font-bold uppercase ${
                        ev.impact === 'High'
                          ? 'border-red-500/40 bg-red-500/15 text-red-700 dark:text-red-300'
                          : 'border-amber-500/40 bg-amber-500/15 text-amber-700 dark:text-amber-300'
                      }`}
                    >
                      {ev.impact}
                    </span>
                    <span className="font-mono text-xs font-bold text-slate-900 dark:text-slate-100">
                      {ev.currency}
                    </span>
                    <span className="text-xs font-medium text-slate-800 dark:text-slate-200">
                      {ev.title}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500 dark:text-slate-400">
                    <span className="font-mono">{formatDateTime(ev.timestamp)}</span>
                    <span>·</span>
                    <span className="font-mono">Pairs: {ev.affectedPairs.join(', ')}</span>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-[11px] font-mono tabular-nums text-slate-600 dark:text-slate-300 shrink-0">
                  {ev.forecast && (
                    <div>
                      <span className="text-slate-400">Fcst </span>
                      <span className="font-semibold">{ev.forecast}</span>
                    </div>
                  )}
                  {ev.previous && (
                    <div>
                      <span className="text-slate-400">Prev </span>
                      <span>{ev.previous}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </PanelShell>
      </div>

      {/* Modify SL/TP Input Modal */}
      {modifyTarget && (
        <div
          className="fixed inset-0 z-40 flex items-center justify-center bg-black/55 dark:bg-black/70 p-4 backdrop-blur-xs"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-[#111824] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Modify SL / TP · {modifyTarget.pair} ({modifyTarget.direction})
              </h2>
              <button
                type="button"
                onClick={() => setModifyTarget(null)}
                className="rounded-md p-1 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                  Stop Loss
                </label>
                <input
                  type="number"
                  step="any"
                  value={modifySl}
                  onChange={(e) => setModifySl(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 font-mono text-xs text-slate-900 dark:text-slate-100"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                  Take Profit
                </label>
                <input
                  type="number"
                  step="any"
                  value={modifyTp}
                  onChange={(e) => setModifyTp(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 font-mono text-xs text-slate-900 dark:text-slate-100"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setModifyTarget(null)}
                className="rounded-lg border border-slate-300 bg-slate-100 px-3.5 py-2 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => setConfirmModifyOpen(true)}
                className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500"
              >
                Review Modification
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Dialogs */}
      <ConfirmDialog
        open={confirmOpen}
        title={isRunning ? 'Stop Trading Bot?' : 'Start Trading Bot?'}
        description={
          isRunning
            ? 'Stopping the bot halts new signal evaluation and order placement. Any currently open broker positions will remain open unless closed manually.'
            : `Starting the bot arms ${botStatus?.activeStrategiesCount ?? 0} active strategies to scan markets and submit orders to your connected broker account.`
        }
        confirmLabel={isRunning ? 'Stop Bot' : 'Start Bot'}
        variant={isRunning ? 'danger' : 'primary'}
        isProcessing={isTogglingBot}
        onConfirm={handleConfirmToggleBot}
        onCancel={() => setConfirmOpen(false)}
      />

      <ConfirmDialog
        open={Boolean(closeTarget)}
        title={`Manually Close ${closeTarget?.pair ?? ''} Position?`}
        description={
          closeTarget
            ? `Close ${closeTarget.direction} ${closeTarget.sizeLots.toFixed(2)} lots of ${closeTarget.pair} at current market price? Estimated floating P/L: ${formatDisplayAmount(closeTarget.floatingPnl, sourceCurrency, { signed: true })}.`
            : ''
        }
        confirmLabel="Close Position Now"
        variant="danger"
        isProcessing={closingPos}
        onConfirm={handleConfirmClosePosition}
        onCancel={() => setCloseTarget(null)}
      />

      <ConfirmDialog
        open={confirmModifyOpen}
        title={`Confirm SL / TP Update for ${modifyTarget?.pair ?? ''}?`}
        description={`Update Stop Loss to ${modifySl} and Take Profit to ${modifyTp} on broker ticket ${modifyTarget?.id ?? ''}?`}
        confirmLabel="Apply SL / TP"
        variant="primary"
        isProcessing={modifyingPos}
        onConfirm={handleConfirmModifySlTp}
        onCancel={() => setConfirmModifyOpen(false)}
      />

      <ConfirmDialog
        open={confirmManualOpen}
        title={`Submit Manual ${manualDir} Order on ${manualPair}?`}
        description={`Confirm manual ${manualDir} execution for ${manualLots} lots of ${manualPair} (SL: ${manualSl}, TP: ${manualTp}). This bypasses automated strategy grading.`}
        confirmLabel="Execute Manual Order"
        variant="danger"
        isProcessing={submittingManual}
        onConfirm={handleConfirmManualOrder}
        onCancel={() => setConfirmManualOpen(false)}
      />
    </div>
  );
}

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
}) {
  const toneClass =
    valueTone === 'profit'
      ? 'text-emerald-600 dark:text-emerald-400'
      : valueTone === 'loss'
      ? 'text-red-600 dark:text-red-400'
      : 'text-slate-900 dark:text-slate-100';

  return (
    <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-4">
      <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</p>
      <p className={`mt-1.5 font-mono text-lg font-bold tracking-tight tabular-nums ${toneClass}`}>
        {value}
      </p>
      <p className="mt-1 text-[11px] text-slate-500 truncate">{subtext}</p>
    </div>
  );
}
