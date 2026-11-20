export type BotRunState = 'Running' | 'Stopped' | 'Error';
export type ConnectionState = 'Connected' | 'Disconnected' | 'Connecting' | 'Error';
export type TradingMode = 'Demo' | 'Live';
export type CurrencyCode = 'ZAR' | 'USD' | 'EUR' | 'GBP';
export type DisplayCurrency = 'ZAR' | 'USD';

export type ForexPair =
  | 'EURUSD'
  | 'GBPUSD'
  | 'USDJPY'
  | 'XAUUSD'
  | 'USDZAR'
  | 'AUDUSD';

export type TradeDirection = 'BUY' | 'SELL';
export type SetupGrade = 'A++' | 'A+' | 'A' | 'B' | 'Bad';
export type VolatilityRegime = 'Low' | 'Normal' | 'High' | 'Extreme';
export type MarketStructure = 'Trending' | 'Ranging' | 'Breakout';
export type TradingSession = 'Asian' | 'London' | 'New York' | 'London/NY Overlap';
export type Timeframe = 'M5' | 'M15' | 'M30' | 'H1' | 'H4' | 'D1';
export type HistoryLength = '1y' | '2y' | '5y' | '10y' | 'Max available';
export type BrokerAccountType = 'Raw Spread / ECN' | 'Standard' | 'Zero Commission';

export interface BotStatusInfo {
  state: BotRunState;
  uptimeSeconds: number;
  startedAt: string | null;
  activeStrategiesCount: number;
  lastHeartbeat: string;
  version: string;
  errorMessage?: string;
}

export interface KillSwitchResult {
  botStatus: BotStatusInfo;
  closedPositionsCount: number;
  triggeredAt: string;
}

export interface PairToggleSetting {
  pair: ForexPair;
  enabled: boolean;
  spreadPips: number;
  maxDailyTrades: number;
  updatedAt: string;
}

export interface AutoPauseRule {
  enabled: boolean;
  threshold: number;
  unit: string;
  description: string;
}

export interface AutoPauseRules {
  dailyLossLimit: AutoPauseRule;
  maxDrawdown: AutoPauseRule;
  connectionLost: {
    enabled: boolean;
    graceSeconds: number;
    description: string;
  };
  consecutiveLosses: AutoPauseRule;
}

export interface AccountSummary {
  currency: CurrencyCode;
  balance: number;
  equity: number;
  openPnl: number;
  todayPnl: number;
  todayPnlPercent: number;
  openTradesCount: number;
  marginUsed: number;
  freeMargin: number;
  marginLevelPercent: number;
  leverage: number;
}

export interface EquityPoint {
  timestamp: string;
  label: string;
  equity: number;
  balance: number;
}

export interface OpenPosition {
  id: string;
  pair: ForexPair;
  direction: TradeDirection;
  entryPrice: number;
  currentPrice: number;
  stopLoss: number;
  takeProfit: number;
  sizeLots: number;
  floatingPnl: number;
  floatingPnlPips: number;
  strategyId: string;
  strategyName: string;
  setupGrade: SetupGrade | 'N/A';
  openedAt: string;
  swap: number;
  commission: number;
}

export interface ManualOrderPayload {
  pair: ForexPair;
  direction: TradeDirection;
  sizeLots: number;
  stopLoss: number;
  takeProfit: number;
  comment?: string;
}

export interface ModifyPositionSlTpPayload {
  stopLoss: number;
  takeProfit: number;
}

export type ActivityLevel = 'info' | 'signal' | 'order' | 'warning' | 'error';

export interface ActivityLogEntry {
  id: string;
  timestamp: string;
  level: ActivityLevel;
  pair?: string;
  strategyName?: string;
  message: string;
  details?: string;
}

export type ErrorSeverity = 'WARNING' | 'ERROR' | 'CRITICAL';

export interface ErrorLogEntry {
  id: string;
  timestamp: string;
  severity: ErrorSeverity;
  component: string;
  message: string;
  stackSummary?: string;
  resolved: boolean;
}

