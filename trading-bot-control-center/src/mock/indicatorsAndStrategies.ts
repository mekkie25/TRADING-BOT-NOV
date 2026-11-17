import type { Indicator, Strategy, ForexPair } from '../types';

export const AVAILABLE_PAIRS: ForexPair[] = [
  'EURUSD',
  'GBPUSD',
  'USDJPY',
  'XAUUSD',
  'USDZAR',
  'AUDUSD',
];

export const MOCK_INDICATORS: Indicator[] = [
  {
    id: 'ind-atr',
    name: 'Average True Range',
    shortCode: 'ATR',
    category: 'Volatility',
    description:
      'Measures market volatility over a rolling lookback window for dynamic stop-loss, take-profit, and regime classification.',
    isCustom: false,
    parameters: [
      { key: 'period', label: 'Lookback Period', type: 'number', defaultValue: 14, min: 5, max: 50, step: 1 },
      { key: 'smoothing', label: 'Smoothing Method', type: 'select', defaultValue: 'RMA', options: ['RMA', 'EMA', 'SMA'] },
    ],
  },
  {
    id: 'ind-ema',
    name: 'Exponential Moving Average',
    shortCode: 'EMA',
    category: 'Trend',
    description:
      'Weighted moving average used for higher-timeframe directional bias and dynamic pullback zones.',
    isCustom: false,
    parameters: [
      { key: 'fastPeriod', label: 'Fast Period', type: 'number', defaultValue: 20, min: 5, max: 100, step: 1 },
      { key: 'slowPeriod', label: 'Slow Period', type: 'number', defaultValue: 50, min: 20, max: 250, step: 5 },
      { key: 'source', label: 'Price Source', type: 'select', defaultValue: 'Close', options: ['Close', 'HL2', 'OHLC4'] },
    ],
  },
  {
    id: 'ind-rsi',
    name: 'Relative Strength Index',
    shortCode: 'RSI',
    category: 'Momentum',
    description:
      'Momentum oscillator measuring speed and magnitude of recent price movements to detect exhaustion and divergence.',
    isCustom: false,
    parameters: [
      { key: 'period', label: 'RSI Period', type: 'number', defaultValue: 14, min: 5, max: 30, step: 1 },
      { key: 'overbought', label: 'Overbought Level', type: 'number', defaultValue: 70, min: 60, max: 85, step: 1 },
      { key: 'oversold', label: 'Oversold Level', type: 'number', defaultValue: 30, min: 15, max: 40, step: 1 },
    ],
  },
  {
    id: 'ind-adx',
    name: 'Average Directional Index',
    shortCode: 'ADX',
    category: 'Trend',
    description:
      'Quantifies trend strength independent of direction; separates trending vs ranging market conditions.',
    isCustom: false,
    parameters: [
      { key: 'period', label: 'ADX Period', type: 'number', defaultValue: 14, min: 7, max: 30, step: 1 },
      { key: 'trendThreshold', label: 'Trend Threshold', type: 'number', defaultValue: 25, min: 15, max: 40, step: 1 },
    ],
  },
  {
    id: 'ind-bb',
    name: 'Bollinger Bands',
    shortCode: 'BB',
    category: 'Volatility',
    description:
      'Standard-deviation envelope around a simple moving average for mean-reversion extremes and volatility squeezes.',
    isCustom: false,
    parameters: [
      { key: 'period', label: 'SMA Period', type: 'number', defaultValue: 20, min: 10, max: 50, step: 1 },
      { key: 'stdDev', label: 'Std Deviation', type: 'number', defaultValue: 2.0, min: 1.0, max: 3.5, step: 0.1 },
    ],
  },
  {
    id: 'ind-vwap',
    name: 'Session Anchored VWAP',
    shortCode: 'AVWAP',
    category: 'Volume',
    description:
      'Tick-volume weighted average price anchored to London or New York session open for institutional fair-value tracking.',
    isCustom: false,
    parameters: [
      { key: 'anchorSession', label: 'Anchor Session', type: 'select', defaultValue: 'London', options: ['Asian', 'London', 'New York'] },
      { key: 'bandMultiplier', label: 'Deviation Band', type: 'number', defaultValue: 1.5, min: 0.5, max: 3.0, step: 0.25 },
    ],
  },
  {
    id: 'ind-swing',
    name: 'Market Structure & Liquidity Pools',
    shortCode: 'MSLP',
    category: 'Structure',
    description:
      'Identifies fractal swing highs/lows, break-of-structure (BOS), and equal high/low liquidity sweeps.',
    isCustom: true,
    parameters: [
      { key: 'swingLeft', label: 'Swing Left Bars', type: 'number', defaultValue: 5, min: 2, max: 15, step: 1 },
      { key: 'swingRight', label: 'Swing Right Bars', type: 'number', defaultValue: 3, min: 1, max: 10, step: 1 },
    ],
  },
  {
    id: 'ind-adr',
    name: 'Average Daily Range',
    shortCode: 'ADR',
    category: 'Volatility',
    description:
      'Tracks rolling daily pip range consumption to avoid chasing exhausted moves late in a session.',
    isCustom: false,
    parameters: [
      { key: 'days', label: 'Lookback Days', type: 'number', defaultValue: 10, min: 5, max: 30, step: 1 },
      { key: 'exhaustionPct', label: 'Exhaustion %', type: 'number', defaultValue: 85, min: 60, max: 120, step: 5 },
    ],
  },
];

