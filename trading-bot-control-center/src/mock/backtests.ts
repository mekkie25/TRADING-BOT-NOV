import type {
  BacktestConfig,
  BacktestEquityPoint,
  BacktestResult,
  ConditionBreakdownItem,
  JournalTrade,
  MaeMfePoint,
  MonteCarloStep,
  SavedBacktestSummary,
  SetupGrade,
  SetupGradeBreakdown,
  SlTpHeatmapCell,
  VolatilityRegime,
} from '../types';
import { generateMockJournalTrades } from './trades';

function buildConditionBuckets(
  trades: JournalTrade[],
  selector: (t: JournalTrade) => string,
  orderedKeys?: string[]
): ConditionBreakdownItem[] {
  const map = new Map<string, JournalTrade[]>();
  if (orderedKeys) {
    for (const k of orderedKeys) map.set(k, []);
  }
  for (const t of trades) {
    const k = selector(t);
    const list = map.get(k) || [];
    list.push(t);
    map.set(k, list);
  }

  const results: ConditionBreakdownItem[] = [];
  for (const [bucket, list] of map.entries()) {
    if (list.length === 0) continue;
    const wins = list.filter((x) => x.pnl > 0).length;
    const grossWin = list.filter((x) => x.pnl > 0).reduce((s, x) => s + x.pnl, 0);
    const grossLoss = Math.abs(list.filter((x) => x.pnl <= 0).reduce((s, x) => s + x.pnl, 0));
    const netProfit = list.reduce((s, x) => s + x.pnl, 0);
    const expectancyR = list.reduce((s, x) => s + x.rMultiple, 0) / list.length;

    results.push({
      bucket,
      trades: list.length,
      wins,
      winRate: Math.round((wins / list.length) * 1000) / 10,
      netProfit: Math.round(netProfit * 100) / 100,
      expectancyR: Math.round(expectancyR * 100) / 100,
      profitFactor: grossLoss > 0 ? Math.round((grossWin / grossLoss) * 100) / 100 : grossWin > 0 ? 3.5 : 0,
      lowSampleWarning: list.length < 20,
    });
  }
  return results;
}

