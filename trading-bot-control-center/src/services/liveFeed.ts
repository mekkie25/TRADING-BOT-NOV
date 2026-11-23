import { useEffect, useState } from 'react';
import type { ConnectionState, MarketSnapshotInfo } from '../types';
import { USE_MOCK, getActiveApiBaseUrl } from './api';

// Live feed calls for ALL watched instruments (not only the 6-pair ForexPair list).

export interface LiveQuote {
  symbol: string;
  time: string;
  bid: number;
  ask: number;
}

export interface LiveCandle {
  symbol: string;
  timeframe: 'M5';
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface LiveFeedSnapshot {
  connectionState: ConnectionState;
  environment: 'Demo' | 'Live' | 'Unknown';
  symbol: string;
  message: string;
  quote: LiveQuote | null;
  lastClosedCandle: LiveCandle | null;
}

export type LiveFeedAll = Record<string, LiveFeedSnapshot>;

export type MarketSnapshotData = Omit<MarketSnapshotInfo, 'symbol'> & { symbol: string };

const DISPLAY_ORDER = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD', 'DAX', 'US30', 'NAS100'];

// Display only. Not checked against the broker's own digits.
const PRICE_DECIMALS: Record<string, number> = {
  EURUSD: 5,
  GBPUSD: 5,
  USDJPY: 3,
  XAUUSD: 2,
  BTCUSD: 2,
  DAX: 2,
  US30: 2,
  NAS100: 2,
};

export function sortSymbols(symbols: string[]): string[] {
  const rank = (symbol: string) => {
    const index = DISPLAY_ORDER.indexOf(symbol);
    return index === -1 ? DISPLAY_ORDER.length : index;
  };
  return [...symbols].sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
}

export function formatLivePrice(price: number, symbol: string): string {
  return price.toFixed(PRICE_DECIMALS[symbol] ?? 5);
}

async function getJson<T>(path: string): Promise<T> {
  const baseUrl = getActiveApiBaseUrl().replace(/\/+$/, '');
  const response = await fetch(`${baseUrl}${path}`);
  if (!response.ok) {
    let detail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (body?.detail) {
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export async function fetchAllLive(): Promise<LiveFeedAll> {
  if (USE_MOCK) {
    return {
      EURUSD: {
        connectionState: 'Disconnected',
        environment: 'Demo',
        symbol: 'EURUSD',
        message: 'Mock mode is enabled; no broker data is connected.',
        quote: null,
        lastClosedCandle: null,
      },
    };
  }
  return getJson<LiveFeedAll>('/api/market/live/all');
}

export async function fetchMarketSnapshot(symbol: string): Promise<MarketSnapshotData | null> {
  if (USE_MOCK) {
    return null;
  }
  return getJson<MarketSnapshotData>(`/api/market/snapshot?symbol=${encodeURIComponent(symbol)}`);
}

// The instrument picked on screen. Shared by the live panel and the snapshot panel.
const STORAGE_KEY = 'tbcc_live_symbol';
const DEFAULT_SYMBOL = 'EURUSD';

function readStoredSymbol(): string {
  try {
    return window.localStorage.getItem(STORAGE_KEY) || DEFAULT_SYMBOL;
  } catch {
    return DEFAULT_SYMBOL;
  }
}

let selectedSymbol = readStoredSymbol();
const listeners = new Set<() => void>();

export function setSelectedSymbol(symbol: string): void {
  if (symbol === selectedSymbol) return;
  selectedSymbol = symbol;
  try {
    window.localStorage.setItem(STORAGE_KEY, symbol);
  } catch {
    // ignore storage errors
  }
  listeners.forEach((listener) => listener());
}

export function useSelectedSymbol(): [string, (symbol: string) => void] {
  const [value, setValue] = useState(selectedSymbol);
  useEffect(() => {
    const listener = () => setValue(selectedSymbol);
    listeners.add(listener);
    listener();
    return () => {
      listeners.delete(listener);
    };
  }, []);
  return [value, setSelectedSymbol];
}