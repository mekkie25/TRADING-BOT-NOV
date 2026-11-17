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

export function BacktesterPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [availablePairs, setAvailablePairs] = useState<ForexPair[]>([]);
  const [savedRuns, setSavedRuns] = useState<SavedBacktestSummary[]>([]);
  const [savedLoading, setSavedLoading] = useState(true);
  const [savedError, setSavedError] = useState<string | null>(null);

  const [activeResult, setActiveResult] = useState<BacktestResult | null>(null);
  const [resultLoading, setResultLoading] = useState(true);
  const [resultError, setResultError] = useState<string | null>(null);

  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [compareResults, setCompareResults] = useState<[BacktestResult, BacktestResult] | null>(null);
  const [comparing, setComparing] = useState(false);

  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  const [config, setConfig] = useState<BacktestConfig>({
    name: '',
    strategyId: '',
    pairs: ['EURUSD', 'GBPUSD', 'USDZAR'],
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
  });
  const [formError, setFormError] = useState<string | null>(null);

  const [job, setJob] = useState<BacktestJobStatus | null>(null);
  const pollTimerRef = useRef<number | null>(null);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  const loadInitialData = useCallback(async () => {
    setSavedLoading(true);
    setSavedError(null);
    setResultLoading(true);
    setResultError(null);
    try {
      const [strats, pairs, saved] = await Promise.all([
        api.getStrategies(),
        api.getAvailablePairs(),
        api.getSavedBacktests(),
      ]);
      setStrategies(strats);
      setAvailablePairs(pairs);
      setSavedRuns(saved);

      if (strats.length > 0) {
        setConfig((prev) => ({
          ...prev,
          strategyId: prev.strategyId || strats[0].id,
        }));
      }

      if (saved.length > 0) {
        const firstResult = await api.getBacktestResult(saved[0].id);
        setActiveResult(firstResult);
      } else {
        setActiveResult(null);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load backtester data';
      setSavedError(msg);
      setResultError(msg);
    } finally {
      setSavedLoading(false);
      setResultLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadInitialData();
  }, [loadInitialData]);

  const handleOpenSaved = async (id: string) => {
    setCompareResults(null);
    setResultLoading(true);
    setResultError(null);
    try {
      const res = await api.getBacktestResult(id);
      setActiveResult(res);
    } catch (err) {
      setResultError(err instanceof Error ? err.message : 'Failed to load backtest result');
    } finally {
      setResultLoading(false);
    }
  };

  const handleToggleCompareSelection = (id: string) => {
    setCompareIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
  };

  const handleCompareSelected = async () => {
    if (compareIds.length !== 2) return;
    setComparing(true);
    try {
      const [r1, r2] = await Promise.all([
        api.getBacktestResult(compareIds[0]),
        api.getBacktestResult(compareIds[1]),
      ]);
      setCompareResults([r1, r2]);
    } catch (err) {
      setResultError(err instanceof Error ? err.message : 'Failed to compare backtests');
    } finally {
      setComparing(false);
    }
  };

  const handleDeleteBacktest = async () => {
    if (!deleteTargetId) return;
    try {
      await api.deleteBacktest(deleteTargetId);
      setSavedRuns((prev) => prev.filter((r) => r.id !== deleteTargetId));
      setCompareIds((prev) => prev.filter((x) => x !== deleteTargetId));
      if (activeResult?.id === deleteTargetId) {
        setActiveResult(null);
      }
    } finally {
      setDeleteTargetId(null);
    }
  };

  const togglePair = (pair: ForexPair) => {
    setConfig((prev) => {
      const exists = prev.pairs.includes(pair);
      const next = exists
        ? prev.pairs.filter((p) => p !== pair)
        : [...prev.pairs, pair];
      return { ...prev, pairs: next };
    });
  };

  const handleRunBacktest = async () => {
    setFormError(null);
    if (!config.strategyId) {
      setFormError('Please select a strategy.');
      return;
    }
    if (config.pairs.length === 0) {
      setFormError('Select at least one forex pair.');
      return;
    }
    if (!Number.isFinite(config.startingBalance) || config.startingBalance < 100) {
      setFormError('Starting balance must be at least 100.');
      return;
    }

    stopPolling();
    try {
      const initialJob = await api.startBacktest(config);
      setJob(initialJob);

      pollTimerRef.current = window.setInterval(async () => {
        try {
          const updated = await api.getBacktestJobStatus(initialJob.jobId);
          setJob(updated);
          if (updated.status === 'completed' && updated.resultId) {
            stopPolling();
            const [res, saved] = await Promise.all([
              api.getBacktestResult(updated.resultId),
              api.getSavedBacktests(),
            ]);
            setActiveResult(res);
            setSavedRuns(saved);
            setCompareResults(null);
          } else if (updated.status === 'cancelled' || updated.status === 'failed') {
            stopPolling();
          }
        } catch (err) {
          stopPolling();
          setFormError(err instanceof Error ? err.message : 'Backtest polling error');
        }
      }, 450);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to start backtest');
    }
  };

  const handleCancelBacktest = async () => {
    if (!job) return;
    stopPolling();
    try {
      const cancelled = await api.cancelBacktestJob(job.jobId);
      setJob(cancelled);
    } catch {
      setJob(null);
    }
  };

  const isRunning = job?.status === 'running' || job?.status === 'queued';

  const inputClass =
    'w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700/80 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Strategy Backtester
          </h1>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Configure historical simulation parameters, execution costs, and analyze multi-dimensional robustness.
          </p>
        </div>

        <div className="inline-flex items-center gap-2 rounded-lg border border-blue-500/30 bg-blue-500/10 px-3.5 py-2 text-xs font-medium text-blue-700 dark:text-blue-200">
          <ShieldCheck className="h-4 w-4 text-blue-600 dark:text-blue-400 shrink-0" />
          <span>Simulation must never use future data.</span>
        </div>
      </div>

      {/* Top Grid: Configuration (8 cols) + Saved Runs (4 cols) */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        {/* Configuration Panel */}
        <section className="xl:col-span-8 rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-5 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Simulation Configuration
            </h2>
            <span className="text-[11px] text-slate-500 dark:text-slate-400">
              Executed in Python FastAPI engine (strict bar-by-bar causal evaluation)
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {/* Strategy */}
            <div className="sm:col-span-2 lg:col-span-1">
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                Strategy
              </label>
              <select
                value={config.strategyId}
                onChange={(e) => setConfig((c) => ({ ...c, strategyId: e.target.value }))}
                className={inputClass}
              >
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Run Label */}
            <div className="sm:col-span-2 lg:col-span-2">
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                Run Name (optional)
              </label>
              <input
                type="text"
                value={config.name ?? ''}
                onChange={(e) => setConfig((c) => ({ ...c, name: e.target.value }))}
                placeholder="e.g. London Breakout · 2Y ZAR Stress Test"
                className={`${inputClass} placeholder:text-slate-400 dark:placeholder:text-slate-500`}
              />
            </div>

            {/* Pairs Multi-select */}
            <div className="sm:col-span-2 lg:col-span-3">
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1.5">
                Pairs ({config.pairs.length} selected)
              </label>
              <div className="flex flex-wrap gap-2">
                {availablePairs.map((pair) => {
                  const selected = config.pairs.includes(pair);
                  return (
                    <button
                      key={pair}
                      type="button"
                      onClick={() => togglePair(pair)}
                      className={`rounded-md border px-3 py-1.5 font-mono text-xs font-medium transition-colors whitespace-nowrap ${
                        selected
                          ? 'border-blue-500 bg-blue-600/15 text-blue-700 dark:bg-blue-600/20 dark:text-blue-200'
                          : 'border-slate-300 bg-slate-50 text-slate-600 hover:text-slate-900 dark:border-slate-700/80 dark:bg-[#0B0F17] dark:text-slate-400 dark:hover:text-slate-200'
                      }`}
                    >
                      {pair}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Timeframe */}
            <div>
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                Timeframe
              </label>
              <select
                value={config.timeframe}
                onChange={(e) =>
                  setConfig((c) => ({ ...c, timeframe: e.target.value as Timeframe }))
                }
                className={inputClass}
              >
                {TIMEFRAMES.map((tf) => (
                  <option key={tf} value={tf}>
                    {tf}
                  </option>
                ))}
              </select>
            </div>

            {/* History Length */}
            <div>
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                History Length
              </label>
              <select
                value={config.historyLength}
                onChange={(e) =>
                  setConfig((c) => ({
                    ...c,
                    historyLength: e.target.value as HistoryLength,
                  }))
                }
                className={inputClass}
              >
                {HISTORY_LENGTHS.map((hl) => (
                  <option key={hl} value={hl}>
                    {hl}
                  </option>
                ))}
              </select>
            </div>

            {/* Broker / Account Type */}
            <div>
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                Broker / Account Type
              </label>
              <select
                value={config.brokerAccountType}
                onChange={(e) =>
                  setConfig((c) => ({
                    ...c,
                    brokerAccountType: e.target.value as BrokerAccountType,
                  }))
                }
                className={inputClass}
              >
                {ACCOUNT_TYPES.map((at) => (
                  <option key={at} value={at}>
                    {at}
                  </option>
                ))}
              </select>
            </div>

            {/* Starting Balance + Currency */}
            <div>
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                Starting Balance (min 100)
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  min={100}
                  step={100}
                  value={config.startingBalance}
                  onChange={(e) =>
                    setConfig((c) => ({
                      ...c,
                      startingBalance: Number(e.target.value),
                    }))
                  }
                  className={`${inputClass} font-mono`}
                />
                <select
                  value={config.currency}
                  onChange={(e) =>
                    setConfig((c) => ({
                      ...c,
                      currency: e.target.value as CurrencyCode,
                    }))
                  }
                  aria-label="Account currency"
                  className="rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700/80 dark:bg-[#0B0F17] px-2.5 py-2 font-mono text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                >
                  {CURRENCIES.map((cur) => (
                    <option key={cur} value={cur}>
                      {cur}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Leverage */}
            <div>
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                Leverage
              </label>
              <select
                value={config.leverage}
                onChange={(e) =>
                  setConfig((c) => ({ ...c, leverage: Number(e.target.value) }))
                }
                className={`${inputClass} font-mono`}
              >
                {LEVERAGES.map((lev) => (
                  <option key={lev} value={lev}>
                    1:{lev}
                  </option>
                ))}
              </select>
            </div>

            {/* Risk per trade % */}
            <div>
              <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                Risk Per Trade (%)
              </label>
              <input
                type="number"
                min={0.1}
                max={10}
                step={0.1}
                value={config.riskPerTradePercent}
                onChange={(e) =>
                  setConfig((c) => ({
                    ...c,
                    riskPerTradePercent: Number(e.target.value),
                  }))
                }
                className={`${inputClass} font-mono`}
              />
            </div>
          </div>

          {/* Execution Cost Settings */}
          <div className="border-t border-slate-200 dark:border-slate-800/80 pt-4">
            <p className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-3">
              Transaction Cost Assumptions
            </p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div>
                <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                  Spread (pips)
                </label>
                <input
                  type="number"
                  min={0}
                  step={0.1}
                  value={config.costs.spreadPips}
                  onChange={(e) =>
                    setConfig((c) => ({
                      ...c,
                      costs: { ...c.costs, spreadPips: Number(e.target.value) },
                    }))
                  }
                  className={`${inputClass} font-mono py-1.5 px-2.5`}
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                  Commission / Lot ({config.currency})
                </label>
                <input
                  type="number"
                  min={0}
                  step={5}
                  value={config.costs.commissionPerLot}
                  onChange={(e) =>
                    setConfig((c) => ({
                      ...c,
                      costs: {
                        ...c.costs,
                        commissionPerLot: Number(e.target.value),
                      },
                    }))
                  }
                  className={`${inputClass} font-mono py-1.5 px-2.5`}
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                  Slippage (pips)
                </label>
                <input
                  type="number"
                  min={0}
                  step={0.05}
                  value={config.costs.slippagePips}
                  onChange={(e) =>
                    setConfig((c) => ({
                      ...c,
                      costs: { ...c.costs, slippagePips: Number(e.target.value) },
                    }))
                  }
                  className={`${inputClass} font-mono py-1.5 px-2.5`}
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                  Swap / Night ({config.currency})
                </label>
                <input
                  type="number"
                  step={5}
                  value={config.costs.swapPerNight}
                  onChange={(e) =>
                    setConfig((c) => ({
                      ...c,
                      costs: { ...c.costs, swapPerNight: Number(e.target.value) },
                    }))
                  }
                  className={`${inputClass} font-mono py-1.5 px-2.5`}
                />
              </div>
            </div>
          </div>

          {formError && (
            <p className="text-xs text-red-600 dark:text-red-400">{formError}</p>
          )}

          {/* Action & Progress Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 dark:border-slate-800/80 pt-4">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleRunBacktest}
                disabled={isRunning}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50 transition-colors whitespace-nowrap"
              >
                <Play className="h-3.5 w-3.5" />
                {isRunning ? 'Simulation Running...' : 'Run Backtest'}
              </button>

              {isRunning && (
                <button
                  type="button"
                  onClick={handleCancelBacktest}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-red-500/40 bg-red-500/15 px-3.5 py-2.5 text-xs font-medium text-red-700 dark:text-red-300 hover:bg-red-500/25 transition-colors whitespace-nowrap"
                >
                  <Square className="h-3.5 w-3.5" />
                  Cancel
                </button>
              )}
            </div>

            {job && (
              <div className="flex-1 min-w-[240px] max-w-md space-y-1.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-600 dark:text-slate-300 truncate">{job.currentStep}</span>
                  <span className="font-mono text-slate-800 dark:text-slate-200 tabular-nums ml-2">
                    {job.progressPercent}%
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                  <div
                    className={`h-full transition-all duration-300 ${
                      job.status === 'cancelled'
                        ? 'bg-amber-500'
                        : job.status === 'completed'
                        ? 'bg-emerald-500'
                        : 'bg-blue-500'
                    }`}
                    style={{ width: `${job.progressPercent}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Saved Backtests List (4 cols) */}
        <PanelShell
          className="xl:col-span-4"
          title="Saved Backtests"
          subtitle="Reopen or select 2 to compare"
          isLoading={savedLoading}
          error={savedError}
          isEmpty={savedRuns.length === 0}
          emptyTitle="No saved backtests"
          emptyDescription="Run a simulation to store results for reopening and side-by-side comparison."
          onRetry={loadInitialData}
          skeletonRows={4}
          headerRight={
            compareIds.length === 2 ? (
              <button
                type="button"
                onClick={handleCompareSelected}
                disabled={comparing}
                className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500 whitespace-nowrap"
              >
                <Columns2 className="h-3.5 w-3.5" />
                {comparing ? 'Loading...' : 'Compare (2)'}
              </button>
            ) : (
              <span className="text-[11px] text-slate-500">
                {compareIds.length}/2 selected
              </span>
            )
          }
        >
          <div className="max-h-[420px] overflow-y-auto space-y-2.5 pr-1">
            {savedRuns.map((run) => {
              const isSelected = activeResult?.id === run.id && !compareResults;
              const isChecked = compareIds.includes(run.id);
              return (
                <div
                  key={run.id}
                  className={`rounded-lg border p-3 transition-colors ${
                    isSelected
                      ? 'border-blue-500/50 bg-blue-500/10'
                      : 'border-slate-200 bg-slate-50 hover:border-slate-300 dark:border-slate-800 dark:bg-[#0B0F17] dark:hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2.5 min-w-0">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleToggleCompareSelection(run.id)}
                        aria-label={`Select ${run.name} for comparison`}
                        className="mt-1 rounded border-slate-400 dark:border-slate-600 bg-white dark:bg-slate-900 text-blue-600"
                      />
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate">
                          {run.name}
                        </p>
                        <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                          {run.timeframe} · {run.historyLength} · {formatDateTime(run.createdAt)}
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setDeleteTargetId(run.id)}
                      className="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-red-600 dark:text-slate-500 dark:hover:bg-slate-800 dark:hover:text-red-400 transition-colors"
                      aria-label={`Delete ${run.name}`}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  <div className="mt-2.5 flex items-center justify-between border-t border-slate-200 dark:border-slate-800/70 pt-2 text-[11px]">
                    <div className="flex items-center gap-3 font-mono tabular-nums">
                      <span
                        className={
                          run.netProfit >= 0
                            ? 'text-emerald-600 dark:text-emerald-400 font-semibold'
                            : 'text-red-600 dark:text-red-400 font-semibold'
                        }
                      >
                        {run.netReturnPercent >= 0 ? '+' : ''}
                        {run.netReturnPercent.toFixed(1)}%
                      </span>
                      <span className="text-slate-500 dark:text-slate-400">WR {run.winRate.toFixed(1)}%</span>
                      <span className="text-slate-500 dark:text-slate-400">PF {run.profitFactor.toFixed(2)}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleOpenSaved(run.id)}
                      className="inline-flex items-center gap-1 font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300 whitespace-nowrap"
                    >
                      <FolderOpen className="h-3 w-3" />
                      Open
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </PanelShell>
      </div>

      {/* Side-by-Side Comparison View OR Active Single Backtest Results */}
      {compareResults ? (
        <ComparisonPanel
          runs={compareResults}
          onClose={() => setCompareResults(null)}
        />
      ) : (
        <PanelShell
          title="Simulation Results"
          subtitle="Detailed analytics across performance, market conditions, SL/TP grid, MAE/MFE, grades, and robustness"
          isLoading={resultLoading}
          error={resultError}
          isEmpty={!activeResult}
          emptyTitle="No backtest result loaded"
          emptyDescription="Run a new backtest above or select a saved simulation from the Saved Backtests panel."
          onRetry={loadInitialData}
          skeletonHeightClass="h-96"
        >
          {activeResult && <BacktestResultsView result={activeResult} />}
        </PanelShell>
      )}

      <ConfirmDialog
        open={Boolean(deleteTargetId)}
        title="Delete Saved Backtest?"
        description="This removes the saved simulation snapshot from your history. It does not affect live trades or strategies."
        confirmLabel="Delete"
        variant="danger"
        onConfirm={handleDeleteBacktest}
        onCancel={() => setDeleteTargetId(null)}
      />
    </div>
  );
}

function ComparisonPanel({
  runs,
  onClose,
}: {
  runs: [BacktestResult, BacktestResult];
  onClose: () => void;
}) {
  const { theme } = useAppContext();
  const isDark = theme === 'dark';
  const [a, b] = runs;

  const maxLen = Math.max(a.overview.equityCurve.length, b.overview.equityCurve.length);
  const chartData = Array.from({ length: maxLen }).map((_, i) => {
    const ptA = a.overview.equityCurve[Math.min(i, a.overview.equityCurve.length - 1)];
    const ptB = b.overview.equityCurve[Math.min(i, b.overview.equityCurve.length - 1)];
    const retA =
      ((ptA.equity - a.config.startingBalance) / a.config.startingBalance) * 100;
    const retB =
      ((ptB.equity - b.config.startingBalance) / b.config.startingBalance) * 100;
    return {
      step: i,
      date: ptA.date,
      runA: Math.round(retA * 100) / 100,
      runB: Math.round(retB * 100) / 100,
    };
  });

  const rows: Array<{
    metric: string;
    valA: string;
    valB: string;
  }> = [
    { metric: 'Strategy', valA: a.strategyName, valB: b.strategyName },
    { metric: 'Pairs', valA: a.config.pairs.join(', '), valB: b.config.pairs.join(', ') },
    { metric: 'Timeframe / History', valA: `${a.config.timeframe} · ${a.config.historyLength}`, valB: `${b.config.timeframe} · ${b.config.historyLength}` },
    {
      metric: 'Net Profit',
      valA: `${formatCurrency(a.overview.netProfit, a.config.currency, { signed: true })} (${a.overview.netReturnPercent.toFixed(1)}%)`,
      valB: `${formatCurrency(b.overview.netProfit, b.config.currency, { signed: true })} (${b.overview.netReturnPercent.toFixed(1)}%)`,
    },
    { metric: 'Win Rate', valA: `${a.overview.winRate.toFixed(1)}%`, valB: `${b.overview.winRate.toFixed(1)}%` },
    { metric: 'Expectancy (R)', valA: `${a.overview.expectancyR.toFixed(2)}R`, valB: `${b.overview.expectancyR.toFixed(2)}R` },
    { metric: 'Profit Factor', valA: a.overview.profitFactor.toFixed(2), valB: b.overview.profitFactor.toFixed(2) },
    { metric: 'Max Drawdown', valA: `-${a.overview.maxDrawdownPercent.toFixed(2)}%`, valB: `-${b.overview.maxDrawdownPercent.toFixed(2)}%` },
    { metric: 'Longest Losing Streak', valA: `${a.overview.longestLosingStreak}`, valB: `${b.overview.longestLosingStreak}` },
    { metric: 'Sharpe Ratio', valA: a.overview.sharpeRatio.toFixed(2), valB: b.overview.sharpeRatio.toFixed(2) },
  ];

  return (
    <section className="rounded-xl border border-blue-500/40 bg-white dark:bg-[#111824] p-5 space-y-6">
      <div className="flex items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-3">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
            Side-by-Side Backtest Comparison
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Comparing cumulative return (%) and statistical metrics across two saved runs.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
        >
          <X className="h-3.5 w-3.5" />
          Exit Comparison
        </button>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid stroke={isDark ? '#1E293B' : '#E2E8F0'} strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="date"
              stroke={isDark ? '#64748B' : '#94A3B8'}
              tick={{ fill: isDark ? '#94A3B8' : '#475569', fontSize: 11 }}
              minTickGap={24}
            />
            <YAxis
              stroke={isDark ? '#64748B' : '#94A3B8'}
              tick={{ fill: isDark ? '#94A3B8' : '#475569', fontSize: 11 }}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: isDark ? '#0E141F' : '#FFFFFF',
                borderColor: isDark ? '#334155' : '#CBD5E1',
                color: isDark ? '#F1F5F9' : '#0F172A',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              formatter={(v) => [`${Number(v ?? 0).toFixed(2)}%`]}
            />
            <Legend />
            <Line type="monotone" dataKey="runA" name={a.name} stroke="#10B981" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="runB" name={b.name} stroke="#3B82F6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
              <th className="py-2 pr-4 font-medium">Metric</th>
              <th className="py-2 px-4 font-medium text-emerald-700 dark:text-emerald-300">{a.name}</th>
              <th className="py-2 pl-4 font-medium text-blue-700 dark:text-blue-300">{b.name}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
            {rows.map((r) => (
              <tr key={r.metric}>
                <td className="py-2.5 pr-4 font-medium text-slate-500 dark:text-slate-400">{r.metric}</td>
                <td className="py-2.5 px-4 font-mono tabular-nums text-slate-900 dark:text-slate-100">{r.valA}</td>
                <td className="py-2.5 pl-4 font-mono tabular-nums text-slate-900 dark:text-slate-100">{r.valB}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
