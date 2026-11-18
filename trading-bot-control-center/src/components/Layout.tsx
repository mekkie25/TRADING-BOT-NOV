import { useState, type ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import {
  Activity,
  BookOpen,
  CalendarDays,
  Cpu,
  Database,
  FileText,
  FlaskConical,
  GitCompare,
  Layers,
  Lock,
  Menu,
  Moon,
  OctagonAlert,
  PieChart,
  ServerCog,
  Settings,
  ShieldAlert,
  Sun,
  Wifi,
  WifiOff,
  X,
} from 'lucide-react';
import { useAppContext } from './AppContext';
import { ConfirmDialog } from './ConfirmDialog';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: Activity, end: true },
  { to: '/journal', label: 'Journal', icon: BookOpen, end: false },
  { to: '/backtester', label: 'Backtester', icon: FlaskConical, end: false },
  { to: '/live-vs-backtest', label: 'Live vs Backtest', icon: GitCompare, end: false },
  { to: '/strategies', label: 'Strategies', icon: Layers, end: false },
  { to: '/indicators', label: 'Indicators', icon: Cpu, end: false },
  { to: '/portfolio', label: 'Portfolio', icon: PieChart, end: false },
  { to: '/risk', label: 'Risk & Safety', icon: ShieldAlert, end: false },
  { to: '/data-manager', label: 'Data Manager', icon: Database, end: false },
  { to: '/economic-calendar', label: 'Economic Calendar', icon: CalendarDays, end: false },
  { to: '/logs', label: 'Logs & Audit', icon: FileText, end: false },
  { to: '/system-status', label: 'System Status', icon: ServerCog, end: false },
  { to: '/settings', label: 'Settings', icon: Settings, end: false },
];

