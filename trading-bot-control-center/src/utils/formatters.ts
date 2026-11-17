import type { CurrencyCode, DisplayCurrency, ForexPair, JournalTrade } from '../types';

const CURRENCY_SYMBOLS: Record<CurrencyCode, string> = {
  ZAR: 'R',
  USD: '$',
  EUR: '€',
  GBP: '£',
};

// Reference UI display conversion rate (ZAR per 1 USD)
export const FX_ZAR_PER_USD = 18.1;

export function convertCurrencyAmount(
  amount: number,
  fromCurrency: CurrencyCode = 'ZAR',
  toCurrency: DisplayCurrency = 'ZAR'
): number {
  if (fromCurrency === toCurrency) return amount;
  // Convert source to ZAR first
  let inZar = amount;
  if (fromCurrency === 'USD') inZar = amount * FX_ZAR_PER_USD;
  else if (fromCurrency === 'EUR') inZar = amount * 19.6;
  else if (fromCurrency === 'GBP') inZar = amount * 22.9;

  if (toCurrency === 'ZAR') return inZar;
  return inZar / FX_ZAR_PER_USD;
}

export function formatCurrency(
  amount: number,
  currency: CurrencyCode = 'ZAR',
  options?: { signed?: boolean; decimals?: number }
): string {
  const decimals = options?.decimals ?? 2;
  const abs = Math.abs(amount);
  const formatted = abs.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  const sym = CURRENCY_SYMBOLS[currency] || currency + ' ';
  if (amount < 0) return `-${sym}${formatted}`;
  if (options?.signed && amount > 0) return `+${sym}${formatted}`;
  return `${sym}${formatted}`;
}

export function formatPairPrice(price: number, pair: ForexPair): string {
  let decimals = 5;
  if (pair === 'USDJPY') decimals = 3;
  else if (pair === 'XAUUSD') decimals = 2;
  else if (pair === 'USDZAR') decimals = 4;
  return price.toFixed(decimals);
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h < 24) return m > 0 ? `${h}h ${m}m` : `${h}h`;
  const d = Math.floor(h / 24);
  const remH = h % 24;
  return remH > 0 ? `${d}d ${remH}h` : `${d}d`;
}

export function formatUptime(totalSeconds: number): string {
  if (totalSeconds <= 0) return '00:00:00';
  const hrs = Math.floor(totalSeconds / 3600);
  const mins = Math.floor((totalSeconds % 3600) / 60);
  const secs = totalSeconds % 60;
  return [hrs, mins, secs].map((v) => String(v).padStart(2, '0')).join(':');
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

export function downloadJsonFile(data: unknown, filename: string): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json;charset=utf-8;',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function exportRowsToCsv(
  headers: string[],
  rows: Array<Array<string | number | boolean | null | undefined>>,
  filename: string
): void {
  const escapeCsv = (val: string | number | boolean | null | undefined) => {
    const str = val === undefined || val === null ? '' : String(val);
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };
  const csvContent = [
    headers.join(','),
    ...rows.map((r) => r.map(escapeCsv).join(',')),
  ].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function exportTradesToCsv(trades: JournalTrade[], filename: string): void {
  const headers = [
    'ID',
    'Opened At',
    'Closed At',
    'Pair',
    'Direction',
    'Strategy',
    'Version',
    'Setup Grade',
    'Entry',
    'Exit',
    'Stop Loss',
    'Take Profit',
    'Size (Lots)',
    'P/L',
    'Currency',
    'R Multiple',
    'Duration (min)',
    'Volatility Regime',
    'Market Structure',
    'Session',
    'News Nearby',
    'Spread (pips)',
    'MAE (R)',
    'MFE (R)',
    'Tags',
    'Notes',
  ];

  const rows = trades.map((t) => [
    t.id,
    t.openedAt,
    t.closedAt,
    t.pair,
    t.direction,
    t.strategyName,
    t.strategyVersion ?? '',
    t.setupGrade,
    t.entryPrice,
    t.exitPrice,
    t.stopLoss,
    t.takeProfit,
    t.sizeLots,
    t.pnl,
    t.currency,
    t.rMultiple,
    t.durationMinutes,
    t.marketConditions.volatilityRegime,
    t.marketConditions.marketStructure,
    t.marketConditions.session,
    t.marketConditions.newsNearby,
    t.marketConditions.spreadPips,
    t.maeR,
    t.mfeR,
    (t.tags ?? []).join(';'),
    t.notes,
  ]);

  exportRowsToCsv(headers, rows, filename);
}