export type BrokerOrderStatus = 'FILLED' | 'REJECTED' | 'REQUOTED' | 'CANCELLED' | 'MODIFIED';

export interface TradeAuditEntry {
  id: string;
  timestamp: string;
  orderId: string;
  pair: ForexPair;
  direction: TradeDirection;
  action: 'OPEN' | 'CLOSE' | 'MODIFY_SLTP';
  requestedPrice: number;
  executedPrice: number | null;
  sizeLots: number;
  brokerResponse: BrokerOrderStatus;
  brokerMessage: string;
  latencyMs: number;
  strategyName: string;
}

export interface SystemStatusInfo {
  serverUptimeSeconds: number;
  cpuPercent: number;
  ramUsedGb: number;
  ramTotalGb: number;
  diskUsedGb: number;
  diskTotalGb: number;
  lastHeartbeat: string;
  ctraderStatus: ConnectionState;
  dataFeedStatus: ConnectionState;
  dataFeedProvider: string;
  lastError: {
    timestamp: string;
    message: string;
    component: string;
  } | null;
  botVersion: string;
  pythonVersion: string;
}

export interface LiveMarketQuoteInfo {
  symbol: ForexPair;
  time: string;
  bid: number;
  ask: number;
}

export interface LiveMarketCandleInfo {
  symbol: ForexPair;
  timeframe: 'M5';
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface LiveMarketDataInfo {
  connectionState: ConnectionState;
  environment: 'Demo' | 'Live' | 'Unknown';
  symbol: ForexPair;
  message: string;
  quote: LiveMarketQuoteInfo | null;
  lastClosedCandle: LiveMarketCandleInfo | null;
}

export interface MarketSnapshotInfo {
  symbol: ForexPair;
  as_of: string;
  updated_by: string;
  entry_criteria_evaluated: false;
  market_time: unknown;
  session: unknown;
  spread: unknown;
  reports: Record<'M1' | 'M5', Record<string, unknown>>;
  multi_timeframe_alignment: unknown;
  trend_lines: unknown;
  previous_day_levels: unknown;
  previous_week_levels: unknown;
  daily_profiles: unknown;
  unavailable_reports: Record<string, string>;
  latest_snapshot_error?: string;
}

export interface MarketConditionTags {
  volatilityRegime: VolatilityRegime;
  marketStructure: MarketStructure;
  session: TradingSession;
  newsNearby: boolean;
  newsEvent?: string;
  spreadPips: number;
  atrPips: number;
  htfBias: 'Bullish' | 'Bearish' | 'Neutral';
}

export interface JournalTrade {
  id: string;
  openedAt: string;
  closedAt: string;
  pair: ForexPair;
  direction: TradeDirection;
  strategyId: string;
  strategyName: string;
  strategyVersion?: string;
  setupGrade: SetupGrade;
  entryPrice: number;
  exitPrice: number;
  stopLoss: number;
  takeProfit: number;
  sizeLots: number;
  pnl: number;
  currency: CurrencyCode;
  rMultiple: number;
  durationMinutes: number;
  marketConditions: MarketConditionTags;
  notes: string;
  tags: string[];
  screenshotUrl?: string;
  maeR: number;
  mfeR: number;
  commission: number;
  swap: number;
}

export interface CapitalTransaction {
  id: string;
  date: string;
  type: 'DEPOSIT' | 'WITHDRAWAL';
  amount: number;
  currency: CurrencyCode;
  reference: string;
  notes?: string;
}

export interface JournalFilters {
  startDate?: string;
  endDate?: string;
  pair?: string;
  strategyId?: string;
  setupGrade?: SetupGrade | '';
  outcome?: 'all' | 'win' | 'loss';
  tag?: string;
  search?: string;
}

export interface JournalStats {
  totalTrades: number;
  wins: number;
  losses: number;
  winRate: number;
  netProfit: number;
  expectancyR: number;
  profitFactor: number;
  avgWin: number;
  avgLoss: number;
}

export interface JournalResponse {
  trades: JournalTrade[];
  stats: JournalStats;
  totalCount: number;
}

export interface BacktestCostSettings {
  spreadPips: number;
  commissionPerLot: number;
  slippagePips: number;
  swapPerNight: number;
}

export interface BacktestConfig {
  id?: string;
  name?: string;
  strategyId: string;
  pairs: ForexPair[];
  timeframe: Timeframe;
  historyLength: HistoryLength;
  startingBalance: number;
  currency: CurrencyCode;
  leverage: number;
  riskPerTradePercent: number;
  brokerAccountType: BrokerAccountType;
  costs: BacktestCostSettings;
}

export interface BacktestEquityPoint {
  date: string;
  equity: number;
  drawdownPercent: number;
}

export interface BacktestOverview {
  equityCurve: BacktestEquityPoint[];
  totalTrades: number;
  wins: number;
  losses: number;
  winRate: number;
  netProfit: number;
  netReturnPercent: number;
  expectancyR: number;
  profitFactor: number;
  avgWin: number;
  avgLoss: number;
  maxDrawdownPercent: number;
  maxDrawdownAmount: number;
  longestLosingStreak: number;
  recoveryTimeDays: number;
  sharpeRatio: number;
  finalBalance: number;
}

export interface ConditionBreakdownItem {
  bucket: string;
  trades: number;
  wins: number;
  winRate: number;
  netProfit: number;
  expectancyR: number;
  profitFactor: number;
  lowSampleWarning: boolean;
}

export interface MarketConditionsBreakdown {
  byVolatility: ConditionBreakdownItem[];
  byStructure: ConditionBreakdownItem[];
  bySession: ConditionBreakdownItem[];
  byDayOfWeek: ConditionBreakdownItem[];
  byTimeOfDay: ConditionBreakdownItem[];
  byWeek: ConditionBreakdownItem[];
  byMonth: ConditionBreakdownItem[];
}

export interface SlTpHeatmapCell {
  slAtrMultiple: number;
  tpAtrMultiple: number;
  expectancyR: number;
  netReturnPercent: number;
  winRate: number;
  profitFactor: number;
  trades: number;
}

export interface VolatilityOptimalSlTp {
  volatilityRegime: VolatilityRegime;
  bestSlAtr: number;
  bestTpAtr: number;
  expectancyR: number;
  winRate: number;
  netReturnPercent: number;
  trades: number;
}

export interface SlTpOptimizationResult {
  slMultiples: number[];
  tpMultiples: number[];
  cells: SlTpHeatmapCell[];
  optimalByVolatility: VolatilityOptimalSlTp[];
}

export interface MaeMfePoint {
  tradeId: string;
  pair: ForexPair;
  outcome: 'win' | 'loss';
  maeR: number;
  mfeR: number;
  rMultiple: number;
  setupGrade: SetupGrade;
}

export interface SetupGradeBreakdown {
  grade: SetupGrade;
  trades: number;
  wins: number;
  winRate: number;
  expectancyR: number;
  profitFactor: number;
  netProfit: number;
}

export interface WalkForwardFold {
  fold: string;
  inSamplePeriod: string;
  outOfSamplePeriod: string;
  inSampleReturnPercent: number;
  outOfSampleReturnPercent: number;
  inSampleExpectancyR: number;
  outOfSampleExpectancyR: number;
  efficiencyRatio: number;
}

export interface MonteCarloStep {
  tradeIndex: number;
  p5: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
  drawdownP50: number;
  drawdownP95: number;
}

export interface ParameterStabilityMetric {
  parameterName: string;
  stabilityScore: number;
  optimalRange: string;
  sensitivity: 'Low' | 'Moderate' | 'High';
}

export interface RobustnessAnalysis {
  walkForwardFolds: WalkForwardFold[];
  monteCarloDistribution: MonteCarloStep[];
  monteCarloMaxDd95Percent: number;
  monteCarloRuinProbabilityPercent: number;
  parameterStability: ParameterStabilityMetric[];
  overallStabilityLabel: 'Robust' | 'Moderate' | 'Fragile' | 'N/A';
}

export interface BacktestJobStatus {
  jobId: string;
  status: 'queued' | 'running' | 'completed' | 'cancelled' | 'failed';
  progressPercent: number;
  currentStep: string;
  startedAt: string;
  resultId?: string;
}

export interface BacktestResult {
  id: string;
  name: string;
  createdAt: string;
  prototypeStatus?: 'unverified';
  assumptions?: string[];
  dataQuality?: {
    status: 'PASS' | 'REVIEW' | 'ERROR';
    timeframe: string;
    candleCount: number;
    firstTime: string | null;
    lastTime: string | null;
    missingColumns: string[];
    invalidTimestampCount: number;
    duplicateTimestampCount: number;
    outOfOrderTimestampCount: number;
    invalidPriceRowCount: number;
    nonPositivePriceRowCount: number;
    invalidOhlcRowCount: number;
    zeroRangeCandleCount: number;
    gapCount: number;
    weekendShapedGapCount: number;
    gapExamples: Array<{
      previousTime: string;
      nextTime: string;
      gapHours: number;
      category: string;
    }>;
    omittedGapCount: number;
    largestCandleRanges: Array<{
      time: string;
      rangePercent: number;
      previousClose: number;
      high: number;
      low: number;
    }>;
    largestCloseChanges: Array<{
      previousTime: string;
      time: string;
      changePercent: number;
      previousClose: number;
      close: number;
    }>;
    summary: string;
  };
  config: BacktestConfig;
  strategyName: string;
  overview: BacktestOverview;
  marketConditions: MarketConditionsBreakdown;
  slTpOptimizer: SlTpOptimizationResult;
  maeMfe: MaeMfePoint[];
  setupGrades: SetupGradeBreakdown[];
  robustness: RobustnessAnalysis;
  trades: JournalTrade[];
}

export interface SavedBacktestSummary {
  id: string;
  name: string;
  createdAt: string;
  strategyId: string;
  strategyName: string;
  pairs: ForexPair[];
  timeframe: Timeframe;
  historyLength: HistoryLength;
  currency: CurrencyCode;
  startingBalance: number;
  netProfit: number;
  netReturnPercent: number;
  winRate: number;
  profitFactor: number;
  maxDrawdownPercent: number;
  expectancyR: number;
  totalTrades: number;
}

export interface LiveVsBacktestPoint {
  tradeIndex: number;
  label: string;
  liveReturnPercent: number;
  backtestReturnPercent: number;
}

export interface LiveVsBacktestMetrics {
  winRate: number;
  expectancyR: number;
  maxDrawdownPercent: number;
  avgTradePnl: number;
  profitFactor: number;
  totalTrades: number;
  netReturnPercent: number;
}

export interface LiveVsBacktestComparison {
  strategyId: string;
  strategyName: string;
  backtestName: string;
  diverging: boolean;
  divergenceReasons: string[];
  live: LiveVsBacktestMetrics;
  backtest: LiveVsBacktestMetrics;
  equityComparison: LiveVsBacktestPoint[];
}

export interface StrategyParameter {
  key: string;
  label: string;
  type: 'number' | 'boolean' | 'string' | 'select';
  value: number | boolean | string;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  description?: string;
}

export interface GradingCondition {
  id: string;
  metric: string;
  operator: '>=' | '<=' | '==' | '!=' | 'in';
  threshold: string;
  description: string;
}

export type SetupGradingRules = Record<SetupGrade, GradingCondition[]>;

export interface StrategyVersion {
  version: string;
  createdAt: string;
  notes: string;
  tradeIds: string[];
  tradeCount: number;
  isCurrent: boolean;
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  isActive: boolean;
  currentVersion: string;
  versions: StrategyVersion[];
  indicatorIds: string[];
  assignedPairs: ForexPair[];
  parameters: StrategyParameter[];
  gradingRules: SetupGradingRules;
  fileName?: string;
  codeSnippet?: string;
  updatedAt: string;
  lastBacktestSummary?: {
    date: string;
    winRate: number;
    profitFactor: number;
    netReturnPercent: number;
    expectancyR: number;
  };
}

export interface CreateStrategyPayload {
  name: string;
  description: string;
  indicatorIds: string[];
  assignedPairs: ForexPair[];
  fileName?: string;
  codeSnippet?: string;
}

export interface IndicatorParameter {
  key: string;
  label: string;
  type: 'number' | 'select';
  defaultValue: number | string;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
}

export interface Indicator {
  id: string;
  name: string;
  shortCode: string;
  category: 'Trend' | 'Momentum' | 'Volatility' | 'Volume' | 'Structure';
  description: string;
  parameters: IndicatorParameter[];
  isCustom: boolean;
}

export interface CreateIndicatorPayload {
  name: string;
  shortCode: string;
  category: Indicator['category'];
  description: string;
  parameters: IndicatorParameter[];
}

export interface HistoricalDataset {
  id: string;
  pair: ForexPair;
  timeframe: Timeframe;
  startDate: string;
  endDate: string;
  candleCount: number;
  gapsFound: number;
  lastUpdated: string;
  status: 'Up to date' | 'Outdated' | 'Validating' | 'Error';
}

export interface DataGap {
  id: string;
  datasetId: string;
  gapStart: string;
  gapEnd: string;
  missingCandles: number;
  reason: string;
}

export interface CurrencyExposureItem {
  currency: string;
  netLots: number;
  netNotionalZar: number;
  direction: 'LONG' | 'SHORT' | 'FLAT';
  percentOfEquity: number;
}

export interface CorrelationMatrixData {
  pairs: ForexPair[];
  matrix: number[][];
}

export interface PortfolioExposureData {
  accountEquity: number;
  currency: CurrencyCode;
  totalOpenRiskAmount: number;
  totalOpenRiskPercent: number;
  marginUsed: number;
  freeMargin: number;
  marginLevelPercent: number;
  currencyExposures: CurrencyExposureItem[];
  correlationMatrix: CorrelationMatrixData;
}

export interface NewsEventItem {
  id: string;
  timestamp: string;
  currency: string;
  title: string;
  impact: 'High' | 'Medium';
  forecast?: string;
  previous?: string;
  affectedPairs: ForexPair[];
}

export interface NewsFilterSettings {
  enabled: boolean;
  minutesBefore: number;
  minutesAfter: number;
}

export interface RiskSettings {
  positionSizingModel: 'fixed_fractional' | 'volatility_adjusted' | 'fixed_lot';
  fixedLotSize: number;
  maxRiskPerTradePercent: number;
  maxDailyLossPercent: number;
  maxDrawdownPercent: number;
  maxOpenTrades: number;
  maxCorrelatedExposurePercent: number;
  haltOnNewsMinutes: number;
}

export interface BrokerSettings {
  provider: 'cTrader';
  clientId: string;
  hasClientSecret: boolean;
  clientSecretMasked: string;
  accountId: string;
  environment: TradingMode;
  connectionState: ConnectionState;
  lastTestedAt?: string;
  statusMessage?: string;
}

export interface BrokerUpdatePayload {
  clientId: string;
  clientSecret?: string;
  accountId: string;
  environment: TradingMode;
}

export interface NotificationPreferences {
  tradeOpened: boolean;
  tradeClosed: boolean;
  error: boolean;
  botStopped: boolean;
  connectionLost: boolean;
  dailySummary: boolean;
  emailEnabled: boolean;
  emailAddress: string;
  telegramEnabled: boolean;
  telegramBotTokenMasked: string;
  hasTelegramToken: boolean;
  telegramChatId: string;
}

export interface SecuritySettings {
  username: string;
  twoFactorEnabled: boolean;
  sessionTimeoutMinutes: 15 | 30 | 60 | 240 | 0;
  lastLoginAt: string;
}

export interface TwoFactorSetupInfo {
  secret: string;
  otpauthUrl: string;
}

export interface AppSettings {
  apiBaseUrl: string;
  useMock: boolean;
  tradingMode: TradingMode;
  defaultCurrency: CurrencyCode;
  displayCurrency: DisplayCurrency;
  broker: BrokerSettings;
  notifications: NotificationPreferences;
  security: SecuritySettings;
}

export interface TestAlertResult {
  channel: 'email' | 'telegram';
  success: boolean;
  message: string;
  sentAt: string;
}