function buildBacktestFromConfig(
  id: string,
  name: string,
  createdAt: string,
  strategyName: string,
  config: BacktestConfig,
  seed: number,
  returnScale = 1
): BacktestResult {
  const rawTrades = generateMockJournalTrades(180, seed).map((t) => ({
    ...t,
    strategyId: config.strategyId,
    strategyName,
    currency: config.currency,
    pnl: Math.round(t.pnl * returnScale * 100) / 100,
  }));

  // Chronological order for equity curve
  const chronoTrades = [...rawTrades].reverse();
  let equity = config.startingBalance;
  let peak = equity;
  let maxDdPct = 0;
  let maxDdAmt = 0;
  let currentLosingStreak = 0;
  let longestLosingStreak = 0;

  const equityCurve: BacktestEquityPoint[] = [
    {
      date: chronoTrades[0]?.openedAt.slice(0, 10) || '2024-01-01',
      equity: Math.round(equity * 100) / 100,
      drawdownPercent: 0,
    },
  ];

  for (let i = 0; i < chronoTrades.length; i++) {
    const tr = chronoTrades[i];
    equity += tr.pnl;
    if (equity > peak) peak = equity;
    const ddAmt = peak - equity;
    const ddPct = peak > 0 ? (ddAmt / peak) * 100 : 0;
    if (ddPct > maxDdPct) maxDdPct = ddPct;
    if (ddAmt > maxDdAmt) maxDdAmt = ddAmt;

    if (tr.pnl <= 0) {
      currentLosingStreak += 1;
      if (currentLosingStreak > longestLosingStreak) longestLosingStreak = currentLosingStreak;
    } else {
      currentLosingStreak = 0;
    }

    if (i % 2 === 0 || i === chronoTrades.length - 1) {
      equityCurve.push({
        date: tr.closedAt.slice(0, 10),
        equity: Math.round(equity * 100) / 100,
        drawdownPercent: -Math.round(ddPct * 100) / 100,
      });
    }
  }

  const winsList = chronoTrades.filter((t) => t.pnl > 0);
  const lossesList = chronoTrades.filter((t) => t.pnl <= 0);
  const grossWin = winsList.reduce((s, t) => s + t.pnl, 0);
  const grossLoss = Math.abs(lossesList.reduce((s, t) => s + t.pnl, 0));
  const netProfit = Math.round((equity - config.startingBalance) * 100) / 100;

  // Market condition breakdowns
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  const byVolatility = buildConditionBuckets(
    chronoTrades,
    (t) => t.marketConditions.volatilityRegime,
    ['Low', 'Normal', 'High', 'Extreme']
  );
  const byStructure = buildConditionBuckets(
    chronoTrades,
    (t) => t.marketConditions.marketStructure,
    ['Trending', 'Ranging', 'Breakout']
  );
  const bySession = buildConditionBuckets(
    chronoTrades,
    (t) => t.marketConditions.session,
    ['Asian', 'London', 'London/NY Overlap', 'New York']
  );
  const byDayOfWeek = buildConditionBuckets(
    chronoTrades,
    (t) => days[(new Date(t.openedAt).getUTCDay() + 6) % 5] || 'Mon',
    days
  );
  const byTimeOfDay = buildConditionBuckets(
    chronoTrades,
    (t) => {
      const h = new Date(t.openedAt).getUTCHours();
      if (h < 4) return '00:00–04:00';
      if (h < 8) return '04:00–08:00';
      if (h < 12) return '08:00–12:00';
      if (h < 16) return '12:00–16:00';
      if (h < 20) return '16:00–20:00';
      return '20:00–24:00';
    },
    ['00:00–04:00', '04:00–08:00', '08:00–12:00', '12:00–16:00', '16:00–20:00', '20:00–24:00']
  );
  const byWeek = buildConditionBuckets(
    chronoTrades,
    (t) => {
      const d = new Date(t.openedAt);
      const weekNum = Math.min(4, Math.floor((d.getUTCDate() - 1) / 7) + 1);
      return `Week ${weekNum}`;
    },
    ['Week 1', 'Week 2', 'Week 3', 'Week 4']
  );
  const byMonth = buildConditionBuckets(
    chronoTrades,
    (t) => months[new Date(t.openedAt).getUTCMonth()],
    months
  );

  // SL/TP Heatmap
  const slMultiples = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5];
  const tpMultiples = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0];
  const cells: SlTpHeatmapCell[] = [];
  for (const sl of slMultiples) {
    for (const tp of tpMultiples) {
      // Smooth bell-shaped expectancy surface peaking around SL 1.5x ATR, TP 3.0x ATR
      const slDist = Math.abs(sl - 1.5);
      const tpDist = Math.abs(tp - 3.0);
      const baseExp = 0.54 - slDist * 0.28 - tpDist * 0.11;
      const expectancyR = Math.round(baseExp * returnScale * 100) / 100;
      const winRate = Math.max(24, Math.min(72, Math.round((64 - tp * 4.8 + sl * 4.2) * 10) / 10));
      const profitFactor = Math.max(0.65, Math.round((1.2 + expectancyR * 1.45) * 100) / 100);
      const netReturnPercent = Math.round(expectancyR * 96 * 10) / 10;
      cells.push({
        slAtrMultiple: sl,
        tpAtrMultiple: tp,
        expectancyR,
        netReturnPercent,
        winRate,
        profitFactor,
        trades: chronoTrades.length,
      });
    }
  }

  const optimalByVolatility: Array<{
    volatilityRegime: VolatilityRegime;
    bestSlAtr: number;
    bestTpAtr: number;
    expectancyR: number;
    winRate: number;
    netReturnPercent: number;
    trades: number;
  }> = [
    { volatilityRegime: 'Low', bestSlAtr: 1.0, bestTpAtr: 2.0, expectancyR: 0.31, winRate: 58.4, netReturnPercent: 14.2, trades: 34 },
    { volatilityRegime: 'Normal', bestSlAtr: 1.5, bestTpAtr: 3.0, expectancyR: 0.54, winRate: 56.1, netReturnPercent: 32.8, trades: 88 },
    { volatilityRegime: 'High', bestSlAtr: 1.75, bestTpAtr: 3.5, expectancyR: 0.44, winRate: 49.0, netReturnPercent: 18.6, trades: 42 },
    { volatilityRegime: 'Extreme', bestSlAtr: 2.25, bestTpAtr: 2.5, expectancyR: -0.08, winRate: 37.5, netReturnPercent: -2.4, trades: 16 },
  ];

  // MAE / MFE points
  const maeMfe: MaeMfePoint[] = chronoTrades.map((t) => ({
    tradeId: t.id,
    pair: t.pair,
    outcome: t.pnl > 0 ? 'win' : 'loss',
    maeR: t.maeR,
    mfeR: t.mfeR,
    rMultiple: t.rMultiple,
    setupGrade: t.setupGrade,
  }));

  // Setup Grades breakdown
  const gradeOrder: SetupGrade[] = ['A++', 'A+', 'A', 'B', 'Bad'];
  const setupGrades: SetupGradeBreakdown[] = gradeOrder.map((g) => {
    const subset = chronoTrades.filter((t) => t.setupGrade === g);
    const w = subset.filter((t) => t.pnl > 0);
    const gw = w.reduce((s, t) => s + t.pnl, 0);
    const gl = Math.abs(subset.filter((t) => t.pnl <= 0).reduce((s, t) => s + t.pnl, 0));
    const np = subset.reduce((s, t) => s + t.pnl, 0);
    const exp = subset.length > 0 ? subset.reduce((s, t) => s + t.rMultiple, 0) / subset.length : 0;
    return {
      grade: g,
      trades: subset.length,
      wins: w.length,
      winRate: subset.length > 0 ? Math.round((w.length / subset.length) * 1000) / 10 : 0,
      expectancyR: Math.round(exp * 100) / 100,
      profitFactor: gl > 0 ? Math.round((gw / gl) * 100) / 100 : gw > 0 ? 3.2 : 0,
      netProfit: Math.round(np * 100) / 100,
    };
  });

  // Robustness: Walk-forward & Monte Carlo
  const walkForwardFolds = [
    { fold: 'Fold 1', inSamplePeriod: '2022-01 – 2022-09', outOfSamplePeriod: '2022-10 – 2022-12', inSampleReturnPercent: 18.4, outOfSampleReturnPercent: 14.1, inSampleExpectancyR: 0.45, outOfSampleExpectancyR: 0.36, efficiencyRatio: 0.77 },
    { fold: 'Fold 2', inSamplePeriod: '2022-04 – 2022-12', outOfSamplePeriod: '2023-01 – 2023-03', inSampleReturnPercent: 21.2, outOfSampleReturnPercent: 16.8, inSampleExpectancyR: 0.49, outOfSampleExpectancyR: 0.41, efficiencyRatio: 0.79 },
    { fold: 'Fold 3', inSamplePeriod: '2022-07 – 2023-03', outOfSamplePeriod: '2023-04 – 2023-06', inSampleReturnPercent: 16.5, outOfSampleReturnPercent: 11.2, inSampleExpectancyR: 0.39, outOfSampleExpectancyR: 0.28, efficiencyRatio: 0.68 },
    { fold: 'Fold 4', inSamplePeriod: '2022-10 – 2023-06', outOfSamplePeriod: '2023-07 – 2023-09', inSampleReturnPercent: 22.8, outOfSampleReturnPercent: 18.9, inSampleExpectancyR: 0.52, outOfSampleExpectancyR: 0.44, efficiencyRatio: 0.83 },
    { fold: 'Fold 5', inSamplePeriod: '2023-01 – 2023-09', outOfSamplePeriod: '2023-10 – 2023-12', inSampleReturnPercent: 19.6, outOfSampleReturnPercent: 15.3, inSampleExpectancyR: 0.46, outOfSampleExpectancyR: 0.38, efficiencyRatio: 0.78 },
  ];

  const monteCarloDistribution: MonteCarloStep[] = [];
  const start = config.startingBalance;
  for (let idx = 0; idx <= 180; idx += 15) {
    const progress = idx / 180;
    const midGain = netProfit * progress;
    const spread = start * 0.26 * Math.sqrt(progress);
    monteCarloDistribution.push({
      tradeIndex: idx,
      p5: Math.round(start + midGain - spread * 1.45),
      p25: Math.round(start + midGain - spread * 0.6),
      p50: Math.round(start + midGain),
      p75: Math.round(start + midGain + spread * 0.65),
      p95: Math.round(start + midGain + spread * 1.55),
      drawdownP50: -Math.round((4.2 + 3.5 * Math.sin(progress * Math.PI)) * 10) / 10,
      drawdownP95: -Math.round((8.4 + 6.2 * Math.sin(progress * Math.PI * 0.85)) * 10) / 10,
    });
  }

  return {
    id,
    name,
    createdAt,
    config,
    strategyName,
    overview: {
      equityCurve,
      totalTrades: chronoTrades.length,
      wins: winsList.length,
      losses: lossesList.length,
      winRate: Math.round((winsList.length / chronoTrades.length) * 1000) / 10,
      netProfit,
      netReturnPercent: Math.round((netProfit / config.startingBalance) * 1000) / 10,
      expectancyR: Math.round((chronoTrades.reduce((s, t) => s + t.rMultiple, 0) / chronoTrades.length) * 100) / 100,
      profitFactor: grossLoss > 0 ? Math.round((grossWin / grossLoss) * 100) / 100 : 2.5,
      avgWin: winsList.length > 0 ? Math.round((grossWin / winsList.length) * 100) / 100 : 0,
      avgLoss: lossesList.length > 0 ? -Math.round((grossLoss / lossesList.length) * 100) / 100 : 0,
      maxDrawdownPercent: Math.round(maxDdPct * 100) / 100,
      maxDrawdownAmount: Math.round(maxDdAmt * 100) / 100,
      longestLosingStreak,
      recoveryTimeDays: 18,
      sharpeRatio: Math.round((1.45 * returnScale) * 100) / 100,
      finalBalance: Math.round(equity * 100) / 100,
    },
    marketConditions: {
      byVolatility,
      byStructure,
      bySession,
      byDayOfWeek,
      byTimeOfDay,
      byWeek,
      byMonth,
    },
    slTpOptimizer: {
      slMultiples,
      tpMultiples,
      cells,
      optimalByVolatility,
    },
    maeMfe,
    setupGrades,
    robustness: {
      walkForwardFolds,
      monteCarloDistribution,
      monteCarloMaxDd95Percent: 14.6,
      monteCarloRuinProbabilityPercent: 0.4,
      overallStabilityLabel: returnScale >= 0.9 ? 'Robust' : 'Moderate',
      parameterStability: [
        { parameterName: 'ATR Stop Loss Multiple', stabilityScore: 86, optimalRange: '1.25 – 1.75x ATR', sensitivity: 'Low' },
        { parameterName: 'ATR Take Profit Multiple', stabilityScore: 79, optimalRange: '2.50 – 3.50x ATR', sensitivity: 'Moderate' },
        { parameterName: 'Minimum ADX Threshold', stabilityScore: 82, optimalRange: '20 – 26', sensitivity: 'Low' },
        { parameterName: 'Asian Box Window (hrs)', stabilityScore: 71, optimalRange: '5 – 7 hrs', sensitivity: 'Moderate' },
      ],
    },
    trades: [...chronoTrades].reverse(),
  };
}

