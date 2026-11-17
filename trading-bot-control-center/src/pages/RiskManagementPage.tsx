import { useCallback, useEffect, useState } from 'react';
import { Check, Save, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import type {
  AutoPauseRules,
  NewsFilterSettings,
  PairToggleSetting,
  RiskSettings,
  Strategy,
} from '../types';
import { PanelShell } from '../components/DataState';
import { useAppContext } from '../components/AppContext';

export function RiskManagementPage() {
  const { refreshGlobalState } = useAppContext();

  const [risk, setRisk] = useState<RiskSettings | null>(null);
  const [pairToggles, setPairToggles] = useState<PairToggleSetting[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [autoPause, setAutoPause] = useState<AutoPauseRules | null>(null);
  const [newsFilter, setNewsFilter] = useState<NewsFilterSettings | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [savingAutoPause, setSavingAutoPause] = useState(false);
  const [savingNews, setSavingNews] = useState(false);
  const [savingRisk, setSavingRisk] = useState(false);
  const [savedBanner, setSavedBanner] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [riskData, pairsData, stratData, pauseData, newsData] = await Promise.all([
        api.getRiskSettings(),
        api.getPairToggles(),
        api.getStrategies(),
        api.getAutoPauseRules(),
        api.getNewsFilterSettings(),
      ]);
      setRisk(riskData);
      setPairToggles(pairsData);
      setStrategies(stratData);
      setAutoPause(pauseData);
      setNewsFilter(newsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load safety controls');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const showSaved = (msg: string) => {
    setSavedBanner(msg);
    window.setTimeout(() => setSavedBanner(null), 2800);
  };

  const handleTogglePair = async (item: PairToggleSetting) => {
    setBusyKey(`pair-${item.pair}`);
    try {
      const updated = await api.togglePairEnabled(item.pair, !item.enabled);
      setPairToggles((prev) => prev.map((p) => (p.pair === item.pair ? updated : p)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle pair');
    } finally {
      setBusyKey(null);
    }
  };

  const handleToggleStrategy = async (strat: Strategy) => {
    setBusyKey(`strat-${strat.id}`);
    try {
      const updated = await api.toggleStrategyActive(strat.id, !strat.isActive);
      setStrategies((prev) => prev.map((s) => (s.id === strat.id ? updated : s)));
      await refreshGlobalState();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle strategy');
    } finally {
      setBusyKey(null);
    }
  };

  const handleSaveAutoPause = async () => {
    if (!autoPause) return;
    setSavingAutoPause(true);
    try {
      const updated = await api.updateAutoPauseRules(autoPause);
      setAutoPause(updated);
      showSaved('Auto-pause circuit breaker rules saved.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save auto-pause rules');
    } finally {
      setSavingAutoPause(false);
    }
  };

  const handleSaveNewsFilter = async () => {
    if (!newsFilter) return;
    setSavingNews(true);
    try {
      const updated = await api.updateNewsFilterSettings(newsFilter);
      setNewsFilter(updated);
      showSaved('News calendar blackout window saved.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save news filter');
    } finally {
      setSavingNews(false);
    }
  };

  const handleSaveRisk = async () => {
    if (!risk) return;
    setSavingRisk(true);
    try {
      const updated = await api.updateRiskSettings(risk);
      setRisk(updated);
      showSaved('Position sizing and exposure limits saved.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save risk settings');
    } finally {
      setSavingRisk(false);
    }
  };

  const inputClass =
    'w-full rounded-lg border border-slate-300 bg-white dark:border-slate-700 dark:bg-[#111824] px-3 py-2 font-mono text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none';

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Risk &amp; Safety Controls
          </h1>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Per-pair and per-strategy kill switches, automated circuit-breaker rules, news blackout windows, and position sizing caps.
          </p>
        </div>

        {savedBanner && (
          <div className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/35 bg-emerald-500/12 px-3 py-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-300">
            <Check className="h-3.5 w-3.5" />
            <span>{savedBanner}</span>
          </div>
        )}
      </div>

      {/* Per-Pair & Per-Strategy Enable/Disable Toggles */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <PanelShell
          title="Per-Pair Trading Toggles"
          subtitle="Instantly enable or disable automated entries per currency pair"
          isLoading={loading}
          error={error}
          isEmpty={pairToggles.length === 0}
          onRetry={loadAll}
          skeletonRows={4}
        >
          <div className="divide-y divide-slate-200 dark:divide-slate-800/70">
            {pairToggles.map((item) => (
              <div key={item.pair} className="flex items-center justify-between gap-3 py-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-slate-900 dark:text-slate-100">
                      {item.pair}
                    </span>
                    <span
                      className={`text-[11px] font-medium ${
                        item.enabled
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-slate-500'
                      }`}
                    >
                      {item.enabled ? 'Armed' : 'Halted'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                    Spread ~{item.spreadPips}p · Max {item.maxDailyTrades} trades/day
                  </p>
                </div>

                <SwitchButton
                  checked={item.enabled}
                  disabled={busyKey === `pair-${item.pair}`}
                  label={`Toggle ${item.pair}`}
                  onToggle={() => void handleTogglePair(item)}
                />
              </div>
            ))}
          </div>
        </PanelShell>

        <PanelShell
          title="Per-Strategy Execution Toggles"
          subtitle="Arm or disarm individual automated strategy engines"
          isLoading={loading}
          error={error}
          isEmpty={strategies.length === 0}
          onRetry={loadAll}
          skeletonRows={4}
        >
          <div className="divide-y divide-slate-200 dark:divide-slate-800/70">
            {strategies.map((strat) => (
              <div key={strat.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
                      {strat.name}
                    </span>
                    <span className="font-mono text-[11px] text-slate-500">
                      {strat.currentVersion}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono truncate">
                    Pairs: {strat.assignedPairs.join(', ') || 'None'}
                  </p>
                </div>

                <SwitchButton
                  checked={strat.isActive}
                  disabled={busyKey === `strat-${strat.id}`}
                  label={`Toggle ${strat.name}`}
                  onToggle={() => void handleToggleStrategy(strat)}
                />
              </div>
            ))}
          </div>
        </PanelShell>
      </div>

      {/* Auto-Pause Rules */}
      <PanelShell
        title="Auto-Pause Circuit Breaker Rules"
        subtitle="Automatically pause the bot when risk thresholds or connectivity faults occur"
        isLoading={loading}
        error={error}
        isEmpty={!autoPause}
        onRetry={loadAll}
        skeletonRows={4}
        headerRight={
          <button
            type="button"
            disabled={savingAutoPause || !autoPause}
            onClick={() => void handleSaveAutoPause()}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
          >
            <Save className="h-3.5 w-3.5" />
            {savingAutoPause ? 'Saving...' : 'Save Auto-Pause Rules'}
          </button>
        }
      >
        {autoPause && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {/* Daily Loss Limit */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                    Daily Loss Limit (%)
                  </h3>
                  <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                    {autoPause.dailyLossLimit.description}
                  </p>
                </div>
                <SwitchButton
                  checked={autoPause.dailyLossLimit.enabled}
                  label="Toggle daily loss limit"
                  onToggle={() =>
                    setAutoPause({
                      ...autoPause,
                      dailyLossLimit: {
                        ...autoPause.dailyLossLimit,
                        enabled: !autoPause.dailyLossLimit.enabled,
                      },
                    })
                  }
                />
              </div>
              <input
                type="number"
                step="0.25"
                min="0.5"
                max="25"
                disabled={!autoPause.dailyLossLimit.enabled}
                value={autoPause.dailyLossLimit.threshold}
                onChange={(e) =>
                  setAutoPause({
                    ...autoPause,
                    dailyLossLimit: {
                      ...autoPause.dailyLossLimit,
                      threshold: Number(e.target.value),
                    },
                  })
                }
                className={`${inputClass} disabled:opacity-45`}
              />
            </div>

            {/* Max Drawdown */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                    Max Account Drawdown (%)
                  </h3>
                  <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                    {autoPause.maxDrawdown.description}
                  </p>
                </div>
                <SwitchButton
                  checked={autoPause.maxDrawdown.enabled}
                  label="Toggle max drawdown limit"
                  onToggle={() =>
                    setAutoPause({
                      ...autoPause,
                      maxDrawdown: {
                        ...autoPause.maxDrawdown,
                        enabled: !autoPause.maxDrawdown.enabled,
                      },
                    })
                  }
                />
              </div>
              <input
                type="number"
                step="0.5"
                min="1"
                max="50"
                disabled={!autoPause.maxDrawdown.enabled}
                value={autoPause.maxDrawdown.threshold}
                onChange={(e) =>
                  setAutoPause({
                    ...autoPause,
                    maxDrawdown: {
                      ...autoPause.maxDrawdown,
                      threshold: Number(e.target.value),
                    },
                  })
                }
                className={`${inputClass} disabled:opacity-45`}
              />
            </div>

            {/* Connection Lost */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                    Pause on Connection Lost (Seconds)
                  </h3>
                  <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                    {autoPause.connectionLost.description}
                  </p>
                </div>
                <SwitchButton
                  checked={autoPause.connectionLost.enabled}
                  label="Toggle connection lost rule"
                  onToggle={() =>
                    setAutoPause({
                      ...autoPause,
                      connectionLost: {
                        ...autoPause.connectionLost,
                        enabled: !autoPause.connectionLost.enabled,
                      },
                    })
                  }
                />
              </div>
              <input
                type="number"
                step="5"
                min="5"
                max="300"
                disabled={!autoPause.connectionLost.enabled}
                value={autoPause.connectionLost.graceSeconds}
                onChange={(e) =>
                  setAutoPause({
                    ...autoPause,
                    connectionLost: {
                      ...autoPause.connectionLost,
                      graceSeconds: Number(e.target.value),
                    },
                  })
                }
                className={`${inputClass} disabled:opacity-45`}
              />
            </div>

            {/* Consecutive Losses */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                    Consecutive Losses Limit (Trades)
                  </h3>
                  <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                    {autoPause.consecutiveLosses.description}
                  </p>
                </div>
                <SwitchButton
                  checked={autoPause.consecutiveLosses.enabled}
                  label="Toggle consecutive losses rule"
                  onToggle={() =>
                    setAutoPause({
                      ...autoPause,
                      consecutiveLosses: {
                        ...autoPause.consecutiveLosses,
                        enabled: !autoPause.consecutiveLosses.enabled,
                      },
                    })
                  }
                />
              </div>
              <input
                type="number"
                step="1"
                min="1"
                max="20"
                disabled={!autoPause.consecutiveLosses.enabled}
                value={autoPause.consecutiveLosses.threshold}
                onChange={(e) =>
                  setAutoPause({
                    ...autoPause,
                    consecutiveLosses: {
                      ...autoPause.consecutiveLosses,
                      threshold: Number(e.target.value),
                    },
                  })
                }
                className={`${inputClass} disabled:opacity-45`}
              />
            </div>
          </div>
        )}
      </PanelShell>

      {/* News Blackout Window + Risk Allocation */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <PanelShell
          className="lg:col-span-5"
          title="News Calendar Blackout Window"
          subtitle="Stay out of new trades before & after high-impact economic releases"
          isLoading={loading}
          error={error}
          isEmpty={!newsFilter}
          onRetry={loadAll}
          headerRight={
            <button
              type="button"
              disabled={savingNews || !newsFilter}
              onClick={() => void handleSaveNewsFilter()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 disabled:opacity-50"
            >
              <Save className="h-3.5 w-3.5" />
              {savingNews ? 'Saving...' : 'Save'}
            </button>
          }
        >
          {newsFilter && (
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-3">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-800 dark:text-slate-200">
                  <ShieldCheck className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  <span>Enforce High-Impact News Blackout</span>
                </div>
                <SwitchButton
                  checked={newsFilter.enabled}
                  label="Toggle news filter"
                  onToggle={() =>
                    setNewsFilter({ ...newsFilter, enabled: !newsFilter.enabled })
                  }
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                    Minutes Before Release
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="240"
                    disabled={!newsFilter.enabled}
                    value={newsFilter.minutesBefore}
                    onChange={(e) =>
                      setNewsFilter({
                        ...newsFilter,
                        minutesBefore: Number(e.target.value),
                      })
                    }
                    className={`${inputClass} disabled:opacity-45`}
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                    Minutes After Release
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="240"
                    disabled={!newsFilter.enabled}
                    value={newsFilter.minutesAfter}
                    onChange={(e) =>
                      setNewsFilter({
                        ...newsFilter,
                        minutesAfter: Number(e.target.value),
                      })
                    }
                    className={`${inputClass} disabled:opacity-45`}
                  />
                </div>
              </div>
            </div>
          )}
        </PanelShell>

        <PanelShell
          className="lg:col-span-7"
          title="Position Sizing &amp; Exposure Caps"
          subtitle="Pre-trade portfolio limits enforced by the FastAPI risk guard"
          isLoading={loading}
          error={error}
          isEmpty={!risk}
          onRetry={loadAll}
          headerRight={
            <button
              type="button"
              disabled={savingRisk || !risk}
              onClick={() => void handleSaveRisk()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 disabled:opacity-50"
            >
              <Save className="h-3.5 w-3.5" />
              {savingRisk ? 'Saving...' : 'Save Limits'}
            </button>
          }
        >
          {risk && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                  Position Sizing Model
                </label>
                <select
                  value={risk.positionSizingModel}
                  onChange={(e) =>
                    setRisk({
                      ...risk,
                      positionSizingModel: e.target.value as RiskSettings['positionSizingModel'],
                    })
                  }
                  className={inputClass}
                >
                  <option value="fixed_fractional">Fixed Fractional (% Equity)</option>
                  <option value="volatility_adjusted">ATR Volatility-Adjusted</option>
                  <option value="fixed_lot">Fixed Lot Size</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                  Max Risk Per Trade (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={risk.maxRiskPerTradePercent}
                  onChange={(e) =>
                    setRisk({ ...risk, maxRiskPerTradePercent: Number(e.target.value) })
                  }
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                  Max Concurrent Open Trades
                </label>
                <input
                  type="number"
                  value={risk.maxOpenTrades}
                  onChange={(e) =>
                    setRisk({ ...risk, maxOpenTrades: Number(e.target.value) })
                  }
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                  Max Correlated Exposure (%)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={risk.maxCorrelatedExposurePercent}
                  onChange={(e) =>
                    setRisk({
                      ...risk,
                      maxCorrelatedExposurePercent: Number(e.target.value),
                    })
                  }
                  className={inputClass}
                />
              </div>
            </div>
          )}
        </PanelShell>
      </div>
    </div>
  );
}

function SwitchButton({
  checked,
  disabled,
  label,
  onToggle,
}: {
  checked: boolean;
  disabled?: boolean;
  label: string;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={onToggle}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none disabled:opacity-50 ${
        checked ? 'bg-emerald-600' : 'bg-slate-300 dark:bg-slate-700'
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${
          checked ? 'translate-x-5' : 'translate-x-0'
        }`}
      />
    </button>
  );
}
