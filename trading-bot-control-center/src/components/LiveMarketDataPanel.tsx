import { useEffect, useState } from 'react';
import { Wifi, WifiOff } from 'lucide-react';
import type { ConnectionState } from '../types';
import { formatDateTime } from '../utils/formatters';
import { useAppContext } from './AppContext';
import {
  fetchAllLive,
  formatLivePrice,
  sortSymbols,
  useSelectedSymbol,
} from '../services/liveFeed';
import type { LiveFeedAll } from '../services/liveFeed';

function dotColor(state: ConnectionState): string {
  if (state === 'Connected') return 'bg-emerald-500';
  if (state === 'Error') return 'bg-red-500';
  if (state === 'Connecting') return 'bg-amber-500';
  return 'bg-slate-400';
}

export function LiveMarketDataPanel() {
  const { setConnectionDirect } = useAppContext();
  const [all, setAll] = useState<LiveFeedAll | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useSelectedSymbol();

  useEffect(() => {
    let active = true;
    let polling = false;

    const poll = async () => {
      if (polling) return;
      polling = true;
      try {
        const result = await fetchAllLive();
        if (!active) return;
        setAll(result);
        setError(null);
        const headline = result.EURUSD ?? result[Object.keys(result)[0]];
        setConnectionDirect(headline ? headline.connectionState : 'Disconnected');
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

  const symbols = all ? sortSymbols(Object.keys(all)) : [];
  const activeSymbol = all && all[selected] ? selected : (symbols[0] ?? selected);
  const data = all ? (all[activeSymbol] ?? null) : null;
  const connectedCount = symbols.filter(
    (symbol) => all?.[symbol]?.connectionState === 'Connected',
  ).length;

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
              : 'cTrader market data · data only'}
          </p>
        </div>
        <div className={`inline-flex items-center gap-1.5 text-xs font-semibold ${statusColor}`}>
          {connected ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
          {connectionState}
        </div>
      </div>

      {symbols.length > 0 && (
        <>
          <div className="mt-3 flex flex-wrap gap-1.5" role="group" aria-label="Choose instrument">
            {symbols.map((symbol) => {
              const state = all?.[symbol]?.connectionState ?? 'Disconnected';
              const isSelected = symbol === activeSymbol;
              return (
                <button
                  key={symbol}
                  type="button"
                  onClick={() => setSelected(symbol)}
                  aria-pressed={isSelected}
                  title={`${symbol}: ${state}`}
                  className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] font-medium ${
                    isSelected
                      ? 'border-sky-500 bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800/60'
                  }`}
                >
                  <span className={`h-1.5 w-1.5 rounded-full ${dotColor(state)}`} />
                  {symbol}
                </button>
              );
            })}
          </div>
          <p className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
            {connectedCount} of {symbols.length} instruments connected
          </p>
        </>
      )}

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">Bid</p>
          <p className="mt-1 font-mono text-lg font-semibold tabular-nums text-slate-900 dark:text-slate-100">
            {data?.quote ? formatLivePrice(data.quote.bid, data.symbol) : '—'}
          </p>
        </div>
        <div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">Ask</p>
          <p className="mt-1 font-mono text-lg font-semibold tabular-nums text-slate-900 dark:text-slate-100">
            {data?.quote ? formatLivePrice(data.quote.ask, data.symbol) : '—'}
          </p>
        </div>
        <div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">
            Last completed M5 close
          </p>
          <p className="mt-1 font-mono text-lg font-semibold tabular-nums text-slate-900 dark:text-slate-100">
            {data?.lastClosedCandle
              ? formatLivePrice(data.lastClosedCandle.close, data.lastClosedCandle.symbol)
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