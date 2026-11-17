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

export function PortfolioPage() {
  const { theme, formatDisplayAmount } = useAppContext();
  const isDark = theme === 'dark';

  const [portfolio, setPortfolio] = useState<PortfolioExposureData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPortfolio = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getPortfolioExposure();
      setPortfolio(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load portfolio exposure');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPortfolio();
  }, [loadPortfolio]);

  const marginUsedPercent = portfolio && portfolio.accountEquity > 0
    ? Math.min(100, (portfolio.marginUsed / portfolio.accountEquity) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Portfolio &amp; Exposure
          </h1>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Net currency exposure, open-position correlation matrix, aggregate stop-loss risk %, and margin utilization.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void loadPortfolio()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors whitespace-nowrap"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Exposure
        </button>
      </div>

      {/* Top Risk & Margin Cards */}
      {portfolio && !loading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-4">
            <p className="text-xs text-slate-500 dark:text-slate-400">Total Open Risk (%)</p>
            <p
              className={`mt-1.5 font-mono text-lg font-bold tabular-nums ${
                portfolio.totalOpenRiskPercent > 4
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-amber-600 dark:text-amber-300'
              }`}
            >
              {portfolio.totalOpenRiskPercent.toFixed(2)}%
            </p>
            <p className="mt-1 text-[11px] font-mono text-slate-500">
              {formatDisplayAmount(portfolio.totalOpenRiskAmount, portfolio.currency)} at SL
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-4">
            <p className="text-xs text-slate-500 dark:text-slate-400">Margin Used</p>
            <p className="mt-1.5 font-mono text-lg font-bold text-slate-900 dark:text-slate-100 tabular-nums">
              {formatDisplayAmount(portfolio.marginUsed, portfolio.currency)}
            </p>
            <div className="mt-2 h-1.5 w-full rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
              <div
                className="h-full rounded-full bg-blue-500"
                style={{ width: `${marginUsedPercent}%` }}
              />
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-4">
            <p className="text-xs text-slate-500 dark:text-slate-400">Free Margin</p>
            <p className="mt-1.5 font-mono text-lg font-bold text-emerald-600 dark:text-emerald-400 tabular-nums">
              {formatDisplayAmount(portfolio.freeMargin, portfolio.currency)}
            </p>
            <p className="mt-1 text-[11px] text-slate-500">
              {(100 - marginUsedPercent).toFixed(1)}% equity unencumbered
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-4">
            <p className="text-xs text-slate-500 dark:text-slate-400">Margin Level</p>
            <p className="mt-1.5 font-mono text-lg font-bold text-slate-900 dark:text-slate-100 tabular-nums">
              {portfolio.marginLevelPercent.toFixed(1)}%
            </p>
            <p className="mt-1 text-[11px] text-slate-500">Healthy (&gt; 300% threshold)</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        {/* Net Exposure by Currency */}
        <PanelShell
          className="xl:col-span-6"
          title="Net Exposure by Currency"
          subtitle="Percentage of account equity long (+) vs short (-)"
          isLoading={loading}
          error={error}
          isEmpty={!portfolio || portfolio.currencyExposures.length === 0}
          onRetry={loadPortfolio}
          skeletonHeightClass="h-72"
        >
          {portfolio && (
            <div className="space-y-4">
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={portfolio.currencyExposures}
                    margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid stroke={isDark ? '#1E293B' : '#E2E8F0'} strokeDasharray="3 3" vertical={false} />
                    <XAxis
                      dataKey="currency"
                      stroke={isDark ? '#64748B' : '#94A3B8'}
                      tick={{ fill: isDark ? '#94A3B8' : '#475569', fontSize: 11 }}
                    />
                    <YAxis
                      stroke={isDark ? '#64748B' : '#94A3B8'}
                      tick={{ fill: isDark ? '#94A3B8' : '#475569', fontSize: 11 }}
                      tickFormatter={(v) => `${v}%`}
                      width={44}
                    />
                    <ReferenceLine y={0} stroke={isDark ? '#475569' : '#94A3B8'} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: isDark ? '#0E141F' : '#FFFFFF',
                        borderColor: isDark ? '#334155' : '#CBD5E1',
                        color: isDark ? '#F1F5F9' : '#0F172A',
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                      formatter={(val) => [`${Number(val ?? 0).toFixed(1)}% of equity`, 'Net Exposure']}
                    />
                    <Bar dataKey="percentOfEquity" radius={[4, 4, 0, 0]}>
                      {portfolio.currencyExposures.map((entry) => (
                        <Cell
                          key={entry.currency}
                          fill={entry.percentOfEquity >= 0 ? '#10B981' : '#EF4444'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                      <th className="py-2 pr-3 font-medium">Currency</th>
                      <th className="py-2 px-3 font-medium">Bias</th>
                      <th className="py-2 px-3 font-medium text-right">Net Lots</th>
                      <th className="py-2 pl-3 font-medium text-right">Notional</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
                    {portfolio.currencyExposures.map((c) => (
                      <tr key={c.currency}>
                        <td className="py-2 pr-3 font-mono font-semibold text-slate-900 dark:text-slate-100">
                          {c.currency}
                        </td>
                        <td
                          className={`py-2 px-3 font-mono font-semibold ${
                            c.direction === 'LONG'
                              ? 'text-emerald-600 dark:text-emerald-400'
                              : c.direction === 'SHORT'
                              ? 'text-red-600 dark:text-red-400'
                              : 'text-slate-400'
                          }`}
                        >
                          {c.direction}
                        </td>
                        <td className="py-2 px-3 text-right font-mono tabular-nums text-slate-700 dark:text-slate-300">
                          {c.netLots >= 0 ? '+' : ''}
                          {c.netLots.toFixed(2)}
                        </td>
                        <td className="py-2 pl-3 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200">
                          {formatDisplayAmount(c.netNotionalZar, 'ZAR', { signed: true, decimals: 0 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </PanelShell>

        {/* Correlation Matrix Between Open Positions */}
        <PanelShell
          className="xl:col-span-6"
          title="Open Position Correlation Matrix"
          subtitle="Rolling 30-day return correlation between active pairs"
          isLoading={loading}
          error={error}
          isEmpty={!portfolio || portfolio.correlationMatrix.pairs.length === 0}
          emptyTitle="No correlated positions open"
          emptyDescription="Open 2 or more positions to inspect cross-pair correlation risk."
          onRetry={loadPortfolio}
          skeletonHeightClass="h-72"
        >
          {portfolio && (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full text-center text-xs font-mono">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                      <th className="py-2 pr-2 text-left">Pair</th>
                      {portfolio.correlationMatrix.pairs.map((p) => (
                        <th key={p} className="py-2 px-2">
                          {p}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
                    {portfolio.correlationMatrix.pairs.map((rowPair, rIdx) => (
                      <tr key={rowPair}>
                        <td className="py-3 pr-2 text-left font-semibold text-slate-900 dark:text-slate-100">
                          {rowPair}
                        </td>
                        {portfolio.correlationMatrix.matrix[rIdx].map((val, cIdx) => {
                          const abs = Math.abs(val);
                          const isDiag = rIdx === cIdx;
                          const cellBg = isDiag
                            ? 'bg-slate-200/70 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
                            : val > 0.6
                            ? 'bg-emerald-500/20 text-emerald-800 dark:text-emerald-200 font-semibold'
                            : val < -0.6
                            ? 'bg-red-500/20 text-red-800 dark:text-red-200 font-semibold'
                            : abs > 0.35
                            ? 'bg-amber-500/12 text-amber-800 dark:text-amber-200'
                            : 'bg-slate-50 text-slate-600 dark:bg-[#0B0F17] dark:text-slate-400';

                          return (
                            <td key={`${rIdx}-${cIdx}`} className="p-1.5">
                              <div className={`rounded-md py-2 px-2 tabular-nums ${cellBg}`}>
                                {val >= 0 && !isDiag ? '+' : ''}
                                {val.toFixed(2)}
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-3 text-xs text-slate-600 dark:text-slate-400">
                High positive correlation (&gt; +0.60) or inverse correlation (&lt; -0.60) amplifies effective directional exposure when both legs share USD risk.
              </div>
            </div>
          )}
        </PanelShell>
      </div>
    </div>
  );
}
