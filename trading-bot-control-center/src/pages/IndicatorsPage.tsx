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

export function IndicatorsPage() {
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<'ALL' | Indicator['category']>('ALL');

  const [editingIndicator, setEditingIndicator] = useState<Indicator | null>(null);
  const [savingEdit, setSavingEdit] = useState(false);

  const [addOpen, setAddOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newShortCode, setNewShortCode] = useState('');
  const [newCategory, setNewCategory] = useState<Indicator['category']>('Momentum');
  const [newDescription, setNewDescription] = useState('');
  const [newParamLabel, setNewParamLabel] = useState('Lookback Period');
  const [newParamDefault, setNewParamDefault] = useState(14);
  const [creating, setCreating] = useState(false);

  const [savedId, setSavedId] = useState<string | null>(null);

  const loadIndicators = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getIndicators();
      setIndicators(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load indicators');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadIndicators();
  }, [loadIndicators]);

  const handleSaveEdit = async () => {
    if (!editingIndicator) return;
    setSavingEdit(true);
    try {
      const updated = await api.updateIndicator(editingIndicator.id, {
        parameters: editingIndicator.parameters,
        description: editingIndicator.description,
      });
      setIndicators((prev) =>
        prev.map((i) => (i.id === updated.id ? updated : i))
      );
      setSavedId(updated.id);
      setEditingIndicator(null);
      window.setTimeout(() => setSavedId(null), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update indicator');
    } finally {
      setSavingEdit(false);
    }
  };

  const handleCreateCustom = async (e: FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !newShortCode.trim()) return;
    setCreating(true);
    try {
      const params: IndicatorParameter[] = [
        {
          key: 'period',
          label: newParamLabel.trim() || 'Period',
          type: 'number',
          defaultValue: newParamDefault,
          min: 1,
          max: 500,
          step: 1,
        },
      ];
      const created = await api.createIndicator({
        name: newName.trim(),
        shortCode: newShortCode.trim().toUpperCase(),
        category: newCategory,
        description: newDescription.trim() || 'Custom indicator module.',
        parameters: params,
      });
      setIndicators((prev) => [...prev, created]);
      setAddOpen(false);
      setNewName('');
      setNewShortCode('');
      setNewDescription('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create indicator');
    } finally {
      setCreating(false);
    }
  };

  const filtered =
    categoryFilter === 'ALL'
      ? indicators
      : indicators.filter((i) => i.category === categoryFilter);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Indicators Library
          </h1>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Technical indicators computed by the Python backend engine. Configure default parameters or register custom entries.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setAddOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500 transition-colors whitespace-nowrap"
        >
          <Plus className="h-4 w-4" />
          Add Custom Indicator
        </button>
      </div>

      {/* Category Filter Bar */}
      <div className="flex flex-wrap items-center gap-1.5 rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-2">
        {(['ALL', ...CATEGORIES] as const).map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setCategoryFilter(cat)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap ${
              categoryFilter === cat
                ? 'bg-slate-200 text-slate-900 dark:bg-slate-800 dark:text-slate-100'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
            }`}
          >
            {cat === 'ALL' ? 'All Categories' : cat}
          </button>
        ))}
      </div>

      <PanelShell
        title="Available Indicators"
        subtitle={`${filtered.length} indicator definition${filtered.length === 1 ? '' : 's'}`}
        isLoading={loading}
        error={error}
        isEmpty={filtered.length === 0}
        emptyTitle="No indicators in this category"
        emptyDescription="Select another category or add a custom indicator entry."
        emptyActionLabel="Add Custom Indicator"
        onEmptyAction={() => setAddOpen(true)}
        onRetry={loadIndicators}
        skeletonRows={5}
      >
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((ind) => (
            <div
              key={ind.id}
              className="flex flex-col justify-between rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-4"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">
                        {ind.shortCode}
                      </span>
                      <span className="text-slate-400 dark:text-slate-600">·</span>
                      <span className="text-xs text-slate-500 dark:text-slate-400">{ind.category}</span>
                      {ind.isCustom && (
                        <>
                          <span className="text-slate-400 dark:text-slate-600">·</span>
                          <span className="text-[11px] font-medium text-amber-600 dark:text-amber-300">
                            Custom
                          </span>
                        </>
                      )}
                    </div>
                    <h3 className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">
                      {ind.name}
                    </h3>
                  </div>

                  {savedId === ind.id ? (
                    <span className="inline-flex items-center gap-1 text-[11px] text-emerald-600 dark:text-emerald-400">
                      <Check className="h-3.5 w-3.5" />
                      Saved
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={() =>
                        setEditingIndicator(JSON.parse(JSON.stringify(ind)) as Indicator)
                      }
                      className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800/80 dark:text-slate-200 dark:hover:bg-slate-700 whitespace-nowrap"
                    >
                      <Pencil className="h-3 w-3" />
                      Edit Params
                    </button>
                  )}
                </div>

                <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                  {ind.description}
                </p>
              </div>

              <div className="border-t border-slate-200 dark:border-slate-800/80 pt-3">
                <p className="text-[11px] font-medium text-slate-500 mb-2">
                  Default Parameters
                </p>
                <div className="space-y-1.5">
                  {ind.parameters.map((p) => (
                    <div
                      key={p.key}
                      className="flex items-center justify-between text-xs"
                    >
                      <span className="text-slate-600 dark:text-slate-300">{p.label}</span>
                      <span className="font-mono text-slate-900 dark:text-slate-100 tabular-nums">
                        {String(p.defaultValue)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </PanelShell>

      {/* Edit Default Parameters Modal */}
      {editingIndicator && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 dark:bg-black/70 p-4 backdrop-blur-xs"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-[#111824] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Edit {editingIndicator.name} ({editingIndicator.shortCode})
              </h2>
              <button
                type="button"
                onClick={() => setEditingIndicator(null)}
                className="rounded p-1 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3">
              {editingIndicator.parameters.map((p) => (
                <div key={p.key}>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    {p.label}
                  </label>
                  {p.type === 'number' ? (
                    <input
                      type="number"
                      min={p.min}
                      max={p.max}
                      step={p.step ?? 1}
                      value={Number(p.defaultValue)}
                      onChange={(e) =>
                        setEditingIndicator((prev) =>
                          prev
                            ? {
                                ...prev,
                                parameters: prev.parameters.map((item) =>
                                  item.key === p.key
                                    ? { ...item, defaultValue: Number(e.target.value) }
                                    : item
                                ),
                              }
                            : null
                        )
                      }
                      className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 font-mono text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                    />
                  ) : (
                    <select
                      value={String(p.defaultValue)}
                      onChange={(e) =>
                        setEditingIndicator((prev) =>
                          prev
                            ? {
                                ...prev,
                                parameters: prev.parameters.map((item) =>
                                  item.key === p.key
                                    ? { ...item, defaultValue: e.target.value }
                                    : item
                                ),
                              }
                            : null
                        )
                      }
                      className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                    >
                      {p.options?.map((opt) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3 border-t border-slate-200 dark:border-slate-800 pt-4">
              <button
                type="button"
                onClick={() => setEditingIndicator(null)}
                className="rounded-lg border border-slate-300 bg-slate-100 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveEdit}
                disabled={savingEdit}
                className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
              >
                <Save className="h-3.5 w-3.5" />
                {savingEdit ? 'Saving...' : 'Save Parameters'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Custom Indicator Modal */}
      {addOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 dark:bg-black/70 p-4 backdrop-blur-xs"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-[#111824] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3 mb-4">
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Add Custom Indicator
              </h2>
              <button
                type="button"
                onClick={() => setAddOpen(false)}
                className="rounded p-1 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreateCustom} className="space-y-3.5">
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Indicator Name
                  </label>
                  <input
                    type="text"
                    required
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="e.g. Hull Moving Average"
                    className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Code
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={10}
                    value={newShortCode}
                    onChange={(e) => setNewShortCode(e.target.value)}
                    placeholder="HMA"
                    className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 font-mono text-xs text-slate-900 dark:text-slate-100 uppercase focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Category
                </label>
                <select
                  value={newCategory}
                  onChange={(e) =>
                    setNewCategory(e.target.value as Indicator['category'])
                  }
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Describe how the indicator behaves and what signals it provides..."
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Primary Parameter Label
                  </label>
                  <input
                    type="text"
                    value={newParamLabel}
                    onChange={(e) => setNewParamLabel(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Default Value
                  </label>
                  <input
                    type="number"
                    value={newParamDefault}
                    onChange={(e) => setNewParamDefault(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 font-mono text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 border-t border-slate-200 dark:border-slate-800 pt-4">
                <button
                  type="button"
                  onClick={() => setAddOpen(false)}
                  className="rounded-lg border border-slate-300 bg-slate-100 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
                >
                  {creating ? 'Adding...' : 'Add Indicator'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