export const MOCK_STRATEGIES: Strategy[] = [
  {
    id: 'strat-london-breakout',
    name: 'London Breakout Momentum',
    description:
      'Captures directional expansion out of the Asian session consolidation box during London open when HTF EMA alignment and ADX confirm impulse.',
    isActive: true,
    currentVersion: 'v1.4',
    versions: [
      {
        version: 'v1.4',
        createdAt: '2026-11-12T08:45:00Z',
        notes: 'Tightened maxSpreadPips from 2.2 to 1.8 and added H4 EMA confluence for A++ grading.',
        tradeIds: ['trd-1204', 'trd-1201', 'trd-1198', 'trd-1194', 'trd-1190'],
        tradeCount: 38,
        isCurrent: true,
      },
      {
        version: 'v1.3',
        createdAt: '2026-10-18T10:15:00Z',
        notes: 'Adjusted ATR take-profit multiple from 2.5x to 3.0x based on Q3 walk-forward fold.',
        tradeIds: ['trd-1182', 'trd-1179', 'trd-1171', 'trd-1166'],
        tradeCount: 29,
        isCurrent: false,
      },
      {
        version: 'v1.2',
        createdAt: '2026-09-02T14:00:00Z',
        notes: 'Initial USDZAR and XAUUSD session box scaling deployment.',
        tradeIds: ['trd-1140', 'trd-1134', 'trd-1122'],
        tradeCount: 18,
        isCurrent: false,
      },
    ],
    indicatorIds: ['ind-atr', 'ind-ema', 'ind-adx', 'ind-adr'],
    assignedPairs: ['EURUSD', 'GBPUSD', 'USDZAR', 'XAUUSD'],
    updatedAt: '2026-11-12T08:45:00Z',
    fileName: 'london_breakout_momentum.py',
    codeSnippet: `class LondonBreakoutMomentum(BaseStrategy):
    def evaluate_signal(self, ctx: MarketContext) -> Optional[Signal]:
        # Evaluated server-side in Python FastAPI engine
        if not ctx.in_session("London") or ctx.spread_pips > self.params["max_spread_pips"]:
            return None
        return self.check_box_breakout(ctx)`,
    parameters: [
      { key: 'asianBoxHours', label: 'Asian Box Window (hrs)', type: 'number', value: 6, min: 3, max: 9, step: 1, description: 'Hours prior to London open used to form range.' },
      { key: 'atrSlMultiple', label: 'Stop Loss (ATR Multiple)', type: 'number', value: 1.5, min: 0.5, max: 4.0, step: 0.1 },
      { key: 'atrTpMultiple', label: 'Take Profit (ATR Multiple)', type: 'number', value: 3.0, min: 1.0, max: 8.0, step: 0.25 },
      { key: 'minAdx', label: 'Minimum ADX Filter', type: 'number', value: 22, min: 10, max: 40, step: 1 },
      { key: 'maxSpreadPips', label: 'Max Spread (pips)', type: 'number', value: 1.8, min: 0.5, max: 5.0, step: 0.1 },
      { key: 'avoidHighImpactNews', label: 'Pause Around Red News', type: 'boolean', value: true },
    ],
    gradingRules: {
      'A++': [
        { id: 'gr-lb-1', metric: 'HTF EMA Alignment', operator: '==', threshold: 'Aligned H4 & H1', description: 'Price above/below both H4 50 EMA and H1 20 EMA in breakout direction.' },
        { id: 'gr-lb-2', metric: 'ADX(14)', operator: '>=', threshold: '26', description: 'Strong emerging trend momentum at breakout.' },
        { id: 'gr-lb-3', metric: 'ADR Consumed', operator: '<=', threshold: '45%', description: 'Plenty of daily range expansion remaining.' },
      ],
      'A+': [
        { id: 'gr-lb-4', metric: 'HTF EMA Alignment', operator: '==', threshold: 'Aligned H1', description: 'H1 EMA aligned with breakout direction.' },
        { id: 'gr-lb-5', metric: 'ADX(14)', operator: '>=', threshold: '22', description: 'Moderate trend strength confirmed.' },
      ],
      'A': [
        { id: 'gr-lb-6', metric: 'Spread Ratio', operator: '<=', threshold: '1.5 pips', description: 'Clean liquidity execution with standard spread.' },
        { id: 'gr-lb-7', metric: 'ADR Consumed', operator: '<=', threshold: '65%', description: 'Moderate daily range remaining.' },
      ],
      'B': [
        { id: 'gr-lb-8', metric: 'ADX(14)', operator: '>=', threshold: '17', description: 'Borderline range expansion; reduced conviction.' },
      ],
      'Bad': [
        { id: 'gr-lb-9', metric: 'News Window', operator: '==', threshold: 'Within 15m', description: 'Signal occurs inside high-impact news spread spike.' },
        { id: 'gr-lb-10', metric: 'ADR Consumed', operator: '>=', threshold: '85%', description: 'Daily range exhausted before entry.' },
      ],
    },
    lastBacktestSummary: {
      date: '2026-11-10',
      winRate: 54.2,
      profitFactor: 1.84,
      netReturnPercent: 46.8,
      expectancyR: 0.42,
    },
  },
  {
    id: 'strat-ny-reversion',
    name: 'NY Session Mean Reversion',
    description:
      'Fades overextended Bollinger Band & AVWAP deviations back toward institutional fair value during low-to-normal volatility New York afternoon windows.',
    isActive: true,
    currentVersion: 'v2.1',
    versions: [
      {
        version: 'v2.1',
        createdAt: '2026-11-11T14:20:00Z',
        notes: 'Disabled entries during Extreme volatility regimes after FOMC whipsaw.',
        tradeIds: ['trd-1203', 'trd-1199', 'trd-1195'],
        tradeCount: 31,
        isCurrent: true,
      },
      {
        version: 'v2.0',
        createdAt: '2026-09-24T09:00:00Z',
        notes: 'Migrated mean target from SMA(20) to London/NY Anchored VWAP midpoint.',
        tradeIds: ['trd-1160', 'trd-1155', 'trd-1149'],
        tradeCount: 42,
        isCurrent: false,
      },
    ],
    indicatorIds: ['ind-bb', 'ind-rsi', 'ind-vwap', 'ind-atr'],
    assignedPairs: ['EURUSD', 'AUDUSD', 'USDJPY'],
    updatedAt: '2026-11-11T14:20:00Z',
    fileName: 'ny_mean_reversion.py',
    codeSnippet: `class NYMeanReversion(BaseStrategy):
    def evaluate_signal(self, ctx: MarketContext) -> Optional[Signal]:
        if ctx.volatility_regime == "Extreme":
            return None
        return self.check_avwap_band_rejection(ctx)`,
    parameters: [
      { key: 'bbStdDev', label: 'Bollinger Std Dev', type: 'number', value: 2.2, min: 1.5, max: 3.0, step: 0.1 },
      { key: 'rsiExtremeLow', label: 'RSI Oversold Trigger', type: 'number', value: 28, min: 15, max: 40, step: 1 },
      { key: 'rsiExtremeHigh', label: 'RSI Overbought Trigger', type: 'number', value: 72, min: 60, max: 85, step: 1 },
      { key: 'atrSlMultiple', label: 'Stop Loss (ATR Multiple)', type: 'number', value: 1.25, min: 0.5, max: 3.0, step: 0.05 },
      { key: 'targetMode', label: 'Take Profit Target', type: 'select', value: 'AVWAP_Mid', options: ['AVWAP_Mid', 'BB_Mid', 'Fixed_2R'] },
    ],
    gradingRules: {
      'A++': [
        { id: 'gr-ny-1', metric: 'ADX(14)', operator: '<=', threshold: '20', description: 'Clear non-trending range regime ideal for reversion.' },
        { id: 'gr-ny-2', metric: 'RSI Divergence', operator: '==', threshold: 'Confirmed', description: 'Momentum divergence on M15 at outer 2.2σ band.' },
      ],
      'A+': [
        { id: 'gr-ny-3', metric: 'Volatility Regime', operator: 'in', threshold: 'Low, Normal', description: 'Orderly liquidity without trend shock.' },
      ],
      'A': [
        { id: 'gr-ny-4', metric: 'Spread', operator: '<=', threshold: '1.2 pips', description: 'Tight spread during NY liquidity.' },
      ],
      'B': [
        { id: 'gr-ny-5', metric: 'ADX(14)', operator: '<=', threshold: '26', description: 'Slight directional drift present.' },
      ],
      'Bad': [
        { id: 'gr-ny-6', metric: 'Volatility Regime', operator: '==', threshold: 'Extreme', description: 'Fading parabolic expansion during macro shock.' },
      ],
    },
    lastBacktestSummary: {
      date: '2026-11-08',
      winRate: 61.5,
      profitFactor: 1.62,
      netReturnPercent: 31.4,
      expectancyR: 0.34,
    },
  },
  {
    id: 'strat-liquidity-sweep',
    name: 'Multi-TF Liquidity Sweep',
    description:
      'Monitors equal highs/lows on H1/H4 and executes counter-sweep displacement entries on M15 following a confirmed market structure shift.',
    isActive: false,
    currentVersion: 'v1.1',
    versions: [
      {
        version: 'v1.1',
        createdAt: '2026-11-04T19:10:00Z',
        notes: 'Raised displacement threshold from 0.9x ATR to 1.1x ATR to filter weak sweeps.',
        tradeIds: ['trd-1202', 'trd-1197'],
        tradeCount: 24,
        isCurrent: true,
      },
      {
        version: 'v1.0',
        createdAt: '2026-08-15T11:30:00Z',
        notes: 'Baseline Multi-TF liquidity sweep implementation.',
        tradeIds: ['trd-1115', 'trd-1108'],
        tradeCount: 22,
        isCurrent: false,
      },
    ],
    indicatorIds: ['ind-swing', 'ind-ema', 'ind-atr', 'ind-rsi'],
    assignedPairs: ['XAUUSD', 'GBPUSD', 'USDJPY', 'USDZAR'],
    updatedAt: '2026-11-04T19:10:00Z',
    fileName: 'mtf_liquidity_sweep.py',
    codeSnippet: `class MultiTFLiquiditySweep(BaseStrategy):
    def evaluate_signal(self, ctx: MarketContext) -> Optional[Signal]:
        sweep = ctx.detect_liquidity_sweep(lookback=self.params["swingLookback"])
        if sweep and ctx.confirm_mss():
            return self.build_limit_entry(sweep)`,
    parameters: [
      { key: 'swingLookback', label: 'Liquidity Swing Lookback', type: 'number', value: 24, min: 10, max: 60, step: 2 },
      { key: 'minDisplacementAtr', label: 'Min Displacement (ATR)', type: 'number', value: 1.1, min: 0.5, max: 2.5, step: 0.1 },
      { key: 'atrSlMultiple', label: 'Stop Loss (ATR Multiple)', type: 'number', value: 1.4, min: 0.6, max: 3.0, step: 0.1 },
      { key: 'atrTpMultiple', label: 'Take Profit (ATR Multiple)', type: 'number', value: 3.5, min: 1.5, max: 6.0, step: 0.25 },
    ],
    gradingRules: {
      'A++': [
        { id: 'gr-ls-1', metric: 'Session', operator: '==', threshold: 'London/NY Overlap', description: 'Peak institutional liquidity sweep window.' },
        { id: 'gr-ls-2', metric: 'Displacement Candle', operator: '>=', threshold: '1.5x ATR', description: 'Aggressive institutional orderflow shift after sweep.' },
      ],
      'A+': [
        { id: 'gr-ls-3', metric: 'HTF Bias', operator: '==', threshold: 'Aligned H4', description: 'Sweep occurs into H4 discount/premium zone.' },
      ],
      'A': [
        { id: 'gr-ls-4', metric: 'Retracement Entry', operator: '<=', threshold: '0.62 Fib', description: 'Clean FVG / order-block pullback fill.' },
      ],
      'B': [
        { id: 'gr-ls-5', metric: 'Session', operator: '==', threshold: 'Asian', description: 'Lower volume sweep outside peak sessions.' },
      ],
      'Bad': [
        { id: 'gr-ls-6', metric: 'Spread Spike', operator: '>=', threshold: '3.0 pips', description: 'Thin book execution distortion.' },
      ],
    },
    lastBacktestSummary: {
      date: '2026-10-29',
      winRate: 48.0,
      profitFactor: 1.95,
      netReturnPercent: 52.1,
      expectancyR: 0.51,
    },
  },
];
