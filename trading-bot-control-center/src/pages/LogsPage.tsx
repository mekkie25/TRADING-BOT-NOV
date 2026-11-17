import { useCallback, useEffect, useMemo, useState } from 'react';
import { Download, RefreshCw, Search } from 'lucide-react';
import { api } from '../services/api';
import type {
  ActivityLogEntry,
  ErrorLogEntry,
  ErrorSeverity,
  TradeAuditEntry,
} from '../types';
import { PanelShell } from '../components/DataState';
import { exportRowsToCsv, formatDateTime } from '../utils/formatters';

type LogTab = 'activity' | 'errors' | 'audit';

export function LogsPage() {
  const [activeTab, setActiveTab] = useState<LogTab>('activity');
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<ErrorSeverity | 'ALL'>('ALL');
  const [auditStatusFilter, setAuditStatusFilter] = useState<string>('ALL');

  const [activity, setActivity] = useState<ActivityLogEntry[]>([]);
  const [errors, setErrors] = useState<ErrorLogEntry[]>([]);
  const [audits, setAudits] = useState<TradeAuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [act, errs, aud] = await Promise.all([
        api.getActivityLog(100),
        api.getErrorLogs(),
        api.getTradeAuditLogs(),
      ]);
      setActivity(act);
      setErrors(errs);
      setAudits(aud);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Failed to load system logs');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const q = search.trim().toLowerCase();

  const filteredActivity = useMemo(
    () =>
      activity.filter(
        (a) =>
          !q ||
          a.message.toLowerCase().includes(q) ||
          (a.pair ?? '').toLowerCase().includes(q) ||
          (a.strategyName ?? '').toLowerCase().includes(q) ||
          (a.details ?? '').toLowerCase().includes(q)
      ),
    [activity, q]
  );

  const filteredErrors = useMemo(
    () =>
      errors.filter((e) => {
        if (severityFilter !== 'ALL' && e.severity !== severityFilter) return false;
        if (!q) return true;
        return (
          e.message.toLowerCase().includes(q) ||
          e.component.toLowerCase().includes(q) ||
          (e.stackSummary ?? '').toLowerCase().includes(q)
        );
      }),
    [errors, severityFilter, q]
  );

  const filteredAudits = useMemo(
    () =>
      audits.filter((a) => {
        if (auditStatusFilter !== 'ALL' && a.brokerResponse !== auditStatusFilter) {
          return false;
        }
        if (!q) return true;
        return (
          a.pair.toLowerCase().includes(q) ||
          a.orderId.toLowerCase().includes(q) ||
          a.brokerMessage.toLowerCase().includes(q) ||
          a.strategyName.toLowerCase().includes(q)
        );
      }),
    [audits, auditStatusFilter, q]
  );

  const handleExportCurrentTab = () => {
    const dateSlug = new Date().toISOString().slice(0, 10);
    if (activeTab === 'activity') {
      exportRowsToCsv(
        ['Timestamp', 'Level', 'Pair', 'Strategy', 'Message', 'Details'],
        filteredActivity.map((a) => [
          a.timestamp,
          a.level,
          a.pair ?? '',
          a.strategyName ?? '',
          a.message,
          a.details ?? '',
        ]),
        `bot-activity-log-${dateSlug}.csv`
      );
    } else if (activeTab === 'errors') {
      exportRowsToCsv(
        ['Timestamp', 'Severity', 'Component', 'Message', 'Stack Summary', 'Resolved'],
        filteredErrors.map((e) => [
          e.timestamp,
          e.severity,
          e.component,
          e.message,
          e.stackSummary ?? '',
          e.resolved,
        ]),
        `bot-error-log-${dateSlug}.csv`
      );
    } else {
      exportRowsToCsv(
        [
          'Timestamp',
          'Order ID',
          'Pair',
          'Direction',
          'Action',
          'Requested Price',
          'Executed Price',
          'Size (Lots)',
          'Broker Response',
          'Latency (ms)',
          'Message',
          'Strategy',
        ],
        filteredAudits.map((a) => [
          a.timestamp,
          a.orderId,
          a.pair,
          a.direction,
          a.action,
          a.requestedPrice,
          a.executedPrice ?? '',
          a.sizeLots,
          a.brokerResponse,
          a.latencyMs,
          a.brokerMessage,
          a.strategyName,
        ]),
        `trade-audit-log-${dateSlug}.csv`
      );
    }
  };

  const currentCount =
    activeTab === 'activity'
      ? filteredActivity.length
      : activeTab === 'errors'
      ? filteredErrors.length
      : filteredAudits.length;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Logs &amp; Trade Audit
          </h1>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Inspect execution activity, severity-tagged system errors, and full broker order audit trails.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => void loadAll()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors whitespace-nowrap"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
          <button
            type="button"
            onClick={handleExportCurrentTab}
            disabled={currentCount === 0}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 disabled:opacity-40 transition-colors whitespace-nowrap"
          >
            <Download className="h-3.5 w-3.5" />
            Export CSV ({currentCount})
          </button>
        </div>
      </div>

      {/* Tabs + Search Filter Bar */}
      <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-4 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap items-center gap-1.5">
          {(
            [
              { id: 'activity', label: `Activity (${filteredActivity.length})` },
              { id: 'errors', label: `Errors (${filteredErrors.length})` },
              { id: 'audit', label: `Trade Audit Log (${filteredAudits.length})` },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-lg border px-3.5 py-1.5 text-xs font-semibold transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-blue-500 bg-blue-600/15 text-blue-700 dark:text-blue-200'
                  : 'border-slate-200 bg-slate-50 text-slate-600 hover:text-slate-900 dark:border-slate-800 dark:bg-[#0B0F17] dark:text-slate-400 dark:hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {activeTab === 'errors' && (
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value as ErrorSeverity | 'ALL')}
              className="rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
            >
              <option value="ALL">All Severities</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          )}

          {activeTab === 'audit' && (
            <select
              value={auditStatusFilter}
              onChange={(e) => setAuditStatusFilter(e.target.value)}
              className="rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
            >
              <option value="ALL">All Responses</option>
              <option value="FILLED">FILLED</option>
              <option value="REQUOTED">REQUOTED</option>
              <option value="REJECTED">REJECTED</option>
              <option value="MODIFIED">MODIFIED</option>
            </select>
          )}

          <div className="relative min-w-[220px] flex-1 sm:flex-initial">
            <Search className="pointer-events-none absolute left-2.5 top-2 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search logs, pair, order ID..."
              className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] py-1.5 pl-8 pr-3 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>
      </div>

      {/* Log Content Panel */}
      <PanelShell
        title={
          activeTab === 'activity'
            ? 'Bot Execution Activity'
            : activeTab === 'errors'
            ? 'System & Broker Error Log'
            : 'Broker Trade Audit Log'
        }
        subtitle={
          activeTab === 'audit'
            ? 'Every order sent, broker acknowledgement, rejection, requote, and round-trip latency'
            : 'Real-time operational records'
        }
        isLoading={loading}
        error={loadError}
        isEmpty={currentCount === 0}
        emptyTitle="No matching log entries"
        emptyDescription="Try clearing your search or severity filter."
        onRetry={loadAll}
        skeletonRows={6}
      >
        {activeTab === 'activity' && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 whitespace-nowrap">
                  <th className="py-2 pr-3 font-medium">Timestamp</th>
                  <th className="py-2 px-3 font-medium">Level</th>
                  <th className="py-2 px-3 font-medium">Pair</th>
                  <th className="py-2 px-3 font-medium">Strategy</th>
                  <th className="py-2 pl-3 font-medium">Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
                {filteredActivity.map((entry) => (
                  <tr key={entry.id}>
                    <td className="py-2.5 pr-3 font-mono text-[11px] text-slate-500 dark:text-slate-400 whitespace-nowrap tabular-nums">
                      {formatDateTime(entry.timestamp)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[11px] font-semibold uppercase whitespace-nowrap">
                      <span
                        className={
                          entry.level === 'order'
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : entry.level === 'signal'
                            ? 'text-blue-600 dark:text-blue-400'
                            : entry.level === 'warning'
                            ? 'text-amber-600 dark:text-amber-400'
                            : entry.level === 'error'
                            ? 'text-red-600 dark:text-red-400'
                            : 'text-slate-500 dark:text-slate-400'
                        }
                      >
                        {entry.level}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-semibold text-slate-800 dark:text-slate-200 whitespace-nowrap">
                      {entry.pair || '—'}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 dark:text-slate-300 whitespace-nowrap">
                      {entry.strategyName || '—'}
                    </td>
                    <td className="py-2.5 pl-3 text-slate-800 dark:text-slate-200">
                      <div>{entry.message}</div>
                      {entry.details && (
                        <div className="text-[11px] text-slate-500 dark:text-slate-400">
                          {entry.details}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'errors' && (
          <div className="space-y-3">
            {filteredErrors.map((err) => {
              const sevStyle =
                err.severity === 'CRITICAL'
                  ? 'border-red-500/40 bg-red-500/15 text-red-700 dark:text-red-300'
                  : err.severity === 'ERROR'
                  ? 'border-orange-500/40 bg-orange-500/15 text-orange-700 dark:text-orange-300'
                  : 'border-amber-500/40 bg-amber-500/15 text-amber-700 dark:text-amber-300';

              return (
                <div
                  key={err.id}
                  className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-1.5"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`rounded border px-2 py-0.5 font-mono text-[11px] font-bold ${sevStyle}`}
                      >
                        {err.severity}
                      </span>
                      <span className="font-mono text-xs font-semibold text-slate-900 dark:text-slate-100">
                        {err.component}
                      </span>
                    </div>
                    <span className="font-mono text-[11px] text-slate-500 tabular-nums">
                      {formatDateTime(err.timestamp)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-800 dark:text-slate-200">{err.message}</p>
                  {err.stackSummary && (
                    <p className="font-mono text-[11px] text-slate-500 dark:text-slate-400">
                      {err.stackSummary}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 whitespace-nowrap">
                  <th className="py-2 pr-3 font-medium">Timestamp</th>
                  <th className="py-2 px-2.5 font-medium">Order ID</th>
                  <th className="py-2 px-2.5 font-medium">Pair / Action</th>
                  <th className="py-2 px-2.5 font-medium text-right">Req Price</th>
                  <th className="py-2 px-2.5 font-medium text-right">Exec Price</th>
                  <th className="py-2 px-2.5 font-medium text-right">Lots</th>
                  <th className="py-2 px-2.5 font-medium">Broker Response</th>
                  <th className="py-2 px-2.5 font-medium text-right">Latency</th>
                  <th className="py-2 pl-2.5 font-medium">Broker Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/70">
                {filteredAudits.map((row) => {
                  const statusTone =
                    row.brokerResponse === 'FILLED' || row.brokerResponse === 'MODIFIED'
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : row.brokerResponse === 'REJECTED' || row.brokerResponse === 'CANCELLED'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-amber-600 dark:text-amber-400';

                  return (
                    <tr key={row.id}>
                      <td className="py-2.5 pr-3 font-mono text-[11px] text-slate-500 dark:text-slate-400 whitespace-nowrap tabular-nums">
                        {formatDateTime(row.timestamp)}
                      </td>
                      <td className="py-2.5 px-2.5 font-mono text-slate-800 dark:text-slate-200 whitespace-nowrap">
                        {row.orderId}
                      </td>
                      <td className="py-2.5 px-2.5 font-mono whitespace-nowrap">
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {row.pair}
                        </span>{' '}
                        <span className="text-slate-500 text-[11px]">
                          {row.direction} · {row.action}
                        </span>
                      </td>
                      <td className="py-2.5 px-2.5 text-right font-mono tabular-nums text-slate-700 dark:text-slate-300">
                        {row.requestedPrice}
                      </td>
                      <td className="py-2.5 px-2.5 text-right font-mono tabular-nums text-slate-900 dark:text-slate-100">
                        {row.executedPrice ?? '—'}
                      </td>
                      <td className="py-2.5 px-2.5 text-right font-mono tabular-nums text-slate-700 dark:text-slate-300">
                        {row.sizeLots.toFixed(2)}
                      </td>
                      <td className={`py-2.5 px-2.5 font-mono font-semibold whitespace-nowrap ${statusTone}`}>
                        {row.brokerResponse}
                      </td>
                      <td className="py-2.5 px-2.5 text-right font-mono tabular-nums text-slate-600 dark:text-slate-300 whitespace-nowrap">
                        {row.latencyMs} ms
                      </td>
                      <td className="py-2.5 pl-2.5 text-slate-600 dark:text-slate-300 min-w-[200px]">
                        {row.brokerMessage}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </PanelShell>
    </div>
  );
}
