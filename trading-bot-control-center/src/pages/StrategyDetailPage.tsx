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

export function StrategyDetailPage() {
  const { strategyId } = useParams<{ strategyId: string }>();
  const { refreshGlobalState } = useAppContext();

  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [availablePairs, setAvailablePairs] = useState<ForexPair[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeGradeTab, setActiveGradeTab] = useState<SetupGrade>('A++');
  const [saving, setSaving] = useState(false);
  const [savedNotice, setSavedNotice] = useState(false);

  const [rollbackTarget, setRollbackTarget] = useState<string | null>(null);
  const [rollingBack, setRollingBack] = useState(false);

  const loadStrategy = useCallback(async () => {
    if (!strategyId) return;
    setLoading(true);
    setError(null);
    try {
      const [strat, inds, pairs] = await Promise.all([
        api.getStrategy(strategyId),
        api.getIndicators(),
        api.getAvailablePairs(),
      ]);
      setStrategy(strat);
      setIndicators(inds);
      setAvailablePairs(pairs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load strategy');
    } finally {
      setLoading(false);
    }
  }, [strategyId]);

  useEffect(() => {
    void loadStrategy();
  }, [loadStrategy]);

  const handleSaveAll = async () => {
    if (!strategy) return;
    setSaving(true);
    setSavedNotice(false);
    setError(null);
    try {
      const updated = await api.updateStrategy(strategy.id, {
        isActive: strategy.isActive,
        assignedPairs: strategy.assignedPairs,
        indicatorIds: strategy.indicatorIds,
        parameters: strategy.parameters,
        gradingRules: strategy.gradingRules,
        codeSnippet: strategy.codeSnippet,
      });
      setStrategy(updated);
      setSavedNotice(true);
      await refreshGlobalState();
      window.setTimeout(() => setSavedNotice(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save strategy changes');
    } finally {
      setSaving(false);
    }
  };

  const handleConfirmRollback = async () => {
    if (!strategy || !rollbackTarget) return;
    setRollingBack(true);
    try {
      const updated = await api.rollbackStrategyVersion(strategy.id, rollbackTarget);
      setStrategy(updated);
      setRollbackTarget(null);
      setSavedNotice(true);
      window.setTimeout(() => setSavedNotice(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rollback failed');
    } finally {
      setRollingBack(false);
    }
  };

  const handleTogglePair = (pair: ForexPair) => {
    if (!strategy) return;
    const exists = strategy.assignedPairs.includes(pair);
    setStrategy({
      ...strategy,
      assignedPairs: exists
        ? strategy.assignedPairs.filter((p) => p !== pair)
        : [...strategy.assignedPairs, pair],
    });
  };

  const handleToggleIndicator = (indId: string) => {
    if (!strategy) return;
    const exists = strategy.indicatorIds.includes(indId);
    setStrategy({
      ...strategy,
      indicatorIds: exists
        ? strategy.indicatorIds.filter((i) => i !== indId)
        : [...strategy.indicatorIds, indId],
    });
  };

  const handleParamChange = (key: string, value: number | boolean | string) => {
    if (!strategy) return;
    setStrategy({
      ...strategy,
      parameters: strategy.parameters.map((p) =>
        p.key === key ? { ...p, value } : p
      ),
    });
  };

  const handleAddRule = () => {
    if (!strategy) return;
    const newRule: GradingCondition = {
      id: `rule-${Date.now()}`,
      metric: 'ADX(14)',
      operator: '>=',
      threshold: '25',
      description: 'New grading condition',
    };
    setStrategy({
      ...strategy,
      gradingRules: {
        ...strategy.gradingRules,
        [activeGradeTab]: [...strategy.gradingRules[activeGradeTab], newRule],
      },
    });
  };

  const handleUpdateRule = (
    ruleId: string,
    patch: Partial<GradingCondition>
  ) => {
    if (!strategy) return;
    setStrategy({
      ...strategy,
      gradingRules: {
        ...strategy.gradingRules,
        [activeGradeTab]: strategy.gradingRules[activeGradeTab].map((r) =>
          r.id === ruleId ? { ...r, ...patch } : r
        ),
      },
    });
  };

  const handleRemoveRule = (ruleId: string) => {
    if (!strategy) return;
    setStrategy({
      ...strategy,
      gradingRules: {
        ...strategy.gradingRules,
        [activeGradeTab]: strategy.gradingRules[activeGradeTab].filter(
          (r) => r.id !== ruleId
        ),
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/strategies"
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-800 dark:bg-[#111824] dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Strategies
          </Link>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                {strategy?.name ?? 'Strategy Configuration'}
              </h1>
              {strategy && (
                <span className="font-mono text-xs font-semibold text-blue-600 dark:text-blue-400">
                  {strategy.currentVersion}
                </span>
              )}
            </div>
            {strategy && (
              <p className="text-xs text-slate-500 dark:text-slate-400">{strategy.description}</p>
            )}
          </div>
        </div>

        {strategy && (
          <div className="flex items-center gap-3">
            {savedNotice && (
              <span className="inline-flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
                <Check className="h-3.5 w-3.5" />
                Saved
              </span>
            )}
            <button
              type="button"
              onClick={() =>
                setStrategy({ ...strategy, isActive: !strategy.isActive })
              }
              className={`rounded-lg border px-3.5 py-2 text-xs font-semibold transition-colors ${
                strategy.isActive
                  ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                  : 'border-slate-300 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300'
              }`}
            >
              Status: {strategy.isActive ? 'Enabled' : 'Disabled'}
            </button>
            <button
              type="button"
              onClick={handleSaveAll}
              disabled={saving}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50 transition-colors whitespace-nowrap"
            >
              <Save className="h-3.5 w-3.5" />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        )}
      </div>

      <PanelShell
        title="Strategy Workspace"
        subtitle="Edit parameters, assigned instruments, indicators, grading criteria, and version rollbacks"
        isLoading={loading}
        error={error}
        isEmpty={!strategy}
        emptyTitle="Strategy not found"
        emptyDescription="The requested strategy identifier does not exist."
        onRetry={loadStrategy}
        skeletonHeightClass="h-96"
      >
        {strategy && (
          <div className="space-y-8">
            {/* Assigned Pairs & Indicators */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-3">
                <h3 className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                  Assigned Forex Pairs
                </h3>
                <div className="flex flex-wrap gap-2">
                  {availablePairs.map((pair) => {
                    const active = strategy.assignedPairs.includes(pair);
                    return (
                      <button
                        key={pair}
                        type="button"
                        onClick={() => handleTogglePair(pair)}
                        className={`rounded-md border px-3 py-1.5 font-mono text-xs font-medium transition-colors ${
                          active
                            ? 'border-emerald-500/50 bg-emerald-500/15 text-emerald-700 dark:text-emerald-200'
                            : 'border-slate-300 bg-white text-slate-600 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
                        }`}
                      >
                        {pair}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-3">
                <h3 className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                  Linked Indicators
                </h3>
                <div className="flex flex-wrap gap-2">
                  {indicators.map((ind) => {
                    const active = strategy.indicatorIds.includes(ind.id);
                    return (
                      <button
                        key={ind.id}
                        type="button"
                        onClick={() => handleToggleIndicator(ind.id)}
                        className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
                          active
                            ? 'border-blue-500/60 bg-blue-600/15 text-blue-700 dark:bg-blue-600/20 dark:text-blue-200'
                            : 'border-slate-300 bg-white text-slate-600 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
                        }`}
                      >
                        {ind.shortCode} · {ind.name}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Parameters Editor */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-5 space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  Strategy Parameters
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Runtime thresholds passed to the Python strategy class.
                </p>
              </div>

              {strategy.parameters.length === 0 ? (
                <p className="text-xs text-slate-500">
                  No configurable parameters defined for this strategy.
                </p>
              ) : (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {strategy.parameters.map((param) => (
                    <div
                      key={param.key}
                      className="rounded-lg border border-slate-200 bg-white dark:border-slate-800/80 dark:bg-[#111824] p-3.5 space-y-2"
                    >
                      <label className="block text-xs font-medium text-slate-800 dark:text-slate-200">
                        {param.label}
                      </label>
                      {param.type === 'number' && (
                        <input
                          type="number"
                          min={param.min}
                          max={param.max}
                          step={param.step ?? 0.1}
                          value={Number(param.value)}
                          onChange={(e) =>
                            handleParamChange(param.key, Number(e.target.value))
                          }
                          className="w-full rounded-md border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-1.5 font-mono text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                        />
                      )}
                      {param.type === 'select' && (
                        <select
                          value={String(param.value)}
                          onChange={(e) =>
                            handleParamChange(param.key, e.target.value)
                          }
                          className="w-full rounded-md border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                        >
                          {param.options?.map((opt) => (
                            <option key={opt} value={opt}>
                              {opt}
                            </option>
                          ))}
                        </select>
                      )}
                      {param.type === 'boolean' && (
                        <button
                          type="button"
                          onClick={() =>
                            handleParamChange(param.key, !Boolean(param.value))
                          }
                          className={`rounded-md border px-3 py-1.5 text-xs font-medium ${
                            param.value
                              ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                              : 'border-slate-300 bg-slate-100 text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400'
                          }`}
                        >
                          {param.value ? 'Enabled (True)' : 'Disabled (False)'}
                        </button>
                      )}
                      {param.type === 'string' && (
                        <input
                          type="text"
                          value={String(param.value)}
                          onChange={(e) =>
                            handleParamChange(param.key, e.target.value)
                          }
                          className="w-full rounded-md border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                        />
                      )}
                      {param.description && (
                        <p className="text-[11px] text-slate-500">
                          {param.description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Setup Grading Rules Editor */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-5 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    Setup Grading Rules
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Define the conditions evaluated by the backend to assign A++ through Bad grades.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleAddRule}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 whitespace-nowrap"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Add Rule to {activeGradeTab}
                </button>
              </div>

              <div className="flex flex-wrap items-center gap-1.5 border-b border-slate-200 dark:border-slate-800 pb-3">
                {GRADES.map((g) => (
                  <button
                    key={g}
                    type="button"
                    onClick={() => setActiveGradeTab(g)}
                    className={`inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                      activeGradeTab === g
                        ? 'border-blue-500 bg-blue-600/15 text-slate-900 dark:bg-blue-600/20 dark:text-slate-100'
                        : 'border-slate-200 bg-white text-slate-600 hover:text-slate-900 dark:border-slate-800 dark:bg-[#111824] dark:text-slate-400 dark:hover:text-slate-200'
                    }`}
                  >
                    <GradeBadge grade={g} />
                    <span className="font-mono text-[11px] text-slate-500 dark:text-slate-400">
                      ({strategy.gradingRules[g].length})
                    </span>
                  </button>
                ))}
              </div>

              {strategy.gradingRules[activeGradeTab].length === 0 ? (
                <p className="py-4 text-center text-xs text-slate-500">
                  No rules configured for grade {activeGradeTab}. Click &ldquo;Add Rule&rdquo; above to define conditions.
                </p>
              ) : (
                <div className="space-y-3">
                  {strategy.gradingRules[activeGradeTab].map((rule) => (
                    <div
                      key={rule.id}
                      className="grid grid-cols-1 gap-2.5 rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#111824] p-3 md:grid-cols-12 md:items-center"
                    >
                      <input
                        type="text"
                        value={rule.metric}
                        onChange={(e) =>
                          handleUpdateRule(rule.id, { metric: e.target.value })
                        }
                        placeholder="Metric (e.g. ADX(14))"
                        className="md:col-span-3 rounded-md border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                      />
                      <select
                        value={rule.operator}
                        onChange={(e) =>
                          handleUpdateRule(rule.id, {
                            operator: e.target.value as GradingCondition['operator'],
                          })
                        }
                        className="md:col-span-2 rounded-md border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2 py-1.5 font-mono text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                      >
                        {OPERATORS.map((op) => (
                          <option key={op} value={op}>
                            {op}
                          </option>
                        ))}
                      </select>
                      <input
                        type="text"
                        value={rule.threshold}
                        onChange={(e) =>
                          handleUpdateRule(rule.id, { threshold: e.target.value })
                        }
                        placeholder="Threshold"
                        className="md:col-span-2 rounded-md border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-1.5 font-mono text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                      />
                      <input
                        type="text"
                        value={rule.description}
                        onChange={(e) =>
                          handleUpdateRule(rule.id, {
                            description: e.target.value,
                          })
                        }
                        placeholder="Rule description"
                        className="md:col-span-4 rounded-md border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-1.5 text-xs text-slate-700 dark:text-slate-300 focus:border-blue-500 focus:outline-none"
                      />
                      <div className="md:col-span-1 flex justify-end">
                        <button
                          type="button"
                          onClick={() => handleRemoveRule(rule.id)}
                          className="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-red-600 dark:text-slate-500 dark:hover:bg-slate-800 dark:hover:text-red-400 transition-colors"
                          aria-label="Remove grading rule"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Version History & Rollback */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-5 space-y-4">
              <div className="flex items-center gap-2">
                <History className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    Version History &amp; Trade Attribution
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Audit which historical trades used each revision or roll back parameters immediately.
                  </p>
                </div>
              </div>

              {strategy.versions.length === 0 ? (
                <p className="text-xs text-slate-500">No version snapshots recorded.</p>
              ) : (
                <div className="space-y-2.5">
                  {strategy.versions.map((ver) => (
                    <div
                      key={ver.version}
                      className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#111824] p-3.5 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-xs font-bold text-slate-900 dark:text-slate-100">
                            {ver.version}
                          </span>
                          {ver.isCurrent && (
                            <span className="rounded border border-emerald-500/35 bg-emerald-500/12 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 dark:text-emerald-300">
                              Active Revision
                            </span>
                          )}
                          <span className="font-mono text-[11px] text-slate-500">
                            {formatDateTime(ver.createdAt)}
                          </span>
                          <span className="font-mono text-[11px] text-blue-600 dark:text-blue-400">
                            {ver.tradeCount} trade{ver.tradeCount === 1 ? '' : 's'} executed
                          </span>
                        </div>
                        <p className="text-xs text-slate-700 dark:text-slate-300">{ver.notes}</p>
                        {ver.tradeIds.length > 0 && (
                          <p className="font-mono text-[11px] text-slate-500">
                            Sample trade IDs: {ver.tradeIds.join(', ')}
                          </p>
                        )}
                      </div>

                      {!ver.isCurrent && (
                        <button
                          type="button"
                          onClick={() => setRollbackTarget(ver.version)}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-1.5 text-xs font-semibold text-amber-800 hover:bg-amber-500/20 dark:text-amber-300 shrink-0 whitespace-nowrap"
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                          Rollback to {ver.version}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Strategy Code Preview */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-5 space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                  Strategy Implementation ({strategy.fileName || 'strategy.py'})
                </h3>
                <span className="text-[11px] text-slate-500">
                  Executed server-side in Python
                </span>
              </div>
              <textarea
                rows={6}
                value={strategy.codeSnippet ?? ''}
                onChange={(e) =>
                  setStrategy({ ...strategy, codeSnippet: e.target.value })
                }
                className="w-full rounded-lg border border-slate-300 bg-white dark:border-slate-800 dark:bg-[#080B12] p-3 font-mono text-[11px] text-slate-800 dark:text-slate-300 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
        )}
      </PanelShell>

      <ConfirmDialog
        open={Boolean(rollbackTarget)}
        title={`Rollback Strategy to ${rollbackTarget ?? ''}?`}
        description={`Rolling back ${strategy?.name ?? 'this strategy'} restores the parameters and grading configuration snapshot from ${rollbackTarget ?? ''}. Active runtime execution will use the restored revision.`}
        confirmLabel={`Rollback to ${rollbackTarget ?? ''}`}
        variant="danger"
        isProcessing={rollingBack}
        onConfirm={handleConfirmRollback}
        onCancel={() => setRollbackTarget(null)}
      />
    </div>
  );
}
