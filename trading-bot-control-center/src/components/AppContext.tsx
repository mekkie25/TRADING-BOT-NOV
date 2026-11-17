import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { api, USE_MOCK } from '../services/api';
import { convertCurrencyAmount, formatCurrency } from '../utils/formatters';
import type {
  AccountSummary,
  BotStatusInfo,
  ConnectionState,
  CurrencyCode,
  DisplayCurrency,
  KillSwitchResult,
  TradingMode,
} from '../types';

export type ThemeMode = 'dark' | 'light';

interface AppContextValue {
  theme: ThemeMode;
  toggleTheme: () => void;
  displayCurrency: DisplayCurrency;
  setDisplayCurrency: (currency: DisplayCurrency) => Promise<void>;
  formatDisplayAmount: (
    amount: number,
    sourceCurrency?: CurrencyCode,
    options?: { signed?: boolean; decimals?: number }
  ) => string;
  botStatus: BotStatusInfo | null;
  account: AccountSummary | null;
  connectionState: ConnectionState;
  tradingMode: TradingMode;
  useMock: boolean;
  isLoadingHeader: boolean;
  headerError: string | null;
  dataVersion: number;
  isAuthenticated: boolean;
  operatorUsername: string;
  lockSession: () => void;
  loginSession: (username: string) => void;
  refreshGlobalState: () => Promise<void>;
  setBotStatusDirect: (status: BotStatusInfo) => void;
  setConnectionDirect: (state: ConnectionState, mode?: TradingMode) => void;
  triggerKillSwitch: () => Promise<KillSwitchResult>;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

const THEME_STORAGE_KEY = 'tbcc_theme';
const CURRENCY_STORAGE_KEY = 'tbcc_display_currency';
const LOCK_STORAGE_KEY = 'tbcc_session_locked';

function getInitialTheme(): ThemeMode {
  try {
    const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (saved === 'light' || saved === 'dark') return saved;
  } catch {
    // ignore storage errors
  }
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
}

function getInitialDisplayCurrency(): DisplayCurrency {
  try {
    const saved = window.localStorage.getItem(CURRENCY_STORAGE_KEY);
    if (saved === 'USD' || saved === 'ZAR') return saved;
  } catch {
    // ignore
  }
  return 'ZAR';
}

function getInitialAuth(): boolean {
  try {
    return window.sessionStorage.getItem(LOCK_STORAGE_KEY) !== 'true';
  } catch {
    return true;
  }
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<ThemeMode>(getInitialTheme);
  const [displayCurrency, setDisplayCurrencyState] = useState<DisplayCurrency>(
    getInitialDisplayCurrency
  );
  const [botStatus, setBotStatus] = useState<BotStatusInfo | null>(null);
  const [account, setAccount] = useState<AccountSummary | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>('Connecting');
  const [tradingMode, setTradingMode] = useState<TradingMode>('Demo');
  const [isLoadingHeader, setIsLoadingHeader] = useState(true);
  const [headerError, setHeaderError] = useState<string | null>(null);
  const [dataVersion, setDataVersion] = useState(0);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(getInitialAuth);
  const [operatorUsername, setOperatorUsername] = useState('operator@desk');

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // ignore storage errors
    }
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  const setDisplayCurrency = useCallback(async (currency: DisplayCurrency) => {
    setDisplayCurrencyState(currency);
    try {
      window.localStorage.setItem(CURRENCY_STORAGE_KEY, currency);
    } catch {
      // ignore
    }
    try {
      await api.updateDisplayCurrency(currency);
    } catch {
      // non-blocking
    }
  }, []);

  const formatDisplayAmount = useCallback(
    (
      amount: number,
      sourceCurrency: CurrencyCode = 'ZAR',
      options?: { signed?: boolean; decimals?: number }
    ) => {
      const converted = convertCurrencyAmount(amount, sourceCurrency, displayCurrency);
      return formatCurrency(converted, displayCurrency, options);
    },
    [displayCurrency]
  );

  const refreshGlobalState = useCallback(async () => {
    setIsLoadingHeader(true);
    setHeaderError(null);
    try {
      const [statusRes, accountRes, settingsRes] = await Promise.all([
        api.getBotStatus(),
        api.getAccountSummary(),
        api.getSettings(),
      ]);
      setBotStatus(statusRes);
      setAccount(accountRes);
      setConnectionState(settingsRes.broker.connectionState);
      setTradingMode(settingsRes.tradingMode);
      setOperatorUsername(settingsRes.security.username);
    } catch (err) {
      setHeaderError(err instanceof Error ? err.message : 'Connection failed');
      setConnectionState('Error');
    } finally {
      setIsLoadingHeader(false);
    }
  }, []);

  useEffect(() => {
    void refreshGlobalState();
  }, [refreshGlobalState]);

  // Increment uptime locally every second while Running
  useEffect(() => {
    if (botStatus?.state !== 'Running') return;
    const timer = window.setInterval(() => {
      setBotStatus((prev) =>
        prev && prev.state === 'Running'
          ? { ...prev, uptimeSeconds: prev.uptimeSeconds + 1 }
          : prev
      );
    }, 1000);
    return () => window.clearInterval(timer);
  }, [botStatus?.state]);

  const setBotStatusDirect = useCallback((status: BotStatusInfo) => {
    setBotStatus(status);
  }, []);

  const setConnectionDirect = useCallback((state: ConnectionState, mode?: TradingMode) => {
    setConnectionState(state);
    if (mode) setTradingMode(mode);
  }, []);

  const triggerKillSwitch = useCallback(async () => {
    const result = await api.triggerKillSwitch();
    setBotStatus(result.botStatus);
    const updatedAccount = await api.getAccountSummary();
    setAccount(updatedAccount);
    setDataVersion((v) => v + 1);
    return result;
  }, []);

  const lockSession = useCallback(() => {
    setIsAuthenticated(false);
    try {
      window.sessionStorage.setItem(LOCK_STORAGE_KEY, 'true');
    } catch {
      // ignore
    }
  }, []);

  const loginSession = useCallback((username: string) => {
    setOperatorUsername(username);
    setIsAuthenticated(true);
    try {
      window.sessionStorage.removeItem(LOCK_STORAGE_KEY);
    } catch {
      // ignore
    }
  }, []);

  return (
    <AppContext.Provider
      value={{
        theme,
        toggleTheme,
        displayCurrency,
        setDisplayCurrency,
        formatDisplayAmount,
        botStatus,
        account,
        connectionState,
        tradingMode,
        useMock: USE_MOCK,
        isLoadingHeader,
        headerError,
        dataVersion,
        isAuthenticated,
        operatorUsername,
        lockSession,
        loginSession,
        refreshGlobalState,
        setBotStatusDirect,
        setConnectionDirect,
        triggerKillSwitch,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error('useAppContext must be used inside AppProvider');
  }
  return ctx;
}
