import type {
  ForexPair,
  JournalTrade,
  MarketStructure,
  SetupGrade,
  TradeDirection,
  TradingSession,
  VolatilityRegime,
} from '../types';

function createSeededRng(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

interface PairSpec {
  pair: ForexPair;
  basePrice: number;
  pipSize: number;
  decimals: number;
  typicalAtrPips: number;
  typicalSpread: number;
}

const PAIR_SPECS: PairSpec[] = [
  { pair: 'EURUSD', basePrice: 1.084, pipSize: 0.0001, decimals: 5, typicalAtrPips: 18, typicalSpread: 0.5 },
  { pair: 'GBPUSD', basePrice: 1.268, pipSize: 0.0001, decimals: 5, typicalAtrPips: 24, typicalSpread: 0.8 },
  { pair: 'USDJPY', basePrice: 153.4, pipSize: 0.01, decimals: 3, typicalAtrPips: 28, typicalSpread: 0.7 },
  { pair: 'XAUUSD', basePrice: 2565.0, pipSize: 0.1, decimals: 2, typicalAtrPips: 75, typicalSpread: 1.8 },
  { pair: 'USDZAR', basePrice: 18.05, pipSize: 0.001, decimals: 4, typicalAtrPips: 42, typicalSpread: 2.2 },
  { pair: 'AUDUSD', basePrice: 0.652, pipSize: 0.0001, decimals: 5, typicalAtrPips: 15, typicalSpread: 0.6 },
];

const STRATEGIES = [
  { id: 'strat-london-breakout', name: 'London Breakout Momentum', version: 'v1.4' },
  { id: 'strat-ny-reversion', name: 'NY Session Mean Reversion', version: 'v2.1' },
  { id: 'strat-liquidity-sweep', name: 'Multi-TF Liquidity Sweep', version: 'v1.1' },
];

const GRADE_PROFILES: Array<{
  grade: SetupGrade;
  weight: number;
  winProb: number;
  avgWinR: number;
  avgLossR: number;
}> = [
  { grade: 'A++', weight: 0.14, winProb: 0.72, avgWinR: 2.55, avgLossR: -0.95 },
  { grade: 'A+', weight: 0.24, winProb: 0.61, avgWinR: 2.15, avgLossR: -0.98 },
  { grade: 'A', weight: 0.34, winProb: 0.53, avgWinR: 1.85, avgLossR: -1.0 },
  { grade: 'B', weight: 0.2, winProb: 0.42, avgWinR: 1.45, avgLossR: -1.02 },
  { grade: 'Bad', weight: 0.08, winProb: 0.26, avgWinR: 1.15, avgLossR: -1.12 },
];

const VOLATILITIES: VolatilityRegime[] = ['Low', 'Normal', 'High', 'Extreme'];
const STRUCTURES: MarketStructure[] = ['Trending', 'Ranging', 'Breakout'];
const SESSIONS: TradingSession[] = ['Asian', 'London', 'New York', 'London/NY Overlap'];
const NEWS_EVENTS = ['US CPI m/m', 'FOMC Rate Decision', 'NFP Payrolls', 'ECB Press Conf', 'UK GDP q/q'];
const SAMPLE_NOTES = [
  'Clean London open displacement with tight spread and H4 EMA alignment.',
  'Partial scale-out triggered at +1.5R; remainder trailed behind M15 swing.',
  'Entered slightly late after pullback; spread widened briefly at NY open.',
  'Stopped out cleanly on reversal candle; respected daily risk limit.',
  'High-conviction liquidity sweep below equal lows; held to full TP.',
  '',
  '',
  '',
];
const TAG_POOL = [
  'htf-aligned',
  'clean-displacement',
  'london-open',
  'spread-spike',
  'partial-tp',
  'retest-entry',
  'news-avoided',
  'trend-continuation',
];

function roundPrice(val: number, decimals: number): number {
  const factor = Math.pow(10, decimals);
  return Math.round(val * factor) / factor;
}

export function generateMockJournalTrades(count = 204, seed = 20261116): JournalTrade[] {
  const rng = createSeededRng(seed);
  const trades: JournalTrade[] = [];
  const endTs = new Date('2026-11-15T20:00:00Z').getTime();

  for (let i = 0; i < count; i++) {
    const spec = PAIR_SPECS[Math.floor(rng() * PAIR_SPECS.length)];
    const strat = STRATEGIES[Math.floor(rng() * STRATEGIES.length)];
    const direction: TradeDirection = rng() > 0.48 ? 'BUY' : 'SELL';

    const gRoll = rng();
    let cumWeight = 0;
    let gradeProfile = GRADE_PROFILES[2];
    for (const gp of GRADE_PROFILES) {
      cumWeight += gp.weight;
      if (gRoll <= cumWeight) {
        gradeProfile = gp;
        break;
      }
    }

    const hoursBack = i * 16 + Math.floor(rng() * 10);
    const closedDate = new Date(endTs - hoursBack * 3600 * 1000);
    if (closedDate.getUTCDay() === 0) closedDate.setUTCDate(closedDate.getUTCDate() - 2);
    if (closedDate.getUTCDay() === 6) closedDate.setUTCDate(closedDate.getUTCDate() - 1);

    const durationMinutes = Math.floor(25 + rng() * 440);
    const openedDate = new Date(closedDate.getTime() - durationMinutes * 60 * 1000);

    const hour = openedDate.getUTCHours();
    let session: TradingSession = SESSIONS[Math.floor(rng() * SESSIONS.length)];
    if (hour >= 1 && hour < 7) session = 'Asian';
    else if (hour >= 7 && hour < 12) session = 'London';
    else if (hour >= 12 && hour < 16) session = 'London/NY Overlap';
    else if (hour >= 16 && hour < 21) session = 'New York';

    const volRoll = rng();
    const volatilityRegime: VolatilityRegime =
      volRoll < 0.18 ? 'Low' : volRoll < 0.68 ? 'Normal' : volRoll < 0.91 ? 'High' : 'Extreme';

    const marketStructure: MarketStructure =
      strat.id === 'strat-ny-reversion'
        ? rng() < 0.65
          ? 'Ranging'
          : 'Trending'
        : STRUCTURES[Math.floor(rng() * STRUCTURES.length)];

    const newsNearby = gradeProfile.grade === 'Bad' ? rng() < 0.55 : rng() < 0.11;
    const spreadMult = volatilityRegime === 'Extreme' ? 1.8 : volatilityRegime === 'High' ? 1.3 : 1.0;
    const spreadPips = Math.round(spec.typicalSpread * spreadMult * (0.85 + rng() * 0.4) * 10) / 10;
    const atrPips = Math.round(spec.typicalAtrPips * (0.8 + rng() * 0.6));

    const isWin = rng() < gradeProfile.winProb;
    const rMultiple = isWin
      ? Math.round((gradeProfile.avgWinR * (0.65 + rng() * 0.75)) * 100) / 100
      : Math.round((gradeProfile.avgLossR * (0.75 + rng() * 0.35)) * 100) / 100;

    const priceJitter = (rng() - 0.5) * spec.typicalAtrPips * 12 * spec.pipSize;
    const entryPrice = roundPrice(spec.basePrice + priceJitter, spec.decimals);
    const slPips = Math.round(spec.typicalAtrPips * (1.1 + rng() * 0.6));
    const tpPips = Math.round(slPips * (2.0 + rng() * 1.2));

    const sign = direction === 'BUY' ? 1 : -1;
    const stopLoss = roundPrice(entryPrice - sign * slPips * spec.pipSize, spec.decimals);
    const takeProfit = roundPrice(entryPrice + sign * tpPips * spec.pipSize, spec.decimals);
    const exitPrice = roundPrice(entryPrice + sign * rMultiple * slPips * spec.pipSize, spec.decimals);

    const oneRValueZar = 2150 + rng() * 450;
    const sizeLots = Math.round((0.08 + rng() * 0.42) * 100) / 100;
    const commission = -Math.round(sizeLots * 125 * 10) / 10;
    const swap = durationMinutes > 360 ? -Math.round(sizeLots * 45 * 10) / 10 : 0;
    const pnl = Math.round((rMultiple * oneRValueZar + commission + swap) * 100) / 100;

    const maeR = isWin
      ? Math.round((0.08 + rng() * 0.68) * 100) / 100
      : Math.round((Math.abs(rMultiple) + rng() * 0.15) * 100) / 100;
    const mfeR = isWin
      ? Math.round((rMultiple + 0.15 + rng() * 0.85) * 100) / 100
      : Math.round((0.1 + rng() * 0.95) * 100) / 100;

    const tagsCount = rng() > 0.35 ? (rng() > 0.65 ? 2 : 1) : 0;
    const tags: string[] = [];
    for (let k = 0; k < tagsCount; k++) {
      const candidate = TAG_POOL[Math.floor(rng() * TAG_POOL.length)];
      if (!tags.includes(candidate)) tags.push(candidate);
    }

    trades.push({
      id: `trd-${String(1000 + count - i)}`,
      openedAt: openedDate.toISOString(),
      closedAt: closedDate.toISOString(),
      pair: spec.pair,
      direction,
      strategyId: strat.id,
      strategyName: strat.name,
      strategyVersion: strat.version,
      setupGrade: gradeProfile.grade,
      entryPrice,
      exitPrice,
      stopLoss,
      takeProfit,
      sizeLots,
      pnl,
      currency: 'ZAR',
      rMultiple,
      durationMinutes,
      marketConditions: {
        volatilityRegime,
        marketStructure,
        session,
        newsNearby,
        newsEvent: newsNearby ? NEWS_EVENTS[Math.floor(rng() * NEWS_EVENTS.length)] : undefined,
        spreadPips,
        atrPips,
        htfBias: direction === 'BUY' ? (rng() > 0.2 ? 'Bullish' : 'Neutral') : rng() > 0.2 ? 'Bearish' : 'Neutral',
      },
      notes: SAMPLE_NOTES[Math.floor(rng() * SAMPLE_NOTES.length)],
      tags,
      maeR,
      mfeR,
      commission,
      swap,
    });
  }

  return trades;
}

export const MOCK_JOURNAL_TRADES: JournalTrade[] = generateMockJournalTrades(204, 20261116);
