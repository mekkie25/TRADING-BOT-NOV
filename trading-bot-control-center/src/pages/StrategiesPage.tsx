import { useCallback, useEffect, useState, type ChangeEvent, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Columns3, Copy, Plus, Upload, X } from 'lucide-react';
import { api } from '../services/api';
import type { ForexPair, Indicator, Strategy } from '../types';
import { PanelShell } from '../components/DataState';
import { useAppContext } from '../components/AppContext';

export function StrategiesPage() {
  const { refreshGlobalState } = useAppContext();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [availablePairs, setAvailablePairs] = useState<ForexPair[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [cloningId, setCloningId] = useState<string | null>(null);

  const [compareOpen, setCompareOpen] = useState(false);
  const [compareIds, setCompareIds] = useState<string[]>([]);

  const [modalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>([]);
  const [selectedPairs, setSelectedPairs] = useState<ForexPair[]>(['EURUSD', 'GBPUSD']);
  const [fileName, setFileName] = useState('');
  const [codeSnippet, setCodeSnippet] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [strats, inds, pairs] = await Promise.all([
        api.getStrategies(),
        api.getIndicators(),
        api.getAvailablePairs(),
      ]);
      setStrategies(strats);
      setIndicators(inds);
      setAvailablePairs(pairs);
      setCompareIds(strats.slice(0, 2).map((s) => s.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load strategies');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleToggleActive = async (strategy: Strategy) => {
    setTogglingId(strategy.id);
    try {
      const updated = await api.toggleStrategyActive(strategy.id, !strategy.isActive);
      setStrategies((prev) => prev.map((s) => (s.id === strategy.id ? updated : s)));
      await refreshGlobalState();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle strategy');
    } finally {
      setTogglingId(null);
    }
  };

  const handleCloneStrategy = async (strategy: Strategy) => {
    setCloningId(strategy.id);
    try {
      const cloned = await api.cloneStrategy(strategy.id);
      setStrategies((prev) => [cloned, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clone strategy');
    } finally {
      setCloningId(null);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        setCodeSnippet(reader.result);
      }
    };
    reader.readAsText(file);
  };

  const handleCreateStrategy = async (e: FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    if (!name.trim()) {
      setCreateError('Strategy name is required.');
      return;
    }
    setCreating(true);
    try {
      const created = await api.createStrategy({
        name: name.trim(),
        description: description.trim() || 'Custom automated trading strategy.',
        indicatorIds: selectedIndicators,
        assignedPairs: selectedPairs,
        fileName: fileName || undefined,
        codeSnippet: codeSnippet || undefined,
      });
      setStrategies((prev) => [created, ...prev]);
      setModalOpen(false);
      setName('');
      setDescription('');
      setSelectedIndicators([]);
      setFileName('');
      setCodeSnippet('');
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create strategy');
    } finally {
      setCreating(false);
    }
  };

  const toggleIndicatorPick = (id: string) => {
    setSelectedIndicators((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const togglePairPick = (pair: ForexPair) => {
    setSelectedPairs((prev) =>
      prev.includes(pair) ? prev.filter((x) => x !== pair) : [...prev, pair]
    );
  };

  const toggleComparePick = (id: string) => {
    setCompareIds((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : prev.length < 3
        ? [...prev, id]
        : [...prev.slice(1), id]
    );
  };

  const comparedStrategies = strategies.filter((s) => compareIds.includes(s.id));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Trading Strategies
          </h1>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Manage automated execution modules, version history, cloning, side-by-side comparison, and setup grading rules.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            disabled={strategies.length < 2}
            onClick={() => setCompareOpen((v) => !v)}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 transition-colors whitespace-nowrap"
          >
            <Columns3 className="h-3.5 w-3.5" />
            {compareOpen ? 'Hide Comparison' : 'Compare Side-by-Side'}
          </button>

          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500 transition-colors whitespace-nowrap"
          >
            <Plus className="h-4 w-4" />
            Add / Upload Strategy
          </button>
        </div>
      </div>

      {/* Side-by-Side Strategy Comparison View */}
      {compareOpen && (
        <PanelShell
          title="Side-by-Side Strategy Comparison"
          subtitle="Select up to 3 strategies to compare metrics, parameters, pairs, and indicators"
          isLoading={false}
          error={null}
          isEmpty={comparedStrategies.length === 0}
        >
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {strategies.map((s) => {
                const selected = compareIds.includes(s.id);
                return (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => toggleComparePick(s.id)}
                    className={`rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                      selected
                        ? 'border-blue-500 bg-blue-600/15 text-blue-700 dark:text-blue-200'
                        : 'border-slate-300 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-[#0B0F17] dark:text-slate-400'
                    }`}
                  >
                    {s.name}
                  </button>
                );
              })}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                    <th className="py-2 pr-4 font-medium">Attribute</th>
                    {comparedStrategies.map((s) => (
                      <th key={s.id} className="py-2 px-3 font-semibold text-slate-900 dark:text-slate-100">
                        {s.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
                  <tr>
                    <td className="py-2.5 pr-4 text-slate-500">Status &amp; Version</td>
                    {comparedStrategies.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 font-mono">
                        {s.isActive ? 'Active' : 'Inactive'} · {s.currentVersion}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 text-slate-500">Assigned Pairs</td>
                    {comparedStrategies.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 font-mono">
                        {s.assignedPairs.join(', ') || 'None'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 text-slate-500">Win Rate (Last BT)</td>
                    {comparedStrategies.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 font-mono tabular-nums">
                        {s.lastBacktestSummary ? `${s.lastBacktestSummary.winRate.toFixed(1)}%` : '—'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 text-slate-500">Profit Factor</td>
                    {comparedStrategies.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 font-mono tabular-nums">
                        {s.lastBacktestSummary ? s.lastBacktestSummary.profitFactor.toFixed(2) : '—'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 text-slate-500">Expectancy (R)</td>
                    {comparedStrategies.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 font-mono tabular-nums">
                        {s.lastBacktestSummary
                          ? `${s.lastBacktestSummary.expectancyR >= 0 ? '+' : ''}${s.lastBacktestSummary.expectancyR.toFixed(2)}R`
                          : '—'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 text-slate-500">Net Return (Last BT)</td>
                    {comparedStrategies.map((s) => (
                      <td
                        key={s.id}
                        className="py-2.5 px-3 font-mono font-semibold text-emerald-600 dark:text-emerald-400 tabular-nums"
                      >
                        {s.lastBacktestSummary
                          ? `+${s.lastBacktestSummary.netReturnPercent.toFixed(1)}%`
                          : '—'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 text-slate-500">Indicators</td>
                    {comparedStrategies.map((s) => (
                      <td key={s.id} className="py-2.5 px-3 font-mono">
                        {s.indicatorIds
                          .map((id) => indicators.find((i) => i.id === id)?.shortCode || id)
                          .join(' · ') || '—'}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </PanelShell>
      )}

      <PanelShell
        title="Configured Strategies"
        subtitle="Toggle execution status, clone a strategy, or open details for version rollback & grading rules"
        isLoading={loading}
        error={error}
        isEmpty={strategies.length === 0}
        emptyTitle="No strategies configured"
        emptyDescription="Upload a Python strategy file or register a new strategy definition to get started."
        emptyActionLabel="Add Strategy"
        onEmptyAction={() => setModalOpen(true)}
        onRetry={loadData}
        skeletonRows={4}
      >
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {strategies.map((strat) => {
            const indicatorNames = strat.indicatorIds
              .map((id) => indicators.find((i) => i.id === id)?.shortCode || id)
              .join(' · ');

            return (
              <div
                key={strat.id}
                className="flex flex-col justify-between rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-5"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                          {strat.name}
                        </h3>
                        <span className="font-mono text-[11px] text-slate-500">
                          {strat.currentVersion}
                        </span>
                        <span
                          className={`rounded border px-2 py-0.5 text-[11px] font-medium ${
                            strat.isActive
                              ? 'border-emerald-500/35 bg-emerald-500/12 text-emerald-700 dark:text-emerald-300'
                              : 'border-slate-300 bg-slate-200/70 text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400'
                          }`}
                        >
                          {strat.isActive ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <p className="mt-1.5 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                        {strat.description}
                      </p>
                    </div>

                    {/* Enable / Disable Toggle */}
                    <button
                      type="button"
                      role="switch"
                      aria-checked={strat.isActive}
                      aria-label={`Toggle ${strat.name}`}
                      disabled={togglingId === strat.id}
                      onClick={() => handleToggleActive(strat)}
                      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none disabled:opacity-50 ${
                        strat.isActive ? 'bg-emerald-600' : 'bg-slate-300 dark:bg-slate-700'
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${
                          strat.isActive ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-500 dark:text-slate-400">
                    <span>
                      Pairs:{' '}
                      <span className="font-mono text-slate-800 dark:text-slate-200">
                        {strat.assignedPairs.length > 0 ? strat.assignedPairs.join(', ') : 'None'}
                      </span>
                    </span>
                    {indicatorNames && (
                      <span>
                        Indicators:{' '}
                        <span className="font-mono text-slate-800 dark:text-slate-200">{indicatorNames}</span>
                      </span>
                    )}
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 dark:border-slate-800/80 pt-3">
                  {strat.lastBacktestSummary ? (
                    <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono tabular-nums">
                      <span className="text-slate-500 dark:text-slate-400">
                        Last BT ({strat.lastBacktestSummary.date}):
                      </span>
                      <span
                        className={
                          strat.lastBacktestSummary.netReturnPercent >= 0
                            ? 'text-emerald-600 dark:text-emerald-400 font-semibold'
                            : 'text-red-600 dark:text-red-400 font-semibold'
                        }
                      >
                        {strat.lastBacktestSummary.netReturnPercent >= 0 ? '+' : ''}
                        {strat.lastBacktestSummary.netReturnPercent.toFixed(1)}%
                      </span>
                      <span className="text-slate-700 dark:text-slate-300">
                        WR {strat.lastBacktestSummary.winRate.toFixed(1)}%
                      </span>
                      <span className="text-slate-700 dark:text-slate-300">
                        PF {strat.lastBacktestSummary.profitFactor.toFixed(2)}
                      </span>
                    </div>
                  ) : (
                    <span className="text-[11px] text-slate-500">
                      No backtest run recorded yet
                    </span>
                  )}

                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      disabled={cloningId === strat.id}
                      onClick={() => void handleCloneStrategy(strat)}
                      className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 disabled:opacity-50 whitespace-nowrap"
                    >
                      <Copy className="h-3 w-3" />
                      {cloningId === strat.id ? 'Cloning...' : 'Clone'}
                    </button>
                    <Link
                      to={`/strategies/${strat.id}`}
                      className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300 whitespace-nowrap"
                    >
                      Configure &amp; Versions
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </PanelShell>

      {/* Add / Upload Strategy Modal */}
      {modalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 dark:bg-black/70 p-4 backdrop-blur-xs"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-xl rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-[#111824] p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3 mb-4">
              <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Add / Upload Strategy
              </h2>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded-md p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreateStrategy} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Strategy Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Tokyo Range Fade"
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe signal triggers, session constraints, and trade management..."
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                  Indicators Used
                </label>
                <div className="flex flex-wrap gap-2">
                  {indicators.map((ind) => {
                    const active = selectedIndicators.includes(ind.id);
                    return (
                      <button
                        key={ind.id}
                        type="button"
                        onClick={() => toggleIndicatorPick(ind.id)}
                        className={`rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                          active
                            ? 'border-blue-500 bg-blue-600/15 text-blue-700 dark:bg-blue-600/20 dark:text-blue-200'
                            : 'border-slate-300 bg-slate-50 text-slate-600 hover:text-slate-900 dark:border-slate-700 dark:bg-[#0B0F17] dark:text-slate-400 dark:hover:text-slate-200'
                        }`}
                      >
                        {ind.shortCode} · {ind.name}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                  Assigned Pairs
                </label>
                <div className="flex flex-wrap gap-2">
                  {availablePairs.map((pair) => {
                    const active = selectedPairs.includes(pair);
                    return (
                      <button
                        key={pair}
                        type="button"
                        onClick={() => togglePairPick(pair)}
                        className={`rounded-md border px-2.5 py-1 font-mono text-xs transition-colors ${
                          active
                            ? 'border-emerald-500/60 bg-emerald-500/15 text-emerald-700 dark:text-emerald-200'
                            : 'border-slate-300 bg-slate-50 text-slate-600 hover:text-slate-900 dark:border-slate-700 dark:bg-[#0B0F17] dark:text-slate-400 dark:hover:text-slate-200'
                        }`}
                      >
                        {pair}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
                    Python Strategy File / Code
                  </label>
                  <label className="inline-flex cursor-pointer items-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300">
                    <Upload className="h-3.5 w-3.5" />
                    <span>{fileName || 'Upload .py file'}</span>
                    <input
                      type="file"
                      accept=".py,.txt"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </label>
                </div>
                <textarea
                  rows={5}
                  value={codeSnippet}
                  onChange={(e) => setCodeSnippet(e.target.value)}
                  placeholder="class CustomStrategy(BaseStrategy):&#10;    def evaluate_signal(self, ctx):&#10;        ..."
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 font-mono text-[11px] text-slate-800 dark:text-slate-200 focus:border-blue-500 focus:outline-none"
                />
              </div>

              {createError && (
                <p className="text-xs text-red-600 dark:text-red-400">{createError}</p>
              )}

              <div className="flex justify-end gap-3 pt-2 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="rounded-lg border border-slate-300 bg-slate-100 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create Strategy'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
