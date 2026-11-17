import { useCallback, useEffect, useState } from 'react';
import {
  CheckCircle2,
  DownloadCloud,
  Eye,
  RefreshCw,
  ShieldCheck,
  X,
} from 'lucide-react';
import { api } from '../services/api';
import type { DataGap, HistoricalDataset } from '../types';
import { PanelShell } from '../components/DataState';
import { formatDateTime } from '../utils/formatters';

export function DataManagerPage() {
  const [datasets, setDatasets] = useState<HistoricalDataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [gapsModalDataset, setGapsModalDataset] = useState<HistoricalDataset | null>(null);
  const [gaps, setGaps] = useState<DataGap[]>([]);
  const [loadingGaps, setLoadingGaps] = useState(false);

  const loadDatasets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await api.getDatasets();
      setDatasets(list);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load historical datasets');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDatasets();
  }, [loadDatasets]);

  const handleDownload = async (ds: HistoricalDataset) => {
    setBusyId(ds.id);
    setNotice(null);
    try {
      const updated = await api.downloadDataset(ds.id);
      setDatasets((prev) => prev.map((d) => (d.id === ds.id ? updated : d)));
      setNotice(`Synced latest ${ds.pair} ${ds.timeframe} candles from broker archive.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Dataset download failed');
    } finally {
      setBusyId(null);
    }
  };

  const handleValidate = async (ds: HistoricalDataset) => {
    setBusyId(ds.id);
    setNotice(null);
    try {
      const updated = await api.validateDataset(ds.id);
      setDatasets((prev) => prev.map((d) => (d.id === ds.id ? updated : d)));
      setNotice(
        `Integrity check completed for ${ds.pair} ${ds.timeframe}: ${updated.gapsFound} gap(s) logged.`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
    } finally {
      setBusyId(null);
    }
  };

  const handleViewGaps = async (ds: HistoricalDataset) => {
    setGapsModalDataset(ds);
    setLoadingGaps(true);
    setGaps([]);
    try {
      const found = await api.getDatasetGaps(ds.id);
      setGaps(found);
    } finally {
      setLoadingGaps(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Historical Data Manager
          </h1>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Inspect cached OHLCV candle stores, trigger broker backfills, validate continuity, and audit missing bar gaps.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void loadDatasets()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors whitespace-nowrap"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Store
        </button>
      </div>

      {notice && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-500/35 bg-emerald-500/10 px-4 py-2.5 text-xs text-emerald-800 dark:text-emerald-300">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{notice}</span>
        </div>
      )}

      <PanelShell
        title="Pair & Timeframe Archives"
        subtitle="Cached Parquet / SQL candle partitions used by the FastAPI backtester"
        isLoading={loading}
        error={error}
        isEmpty={datasets.length === 0}
        onRetry={loadDatasets}
        skeletonRows={6}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 whitespace-nowrap">
                <th className="py-2.5 pr-3 font-medium">Pair</th>
                <th className="py-2.5 px-3 font-medium">Timeframe</th>
                <th className="py-2.5 px-3 font-medium">Start Date</th>
                <th className="py-2.5 px-3 font-medium">End Date</th>
                <th className="py-2.5 px-3 font-medium text-right">Candles</th>
                <th className="py-2.5 px-3 font-medium text-right">Gaps Found</th>
                <th className="py-2.5 px-3 font-medium">Last Updated</th>
                <th className="py-2.5 px-3 font-medium">Status</th>
                <th className="py-2.5 pl-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
              {datasets.map((ds) => {
                const isBusy = busyId === ds.id;
                return (
                  <tr key={ds.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/35">
                    <td className="py-3 pr-3 font-mono font-semibold text-slate-900 dark:text-slate-100 whitespace-nowrap">
                      {ds.pair}
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-700 dark:text-slate-300 whitespace-nowrap">
                      {ds.timeframe}
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-600 dark:text-slate-300 tabular-nums whitespace-nowrap">
                      {ds.startDate}
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-600 dark:text-slate-300 tabular-nums whitespace-nowrap">
                      {ds.endDate}
                    </td>
                    <td className="py-3 px-3 text-right font-mono tabular-nums text-slate-800 dark:text-slate-200 whitespace-nowrap">
                      {ds.candleCount.toLocaleString('en-US')}
                    </td>
                    <td className="py-3 px-3 text-right font-mono tabular-nums whitespace-nowrap">
                      <span
                        className={
                          ds.gapsFound > 0
                            ? 'font-semibold text-amber-600 dark:text-amber-400'
                            : 'text-emerald-600 dark:text-emerald-400'
                        }
                      >
                        {ds.gapsFound}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-500 dark:text-slate-400 whitespace-nowrap">
                      {formatDateTime(ds.lastUpdated)}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span
                        className={`rounded border px-2 py-0.5 text-[11px] font-medium ${
                          ds.status === 'Up to date'
                            ? 'border-emerald-500/35 bg-emerald-500/12 text-emerald-700 dark:text-emerald-300'
                            : 'border-amber-500/35 bg-amber-500/12 text-amber-700 dark:text-amber-300'
                        }`}
                      >
                        {ds.status}
                      </span>
                    </td>
                    <td className="py-3 pl-3 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          type="button"
                          disabled={isBusy}
                          onClick={() => void handleDownload(ds)}
                          className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 disabled:opacity-50"
                        >
                          <DownloadCloud className="h-3 w-3" />
                          Update
                        </button>
                        <button
                          type="button"
                          disabled={isBusy}
                          onClick={() => void handleValidate(ds)}
                          className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 disabled:opacity-50"
                        >
                          <ShieldCheck className="h-3 w-3" />
                          Validate
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleViewGaps(ds)}
                          className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                        >
                          <Eye className="h-3 w-3" />
                          Gaps
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

      {/* View Gaps Modal */}
      {gapsModalDataset && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 dark:bg-black/70 p-4 backdrop-blur-xs"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-2xl rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-[#111824] p-6 shadow-2xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3 mb-4">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Detected Candle Gaps · {gapsModalDataset.pair} ({gapsModalDataset.timeframe})
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Missing bar timestamps excluded from indicator lookback windows
                </p>
              </div>
              <button
                type="button"
                onClick={() => setGapsModalDataset(null)}
                className="rounded-md p-1 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {loadingGaps ? (
              <div className="py-8 text-center text-xs text-slate-500">Scanning gap index...</div>
            ) : gaps.length === 0 ? (
              <div className="rounded-lg border border-emerald-500/35 bg-emerald-500/10 p-4 text-xs text-emerald-700 dark:text-emerald-300">
                Zero continuity gaps detected in {gapsModalDataset.pair} {gapsModalDataset.timeframe}.
              </div>
            ) : (
              <div className="space-y-2.5">
                {gaps.map((g) => (
                  <div
                    key={g.id}
                    className="rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-3 text-xs"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-mono font-semibold text-slate-900 dark:text-slate-100">
                        {formatDateTime(g.gapStart)} → {formatDateTime(g.gapEnd)}
                      </span>
                      <span className="font-mono text-amber-600 dark:text-amber-400 font-semibold">
                        {g.missingCandles} missing bar{g.missingCandles === 1 ? '' : 's'}
                      </span>
                    </div>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">{g.reason}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