export const MOCK_BACKTEST_RESULTS: Record<string, BacktestResult> = {
  'bt-run-01': buildBacktestFromConfig(
    'bt-run-01',
    'London Breakout · 2Y Multi-Pair ZAR',
    '2026-11-10T16:40:00Z',
    'London Breakout Momentum',
    {
      id: 'bt-run-01',
      name: 'London Breakout · 2Y Multi-Pair ZAR',
      strategyId: 'strat-london-breakout',
      pairs: ['EURUSD', 'GBPUSD', 'USDZAR', 'XAUUSD'],
      timeframe: 'M15',
      historyLength: '2y',
      startingBalance: 200000,
      currency: 'ZAR',
      leverage: 100,
      riskPerTradePercent: 1.0,
      brokerAccountType: 'Raw Spread / ECN',
      costs: {
        spreadPips: 0.8,
        commissionPerLot: 110,
        slippagePips: 0.2,
        swapPerNight: -35,
      },
    },
    88412,
    1.0
  ),
  'bt-run-02': buildBacktestFromConfig(
    'bt-run-02',
    'NY Mean Reversion · 5Y Majors',
    '2026-11-08T11:15:00Z',
    'NY Session Mean Reversion',
    {
      id: 'bt-run-02',
      name: 'NY Mean Reversion · 5Y Majors',
      strategyId: 'strat-ny-reversion',
      pairs: ['EURUSD', 'AUDUSD', 'USDJPY'],
      timeframe: 'M15',
      historyLength: '5y',
      startingBalance: 200000,
      currency: 'ZAR',
      leverage: 100,
      riskPerTradePercent: 0.75,
      brokerAccountType: 'Raw Spread / ECN',
      costs: {
        spreadPips: 0.6,
        commissionPerLot: 110,
        slippagePips: 0.15,
        swapPerNight: -28,
      },
    },
    44910,
    0.78
  ),
  'bt-run-03': buildBacktestFromConfig(
    'bt-run-03',
    'Liquidity Sweep · 1Y Gold & GBP',
    '2026-10-29T19:05:00Z',
    'Multi-TF Liquidity Sweep',
    {
      id: 'bt-run-03',
      name: 'Liquidity Sweep · 1Y Gold & GBP',
      strategyId: 'strat-liquidity-sweep',
      pairs: ['XAUUSD', 'GBPUSD'],
      timeframe: 'H1',
      historyLength: '1y',
      startingBalance: 200000,
      currency: 'ZAR',
      leverage: 100,
      riskPerTradePercent: 1.25,
      brokerAccountType: 'Standard',
      costs: {
        spreadPips: 1.4,
        commissionPerLot: 0,
        slippagePips: 0.3,
        swapPerNight: -45,
      },
    },
    99103,
    1.18
  ),
};

