import { useEffect, useState } from 'react';
import { Wifi, WifiOff } from 'lucide-react';
import { api } from '../services/api';
import type { LiveMarketDataInfo } from '../types';
import { formatDateTime, formatPairPrice } from '../utils/formatters';
import { useAppContext } from './AppContext';

export function LiveMarketDataPanel() {
  const { setConnectionDirect } = useAppContext();
  const [data, setData] = useState<LiveMarketDataInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let polling = false;

    const poll = async () => {
      if (polling) return;
      polling = true;
      try {
        const result = await api.getLiveMarketData();
        if (!active) return;
        setData(result);
        setError(null);
        setConnectionDirect(result.connectionState);
      } catch (requestError) {
        if (!active) return;
        const message =
          requestError instanceof Error
            ? requestError.message
            : 'Could not load live market data.';
        setError(message);
        setConnectionDirect('Error');
      } finally {
        polling = false;
      }
    };

    void poll();
    const timer = window.setInterval(() => void poll(), 1000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [setConnectionDirect]);

  const connectionState = error ? 'Error' : data?.connectionState ?? 'Connecting';
  const connected = connectionState === 'Connected';
  const statusColor = connected
    ? 'text-emerald-600 dark:text-emerald-400'
    : connectionState === 'Error'
      ? 'text-red-600 dark:text-red-400'
      : 'text-amber-600 dark:text-amber-400';

  return (
    <section
      aria-label="Live market data"
      className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800/90 dark:bg-[#111824]"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Live Market Feed
          </h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {data
              ? `${data.symbol} · cTrader ${data.environment} · data only`
              : 'EURUSD · cTrader market data · data only'}
          </p>
        </div>
        <div className={`inline-flex items-center gap-1.5 text-xs font-semibold ${statusColor}`}>
          {connected ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
          {connectionState}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">Bid</p>
          <p className="mt-1 font-mono text-lg font-semibold tabular-nums text-slate-900 dark:text-slate-100">
            {data?.quote ? formatPairPrice(data.quote.bid, data.symbol) : '—'}
          </p>
        </div>
        <div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">Ask</p>
          <p className="mt-1 font-mono text-lg font-semibold tabular-nums text-slate-900 dark:text-slate-100">
            {data?.quote ? formatPairPrice(data.quote.ask, data.symbol) : '—'}
          </p>
        </div>
        <div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">
            Last completed M5 close
          </p>
          <p className="mt-1 font-mono text-lg font-semibold tabular-nums text-slate-900 dark:text-slate-100">
            {data?.lastClosedCandle
              ? formatPairPrice(data.lastClosedCandle.close, data.lastClosedCandle.symbol)
              : '—'}
          </p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap justify-between gap-2 text-[11px] text-slate-500 dark:text-slate-400">
        <p role="status" aria-live="polite">
          {error ?? data?.message ?? 'Waiting for the feed status.'}
        </p>
        <p>
          {data?.quote
            ? `Last quote: ${formatDateTime(data.quote.time)}`
            : data?.lastClosedCandle
              ? `Last M5 bar: ${formatDateTime(data.lastClosedCandle.time)}`
              : 'No quote received yet'}
        </p>
      </div>
    </section>
  );
}
