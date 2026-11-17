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
): BreakdownBucket[] {
  const map = new Map<string, JournalTrade[]>();
  for (const t of trades) {
    const k = keyFn(t);
    const arr = map.get(k) ?? [];
    arr.push(t);
    map.set(k, arr);
  }
  return Array.from(map.entries()).map(([label, list]) => {
    const wins = list.filter((x) => x.pnl > 0).length;
    const pnl = list.reduce((s, x) => s + x.pnl, 0);
    const avgR = list.reduce((s, x) => s + x.rMultiple, 0) / list.length;
    return { label, trades: list.length, wins, pnl, avgR };
  });
}

export function JournalPage() {
  const { formatDisplayAmount, displayCurrency } = useAppContext();

  const [activeTab, setActiveTab] = useState<JournalTab>('ledger');
  const [filters, setFilters] = useState<JournalFilters>({
    startDate: '',
    endDate: '',
    pair: 'ALL',
    strategyId: 'ALL',
    setupGrade: '',
    outcome: 'all',
    tag: 'ALL',
    search: '',
  });

  const [pairs, setPairs] = useState<ForexPair[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [trades, setTrades] = useState<JournalTrade[]>([]);
  const [stats, setStats] = useState<JournalStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [selectedTrade, setSelectedTrade] = useState<JournalTrade | null>(null);

  // Calendar month state (defaults to latest trade month or Nov 2026)
  const [calendarMonth, setCalendarMonth] = useState(() => new Date('2026-11-01T00:00:00Z'));

  // Deposits / Withdrawals state
  const [capitalTxs, setCapitalTxs] = useState<CapitalTransaction[]>([]);
  const [capitalLoading, setCapitalLoading] = useState(true);
  const [txType, setTxType] = useState<'DEPOSIT' | 'WITHDRAWAL'>('DEPOSIT');
  const [txAmount, setTxAmount] = useState('10000');
  const [txDate, setTxDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [txRef, setTxRef] = useState('');
  const [txNotes, setTxNotes] = useState('');
  const [addingTx, setAddingTx] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const [p, s, caps] = await Promise.all([
          api.getAvailablePairs(),
          api.getStrategies(),
          api.getCapitalTransactions(),
        ]);
        setPairs(p);
        setStrategies(s);
        setCapitalTxs(caps);
      } catch {
        // Non-blocking
      } finally {
        setCapitalLoading(false);
      }
    })();
  }, []);

  const fetchTrades = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getJournalTrades(filters);
      setTrades(res.trades);
      setStats(res.stats);
      setPage(1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trade journal');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    void fetchTrades();
  }, [fetchTrades]);

  const handleResetFilters = () => {
    setFilters({
      startDate: '',
      endDate: '',
      pair: 'ALL',
      strategyId: 'ALL',
      setupGrade: '',
      outcome: 'all',
      tag: 'ALL',
      search: '',
    });
  };

  const handleSaveMeta = async (
    tradeId: string,
    patch: { notes?: string; tags?: string[]; screenshotUrl?: string }
  ) => {
    const updated = await api.updateTradeMeta(tradeId, patch);
    setTrades((prev) => prev.map((t) => (t.id === tradeId ? updated : t)));
    setSelectedTrade(updated);
  };

  const handleAddCapitalTx = async (e: FormEvent) => {
    e.preventDefault();
    const amt = Number(txAmount);
    if (!amt || amt <= 0) return;
    setAddingTx(true);
    try {
      const created = await api.addCapitalTransaction({
        date: txDate,
        type: txType,
        amount: amt,
        currency: 'ZAR',
        reference: txRef.trim() || `${txType.slice(0, 3)}-${Date.now().toString().slice(-5)}`,
        notes: txNotes.trim() || undefined,
      });
      setCapitalTxs((prev) => [created, ...prev]);
      setTxRef('');
      setTxNotes('');
    } finally {
      setAddingTx(false);
    }
  };

  const allTags = useMemo(() => {
    const set = new Set<string>();
    trades.forEach((t) => (t.tags ?? []).forEach((tg) => set.add(tg)));
    return Array.from(set).sort();
  }, [trades]);

  // Daily P/L map for calendar
  const dailyMap = useMemo(() => {
    const map = new Map<string, { pnl: number; count: number; wins: number }>();
    for (const t of trades) {
      const dayKey = t.closedAt.slice(0, 10);
      const cur = map.get(dayKey) ?? { pnl: 0, count: 0, wins: 0 };
      cur.pnl += t.pnl;
      cur.count += 1;
      if (t.pnl > 0) cur.wins += 1;
      map.set(dayKey, cur);
    }
    return map;
  }, [trades]);

  const calendarCells = useMemo(() => {
    const year = calendarMonth.getUTCFullYear();
    const month = calendarMonth.getUTCMonth();
    const firstDay = new Date(Date.UTC(year, month, 1));
    const daysInMonth = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
    const startWeekday = (firstDay.getUTCDay() + 6) % 7; // Mon=0..Sun=6
    const cells: Array<{ day: number | null; dateStr?: string }> = [];
    for (let i = 0; i < startWeekday; i += 1) cells.push({ day: null });
    for (let d = 1; d <= daysInMonth; d += 1) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      cells.push({ day: d, dateStr });
    }
    return cells;
  }, [calendarMonth]);

  const bySession = useMemo(
    () => buildBreakdown(trades, (t) => t.marketConditions.session),
    [trades]
  );
  const byDay = useMemo(() => {
    const names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    return buildBreakdown(trades, (t) => names[new Date(t.openedAt).getUTCDay()]);
  }, [trades]);
  const byPair = useMemo(() => buildBreakdown(trades, (t) => t.pair), [trades]);

  const capitalTotals = useMemo(() => {
    const deposits = capitalTxs
      .filter((c) => c.type === 'DEPOSIT')
      .reduce((s, c) => s + c.amount, 0);
    const withdrawals = capitalTxs
      .filter((c) => c.type === 'WITHDRAWAL')
      .reduce((s, c) => s + c.amount, 0);
    const netAdded = deposits - withdrawals;
    const pureTradingProfit = stats?.netProfit ?? 0;
    return {
      deposits,
      withdrawals,
      netAdded,
      pureTradingProfit,
      combinedEquityChange: netAdded + pureTradingProfit,
    };
  }, [capitalTxs, stats?.netProfit]);

  const totalPages = Math.max(1, Math.ceil(trades.length / PAGE_SIZE));
  const paginatedTrades = trades.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const sourceCurrency = trades[0]?.currency ?? 'ZAR';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Trade Journal
          </h1>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Complete trade ledger, daily P/L calendar, session/day/pair performance breakdown, and capital deposit tracking.
          </p>
        </div>

        <button
          type="button"
          onClick={() =>
            exportTradesToCsv(
              trades,
              `trading-bot-journal-${new Date().toISOString().slice(0, 10)}.csv`
            )
          }
          disabled={trades.length === 0 || loading}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 disabled:opacity-50 transition-colors whitespace-nowrap"
        >
          <Download className="h-3.5 w-3.5" />
          Export CSV ({trades.length})
        </button>
      </div>

      {/* View Switcher Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        {(
          [
            { id: 'ledger', label: 'Trades Ledger', icon: Table2 },
            { id: 'calendar', label: 'Daily P/L Calendar', icon: CalendarDays },
            { id: 'summary', label: 'Session / Day / Pair Summary', icon: BarChart3 },
            { id: 'capital', label: 'Deposits & Withdrawals', icon: Landmark },
          ] as const
        ).map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`inline-flex items-center gap-1.5 rounded-lg border px-3.5 py-2 text-xs font-semibold transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-blue-500 bg-blue-600/15 text-blue-700 dark:text-blue-200'
                  : 'border-slate-200 bg-white text-slate-600 hover:text-slate-900 dark:border-slate-800 dark:bg-[#111824] dark:text-slate-400 dark:hover:text-slate-200'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Summary Stats Strip */}
      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          <StatTile label="Total Trades" value={String(stats.totalTrades)} />
          <StatTile label="Wins" value={String(stats.wins)} tone="profit" />
          <StatTile label="Losses" value={String(stats.losses)} tone="loss" />
          <StatTile label="Win Rate" value={`${stats.winRate.toFixed(1)}%`} />
          <StatTile
            label={`Trading P/L (${displayCurrency})`}
            value={formatDisplayAmount(stats.netProfit, sourceCurrency, { signed: true })}
            tone={stats.netProfit >= 0 ? 'profit' : 'loss'}
          />
          <StatTile
            label="Expectancy (R)"
            value={`${stats.expectancyR >= 0 ? '+' : ''}${stats.expectancyR.toFixed(2)}R`}
            tone={stats.expectancyR >= 0 ? 'profit' : 'loss'}
          />
          <StatTile
            label="Profit Factor"
            value={stats.profitFactor.toFixed(2)}
            tone={stats.profitFactor >= 1.2 ? 'profit' : stats.profitFactor < 1 ? 'loss' : 'neutral'}
          />
        </div>
      )}

      {/* Filters Panel (shown for Ledger, Calendar & Summary) */}
      {activeTab !== 'capital' && (
        <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-8">
            <div className="lg:col-span-2">
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                Search
              </label>
              <div className="relative">
                <Search className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400 dark:text-slate-500" />
                <input
                  type="text"
                  value={filters.search ?? ''}
                  onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
                  placeholder="Pair, strategy, tag, notes..."
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700/80 dark:bg-[#0B0F17] py-1.5 pl-8 pr-3 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                From Date
              </label>
              <input
                type="date"
                value={filters.startDate ?? ''}
                onChange={(e) => setFilters((f) => ({ ...f, startDate: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700/80 dark:bg-[#0B0F17] px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                To Date
              </label>
              <input
                type="date"
                value={filters.endDate ?? ''}
                onChange={(e) => setFilters((f) => ({ ...f, endDate: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700/80 dark:bg-[#0B0F17] px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                Pair
              </label>
              <select
                value={filters.pair ?? 'ALL'}
                onChange={(e) => setFilters((f) => ({ ...f, pair: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700/80 dark:bg-[#0B0F17] px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
              >
                <option value="ALL">All Pairs</option>
                {pairs.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                Strategy
              </label>
              <select
                value={filters.strategyId ?? 'ALL'}
                onChange={(e) => setFilters((f) => ({ ...f, strategyId: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700/80 dark:bg-[#0B0F17] px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
              >
                <option value="ALL">All Strategies</option>
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                Tag
              </label>
              <select
                value={filters.tag ?? 'ALL'}
                onChange={(e) => setFilters((f) => ({ ...f, tag: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700/80 dark:bg-[#0B0F17] px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
              >
                <option value="ALL">All Tags</option>
                {allTags.map((tg) => (
                  <option key={tg} value={tg}>
                    #{tg}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Grade
                </label>
                <select
                  value={filters.setupGrade ?? ''}
                  onChange={(e) =>
                    setFilters((f) => ({
                      ...f,
                      setupGrade: e.target.value as SetupGrade | '',
                    }))
                  }
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700/80 dark:bg-[#0B0F17] px-2 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                >
                  <option value="">All</option>
                  {GRADES.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Outcome
                </label>
                <select
                  value={filters.outcome ?? 'all'}
                  onChange={(e) =>
                    setFilters((f) => ({
                      ...f,
                      outcome: e.target.value as 'all' | 'win' | 'loss',
                    }))
                  }
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700/80 dark:bg-[#0B0F17] px-2 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                >
                  <option value="all">All</option>
                  <option value="win">Wins</option>
                  <option value="loss">Losses</option>
                </select>
              </div>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between border-t border-slate-200 dark:border-slate-800/70 pt-3 text-xs text-slate-500 dark:text-slate-400">
            <span>
              Showing{' '}
              <span className="font-mono text-slate-800 dark:text-slate-200 tabular-nums">
                {trades.length}
              </span>{' '}
              matching trades · Click any row to edit notes, tags &amp; chart screenshot
            </span>
            <button
              type="button"
              onClick={handleResetFilters}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white transition-colors whitespace-nowrap"
            >
              <RotateCcw className="h-3 w-3" />
              Reset Filters
            </button>
          </div>
        </div>
      )}

      {/* TAB 1: Trades Ledger Table */}
      {activeTab === 'ledger' && (
        <PanelShell
          title="Executed Trades"
          subtitle={`Page ${page} of ${totalPages}`}
          isLoading={loading}
          error={error}
          isEmpty={trades.length === 0}
          emptyTitle="No matching trades found"
          emptyDescription="No historical trades match your active filter criteria."
          emptyActionLabel="Clear Filters"
          onEmptyAction={handleResetFilters}
          onRetry={fetchTrades}
          skeletonRows={8}
          headerRight={
            trades.length > PAGE_SIZE ? (
              <div className="flex items-center gap-2 text-xs">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 disabled:opacity-40 whitespace-nowrap"
                >
                  Prev
                </button>
                <span className="font-mono text-slate-500 dark:text-slate-400 tabular-nums">
                  {page} / {totalPages}
                </span>
                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 disabled:opacity-40 whitespace-nowrap"
                >
                  Next
                </button>
              </div>
            ) : undefined
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 whitespace-nowrap">
                  <th className="py-2.5 pr-3 font-medium">Date / Time</th>
                  <th className="py-2.5 px-2.5 font-medium">Pair</th>
                  <th className="py-2.5 px-2.5 font-medium">Dir</th>
                  <th className="py-2.5 px-2.5 font-medium">Strategy</th>
                  <th className="py-2.5 px-2.5 font-medium">Grade</th>
                  <th className="py-2.5 px-2.5 font-medium text-right">Entry</th>
                  <th className="py-2.5 px-2.5 font-medium text-right">Exit</th>
                  <th className="py-2.5 px-2.5 font-medium text-right">Size</th>
                  <th className="py-2.5 px-2.5 font-medium text-right">P/L</th>
                  <th className="py-2.5 px-2.5 font-medium text-right">R</th>
                  <th className="py-2.5 px-2.5 font-medium text-right">Dur</th>
                  <th className="py-2.5 pl-2.5 font-medium">Tags &amp; Conditions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
                {paginatedTrades.map((t) => {
                  const isWin = t.pnl > 0;
                  return (
                    <tr
                      key={t.id}
                      onClick={() => setSelectedTrade(t)}
                      className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/45 transition-colors"
                    >
                      <td className="py-2.5 pr-3 font-mono text-[11px] text-slate-600 dark:text-slate-300 tabular-nums whitespace-nowrap">
                        {formatDateTime(t.openedAt)}
                      </td>
                      <td className="py-2.5 px-2.5 font-mono font-semibold text-slate-900 dark:text-slate-100 whitespace-nowrap">
                        {t.pair}
                      </td>
                      <td className="py-2.5 px-2.5 whitespace-nowrap">
                        <span
                          className={`font-mono text-[11px] font-semibold ${
                            t.direction === 'BUY'
                              ? 'text-emerald-600 dark:text-emerald-400'
                              : 'text-red-600 dark:text-red-400'
                          }`}
                        >
                          {t.direction}
                        </span>
                      </td>
                      <td className="py-2.5 px-2.5 text-slate-700 dark:text-slate-300 max-w-[160px] truncate">
                        {t.strategyName}
                      </td>
                      <td className="py-2.5 px-2.5 whitespace-nowrap">
                        <GradeBadge grade={t.setupGrade} />
                      </td>
                      <td className="py-2.5 px-2.5 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200 whitespace-nowrap">
                        {formatPairPrice(t.entryPrice, t.pair)}
                      </td>
                      <td className="py-2.5 px-2.5 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200 whitespace-nowrap">
                        {formatPairPrice(t.exitPrice, t.pair)}
                      </td>
                      <td className="py-2.5 px-2.5 text-right font-mono tabular-nums text-slate-700 dark:text-slate-300 whitespace-nowrap">
                        {t.sizeLots.toFixed(2)}
                      </td>
                      <td
                        className={`py-2.5 px-2.5 text-right font-mono font-semibold tabular-nums whitespace-nowrap ${
                          isWin
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : 'text-red-600 dark:text-red-400'
                        }`}
                      >
                        {formatDisplayAmount(t.pnl, t.currency, { signed: true })}
                      </td>
                      <td
                        className={`py-2.5 px-2.5 text-right font-mono font-medium tabular-nums whitespace-nowrap ${
                          t.rMultiple >= 0
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : 'text-red-600 dark:text-red-400'
                        }`}
                      >
                        {t.rMultiple >= 0 ? '+' : ''}
                        {t.rMultiple.toFixed(2)}R
                      </td>
                      <td className="py-2.5 px-2.5 text-right font-mono text-slate-500 dark:text-slate-400 tabular-nums whitespace-nowrap">
                        {formatDuration(t.durationMinutes)}
                      </td>
                      <td className="py-2.5 pl-2.5 text-[11px] text-slate-500 dark:text-slate-400 whitespace-nowrap">
                        <span>{t.marketConditions.session}</span>
                        <span className="mx-1 text-slate-300 dark:text-slate-600">·</span>
                        <span>{t.marketConditions.volatilityRegime}</span>
                        {(t.tags ?? []).length > 0 && (
                          <>
                            <span className="mx-1 text-slate-300 dark:text-slate-600">·</span>
                            <span className="font-mono text-blue-600 dark:text-blue-400">
                              {(t.tags ?? []).map((tg) => `#${tg}`).join(' ')}
                            </span>
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </PanelShell>
      )}

      {/* TAB 2: Daily P/L Calendar View */}
      {activeTab === 'calendar' && (
        <PanelShell
          title="Daily P/L Calendar"
          subtitle="Realized closed-trade P/L aggregated by trading date"
          isLoading={loading}
          error={error}
          isEmpty={false}
          onRetry={fetchTrades}
          headerRight={
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() =>
                  setCalendarMonth(
                    (d) => new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() - 1, 1))
                  )
                }
                className="rounded-md border border-slate-300 bg-white p-1.5 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                aria-label="Previous month"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="min-w-[120px] text-center font-mono text-xs font-semibold text-slate-800 dark:text-slate-200">
                {calendarMonth.toLocaleString('en-GB', {
                  month: 'long',
                  year: 'numeric',
                  timeZone: 'UTC',
                })}
              </span>
              <button
                type="button"
                onClick={() =>
                  setCalendarMonth(
                    (d) => new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1))
                  )
                }
                className="rounded-md border border-slate-300 bg-white p-1.5 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                aria-label="Next month"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          }
        >
          <div className="grid grid-cols-7 gap-1.5 text-center text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-2">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => (
              <div key={d} className="py-1">
                {d}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1.5">
            {calendarCells.map((cell, idx) => {
              if (!cell.day || !cell.dateStr) {
                return <div key={`empty-${idx}`} className="h-20 rounded-lg bg-slate-50/40 dark:bg-[#0B0F17]/40" />;
              }
              const rec = dailyMap.get(cell.dateStr);
              const tone = !rec
                ? 'border-slate-200 bg-slate-50 dark:border-slate-800/80 dark:bg-[#0B0F17]'
                : rec.pnl >= 0
                ? 'border-emerald-500/35 bg-emerald-500/12'
                : 'border-red-500/35 bg-red-500/12';

              return (
                <div
                  key={cell.dateStr}
                  className={`h-20 rounded-lg border p-2 flex flex-col justify-between text-left ${tone}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                      {cell.day}
                    </span>
                    {rec && (
                      <span className="font-mono text-[10px] text-slate-500 dark:text-slate-400">
                        {rec.count}t
                      </span>
                    )}
                  </div>
                  {rec ? (
                    <div
                      className={`font-mono text-[11px] font-bold tabular-nums truncate ${
                        rec.pnl >= 0
                          ? 'text-emerald-700 dark:text-emerald-300'
                          : 'text-red-700 dark:text-red-300'
                      }`}
                    >
                      {formatDisplayAmount(rec.pnl, sourceCurrency, {
                        signed: true,
                        decimals: 0,
                      })}
                    </div>
                  ) : (
                    <span className="text-[10px] text-slate-400">—</span>
                  )}
                </div>
              );
            })}
          </div>
        </PanelShell>
      )}

      {/* TAB 3: Performance Summary by Session / Day / Pair */}
      {activeTab === 'summary' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <BreakdownCard
            title="By Trading Session"
            rows={bySession}
            formatAmount={(v) => formatDisplayAmount(v, sourceCurrency, { signed: true })}
          />
          <BreakdownCard
            title="By Day of Week"
            rows={byDay}
            formatAmount={(v) => formatDisplayAmount(v, sourceCurrency, { signed: true })}
          />
          <BreakdownCard
            title="By Currency Pair"
            rows={byPair}
            formatAmount={(v) => formatDisplayAmount(v, sourceCurrency, { signed: true })}
          />
        </div>
      )}

      {/* TAB 4: Deposits & Withdrawals Tracker */}
      {activeTab === 'capital' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile
              label="Total Deposits"
              value={formatDisplayAmount(capitalTotals.deposits, 'ZAR')}
            />
            <StatTile
              label="Total Withdrawals"
              value={formatDisplayAmount(capitalTotals.withdrawals, 'ZAR')}
            />
            <StatTile
              label="Pure Trading Net Profit"
              value={formatDisplayAmount(capitalTotals.pureTradingProfit, sourceCurrency, { signed: true })}
              tone={capitalTotals.pureTradingProfit >= 0 ? 'profit' : 'loss'}
            />
            <StatTile
              label="Net Capital + Trading Equity"
              value={formatDisplayAmount(capitalTotals.combinedEquityChange, 'ZAR')}
            />
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            <PanelShell
              className="lg:col-span-4"
              title="Record Deposit / Withdrawal"
              subtitle="Separate broker funding transfers from trading performance"
              isLoading={false}
              error={null}
              isEmpty={false}
            >
              <form onSubmit={handleAddCapitalTx} className="space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  {(['DEPOSIT', 'WITHDRAWAL'] as const).map((kind) => (
                    <button
                      key={kind}
                      type="button"
                      onClick={() => setTxType(kind)}
                      className={`rounded-lg border py-2 text-xs font-semibold transition-colors ${
                        txType === kind
                          ? kind === 'DEPOSIT'
                            ? 'border-emerald-500 bg-emerald-600/15 text-emerald-700 dark:text-emerald-300'
                            : 'border-amber-500 bg-amber-600/15 text-amber-700 dark:text-amber-300'
                          : 'border-slate-300 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-[#0B0F17] dark:text-slate-400'
                      }`}
                    >
                      {kind}
                    </button>
                  ))}
                </div>
                <div>
                  <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                    Amount (ZAR)
                  </label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={txAmount}
                    onChange={(e) => setTxAmount(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 font-mono text-xs text-slate-900 dark:text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                    Transfer Date
                  </label>
                  <input
                    type="date"
                    required
                    value={txDate}
                    onChange={(e) => setTxDate(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 font-mono text-xs text-slate-900 dark:text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                    Reference
                  </label>
                  <input
                    type="text"
                    value={txRef}
                    onChange={(e) => setTxRef(e.target.value)}
                    placeholder="EFT / Wire reference"
                    className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                    Notes
                  </label>
                  <input
                    type="text"
                    value={txNotes}
                    onChange={(e) => setTxNotes(e.target.value)}
                    placeholder="Optional memo"
                    className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100"
                  />
                </div>
                <button
                  type="submit"
                  disabled={addingTx}
                  className="w-full inline-flex items-center justify-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
                >
                  <Plus className="h-3.5 w-3.5" />
                  {addingTx ? 'Recording...' : 'Record Capital Transfer'}
                </button>
              </form>
            </PanelShell>

            <PanelShell
              className="lg:col-span-8"
              title="Capital Transfer History"
              subtitle="Verified deposits and withdrawals excluded from strategy expectancy"
              isLoading={capitalLoading}
              error={null}
              isEmpty={capitalTxs.length === 0}
              skeletonRows={4}
            >
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                      <th className="py-2 pr-3 font-medium">Date</th>
                      <th className="py-2 px-3 font-medium">Type</th>
                      <th className="py-2 px-3 font-medium">Reference</th>
                      <th className="py-2 px-3 font-medium">Notes</th>
                      <th className="py-2 pl-3 font-medium text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
                    {capitalTxs.map((tx) => (
                      <tr key={tx.id}>
                        <td className="py-2.5 pr-3 font-mono text-slate-600 dark:text-slate-300">
                          {tx.date}
                        </td>
                        <td
                          className={`py-2.5 px-3 font-mono font-semibold ${
                            tx.type === 'DEPOSIT'
                              ? 'text-emerald-600 dark:text-emerald-400'
                              : 'text-amber-600 dark:text-amber-400'
                          }`}
                        >
                          {tx.type}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-800 dark:text-slate-200">
                          {tx.reference}
                        </td>
                        <td className="py-2.5 px-3 text-slate-500 dark:text-slate-400">
                          {tx.notes || '—'}
                        </td>
                        <td className="py-2.5 pl-3 text-right font-mono font-semibold tabular-nums text-slate-900 dark:text-slate-100">
                          {tx.type === 'WITHDRAWAL' ? '-' : '+'}
                          {formatDisplayAmount(tx.amount, tx.currency)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </PanelShell>
          </div>
        </div>
      )}

      <JournalDrawer
        trade={selectedTrade}
        onClose={() => setSelectedTrade(null)}
        onSaveMeta={handleSaveMeta}
      />
    </div>
  );
}

function BreakdownCard({
  title,
  rows,
  formatAmount,
}: {
  title: string;
  rows: BreakdownBucket[];
  formatAmount: (amount: number) => string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-5 space-y-3">
      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
              <th className="py-2 pr-2 font-medium">Bucket</th>
              <th className="py-2 px-2 font-medium text-right">Trades</th>
              <th className="py-2 px-2 font-medium text-right">WR</th>
              <th className="py-2 pl-2 font-medium text-right">Net P/L</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
            {rows.map((r) => {
              const wr = r.trades > 0 ? (r.wins / r.trades) * 100 : 0;
              return (
                <tr key={r.label}>
                  <td className="py-2 pr-2 font-medium text-slate-800 dark:text-slate-200">
                    {r.label}
                  </td>
                  <td className="py-2 px-2 text-right font-mono tabular-nums text-slate-600 dark:text-slate-300">
                    {r.trades}
                  </td>
                  <td className="py-2 px-2 text-right font-mono tabular-nums text-slate-600 dark:text-slate-300">
                    {wr.toFixed(0)}%
                  </td>
                  <td
                    className={`py-2 pl-2 text-right font-mono font-semibold tabular-nums ${
                      r.pnl >= 0
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {formatAmount(r.pnl)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatTile({
  label,
  value,
  tone = 'neutral',
}: {
  label: string;
  value: string;
  tone?: 'neutral' | 'profit' | 'loss';
}) {
  const color =
    tone === 'profit'
      ? 'text-emerald-600 dark:text-emerald-400'
      : tone === 'loss'
      ? 'text-red-600 dark:text-red-400'
      : 'text-slate-900 dark:text-slate-100';

  return (
    <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] px-3.5 py-3">
      <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">{label}</p>
      <p className={`mt-1 font-mono text-base font-bold tabular-nums ${color}`}>
        {value}
      </p>
    </div>
  );
}