export function toSavedSummary(r: BacktestResult): SavedBacktestSummary {
  return {
    id: r.id,
    name: r.name,
    createdAt: r.createdAt,
    strategyId: r.config.strategyId,
    strategyName: r.strategyName,
    pairs: r.config.pairs,
    timeframe: r.config.timeframe,
    historyLength: r.config.historyLength,
    currency: r.config.currency,
    startingBalance: r.config.startingBalance,
    netProfit: r.overview.netProfit,
    netReturnPercent: r.overview.netReturnPercent,
    winRate: r.overview.winRate,
    profitFactor: r.overview.profitFactor,
    maxDrawdownPercent: r.overview.maxDrawdownPercent,
    expectancyR: r.overview.expectancyR,
    totalTrades: r.overview.totalTrades,
  };
}

export function generateBacktestResultFromConfig(config: BacktestConfig, strategyName: string): BacktestResult {
  const id = `bt-run-${Date.now()}`;
  const seed = Math.floor(Date.now() % 1000000);
  const scale = (config.startingBalance / 200000) * (config.riskPerTradePercent / 1.0);
  const name =
    config.name?.trim() ||
    `${strategyName} · ${config.historyLength} ${config.timeframe} (${config.currency})`;

  return buildBacktestFromConfig(
    id,
    name,
    new Date().toISOString(),
    strategyName,
    { ...config, id, name },
    seed,
    Math.max(0.25, scale)
  );
}
