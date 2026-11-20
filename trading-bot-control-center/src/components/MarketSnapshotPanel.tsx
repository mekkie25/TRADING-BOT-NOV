import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { MarketSnapshotInfo } from '../types';
import { formatDateTime } from '../utils/formatters';

const SNAPSHOT_POLL_INTERVAL_MS = 5000;
const INDICATOR_REPORTS = new Set(['exponential_moving_averages']);

function formatReport(value: unknown): string {
  if (typeof value === 'string') {
    return value;
  }
  return JSON.stringify(value, null, 2) ?? 'Unavailable';
}

function getReportSummary(value: unknown): string | null {
  if (
    typeof value === 'object' &&
    value !== null &&
    'summary' in value &&
    typeof value.summary === 'string'
  ) {
    return value.summary;
  }
  return null;
}

function ReportDetails({ name, value }: { name: string; value: unknown }) {
  const summary = getReportSummary(value);

  return (
    <details className="rounded-lg border border-slate-200 dark:border-slate-700">
      <summary className="cursor-pointer px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-200">
        {name.replaceAll('_', ' ')}
      </summary>
      {summary && (
        <p className="border-t border-slate-200 px-3 py-2 text-xs text-slate-600 dark:border-slate-700 dark:text-slate-300">
          {summary}
        </p>
      )}
      <pre className="max-h-72 overflow-auto border-t border-slate-200 px-3 py-2 text-[11px] leading-relaxed text-slate-600 dark:border-slate-700 dark:text-slate-300">
        {formatReport(value)}
      </pre>
    </details>
  );
}

export function MarketSnapshotPanel() {
  const [snapshot, setSnapshot] = useState<MarketSnapshotInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    let polling = false;

    const poll = async () => {
      if (polling) return;
      polling = true;
      try {
        const result = await api.getMarketSnapshot();
        if (!active) return;
        setSnapshot(result);
        setError(null);
      } catch (requestError) {
        if (!active) return;
        setError(
          requestError instanceof Error
            ? requestError.message
            : 'Could not load the market snapshot.',
        );
      } finally {
        polling = false;
        if (active) setLoading(false);
      }
    };

    void poll();
    const timer = window.setInterval(() => void poll(), SNAPSHOT_POLL_INTERVAL_MS);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const contextReports = snapshot
    ? {
        market_time: snapshot.market_time,
        session: snapshot.session,
        spread: snapshot.spread,
        multi_timeframe_alignment: snapshot.multi_timeframe_alignment,
        trend_lines: snapshot.trend_lines,
        previous_day_levels: snapshot.previous_day_levels,
        previous_week_levels: snapshot.previous_week_levels,
        daily_profiles: snapshot.daily_profiles,
      }
    : null;

  return (
    <section
      aria-label="One-minute market snapshot"
      className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800/90 dark:bg-[#111824]"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            One-Minute Market Snapshot
          </h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Read-only reports update after completed M1 candles. This panel checks for
            new reports every five seconds.
          </p>
        </div>
        {snapshot && (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {snapshot.symbol} · Report time: {formatDateTime(snapshot.as_of)}
          </p>
        )}
      </div>

      {error && (
        <p
          role="status"
          aria-live="polite"
          className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-950/30 dark:text-amber-300"
        >
          {error}
        </p>
      )}
      {snapshot?.latest_snapshot_error && (
        <p
          role="status"
          aria-live="polite"
          className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-950/30 dark:text-amber-300"
        >
          The latest report could not be refreshed: {snapshot.latest_snapshot_error}
        </p>
      )}

      {!snapshot ? (
        <p className="mt-4 text-xs text-slate-500 dark:text-slate-400" role="status">
          {loading
            ? 'Waiting for the first completed market report.'
            : 'No market snapshot is available yet.'}
        </p>
      ) : (
        <>
          <div className="mt-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Market context
            </h3>
            <div className="grid gap-2 md:grid-cols-2">
              {Object.entries(contextReports ?? {}).map(([name, value]) => (
                <ReportDetails key={name} name={name} value={value} />
              ))}
            </div>
          </div>

          {(['M1', 'M5'] as const).map((timeframe) => {
            const reports = snapshot.reports[timeframe] ?? {};
            const marketReports = Object.entries(reports).filter(
              ([name]) => !INDICATOR_REPORTS.has(name),
            );
            const indicatorReports = Object.entries(reports).filter(([name]) =>
              INDICATOR_REPORTS.has(name),
            );

            return (
              <div className="mt-4" key={timeframe}>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  {timeframe} market reports
                </h3>
                <div className="grid gap-2 md:grid-cols-2">
                  {marketReports.map(([name, value]) => (
                    <ReportDetails key={name} name={name} value={value} />
                  ))}
                </div>
                {indicatorReports.length > 0 && (
                  <div className="mt-4">
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      {timeframe} indicator reports
                    </h4>
                    <div className="grid gap-2 md:grid-cols-2">
                      {indicatorReports.map(([name, value]) => (
                        <ReportDetails key={name} name={name} value={value} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          <div className="mt-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Unavailable reports
            </h3>
            <dl className="grid gap-2 md:grid-cols-2">
              {Object.entries(snapshot.unavailable_reports).map(([name, reason]) => (
                <div
                  className="rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-700"
                  key={name}
                >
                  <dt className="text-xs font-medium capitalize text-slate-700 dark:text-slate-200">
                    {name.replaceAll('_', ' ')}
                  </dt>
                  <dd className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                    {reason}
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          <p className="mt-4 text-[11px] text-slate-500 dark:text-slate-400">
            Entry criteria were not evaluated. Reports remain separate observations; no
            combined score or trade decision is produced.
          </p>
        </>
      )}
    </section>
  );
}