export function Layout({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [killOpen, setKillOpen] = useState(false);
  const [killing, setKilling] = useState(false);
  const [killNotice, setKillNotice] = useState<string | null>(null);

  const {
    theme,
    toggleTheme,
    displayCurrency,
    setDisplayCurrency,
    formatDisplayAmount,
    botStatus,
    account,
    connectionState,
    tradingMode,
    useMock,
    isLoadingHeader,
    triggerKillSwitch,
    lockSession,
  } = useAppContext();

  const botState = botStatus?.state ?? 'Stopped';
  const botBadgeStyle =
    botState === 'Running'
      ? 'border-emerald-500/35 bg-emerald-500/12 text-emerald-700 dark:text-emerald-300'
      : botState === 'Error'
      ? 'border-red-500/35 bg-red-500/12 text-red-700 dark:text-red-300'
      : 'border-slate-300 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-800/80 dark:text-slate-300';

  const connColor =
    connectionState === 'Connected'
      ? 'text-emerald-600 dark:text-emerald-400'
      : connectionState === 'Error'
      ? 'text-red-600 dark:text-red-400'
      : 'text-amber-600 dark:text-amber-400';

  const isLiveMode = tradingMode === 'Live';

  const handleConfirmKillSwitch = async () => {
    setKilling(true);
    try {
      const res = await triggerKillSwitch();
      setKillOpen(false);
      setKillNotice(
        `Kill Switch engaged: closed ${res.closedPositionsCount} open position(s) and stopped bot.`
      );
      window.setTimeout(() => setKillNotice(null), 6000);
    } finally {
      setKilling(false);
    }
  };

  const renderNavLinks = (onNavigate?: () => void) => (
    <nav className="flex-1 overflow-y-auto space-y-0.5 px-3 py-3" aria-label="Main navigation">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors whitespace-nowrap ${
                isActive
                  ? 'bg-blue-600/10 text-blue-700 border border-blue-600/25 dark:bg-blue-600/15 dark:text-blue-300 dark:border-blue-500/25'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/60 dark:hover:text-slate-100 border border-transparent'
              }`
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="truncate">{item.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );

  const renderSidebarFooter = (onNavigate?: () => void) => (
    <div className="border-t border-slate-200 dark:border-slate-800/90 px-4 py-3 text-xs text-slate-500 dark:text-slate-400 space-y-2">
      <div className="flex items-center justify-between">
        <span>Data Source</span>
        <span className="font-mono text-slate-800 dark:text-slate-200">
          {useMock ? 'Mock Store' : 'FastAPI'}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span>Bot Version</span>
        <span className="font-mono text-slate-800 dark:text-slate-200">
          v{botStatus?.version ?? '2.4.1'}
        </span>
      </div>
      <button
        type="button"
        onClick={() => {
          onNavigate?.();
          lockSession();
        }}
        className="w-full inline-flex items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 transition-colors"
      >
        <Lock className="h-3.5 w-3.5" />
        Lock Session
      </button>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-[#0B0F17] dark:text-slate-100 flex transition-colors duration-150">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex lg:w-60 lg:flex-col lg:fixed lg:inset-y-0 border-r border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#0E141F]">
        <div className="flex h-16 items-center px-5 border-b border-slate-200 dark:border-slate-800/90">
          <span className="font-display text-sm font-bold tracking-tight text-slate-900 dark:text-slate-100 whitespace-nowrap">
            Trading Bot Control Center
          </span>
        </div>

        {renderNavLinks()}
        {renderSidebarFooter()}
      </aside>

      {/* Mobile Sidebar Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden flex">
          <div
            className="fixed inset-0 bg-black/50 dark:bg-black/65"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="relative z-50 flex w-64 flex-col bg-white border-r border-slate-200 dark:bg-[#0E141F] dark:border-slate-800">
            <div className="flex h-16 items-center justify-between px-4 border-b border-slate-200 dark:border-slate-800">
              <span className="font-display text-sm font-bold text-slate-900 dark:text-slate-100">
                Trading Bot Control Center
              </span>
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                aria-label="Close navigation"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            {renderNavLinks(() => setMobileOpen(false))}
            {renderSidebarFooter(() => setMobileOpen(false))}
          </aside>
        </div>
      )}

      {/* Main Column */}
      <div className="flex-1 lg:pl-60 flex flex-col min-w-0">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 flex min-h-16 flex-wrap items-center justify-between gap-2 border-b border-slate-200 bg-white/95 dark:border-slate-800/90 dark:bg-[#0E141F]/95 px-3 py-2 sm:px-6 backdrop-blur-xs">
          <div className="flex items-center gap-2.5 min-w-0">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              className="lg:hidden rounded-lg border border-slate-200 bg-slate-100 p-2 text-slate-700 hover:bg-slate-200 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 shrink-0"
              aria-label="Open navigation"
            >
              <Menu className="h-4 w-4" />
            </button>

            {/* Persistent PAPER / LIVE Mode Badge on Every Page */}
            <span
              className={`inline-flex items-center rounded-md border px-2.5 py-1 font-mono text-[11px] font-bold tracking-wider uppercase whitespace-nowrap shrink-0 ${
                isLiveMode
                  ? 'border-red-500 bg-red-600 text-white shadow-xs'
                  : 'border-amber-500/40 bg-amber-500/15 text-amber-800 dark:text-amber-300'
              }`}
              title={
                isLiveMode
                  ? 'LIVE execution armed (Real Capital)'
                  : 'PAPER / Demo execution environment'
              }
            >
              {isLiveMode ? 'LIVE' : 'PAPER'}
            </span>

            <span className="lg:hidden font-display text-xs sm:text-sm font-bold text-slate-900 dark:text-slate-100 truncate">
              TBCC
            </span>
          </div>

          {/* Right Status Cluster */}
          <div className="flex flex-wrap items-center gap-2 sm:gap-3 shrink-0">
            {/* Bot Status */}
            <div
              className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium whitespace-nowrap ${botBadgeStyle}`}
            >
              <span className="hidden sm:inline">Bot:</span>
              <span className="font-semibold">
                {isLoadingHeader && !botStatus ? 'Loading...' : botState}
              </span>
            </div>

            {/* Account Balance */}
            <div className="hidden md:flex items-center gap-1.5 text-xs whitespace-nowrap">
              <span className="text-slate-500 dark:text-slate-400">Balance</span>
              <span className="font-mono font-semibold text-slate-900 dark:text-slate-100 tabular-nums">
                {account
                  ? formatDisplayAmount(account.balance, account.currency)
                  : '—'}
              </span>
            </div>

            {/* Connection Indicator */}
            <div className="hidden sm:flex items-center gap-1.5 text-xs whitespace-nowrap">
              {connectionState === 'Connected' ? (
                <Wifi className={`h-3.5 w-3.5 ${connColor}`} />
              ) : (
                <WifiOff className={`h-3.5 w-3.5 ${connColor}`} />
              )}
              <span className={`font-medium ${connColor}`}>{connectionState}</span>
            </div>

            {/* Display Currency Toggle (ZAR / USD) */}
            <button
              type="button"
              onClick={() =>
                void setDisplayCurrency(displayCurrency === 'ZAR' ? 'USD' : 'ZAR')
              }
              title="Toggle Display Currency (ZAR / USD)"
              className="inline-flex items-center rounded-lg border border-slate-200 bg-slate-100 px-2.5 py-1.5 font-mono text-xs font-semibold text-slate-800 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800/80 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors whitespace-nowrap shrink-0"
            >
              {displayCurrency}
            </button>

            {/* Theme Switch Button */}
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
              title={theme === 'dark' ? 'Switch to Light theme' : 'Switch to Dark theme'}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-100 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800/80 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors whitespace-nowrap shrink-0"
            >
              {theme === 'dark' ? (
                <>
                  <Sun className="h-3.5 w-3.5 text-amber-400" />
                  <span className="hidden sm:inline">Light</span>
                </>
              ) : (
                <>
                  <Moon className="h-3.5 w-3.5 text-slate-700" />
                  <span className="hidden sm:inline">Dark</span>
                </>
              )}
            </button>

            {/* Red Emergency Kill Switch */}
            <button
              type="button"
              onClick={() => setKillOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-red-500 shadow-xs transition-colors whitespace-nowrap shrink-0"
            >
              <OctagonAlert className="h-3.5 w-3.5" />
              <span>Kill Switch</span>
            </button>
          </div>
        </header>

        {killNotice && (
          <div className="border-b border-red-500/40 bg-red-500/15 px-4 py-2.5 text-xs font-medium text-red-800 dark:text-red-200">
            {killNotice}
          </div>
        )}

        {/* Page Content */}
        <main className="flex-1 p-3 sm:p-6 max-w-[1440px] w-full mx-auto">
          {children}
        </main>
      </div>

      <ConfirmDialog
        open={killOpen}
        title="EMERGENCY KILL SWITCH"
        description="This immediately closes ALL open broker positions at market price and halts the automated trading bot loop. This action cannot be undone. Proceed?"
        confirmLabel="Close All & Stop Bot"
        variant="danger"
        isProcessing={killing}
        onConfirm={handleConfirmKillSwitch}
        onCancel={() => setKillOpen(false)}
      />
    </div>
  );
}
