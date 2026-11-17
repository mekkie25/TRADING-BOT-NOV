import { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Cpu,
  HardDrive,
  RefreshCw,
  Server,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { api } from '../services/api';
import type { ConnectionState, SystemStatusInfo } from '../types';
import { PanelShell } from '../components/DataState';
import { formatDateTime } from '../utils/formatters';

function formatServerUptime(totalSeconds: number): string {
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const mins = Math.floor((totalSeconds % 3600) / 60);
  return `${days}d ${hours}h ${mins}m`;
}

export function SystemStatusPage() {
  const [status, setStatus] = useState<SystemStatusInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSystemStatus();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load system status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  const ramPct = status ? Math.round((status.ramUsedGb / status.ramTotalGb) * 100) : 0;
  const diskPct = status ? Math.round((status.diskUsedGb / status.diskTotalGb) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            System Status
          </h1>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Host telemetry, broker &amp; tick-feed connectivity, bot heartbeat, and runtime diagnostics.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void loadStatus()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors whitespace-nowrap"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Telemetry
        </button>
      </div>

      <PanelShell
        title="Infrastructure &amp; Runtime Health"
        subtitle="Polled from FastAPI /api/system/status"
        isLoading={loading}
        error={error}
        isEmpty={!status}
        onRetry={loadStatus}
        skeletonRows={5}
      >
        {status && (
          <div className="space-y-6">
            {/* Top Telemetry Grid */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-1.5">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                  <span>Server Uptime</span>
                  <Server className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                </div>
                <p className="font-mono text-lg font-bold text-slate-900 dark:text-slate-100 tabular-nums">
                  {formatServerUptime(status.serverUptimeSeconds)}
                </p>
                <p className="text-[11px] text-slate-500 font-mono">
                  Bot v{status.botVersion} · Python {status.pythonVersion}
                </p>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                  <span>CPU Utilization</span>
                  <Cpu className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                </div>
                <p className="font-mono text-lg font-bold text-slate-900 dark:text-slate-100 tabular-nums">
                  {status.cpuPercent.toFixed(1)}%
                </p>
                <div className="h-1.5 w-full rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      status.cpuPercent > 80
                        ? 'bg-red-500'
                        : status.cpuPercent > 60
                        ? 'bg-amber-500'
                        : 'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.min(100, status.cpuPercent)}%` }}
                  />
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                  <span>Memory (RAM)</span>
                  <Activity className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                </div>
                <p className="font-mono text-lg font-bold text-slate-900 dark:text-slate-100 tabular-nums">
                  {status.ramUsedGb.toFixed(1)} / {status.ramTotalGb.toFixed(1)} GB
                </p>
                <div className="h-1.5 w-full rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-blue-500"
                    style={{ width: `${Math.min(100, ramPct)}%` }}
                  />
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                  <span>Disk Storage</span>
                  <HardDrive className="h-4 w-4 text-slate-500 dark:text-slate-400" />
                </div>
                <p className="font-mono text-lg font-bold text-slate-900 dark:text-slate-100 tabular-nums">
                  {status.diskUsedGb.toFixed(1)} / {status.diskTotalGb.toFixed(0)} GB
                </p>
                <div className="h-1.5 w-full rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-slate-500 dark:bg-slate-400"
                    style={{ width: `${Math.min(100, diskPct)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Connectivity & Heartbeat Cards */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <ConnectionCard
                title="cTrader Open API"
                status={status.ctraderStatus}
                detail="Order execution & position sync channel"
              />
              <ConnectionCard
                title="Market Data Feed"
                status={status.dataFeedStatus}
                detail={status.dataFeedProvider}
              />
              <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-1.5">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  Last Bot Heartbeat
                </span>
                <p className="font-mono text-sm font-semibold text-slate-900 dark:text-slate-100 tabular-nums">
                  {formatDateTime(status.lastHeartbeat)}
                </p>
                <p className="text-[11px] text-slate-500">
                  Heartbeat interval: 5s expected
                </p>
              </div>
            </div>

            {/* Last Recorded Error */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                  Most Recent Runtime Exception / Warning
                </h3>
              </div>
              {status.lastError ? (
                <div className="space-y-1 text-xs">
                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                    <span>{formatDateTime(status.lastError.timestamp)}</span>
                    <span>·</span>
                    <span className="text-slate-800 dark:text-slate-200 font-semibold">
                      {status.lastError.component}
                    </span>
                  </div>
                  <p className="text-slate-800 dark:text-slate-200">
                    {status.lastError.message}
                  </p>
                </div>
              ) : (
                <p className="text-xs text-emerald-600 dark:text-emerald-400">
                  Zero runtime errors recorded in current server session.
                </p>
              )}
            </div>
          </div>
        )}
      </PanelShell>
    </div>
  );
}

function ConnectionCard({
  title,
  status,
  detail,
}: {
  title: string;
  status: ConnectionState;
  detail: string;
}) {
  const isOk = status === 'Connected';
  const color = isOk
    ? 'text-emerald-600 dark:text-emerald-400'
    : status === 'Error'
    ? 'text-red-600 dark:text-red-400'
    : 'text-amber-600 dark:text-amber-400';

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-4 space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
          {title}
        </span>
        {isOk ? (
          <Wifi className={`h-4 w-4 ${color}`} />
        ) : (
          <WifiOff className={`h-4 w-4 ${color}`} />
        )}
      </div>
      <p className={`font-mono text-sm font-bold ${color}`}>{status}</p>
      <p className="text-[11px] text-slate-500 truncate">{detail}</p>
    </div>
  );
}
