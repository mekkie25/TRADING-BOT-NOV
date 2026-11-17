import { useEffect, useState, type ChangeEvent } from 'react';
import { Check, ImagePlus, Plus, Save, Trash2, X } from 'lucide-react';
import type { JournalTrade } from '../types';
import { GradeBadge } from './GradeBadge';
import { useAppContext } from './AppContext';
import {
  formatDateTime,
  formatDuration,
  formatPairPrice,
} from '../utils/formatters';

interface JournalDrawerProps {
  trade: JournalTrade | null;
  onClose: () => void;
  onSaveMeta: (
    tradeId: string,
    patch: { notes?: string; tags?: string[]; screenshotUrl?: string }
  ) => Promise<void>;
}

export function JournalDrawer({
  trade,
  onClose,
  onSaveMeta,
}: JournalDrawerProps) {
  const { formatDisplayAmount } = useAppContext();

  const [notes, setNotes] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');
  const [screenshotUrl, setScreenshotUrl] = useState<string | undefined>(undefined);
  const [saving, setSaving] = useState(false);
  const [savedNotice, setSavedNotice] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    setNotes(trade?.notes ?? '');
    setTags(trade?.tags ?? []);
    setScreenshotUrl(trade?.screenshotUrl);
    setNewTag('');
    setSavedNotice(false);
    setSaveError(null);
  }, [trade]);

  if (!trade) return null;

  const isWin = trade.pnl > 0;

  const handleAddTag = () => {
    const cleaned = newTag.trim().toLowerCase().replace(/\s+/g, '-');
    if (!cleaned || tags.includes(cleaned)) return;
    setTags((prev) => [...prev, cleaned]);
    setNewTag('');
  };

  const handleRemoveTag = (tag: string) => {
    setTags((prev) => prev.filter((t) => t !== tag));
  };

  const handleScreenshotChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        setScreenshotUrl(reader.result);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);
    setSavedNotice(false);
    try {
      await onSaveMeta(trade.id, { notes, tags, screenshotUrl });
      setSavedNotice(true);
      window.setTimeout(() => setSavedNotice(false), 2500);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save trade review');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50 dark:bg-black/60 backdrop-blur-xs">
      <div className="fixed inset-0" onClick={onClose} />
      <aside
        className="relative z-10 flex h-full w-full max-w-lg flex-col border-l border-slate-200 bg-white dark:border-slate-800 dark:bg-[#111824] shadow-2xl"
        aria-label="Trade details"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="font-mono text-base font-bold text-slate-900 dark:text-slate-100">
              {trade.pair}
            </span>
            <span
              className={`font-mono text-xs font-semibold ${
                trade.direction === 'BUY'
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              {trade.direction}
            </span>
            <GradeBadge grade={trade.setupGrade} />
            {trade.strategyVersion && (
              <span className="font-mono text-[11px] text-slate-500">
                {trade.strategyVersion}
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition-colors"
            aria-label="Close trade detail panel"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
          {/* P/L & R Banner */}
          <div className="grid grid-cols-3 gap-3 rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4">
            <div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Net P/L</p>
              <p
                className={`mt-1 font-mono text-base font-bold tabular-nums ${
                  isWin
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-red-600 dark:text-red-400'
                }`}
              >
                {formatDisplayAmount(trade.pnl, trade.currency, { signed: true })}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">R Multiple</p>
              <p
                className={`mt-1 font-mono text-base font-bold tabular-nums ${
                  trade.rMultiple >= 0
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-red-600 dark:text-red-400'
                }`}
              >
                {trade.rMultiple >= 0 ? '+' : ''}
                {trade.rMultiple.toFixed(2)}R
              </p>
            </div>
            <div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Duration</p>
              <p className="mt-1 font-mono text-base font-bold text-slate-900 dark:text-slate-100 tabular-nums">
                {formatDuration(trade.durationMinutes)}
              </p>
            </div>
          </div>

          {/* Execution Levels */}
          <div>
            <h3 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-3">
              Execution &amp; Price Levels
            </h3>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2.5 text-xs border-t border-slate-200 dark:border-slate-800 pt-3">
              <DetailItem label="Trade ID" value={trade.id} mono />
              <DetailItem label="Strategy" value={trade.strategyName} />
              <DetailItem label="Opened At" value={formatDateTime(trade.openedAt)} mono />
              <DetailItem label="Closed At" value={formatDateTime(trade.closedAt)} mono />
              <DetailItem label="Entry Price" value={formatPairPrice(trade.entryPrice, trade.pair)} mono />
              <DetailItem label="Exit Price" value={formatPairPrice(trade.exitPrice, trade.pair)} mono />
              <DetailItem label="Stop Loss" value={formatPairPrice(trade.stopLoss, trade.pair)} mono />
              <DetailItem label="Take Profit" value={formatPairPrice(trade.takeProfit, trade.pair)} mono />
              <DetailItem label="Position Size" value={`${trade.sizeLots.toFixed(2)} lots`} mono />
              <DetailItem
                label="Commission / Swap"
                value={`${formatDisplayAmount(trade.commission, trade.currency)} / ${formatDisplayAmount(trade.swap, trade.currency)}`}
                mono
              />
              <DetailItem label="MAE (Max Adverse)" value={`-${trade.maeR.toFixed(2)}R`} mono />
              <DetailItem label="MFE (Max Favourable)" value={`+${trade.mfeR.toFixed(2)}R`} mono />
            </dl>
          </div>

          {/* Market Conditions at Entry */}
          <div>
            <h3 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-3">
              Market Conditions at Entry
            </h3>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2.5 text-xs border-t border-slate-200 dark:border-slate-800 pt-3">
              <DetailItem label="Volatility Regime" value={trade.marketConditions.volatilityRegime} />
              <DetailItem label="Market Structure" value={trade.marketConditions.marketStructure} />
              <DetailItem label="Session" value={trade.marketConditions.session} />
              <DetailItem label="HTF Bias" value={trade.marketConditions.htfBias} />
              <DetailItem
                label="Spread at Entry"
                value={`${trade.marketConditions.spreadPips.toFixed(1)} pips`}
                mono
              />
              <DetailItem label="ATR(14)" value={`${trade.marketConditions.atrPips} pips`} mono />
              <DetailItem
                label="News Nearby"
                value={
                  trade.marketConditions.newsNearby
                    ? `Yes (${trade.marketConditions.newsEvent || 'High-impact'})`
                    : 'No'
                }
              />
            </dl>
          </div>

          {/* Trade Tags */}
          <div className="space-y-2.5">
            <h3 className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Trade Tags
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {tags.length === 0 ? (
                <span className="text-[11px] text-slate-500">No tags assigned</span>
              ) : (
                tags.map((tg) => (
                  <span
                    key={tg}
                    className="inline-flex items-center gap-1 rounded border border-slate-300 bg-slate-100 dark:border-slate-700 dark:bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-slate-700 dark:text-slate-200"
                  >
                    #{tg}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tg)}
                      className="text-slate-400 hover:text-red-500"
                      aria-label={`Remove tag ${tg}`}
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))
              )}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddTag();
                  }
                }}
                placeholder="Add tag (e.g. a-plus-retest)"
                className="flex-1 rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={handleAddTag}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                <Plus className="h-3.5 w-3.5" />
                Add
              </button>
            </div>
          </div>

          {/* Chart Screenshot Attachment */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Chart Screenshot Attachment
              </h3>
              <label className="inline-flex cursor-pointer items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400">
                <ImagePlus className="h-3.5 w-3.5" />
                <span>{screenshotUrl ? 'Replace Image' : 'Attach Chart Image'}</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleScreenshotChange}
                  className="hidden"
                />
              </label>
            </div>

            {screenshotUrl ? (
              <div className="relative rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden bg-slate-50 dark:bg-[#0B0F17]">
                <img
                  src={screenshotUrl}
                  alt={`Chart screenshot for ${trade.pair}`}
                  className="max-h-52 w-full object-contain"
                />
                <button
                  type="button"
                  onClick={() => setScreenshotUrl(undefined)}
                  className="absolute top-2 right-2 rounded-md bg-black/70 p-1.5 text-white hover:bg-red-600"
                  aria-label="Remove screenshot"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ) : (
              <p className="rounded-lg border border-dashed border-slate-300 dark:border-slate-700 py-4 text-center text-[11px] text-slate-500">
                No chart screenshot attached to this trade.
              </p>
            )}
          </div>

          {/* Editable Notes */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label
                htmlFor="trade-notes-input"
                className="text-xs font-semibold text-slate-700 dark:text-slate-300"
              >
                Trade Notes &amp; Review
              </label>
              {savedNotice && (
                <span className="inline-flex items-center gap-1 text-[11px] text-emerald-600 dark:text-emerald-400">
                  <Check className="h-3 w-3" />
                  Saved
                </span>
              )}
            </div>
            <textarea
              id="trade-notes-input"
              rows={4}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record execution observations, setup quality nuances, or psychology notes..."
              className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2.5 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
            />
            {saveError && (
              <p className="mt-1.5 text-xs text-red-600 dark:text-red-400">{saveError}</p>
            )}
            <div className="mt-3 flex justify-end">
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-60 transition-colors whitespace-nowrap"
              >
                <Save className="h-3.5 w-3.5" />
                {saving ? 'Saving...' : 'Save Review'}
              </button>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}

function DetailItem({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <dt className="text-[11px] text-slate-500">{label}</dt>
      <dd
        className={`mt-0.5 text-slate-800 dark:text-slate-200 ${
          mono ? 'font-mono tabular-nums' : ''
        }`}
      >
        {value}
      </dd>
    </div>
  );
}
