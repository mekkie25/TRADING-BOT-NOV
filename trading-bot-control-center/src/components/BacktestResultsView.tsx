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

export function BacktestResultsView({ result }: { result: BacktestResult }) {
  const { theme } = useAppContext();
  const isDark = theme === 'dark';

  const chartPalette = {
    grid: isDark ? '#1E293B' : '#E2E8F0',
    axisStroke: isDark ? '#64748B' : '#94A3B8',
    tickFill: isDark ? '#94A3B8' : '#475569',
    tooltipBg: isDark ? '#0E141F' : '#FFFFFF',
    tooltipBorder: isDark ? '#334155' : '#CBD5E1',
    tooltipText: isDark ? '#F1F5F9' : '#0F172A',
  };

  const [activeTab, setActiveTab] = useState<ResultsTab>('overview');
  const [conditionDim, setConditionDim] = useState<ConditionDimension>('byVolatility');
  const [heatmapMetric, setHeatmapMetric] = useState<'expectancyR' | 'netReturnPercent' | 'profitFactor'>('expectancyR');
  const [tradePage, setTradePage] = useState(1);

  const currency = result.config.currency;
  const ov = result.overview;

  return (
    <div className="space-y-5">
      {/* Result Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] px-5 py-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">{result.name}</h2>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            {result.strategyName} · {result.config.pairs.join(', ')} · {result.config.timeframe} · {result.config.historyLength} · Risk {result.config.riskPerTradePercent}%
          </p>
        </div>
        <div className="flex items-center gap-6 text-right">
          <div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Net Profit</p>
            <p
              className={`font-mono text-sm font-bold tabular-nums ${
                ov.netProfit >= 0
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              {formatCurrency(ov.netProfit, currency, { signed: true })} ({ov.netReturnPercent >= 0 ? '+' : ''}
              {ov.netReturnPercent.toFixed(1)}%)
            </p>
          </div>
          <div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Expectancy</p>
            <p
              className={`font-mono text-sm font-bold tabular-nums ${
                ov.expectancyR >= 0
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              {ov.expectancyR >= 0 ? '+' : ''}
              {ov.expectancyR.toFixed(2)}R
            </p>
          </div>
        </div>
      </div>

      {result.prototypeStatus === 'unverified' && (
        <div
          role="alert"
          className="flex gap-3 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-900 dark:text-amber-200"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <div>
            <p className="font-semibold">Prototype results — unverified; do not treat as proven performance.</p>
            {result.assumptions && (
              <ul className="mt-1 list-disc space-y-0.5 pl-4 text-xs">
                {result.assumptions.map((assumption) => <li key={assumption}>{assumption}</li>)}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="flex items-center gap-1 overflow-x-auto rounded-xl border border-slate-200 bg-slate-100 dark:border-slate-800/90 dark:bg-[#0B0F17] p-1.5">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setActiveTab(t.id)}
            className={`rounded-lg px-3.5 py-2 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              activeTab === t.id
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-white hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/70 dark:hover:text-slate-100'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Metrics Grid */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <MetricBox label="Wins / Losses" value={`${ov.wins} / ${ov.losses}`} />
            <MetricBox label="Win Rate" value={`${ov.winRate.toFixed(1)}%`} />
            <MetricBox
              label="Net Profit"
              value={formatCurrency(ov.netProfit, currency, { signed: true })}
              tone={ov.netProfit >= 0 ? 'profit' : 'loss'}
            />
            <MetricBox
              label="Expectancy"
              value={`${ov.expectancyR >= 0 ? '+' : ''}${ov.expectancyR.toFixed(2)}R`}
              tone={ov.expectancyR >= 0 ? 'profit' : 'loss'}
            />
            <MetricBox label="Profit Factor" value={ov.profitFactor.toFixed(2)} />
            <MetricBox label="Sharpe Ratio" value={ov.sharpeRatio.toFixed(2)} />
            <MetricBox
              label="Avg Win"
              value={formatCurrency(ov.avgWin, currency, { signed: true })}
              tone="profit"
            />
            <MetricBox
              label="Avg Loss"
              value={formatCurrency(ov.avgLoss, currency)}
              tone="loss"
            />
            <MetricBox
              label="Max Drawdown"
              value={`-${ov.maxDrawdownPercent.toFixed(2)}%`}
              tone="loss"
              subtext={formatCurrency(-ov.maxDrawdownAmount, currency)}
            />
            <MetricBox
              label="Longest Losing Streak"
              value={`${ov.longestLosingStreak} trades`}
            />
            <MetricBox label="Recovery Time" value={`${ov.recoveryTimeDays} days`} />
            <MetricBox
              label="Final Balance"
              value={formatCurrency(ov.finalBalance, currency)}
            />
          </div>

          {/* Equity Curve */}
          <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">
              Simulated Equity Curve
            </h3>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={ov.equityCurve} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
                  <defs>
                    <linearGradient id="btEqGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke={chartPalette.grid} strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" stroke={chartPalette.axisStroke} tick={{ fill: chartPalette.tickFill, fontSize: 11 }} minTickGap={24} />
                  <YAxis
                    stroke={chartPalette.axisStroke}
                    tick={{ fill: chartPalette.tickFill, fontSize: 11 }}
                    domain={['auto', 'auto']}
                    tickFormatter={(v) => `${(Number(v) / 1000).toFixed(0)}k`}
                    width={52}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: chartPalette.tooltipBg,
                      borderColor: chartPalette.tooltipBorder,
                      color: chartPalette.tooltipText,
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                    formatter={(val) => [formatCurrency(Number(val ?? 0), currency), 'Equity']}
                  />
                  <Area type="monotone" dataKey="equity" stroke="#10B981" strokeWidth={2} fill="url(#btEqGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Drawdown Curve */}
          <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">
              Underwater Drawdown (%)
            </h3>
            <div className="h-52 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={ov.equityCurve} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
                  <defs>
                    <linearGradient id="btDdGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#EF4444" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#EF4444" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke={chartPalette.grid} strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" stroke={chartPalette.axisStroke} tick={{ fill: chartPalette.tickFill, fontSize: 11 }} minTickGap={24} />
                  <YAxis
                    stroke={chartPalette.axisStroke}
                    tick={{ fill: chartPalette.tickFill, fontSize: 11 }}
                    tickFormatter={(v) => `${Number(v).toFixed(1)}%`}
                    width={52}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: chartPalette.tooltipBg,
                      borderColor: chartPalette.tooltipBorder,
                      color: chartPalette.tooltipText,
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                    formatter={(val) => [`${Number(val ?? 0).toFixed(2)}%`, 'Drawdown']}
                  />
                  <Area type="monotone" dataKey="drawdownPercent" stroke="#EF4444" strokeWidth={1.75} fill="url(#btDdGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'conditions' && (
        <MarketConditionsTab
          items={result.marketConditions[conditionDim]}
          dimension={conditionDim}
          onChangeDimension={setConditionDim}
          currency={currency}
          chartPalette={chartPalette}
        />
      )}

      {activeTab === 'sltp' && (
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  SL vs TP Optimization Heatmap (ATR Multiples)
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Rows: Stop-Loss ATR multiple · Columns: Take-Profit ATR multiple
                </p>
              </div>
              <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#111824] p-1">
                {(
                  [
                    { key: 'expectancyR', label: 'Expectancy (R)' },
                    { key: 'netReturnPercent', label: 'Return %' },
                    { key: 'profitFactor', label: 'Profit Factor' },
                  ] as const
                ).map((m) => (
                  <button
                    key={m.key}
                    type="button"
                    onClick={() => setHeatmapMetric(m.key)}
                    className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors whitespace-nowrap ${
                      heatmapMetric === m.key
                        ? 'bg-slate-200 text-slate-900 dark:bg-slate-800 dark:text-slate-100'
                        : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-xs">
                <thead>
                  <tr>
                    <th className="p-2 text-left font-medium text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                      SL \ TP
                    </th>
                    {result.slTpOptimizer.tpMultiples.map((tp) => (
                      <th
                        key={tp}
                        className="p-2 text-center font-mono font-semibold text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800"
                      >
                        {tp.toFixed(1)}x ATR
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.slTpOptimizer.slMultiples.map((sl) => (
                    <tr key={sl}>
                      <td className="p-2 font-mono font-semibold text-slate-700 dark:text-slate-300 border-r border-slate-200 dark:border-slate-800 whitespace-nowrap">
                        {sl.toFixed(2)}x ATR
                      </td>
                      {result.slTpOptimizer.tpMultiples.map((tp) => {
                        const cell = result.slTpOptimizer.cells.find(
                          (c) => c.slAtrMultiple === sl && c.tpAtrMultiple === tp
                        );
                        if (!cell) return <td key={tp} className="p-2" />;
                        const val = cell[heatmapMetric];
                        const isPositive =
                          heatmapMetric === 'profitFactor' ? val >= 1.0 : val >= 0;
                        const intensity =
                          heatmapMetric === 'expectancyR'
                            ? Math.min(isDark ? 0.65 : 0.38, Math.max(0.08, Math.abs(val) * 0.9))
                            : heatmapMetric === 'netReturnPercent'
                            ? Math.min(isDark ? 0.65 : 0.38, Math.max(0.08, Math.abs(val) / 80))
                            : Math.min(isDark ? 0.65 : 0.38, Math.max(0.08, Math.abs(val - 1) * 0.65));
                        const bgColor = isPositive
                          ? `rgba(16, 185, 129, ${intensity})`
                          : `rgba(239, 68, 68, ${intensity})`;

                        return (
                          <td
                            key={tp}
                            className="p-2.5 text-center font-mono tabular-nums border border-slate-200 dark:border-slate-900/80"
                            style={{ backgroundColor: bgColor }}
                            title={`SL ${sl}x / TP ${tp}x · WR ${cell.winRate}% · PF ${cell.profitFactor}`}
                          >
                            <div className="font-semibold text-slate-900 dark:text-slate-100">
                              {heatmapMetric === 'expectancyR'
                                ? `${val >= 0 ? '+' : ''}${val.toFixed(2)}R`
                                : heatmapMetric === 'netReturnPercent'
                                ? `${val >= 0 ? '+' : ''}${val.toFixed(1)}%`
                                : val.toFixed(2)}
                            </div>
                            <div className="text-[10px] text-slate-700 dark:text-slate-300/80">
                              WR {cell.winRate.toFixed(0)}%
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Optimal SL/TP by Volatility Level */}
          <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">
              Optimal SL / TP by Volatility Regime
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                    <th className="py-2 pr-4 font-medium">Volatility Level</th>
                    <th className="py-2 px-3 font-medium text-right">Best SL (ATR)</th>
                    <th className="py-2 px-3 font-medium text-right">Best TP (ATR)</th>
                    <th className="py-2 px-3 font-medium text-right">Expectancy (R)</th>
                    <th className="py-2 px-3 font-medium text-right">Win Rate</th>
                    <th className="py-2 px-3 font-medium text-right">Net Return</th>
                    <th className="py-2 pl-3 font-medium text-right">Trades</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
                  {result.slTpOptimizer.optimalByVolatility.map((row) => (
                    <tr key={row.volatilityRegime}>
                      <td className="py-2.5 pr-4 font-medium text-slate-900 dark:text-slate-100">
                        {row.volatilityRegime}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-700 dark:text-slate-200">
                        {row.bestSlAtr.toFixed(2)}x
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-700 dark:text-slate-200">
                        {row.bestTpAtr.toFixed(2)}x
                      </td>
                      <td
                        className={`py-2.5 px-3 text-right font-mono font-semibold tabular-nums ${
                          row.expectancyR >= 0
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : 'text-red-600 dark:text-red-400'
                        }`}
                      >
                        {row.expectancyR >= 0 ? '+' : ''}
                        {row.expectancyR.toFixed(2)}R
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-700 dark:text-slate-200">
                        {row.winRate.toFixed(1)}%
                      </td>
                      <td
                        className={`py-2.5 px-3 text-right font-mono font-semibold tabular-nums ${
                          row.netReturnPercent >= 0
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : 'text-red-600 dark:text-red-400'
                        }`}
                      >
                        {row.netReturnPercent >= 0 ? '+' : ''}
                        {row.netReturnPercent.toFixed(1)}%
                      </td>
                      <td className="py-2.5 pl-3 text-right font-mono tabular-nums text-slate-600 dark:text-slate-300">
                        <span className="inline-flex items-center gap-1.5">
                          {row.trades < 20 && (
                            <AlertTriangle
                              className="h-3.5 w-3.5 text-amber-500 dark:text-amber-400"
                              aria-label="Low sample size"
                            />
                          )}
                          {row.trades}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'maemfe' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              MAE (Max Adverse Excursion) vs Final R
            </h3>
            <p className="mt-0.5 mb-4 text-xs text-slate-500 dark:text-slate-400">
              Shows how far trades went against entry (in R) before closing.
            </p>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 16, bottom: 10, left: 0 }}>
                  <CartesianGrid stroke={chartPalette.grid} strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    dataKey="maeR"
                    name="MAE (R)"
                    stroke={chartPalette.axisStroke}
                    tick={{ fill: chartPalette.tickFill, fontSize: 11 }}
                    unit="R"
                  />
                  <YAxis
                    type="number"
                    dataKey="rMultiple"
                    name="Final R"
                    stroke={chartPalette.axisStroke}
                    tick={{ fill: chartPalette.tickFill, fontSize: 11 }}
                    unit="R"
                  />
                  <ZAxis range={[36, 36]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: chartPalette.tooltipBg,
                      borderColor: chartPalette.tooltipBorder,
                      color: chartPalette.tooltipText,
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend />
                  <Scatter
                    name="Winning Trades"
                    data={result.maeMfe.filter((p) => p.outcome === 'win')}
                    fill="#10B981"
                  />
                  <Scatter
                    name="Losing Trades"
                    data={result.maeMfe.filter((p) => p.outcome === 'loss')}
                    fill="#EF4444"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              MFE (Max Favourable Excursion) vs Final R
            </h3>
            <p className="mt-0.5 mb-4 text-xs text-slate-500 dark:text-slate-400">
              Reveals unrealized profit potential captured vs left on the table.
            </p>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 16, bottom: 10, left: 0 }}>
                  <CartesianGrid stroke={chartPalette.grid} strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    dataKey="mfeR"
                    name="MFE (R)"
                    stroke={chartPalette.axisStroke}
                    tick={{ fill: chartPalette.tickFill, fontSize: 11 }}
                    unit="R"
                  />
                  <YAxis
                    type="number"
                    dataKey="rMultiple"
                    name="Final R"
                    stroke={chartPalette.axisStroke}
                    tick={{ fill: chartPalette.tickFill, fontSize: 11 }}
                    unit="R"
                  />
                  <ZAxis range={[36, 36]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: chartPalette.tooltipBg,
                      borderColor: chartPalette.tooltipBorder,
                      color: chartPalette.tooltipText,
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend />
                  <Scatter
                    name="Winning Trades"
                    data={result.maeMfe.filter((p) => p.outcome === 'win')}
                    fill="#10B981"
                  />
                  <Scatter
                    name="Losing Trades"
                    data={result.maeMfe.filter((p) => p.outcome === 'loss')}
                    fill="#EF4444"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'grades' && (
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">
              Expectancy (R) &amp; Win Rate by Setup Grade
            </h3>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={result.setupGrades} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke={chartPalette.grid} strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="grade" stroke={chartPalette.axisStroke} tick={{ fill: chartPalette.tickFill, fontSize: 12 }} />
                  <YAxis
                    yAxisId="left"
                    stroke={chartPalette.axisStroke}
                    tick={{ fill: chartPalette.tickFill, fontSize: 11 }}
                    tickFormatter={(v) => `${v}R`}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    stroke={chartPalette.axisStroke}
                    tick={{ fill: chartPalette.tickFill, fontSize: 11 }}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: chartPalette.tooltipBg,
                      borderColor: chartPalette.tooltipBorder,
                      color: chartPalette.tooltipText,
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend />
                  <Bar yAxisId="left" dataKey="expectancyR" name="Expectancy (R)" radius={[4, 4, 0, 0]}>
                    {result.setupGrades.map((entry) => (
                      <Cell
                        key={entry.grade}
                        fill={entry.expectancyR >= 0 ? '#10B981' : '#EF4444'}
                      />
                    ))}
                  </Bar>
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="winRate"
                    name="Win Rate (%)"
                    stroke="#3B82F6"
                    strokeWidth={2}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                  <th className="py-2 pr-4 font-medium">Setup Grade</th>
                  <th className="py-2 px-3 font-medium text-right">Trades</th>
                  <th className="py-2 px-3 font-medium text-right">Wins</th>
                  <th className="py-2 px-3 font-medium text-right">Win Rate</th>
                  <th className="py-2 px-3 font-medium text-right">Expectancy (R)</th>
                  <th className="py-2 px-3 font-medium text-right">Profit Factor</th>
                  <th className="py-2 pl-3 font-medium text-right">Net Profit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
                {result.setupGrades.map((g) => (
                  <tr key={g.grade}>
                    <td className="py-2.5 pr-4">
                      <GradeBadge grade={g.grade} />
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200">
                      <span className="inline-flex items-center gap-1.5">
                        {g.trades < 20 && (
                          <AlertTriangle
                            className="h-3.5 w-3.5 text-amber-500 dark:text-amber-400"
                            aria-label="Low sample size"
                          />
                        )}
                        {g.trades}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-600 dark:text-slate-300">
                      {g.wins}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200">
                      {g.winRate.toFixed(1)}%
                    </td>
                    <td
                      className={`py-2.5 px-3 text-right font-mono font-semibold tabular-nums ${
                        g.expectancyR >= 0
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {g.expectancyR >= 0 ? '+' : ''}
                      {g.expectancyR.toFixed(2)}R
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200">
                      {g.profitFactor.toFixed(2)}
                    </td>
                    <td
                      className={`py-2.5 pl-3 text-right font-mono font-semibold tabular-nums ${
                        g.netProfit >= 0
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {formatCurrency(g.netProfit, currency, { signed: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'robustness' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <MetricBox
              label="Parameter Stability Rating"
              value={result.robustness.overallStabilityLabel}
              tone={result.robustness.overallStabilityLabel === 'Robust' ? 'profit' : 'neutral'}
            />
            <MetricBox
              label="Monte Carlo 95th Pct Max DD"
              value={`-${result.robustness.monteCarloMaxDd95Percent.toFixed(1)}%`}
              tone="loss"
            />
            <MetricBox
              label="Risk of Ruin (50% DD)"
              value={`${result.robustness.monteCarloRuinProbabilityPercent.toFixed(1)}%`}
            />
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Walk-Forward In-Sample vs Out-of-Sample */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">
                Walk-Forward Analysis (In-Sample vs Out-of-Sample %)
              </h3>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={result.robustness.walkForwardFolds}>
                    <CartesianGrid stroke={chartPalette.grid} strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="fold" stroke={chartPalette.axisStroke} tick={{ fill: chartPalette.tickFill, fontSize: 11 }} />
                    <YAxis
                      stroke={chartPalette.axisStroke}
                      tick={{ fill: chartPalette.tickFill, fontSize: 11 }}
                      tickFormatter={(v) => `${v}%`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: chartPalette.tooltipBg,
                        borderColor: chartPalette.tooltipBorder,
                        color: chartPalette.tooltipText,
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                    />
                    <Legend />
                    <Bar dataKey="inSampleReturnPercent" name="In-Sample %" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="outOfSampleReturnPercent" name="Out-of-Sample %" fill="#10B981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Monte Carlo Percentile Drawdown */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">
                Monte Carlo Drawdown Range (50th vs 95th Percentile)
              </h3>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={result.robustness.monteCarloDistribution}>
                    <CartesianGrid stroke={chartPalette.grid} strokeDasharray="3 3" vertical={false} />
                    <XAxis
                      dataKey="tradeIndex"
                      stroke={chartPalette.axisStroke}
                      tick={{ fill: chartPalette.tickFill, fontSize: 11 }}
                      tickFormatter={(v) => `T${v}`}
                    />
                    <YAxis
                      stroke={chartPalette.axisStroke}
                      tick={{ fill: chartPalette.tickFill, fontSize: 11 }}
                      tickFormatter={(v) => `${v}%`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: chartPalette.tooltipBg,
                        borderColor: chartPalette.tooltipBorder,
                        color: chartPalette.tooltipText,
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                      formatter={(val, name) => [`${Number(val ?? 0).toFixed(1)}%`, String(name ?? '')]}
                    />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="drawdownP50"
                      name="Median Drawdown (P50)"
                      stroke="#F59E0B"
                      fill="#F59E0B"
                      fillOpacity={0.18}
                    />
                    <Area
                      type="monotone"
                      dataKey="drawdownP95"
                      name="Worst-Case Drawdown (P95)"
                      stroke="#EF4444"
                      fill="#EF4444"
                      fillOpacity={0.22}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Parameter Stability Table */}
          <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5 overflow-x-auto">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">
              Parameter Stability Indicators
            </h3>
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                  <th className="py-2 pr-4 font-medium">Parameter</th>
                  <th className="py-2 px-3 font-medium">Optimal Plateau</th>
                  <th className="py-2 px-3 font-medium">Sensitivity</th>
                  <th className="py-2 pl-3 font-medium text-right">Stability Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
                {result.robustness.parameterStability.map((p) => (
                  <tr key={p.parameterName}>
                    <td className="py-2.5 pr-4 font-medium text-slate-800 dark:text-slate-200">{p.parameterName}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-600 dark:text-slate-300">{p.optimalRange}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`font-medium ${
                          p.sensitivity === 'Low'
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : p.sensitivity === 'Moderate'
                            ? 'text-amber-600 dark:text-amber-400'
                            : 'text-red-600 dark:text-red-400'
                        }`}
                      >
                        {p.sensitivity}
                      </span>
                    </td>
                    <td className="py-2.5 pl-3 text-right font-mono tabular-nums text-slate-900 dark:text-slate-100">
                      {p.stabilityScore} / 100
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'trades' && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                Simulated Backtest Trades ({result.trades.length})
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Chronologically ordered simulated fills including spread, commission, and slippage.
              </p>
            </div>
            <button
              type="button"
              onClick={() =>
                exportTradesToCsv(result.trades, `${result.id}-trades.csv`)
              }
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 whitespace-nowrap"
            >
              <Download className="h-3.5 w-3.5" />
              Export Simulated Trades
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 whitespace-nowrap">
                  <th className="py-2 pr-3 font-medium">Opened</th>
                  <th className="py-2 px-2.5 font-medium">Pair</th>
                  <th className="py-2 px-2.5 font-medium">Dir</th>
                  <th className="py-2 px-2.5 font-medium">Grade</th>
                  <th className="py-2 px-2.5 font-medium text-right">Entry</th>
                  <th className="py-2 px-2.5 font-medium text-right">Exit</th>
                  <th className="py-2 px-2.5 font-medium text-right">Lots</th>
                  <th className="py-2 px-2.5 font-medium text-right">P/L</th>
                  <th className="py-2 px-2.5 font-medium text-right">R</th>
                  <th className="py-2 pl-2.5 font-medium text-right">Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
                {result.trades.slice((tradePage - 1) * 20, tradePage * 20).map((t) => (
                  <tr key={t.id} className="hover:bg-slate-100 dark:hover:bg-slate-800/35">
                    <td className="py-2 pr-3 font-mono text-[11px] text-slate-600 dark:text-slate-300 tabular-nums whitespace-nowrap">
                      {formatDateTime(t.openedAt)}
                    </td>
                    <td className="py-2 px-2.5 font-mono font-semibold text-slate-900 dark:text-slate-100">
                      {t.pair}
                    </td>
                    <td className="py-2 px-2.5 font-mono text-[11px] font-semibold">
                      <span
                        className={
                          t.direction === 'BUY'
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : 'text-red-600 dark:text-red-400'
                        }
                      >
                        {t.direction}
                      </span>
                    </td>
                    <td className="py-2 px-2.5">
                      <GradeBadge grade={t.setupGrade} />
                    </td>
                    <td className="py-2 px-2.5 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200">
                      {formatPairPrice(t.entryPrice, t.pair)}
                    </td>
                    <td className="py-2 px-2.5 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200">
                      {formatPairPrice(t.exitPrice, t.pair)}
                    </td>
                    <td className="py-2 px-2.5 text-right font-mono tabular-nums text-slate-600 dark:text-slate-300">
                      {t.sizeLots.toFixed(2)}
                    </td>
                    <td
                      className={`py-2 px-2.5 text-right font-mono font-semibold tabular-nums ${
                        t.pnl >= 0
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {formatCurrency(t.pnl, t.currency, { signed: true })}
                    </td>
                    <td
                      className={`py-2 px-2.5 text-right font-mono tabular-nums ${
                        t.rMultiple >= 0
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {t.rMultiple >= 0 ? '+' : ''}
                      {t.rMultiple.toFixed(2)}R
                    </td>
                    <td className="py-2 pl-2.5 text-right font-mono text-slate-500 dark:text-slate-400 tabular-nums">
                      {formatDuration(t.durationMinutes)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between pt-2 text-xs text-slate-500 dark:text-slate-400">
            <span>
              Page {tradePage} of {Math.max(1, Math.ceil(result.trades.length / 20))}
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={tradePage <= 1}
                onClick={() => setTradePage((p) => Math.max(1, p - 1))}
                className="rounded-md border border-slate-300 bg-white px-3 py-1 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 disabled:opacity-40"
              >
                Prev
              </button>
              <button
                type="button"
                disabled={tradePage >= Math.ceil(result.trades.length / 20)}
                onClick={() => setTradePage((p) => p + 1)}
                className="rounded-md border border-slate-300 bg-white px-3 py-1 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

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
}) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-100 dark:border-slate-800/90 dark:bg-[#0B0F17] p-2">
        {CONDITION_DIMENSIONS.map((d) => (
          <button
            key={d.key}
            type="button"
            onClick={() => onChangeDimension(d.key)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap ${
              dimension === d.key
                ? 'bg-white text-slate-900 shadow-xs dark:bg-slate-800 dark:text-slate-100'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
            }`}
          >
            {d.label}
          </button>
        ))}
      </div>

      <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">
          Expectancy (R) &amp; Net Profit by{' '}
          {CONDITION_DIMENSIONS.find((d) => d.key === dimension)?.label}
        </h3>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={items} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={chartPalette.grid} strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="bucket" stroke={chartPalette.axisStroke} tick={{ fill: chartPalette.tickFill, fontSize: 11 }} />
              <YAxis
                stroke={chartPalette.axisStroke}
                tick={{ fill: chartPalette.tickFill, fontSize: 11 }}
                tickFormatter={(v) => `${v}R`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: chartPalette.tooltipBg,
                  borderColor: chartPalette.tooltipBorder,
                  color: chartPalette.tooltipText,
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
                formatter={(val) => [`${Number(val ?? 0).toFixed(2)}R`, 'Expectancy']}
              />
              <Bar dataKey="expectancyR" name="Expectancy (R)" radius={[4, 4, 0, 0]}>
                {items.map((item) => (
                  <Cell
                    key={item.bucket}
                    fill={item.expectancyR >= 0 ? '#10B981' : '#EF4444'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] p-5 overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
              <th className="py-2 pr-4 font-medium">Bucket</th>
              <th className="py-2 px-3 font-medium text-right">Trades</th>
              <th className="py-2 px-3 font-medium text-right">Win Rate</th>
              <th className="py-2 px-3 font-medium text-right">Expectancy (R)</th>
              <th className="py-2 px-3 font-medium text-right">Profit Factor</th>
              <th className="py-2 pl-3 font-medium text-right">Net Profit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
            {items.map((row) => (
              <tr key={row.bucket}>
                <td className="py-2.5 pr-4 font-medium text-slate-900 dark:text-slate-100">{row.bucket}</td>
                <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200">
                  <span className="inline-flex items-center gap-1.5">
                    {row.lowSampleWarning && (
                      <span
                        className="inline-flex items-center gap-1 text-[11px] text-amber-500 dark:text-amber-400"
                        title="Sample size under 20 trades — treat with caution"
                      >
                        <AlertTriangle className="h-3.5 w-3.5" />
                      </span>
                    )}
                    {row.trades}
                  </span>
                </td>
                <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-600 dark:text-slate-300">
                  {row.winRate.toFixed(1)}%
                </td>
                <td
                  className={`py-2.5 px-3 text-right font-mono font-semibold tabular-nums ${
                    row.expectancyR >= 0
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {row.expectancyR >= 0 ? '+' : ''}
                  {row.expectancyR.toFixed(2)}R
                </td>
                <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200">
                  {row.profitFactor.toFixed(2)}
                </td>
                <td
                  className={`py-2.5 pl-3 text-right font-mono font-semibold tabular-nums ${
                    row.netProfit >= 0
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {formatCurrency(row.netProfit, currency, { signed: true })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

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
}) {
  const color =
    tone === 'profit'
      ? 'text-emerald-600 dark:text-emerald-400'
      : tone === 'loss'
      ? 'text-red-600 dark:text-red-400'
      : 'text-slate-900 dark:text-slate-100';

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-[#0B0F17] px-3.5 py-3">
      <p className="text-[11px] text-slate-500 dark:text-slate-400">{label}</p>
      <p className={`mt-1 font-mono text-sm font-bold tabular-nums ${color}`}>{value}</p>
      {subtext && <p className="mt-0.5 font-mono text-[11px] text-slate-500">{subtext}</p>}
    </div>
  );
}
