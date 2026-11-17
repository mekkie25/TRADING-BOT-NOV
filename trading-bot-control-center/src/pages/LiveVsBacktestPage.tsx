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

export function LiveVsBacktestPage() {
  const { theme, formatDisplayAmount } = useAppContext();
  const isDark = theme === 'dark';

  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [comparison, setComparison] = useState<LiveVsBacktestComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const list = await api.getStrategies();
        setStrategies(list);
        if (list.length > 0) {
          setSelectedId(list[0].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load strategies');
        setLoading(false);
      }
    })();
  }, []);

  const loadComparison = useCallback(async (stratId: string) => {
    if (!stratId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getLiveVsBacktest(stratId);
      setComparison(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load comparison');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedId) {
      void loadComparison(selectedId);
    }
  }, [selectedId, loadComparison]);

  const metricsRows = comparison
    ? [
        {
          label: 'Win Rate',
          live: `${comparison.live.winRate.toFixed(1)}%`,
          bt: `${comparison.backtest.winRate.toFixed(1)}%`,
          delta: `${(comparison.live.winRate - comparison.backtest.winRate).toFixed(1)}%`,
          warn: Math.abs(comparison.live.winRate - comparison.backtest.winRate) > 8,
        },
        {
          label: 'Expectancy (R)',
          live: `${comparison.live.expectancyR >= 0 ? '+' : ''}${comparison.live.expectancyR.toFixed(2)}R`,
          bt: `${comparison.backtest.expectancyR >= 0 ? '+' : ''}${comparison.backtest.expectancyR.toFixed(2)}R`,
          delta: `${(comparison.live.expectancyR - comparison.backtest.expectancyR).toFixed(2)}R`,
          warn: comparison.live.expectancyR - comparison.backtest.expectancyR < -0.15,
        },
        {
          label: 'Max Drawdown',
          live: `-${comparison.live.maxDrawdownPercent.toFixed(1)}%`,
          bt: `-${comparison.backtest.maxDrawdownPercent.toFixed(1)}%`,
          delta: `${(comparison.live.maxDrawdownPercent - comparison.backtest.maxDrawdownPercent).toFixed(1)}%`,
          warn: comparison.live.maxDrawdownPercent > comparison.backtest.maxDrawdownPercent + 2,
        },
        {
          label: 'Average Trade P/L',
          live: formatDisplayAmount(comparison.live.avgTradePnl, 'ZAR', { signed: true }),
          bt: formatDisplayAmount(comparison.backtest.avgTradePnl, 'ZAR', { signed: true }),
          delta: formatDisplayAmount(
            comparison.live.avgTradePnl - comparison.backtest.avgTradePnl,
            'ZAR',
            { signed: true }
          ),
          warn: comparison.live.avgTradePnl < comparison.backtest.avgTradePnl * 0.65,
        },
        {
          label: 'Profit Factor',
          live: comparison.live.profitFactor.toFixed(2),
          bt: comparison.backtest.profitFactor.toFixed(2),
          delta: (comparison.live.profitFactor - comparison.backtest.profitFactor).toFixed(2),
          warn: comparison.live.profitFactor < comparison.backtest.profitFactor - 0.35,
        },
        {
          label: 'Sample Size (Trades)',
          live: String(comparison.live.totalTrades),
          bt: String(comparison.backtest.totalTrades),
          delta: '—',
          warn: false,
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Live vs Backtest Comparison
          </h1>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Detect execution drift by comparing realized live/paper trades against the strategy’s baseline simulation.
          </p>
        </div>

        <div className="min-w-[240px]">
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            aria-label="Select strategy to compare"
            className="w-full rounded-lg border border-slate-300 bg-white dark:border-slate-700 dark:bg-[#111824] px-3 py-2 text-xs font-medium text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
          >
            {strategies.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Divergence Alert Banner */}
      {comparison && !loading && (
        comparison.diverging ? (
          <div className="rounded-xl border border-red-500/45 bg-red-500/12 p-4 space-y-2">
            <div className="flex items-center gap-2 text-sm font-bold text-red-700 dark:text-red-300">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>Performance Divergence Warning — Review Execution Immediately</span>
            </div>
            <ul className="list-disc pl-5 text-xs text-red-800 dark:text-red-200 space-y-1">
              {comparison.divergenceReasons.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="flex items-center gap-2.5 rounded-xl border border-emerald-500/35 bg-emerald-500/10 px-4 py-3 text-xs font-medium text-emerald-800 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>
              Live execution metrics align within acceptable variance of the baseline backtest ({comparison.backtestName}).
            </span>
          </div>
        )
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        {/* Equity Return Curve Comparison */}
        <PanelShell
          className="xl:col-span-7"
          title="Cumulative Return Curve (%)"
          subtitle={comparison ? `${comparison.strategyName} vs ${comparison.backtestName}` : ''}
          isLoading={loading}
          error={error}
          isEmpty={!comparison || comparison.equityComparison.length === 0}
          onRetry={() => loadComparison(selectedId)}
          skeletonHeightClass="h-72"
        >
          {comparison && (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={comparison.equityComparison} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke={isDark ? '#1E293B' : '#E2E8F0'} strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="label"
                    stroke={isDark ? '#64748B' : '#94A3B8'}
                    tick={{ fill: isDark ? '#94A3B8' : '#475569', fontSize: 11 }}
                  />
                  <YAxis
                    stroke={isDark ? '#64748B' : '#94A3B8'}
                    tick={{ fill: isDark ? '#94A3B8' : '#475569', fontSize: 11 }}
                    tickFormatter={(v) => `${v}%`}
                    width={45}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: isDark ? '#0E141F' : '#FFFFFF',
                      borderColor: isDark ? '#334155' : '#CBD5E1',
                      color: isDark ? '#F1F5F9' : '#0F172A',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                    formatter={(val, name) => [`${Number(val ?? 0).toFixed(2)}%`, String(name ?? '')]}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Line
                    type="monotone"
                    dataKey="liveReturnPercent"
                    name="Live Return %"
                    stroke={comparison.diverging ? '#EF4444' : '#10B981'}
                    strokeWidth={2.5}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="backtestReturnPercent"
                    name="Backtest Expected %"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </PanelShell>

        {/* Key Metric Variance Table */}
        <PanelShell
          className="xl:col-span-5"
          title="Metric Comparison"
          subtitle="Live realized vs backtest benchmark"
          isLoading={loading}
          error={error}
          isEmpty={!comparison}
          onRetry={() => loadComparison(selectedId)}
          skeletonRows={6}
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                  <th className="py-2 pr-3 font-medium">Metric</th>
                  <th className="py-2 px-3 font-medium text-right">Live</th>
                  <th className="py-2 px-3 font-medium text-right">Backtest</th>
                  <th className="py-2 pl-3 font-medium text-right">Variance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
                {metricsRows.map((r) => (
                  <tr key={r.label}>
                    <td className="py-3 pr-3 font-medium text-slate-800 dark:text-slate-200">
                      {r.label}
                    </td>
                    <td
                      className={`py-3 px-3 text-right font-mono font-semibold tabular-nums ${
                        r.warn
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-slate-900 dark:text-slate-100'
                      }`}
                    >
                      {r.live}
                    </td>
                    <td className="py-3 px-3 text-right font-mono tabular-nums text-slate-600 dark:text-slate-300">
                      {r.bt}
                    </td>
                    <td
                      className={`py-3 pl-3 text-right font-mono tabular-nums ${
                        r.warn
                          ? 'text-red-600 dark:text-red-400 font-semibold'
                          : 'text-slate-500 dark:text-slate-400'
                      }`}
                    >
                      {r.delta}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </PanelShell>
      </div>
    </div>
  );
}
