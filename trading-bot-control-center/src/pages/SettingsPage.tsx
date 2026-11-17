import { useCallback, useEffect, useState, type ChangeEvent, type FormEvent } from 'react';
import {
  AlertTriangle,
  Bell,
  Check,
  Download,
  KeyRound,
  Lock,
  PlugZap,
  Save,
  Send,
  Server,
  ShieldCheck,
  Upload,
} from 'lucide-react';
import { api, USE_MOCK } from '../services/api';
import type {
  AppSettings,
  DisplayCurrency,
  NotificationPreferences,
  SecuritySettings,
  TradingMode,
  TwoFactorSetupInfo,
} from '../types';
import { PanelShell } from '../components/DataState';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { useAppContext } from '../components/AppContext';
import { downloadJsonFile, formatDateTime } from '../utils/formatters';

export function SettingsPage() {
  const {
    setConnectionDirect,
    refreshGlobalState,
    displayCurrency,
    setDisplayCurrency,
    lockSession,
  } = useAppContext();

  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [clientId, setClientId] = useState('');
  const [clientSecretInput, setClientSecretInput] = useState('');
  const [accountId, setAccountId] = useState('');
  const [brokerEnv, setBrokerEnv] = useState<TradingMode>('Demo');
  const [savingBroker, setSavingBroker] = useState(false);
  const [testingBroker, setTestingBroker] = useState(false);
  const [brokerFeedback, setBrokerFeedback] = useState<string | null>(null);

  const [apiUrlInput, setApiUrlInput] = useState('');
  const [savingUrl, setSavingUrl] = useState(false);
  const [urlSaved, setUrlSaved] = useState(false);

  const [liveWarningOpen, setLiveWarningOpen] = useState(false);
  const [switchingMode, setSwitchingMode] = useState(false);

  // Alerts state
  const [notif, setNotif] = useState<NotificationPreferences | null>(null);
  const [telegramTokenInput, setTelegramTokenInput] = useState('');
  const [savingNotif, setSavingNotif] = useState(false);
  const [notifSaved, setNotifSaved] = useState(false);
  const [testingAlertChannel, setTestingAlertChannel] = useState<'email' | 'telegram' | null>(null);
  const [alertFeedback, setAlertFeedback] = useState<string | null>(null);

  // Security & 2FA state
  const [security, setSecurity] = useState<SecuritySettings | null>(null);
  const [twoFactorSetup, setTwoFactorSetup] = useState<TwoFactorSetupInfo | null>(null);
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [securityFeedback, setSecurityFeedback] = useState<string | null>(null);
  const [securityBusy, setSecurityBusy] = useState(false);

  // Backup state
  const [backupFeedback, setBackupFeedback] = useState<string | null>(null);

  const loadSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSettings();
      setSettings(data);
      setClientId(data.broker.clientId);
      setAccountId(data.broker.accountId);
      setBrokerEnv(data.broker.environment);
      setClientSecretInput('');
      setApiUrlInput(data.apiBaseUrl);
      setNotif(data.notifications);
      setSecurity(data.security);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  const handleSaveBroker = async (e: FormEvent) => {
    e.preventDefault();
    setSavingBroker(true);
    setBrokerFeedback(null);
    try {
      const updatedBroker = await api.updateBrokerSettings({
        clientId: clientId.trim(),
        clientSecret: clientSecretInput.trim() || undefined,
        accountId: accountId.trim(),
        environment: brokerEnv,
      });
      setSettings((prev) => (prev ? { ...prev, broker: updatedBroker } : null));
      setClientSecretInput('');
      setBrokerFeedback('Broker credentials saved securely server-side (secret hidden).');
      setConnectionDirect(updatedBroker.connectionState);
    } catch (err) {
      setBrokerFeedback(
        err instanceof Error ? err.message : 'Failed to save broker credentials'
      );
    } finally {
      setSavingBroker(false);
    }
  };

  const handleTestConnection = async () => {
    setTestingBroker(true);
    setBrokerFeedback(null);
    try {
      const tested = await api.testBrokerConnection();
      setSettings((prev) => (prev ? { ...prev, broker: tested } : null));
      setConnectionDirect(tested.connectionState);
      setBrokerFeedback(
        tested.statusMessage || `Connection state: ${tested.connectionState}`
      );
    } catch (err) {
      setBrokerFeedback(
        err instanceof Error ? err.message : 'Connection test failed'
      );
    } finally {
      setTestingBroker(false);
    }
  };

  const handleSaveApiUrl = async (e: FormEvent) => {
    e.preventDefault();
    setSavingUrl(true);
    setUrlSaved(false);
    try {
      const updated = await api.updateApiBaseUrl(apiUrlInput);
      setSettings(updated);
      setUrlSaved(true);
      window.setTimeout(() => setUrlSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update API URL');
    } finally {
      setSavingUrl(false);
    }
  };

  const handleRequestTradingMode = (target: TradingMode) => {
    if (!settings || settings.tradingMode === target) return;
    if (target === 'Live') {
      setLiveWarningOpen(true);
    } else {
      void commitTradingMode('Demo');
    }
  };

  const commitTradingMode = async (mode: TradingMode) => {
    setSwitchingMode(true);
    try {
      const updated = await api.setTradingMode(mode);
      setSettings(updated);
      setBrokerEnv(updated.broker.environment);
      setConnectionDirect(updated.broker.connectionState, updated.tradingMode);
      await refreshGlobalState();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to switch trading mode');
    } finally {
      setSwitchingMode(false);
      setLiveWarningOpen(false);
    }
  };

  const handleSaveNotifications = async () => {
    if (!notif) return;
    setSavingNotif(true);
    setNotifSaved(false);
    setAlertFeedback(null);
    try {
      const updated = await api.updateNotificationPreferences(
        notif,
        telegramTokenInput.trim() || undefined
      );
      setNotif(updated);
      setTelegramTokenInput('');
      setNotifSaved(true);
      window.setTimeout(() => setNotifSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save alert preferences');
    } finally {
      setSavingNotif(false);
    }
  };

  const handleSendTestAlert = async (channel: 'email' | 'telegram') => {
    setTestingAlertChannel(channel);
    setAlertFeedback(null);
    try {
      const res = await api.sendTestAlert(channel);
      setAlertFeedback(res.message);
    } catch (err) {
      setAlertFeedback(err instanceof Error ? err.message : 'Test alert failed');
    } finally {
      setTestingAlertChannel(null);
    }
  };

  const handleStart2FASetup = async () => {
    setSecurityBusy(true);
    setSecurityFeedback(null);
    try {
      const info = await api.setupTwoFactor();
      setTwoFactorSetup(info);
      setTwoFactorCode('');
    } catch (err) {
      setSecurityFeedback(err instanceof Error ? err.message : '2FA setup failed');
    } finally {
      setSecurityBusy(false);
    }
  };

  const handleVerify2FA = async (e: FormEvent) => {
    e.preventDefault();
    setSecurityBusy(true);
    setSecurityFeedback(null);
    try {
      const updated = await api.verifyTwoFactor(twoFactorCode);
      setSecurity(updated);
      setTwoFactorSetup(null);
      setTwoFactorCode('');
      setSecurityFeedback('Two-factor authentication is now enabled.');
    } catch (err) {
      setSecurityFeedback(err instanceof Error ? err.message : 'Invalid verification code');
    } finally {
      setSecurityBusy(false);
    }
  };

  const handleDisable2FA = async () => {
    setSecurityBusy(true);
    try {
      const updated = await api.disableTwoFactor();
      setSecurity(updated);
      setSecurityFeedback('Two-factor authentication disabled.');
    } finally {
      setSecurityBusy(false);
    }
  };

  const handleSessionTimeoutChange = async (
    minutes: SecuritySettings['sessionTimeoutMinutes']
  ) => {
    try {
      const updated = await api.updateSessionTimeout(minutes);
      setSecurity(updated);
      setSecurityFeedback('Session timeout updated.');
    } catch (err) {
      setSecurityFeedback(err instanceof Error ? err.message : 'Failed to update timeout');
    }
  };

  const handleExportBackup = async (section: 'journal' | 'strategies' | 'settings') => {
    setBackupFeedback(null);
    try {
      const data = await api.exportBackupSection(section);
      downloadJsonFile(
        data,
        `tbcc-${section}-backup-${new Date().toISOString().slice(0, 10)}.json`
      );
      setBackupFeedback(`Exported ${section} backup JSON.`);
    } catch (err) {
      setBackupFeedback(err instanceof Error ? err.message : 'Backup export failed');
    }
  };

  const handleImportBackup = (
    section: 'journal' | 'strategies' | 'settings',
    e: ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const parsed = JSON.parse(String(reader.result)) as Record<string, unknown>;
        const res = await api.importBackupSection(section, parsed);
        setBackupFeedback(res.message);
        if (section === 'settings') {
          await loadSettings();
          await refreshGlobalState();
        }
      } catch (err) {
        setBackupFeedback(
          err instanceof Error ? err.message : `Failed to import ${section} backup`
        );
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  const fieldClass =
    'w-full rounded-lg border border-slate-300 bg-white dark:border-slate-700 dark:bg-[#111824] px-3 py-2 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:outline-none';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Settings, Alerts, Security &amp; Backup
        </h1>
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          Configure cTrader API credentials, FastAPI URL, display currency, Telegram/Email alerts, 2FA security, and JSON backups.
        </p>
      </div>

      <PanelShell
        title="System & Broker Configuration"
        subtitle="API keys and broker secrets are stored encrypted server-side only and are never returned to the browser."
        isLoading={loading}
        error={error}
        isEmpty={!settings}
        onRetry={loadSettings}
        skeletonRows={6}
      >
        {settings && (
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
            {/* cTrader Broker Connection Panel (7 cols) */}
            <form
              onSubmit={handleSaveBroker}
              className="xl:col-span-7 rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-5 space-y-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <KeyRound className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    cTrader Open API Connection
                  </h3>
                </div>
                <span
                  className={`rounded border px-2.5 py-0.5 text-xs font-semibold ${
                    settings.broker.connectionState === 'Connected'
                      ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                      : settings.broker.connectionState === 'Error'
                      ? 'border-red-500/40 bg-red-500/15 text-red-700 dark:text-red-300'
                      : 'border-amber-500/40 bg-amber-500/15 text-amber-700 dark:text-amber-300'
                  }`}
                >
                  {settings.broker.connectionState}
                </span>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                    Client ID
                  </label>
                  <input
                    type="text"
                    value={clientId}
                    onChange={(e) => setClientId(e.target.value)}
                    placeholder="cTrader application Client ID"
                    className={`${fieldClass} font-mono`}
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                    Client Secret{' '}
                    <span className="text-slate-400 dark:text-slate-500">
                      ({settings.broker.hasClientSecret ? 'Stored server-side' : 'Not set'})
                    </span>
                  </label>
                  <input
                    type="password"
                    autoComplete="new-password"
                    value={clientSecretInput}
                    onChange={(e) => setClientSecretInput(e.target.value)}
                    placeholder={
                      settings.broker.hasClientSecret
                        ? settings.broker.clientSecretMasked
                        : 'Enter new Client Secret'
                    }
                    className={`${fieldClass} font-mono`}
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                    cTrader Account ID
                  </label>
                  <input
                    type="text"
                    value={accountId}
                    onChange={(e) => setAccountId(e.target.value)}
                    placeholder="e.g. 49201847"
                    className={`${fieldClass} font-mono`}
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                    Broker Environment
                  </label>
                  <select
                    value={brokerEnv}
                    onChange={(e) => setBrokerEnv(e.target.value as TradingMode)}
                    className={fieldClass}
                  >
                    <option value="Demo">Demo (Paper)</option>
                    <option value="Live">Live (Real Funds)</option>
                  </select>
                </div>
              </div>

              {(brokerFeedback || settings.broker.statusMessage) && (
                <div className="rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#111824] px-3 py-2 text-xs text-slate-700 dark:text-slate-300">
                  <p>{brokerFeedback || settings.broker.statusMessage}</p>
                  {settings.broker.lastTestedAt && (
                    <p className="mt-0.5 text-[11px] text-slate-500">
                      Last verified: {formatDateTime(settings.broker.lastTestedAt)}
                    </p>
                  )}
                </div>
              )}

              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 dark:border-slate-800 pt-4">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={testingBroker}
                  className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 disabled:opacity-50 whitespace-nowrap"
                >
                  <PlugZap className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                  {testingBroker ? 'Testing...' : 'Test Connection'}
                </button>

                <button
                  type="submit"
                  disabled={savingBroker}
                  className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50 whitespace-nowrap"
                >
                  <Save className="h-3.5 w-3.5" />
                  {savingBroker ? 'Saving...' : 'Save Broker Settings'}
                </button>
              </div>
            </form>

            {/* Right Column: API URL + Trading Mode + Display Currency (5 cols) */}
            <div className="xl:col-span-5 space-y-5">
              <form
                onSubmit={handleSaveApiUrl}
                className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-5 space-y-3"
              >
                <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2.5">
                  <div className="flex items-center gap-2">
                    <Server className="h-4 w-4 text-slate-600 dark:text-slate-300" />
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                      FastAPI Server Endpoint
                    </h3>
                  </div>
                  <span className="font-mono text-[11px] text-slate-500">
                    USE_MOCK: {String(USE_MOCK)}
                  </span>
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                    Server / API Base URL
                  </label>
                  <input
                    type="url"
                    value={apiUrlInput}
                    onChange={(e) => setApiUrlInput(e.target.value)}
                    placeholder="http://localhost:8000"
                    className={`${fieldClass} font-mono`}
                  />
                </div>

                <div className="flex items-center justify-end gap-3">
                  {urlSaved && (
                    <span className="inline-flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
                      <Check className="h-3.5 w-3.5" />
                      Updated
                    </span>
                  )}
                  <button
                    type="submit"
                    disabled={savingUrl}
                    className="rounded-lg border border-slate-300 bg-white px-4 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 disabled:opacity-50"
                  >
                    {savingUrl ? 'Saving...' : 'Save Endpoint'}
                  </button>
                </div>
              </form>

              {/* Execution Mode & Display Currency */}
              <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2.5">
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    Execution Mode &amp; Display Currency
                  </h3>
                  <span
                    className={`rounded border px-2 py-0.5 font-mono text-[11px] font-bold ${
                      settings.tradingMode === 'Live'
                        ? 'border-red-500 bg-red-600 text-white'
                        : 'border-amber-500/40 bg-amber-500/15 text-amber-700 dark:text-amber-300'
                    }`}
                  >
                    {settings.tradingMode === 'Live' ? 'LIVE' : 'PAPER'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2.5">
                  <button
                    type="button"
                    disabled={switchingMode}
                    onClick={() => handleRequestTradingMode('Demo')}
                    className={`rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${
                      settings.tradingMode === 'Demo'
                        ? 'border-amber-500/60 bg-amber-500/15 text-amber-800 dark:text-amber-200'
                        : 'border-slate-300 bg-white text-slate-600 dark:border-slate-700 dark:bg-[#111824] dark:text-slate-400'
                    }`}
                  >
                    Paper / Demo
                  </button>
                  <button
                    type="button"
                    disabled={switchingMode}
                    onClick={() => handleRequestTradingMode('Live')}
                    className={`rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${
                      settings.tradingMode === 'Live'
                        ? 'border-red-500 bg-red-600/20 text-red-700 dark:text-red-200'
                        : 'border-slate-300 bg-white text-slate-600 hover:border-red-500/40 hover:text-red-600 dark:border-slate-700 dark:bg-[#111824] dark:text-slate-400'
                    }`}
                  >
                    Live (Real Funds)
                  </button>
                </div>

                {settings.tradingMode === 'Live' && (
                  <div className="flex items-start gap-2 rounded-lg border border-red-500/40 bg-red-500/10 p-2.5 text-xs text-red-800 dark:text-red-200">
                    <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                    <span>Live mode armed — orders execute with real capital on cTrader.</span>
                  </div>
                )}

                <div className="flex items-center justify-between border-t border-slate-200 dark:border-slate-800 pt-3">
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                    Display Currency
                  </span>
                  <div className="inline-flex rounded-lg border border-slate-300 dark:border-slate-700 overflow-hidden">
                    {(['ZAR', 'USD'] as DisplayCurrency[]).map((curr) => (
                      <button
                        key={curr}
                        type="button"
                        onClick={() => void setDisplayCurrency(curr)}
                        className={`px-3 py-1 font-mono text-xs font-semibold transition-colors ${
                          displayCurrency === curr
                            ? 'bg-blue-600 text-white'
                            : 'bg-white text-slate-600 dark:bg-[#111824] dark:text-slate-300'
                        }`}
                      >
                        {curr}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Alerts Configuration (Telegram + Email + 6 Event Toggles + Send Test Message) */}
            {notif && (
              <div className="xl:col-span-12 rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <Bell className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                        Alerts &amp; Notifications (Telegram &amp; Email)
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Toggle individual notification events and dispatch test alerts to verify delivery.
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {notifSaved && (
                      <span className="inline-flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
                        <Check className="h-3.5 w-3.5" />
                        Saved
                      </span>
                    )}
                    <button
                      type="button"
                      disabled={testingAlertChannel !== null}
                      onClick={() => void handleSendTestAlert('telegram')}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 disabled:opacity-50"
                    >
                      <Send className="h-3 w-3" />
                      {testingAlertChannel === 'telegram' ? 'Sending...' : 'Test Telegram'}
                    </button>
                    <button
                      type="button"
                      disabled={testingAlertChannel !== null}
                      onClick={() => void handleSendTestAlert('email')}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 disabled:opacity-50"
                    >
                      <Send className="h-3 w-3" />
                      {testingAlertChannel === 'email' ? 'Sending...' : 'Test Email'}
                    </button>
                    <button
                      type="button"
                      onClick={handleSaveNotifications}
                      disabled={savingNotif}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
                    >
                      <Save className="h-3.5 w-3.5" />
                      {savingNotif ? 'Saving...' : 'Save Alerts'}
                    </button>
                  </div>
                </div>

                {alertFeedback && (
                  <div className="rounded-lg border border-emerald-500/35 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-700 dark:text-emerald-300">
                    {alertFeedback}
                  </div>
                )}

                <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
                  <div className="lg:col-span-6 space-y-2.5">
                    <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">
                      Event Triggers
                    </p>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                      {(
                        [
                          ['tradeOpened', 'Trade Opened'],
                          ['tradeClosed', 'Trade Closed'],
                          ['error', 'Error / Exception'],
                          ['botStopped', 'Bot Stopped'],
                          ['connectionLost', 'Connection Lost'],
                          ['dailySummary', 'Daily Summary Report'],
                        ] as const
                      ).map(([key, label]) => (
                        <label
                          key={key}
                          className="flex items-center justify-between gap-2 rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#111824] px-3 py-2 text-xs text-slate-800 dark:text-slate-200 cursor-pointer"
                        >
                          <span>{label}</span>
                          <input
                            type="checkbox"
                            checked={notif[key]}
                            onChange={(e) =>
                              setNotif((prev) =>
                                prev ? { ...prev, [key]: e.target.checked } : null
                              )
                            }
                            className="rounded border-slate-400 dark:border-slate-600 text-blue-600"
                          />
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="lg:col-span-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div className="space-y-2">
                      <label className="flex items-center gap-2 text-xs font-medium text-slate-700 dark:text-slate-300">
                        <input
                          type="checkbox"
                          checked={notif.emailEnabled}
                          onChange={(e) =>
                            setNotif((prev) =>
                              prev ? { ...prev, emailEnabled: e.target.checked } : null
                            )
                          }
                          className="rounded border-slate-400 dark:border-slate-600 text-blue-600"
                        />
                        Email Notifications
                      </label>
                      <input
                        type="email"
                        disabled={!notif.emailEnabled}
                        value={notif.emailAddress}
                        onChange={(e) =>
                          setNotif((prev) =>
                            prev ? { ...prev, emailAddress: e.target.value } : null
                          )
                        }
                        placeholder="alerts@example.com"
                        className={`${fieldClass} disabled:opacity-45`}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="flex items-center gap-2 text-xs font-medium text-slate-700 dark:text-slate-300">
                        <input
                          type="checkbox"
                          checked={notif.telegramEnabled}
                          onChange={(e) =>
                            setNotif((prev) =>
                              prev ? { ...prev, telegramEnabled: e.target.checked } : null
                            )
                          }
                          className="rounded border-slate-400 dark:border-slate-600 text-blue-600"
                        />
                        Telegram Bot Alerts
                      </label>
                      <input
                        type="text"
                        disabled={!notif.telegramEnabled}
                        value={notif.telegramChatId}
                        onChange={(e) =>
                          setNotif((prev) =>
                            prev ? { ...prev, telegramChatId: e.target.value } : null
                          )
                        }
                        placeholder="Telegram Chat ID"
                        className={`${fieldClass} font-mono disabled:opacity-45`}
                      />
                      <input
                        type="password"
                        autoComplete="new-password"
                        disabled={!notif.telegramEnabled}
                        value={telegramTokenInput}
                        onChange={(e) => setTelegramTokenInput(e.target.value)}
                        placeholder={
                          notif.hasTelegramToken
                            ? notif.telegramBotTokenMasked
                            : 'Bot token (stored server-side)'
                        }
                        className={`${fieldClass} font-mono disabled:opacity-45`}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Account Security & 2FA (6 cols) + Export & Backup (6 cols) */}
            {security && (
              <div className="xl:col-span-6 rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                      Account Security &amp; Two-Factor Auth
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={lockSession}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  >
                    <Lock className="h-3.5 w-3.5" />
                    Open Login Screen
                  </button>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                      Operator Account
                    </label>
                    <p className="font-mono text-xs font-semibold text-slate-900 dark:text-slate-100">
                      {security.username}
                    </p>
                    <p className="text-[11px] text-slate-500">
                      Last login: {formatDateTime(security.lastLoginAt)}
                    </p>
                  </div>

                  <div>
                    <label className="block text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                      Session Auto-Lock Timeout
                    </label>
                    <select
                      value={security.sessionTimeoutMinutes}
                      onChange={(e) =>
                        void handleSessionTimeoutChange(
                          Number(e.target.value) as SecuritySettings['sessionTimeoutMinutes']
                        )
                      }
                      className={fieldClass}
                    >
                      <option value={15}>15 minutes</option>
                      <option value={30}>30 minutes</option>
                      <option value={60}>60 minutes</option>
                      <option value={240}>4 hours</option>
                      <option value={0}>Never auto-lock</option>
                    </select>
                  </div>
                </div>

                <div className="rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#111824] p-3.5 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                        Two-Factor Authentication (TOTP)
                      </p>
                      <p className="text-[11px] text-slate-500">
                        Status:{' '}
                        <span
                          className={
                            security.twoFactorEnabled
                              ? 'text-emerald-600 dark:text-emerald-400 font-semibold'
                              : 'text-amber-600 dark:text-amber-400 font-semibold'
                          }
                        >
                          {security.twoFactorEnabled ? 'Enabled' : 'Not enabled'}
                        </span>
                      </p>
                    </div>
                    {security.twoFactorEnabled ? (
                      <button
                        type="button"
                        disabled={securityBusy}
                        onClick={() => void handleDisable2FA()}
                        className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-700 dark:text-red-300"
                      >
                        Disable 2FA
                      </button>
                    ) : (
                      <button
                        type="button"
                        disabled={securityBusy}
                        onClick={() => void handleStart2FASetup()}
                        className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-500"
                      >
                        Configure 2FA
                      </button>
                    )}
                  </div>

                  {twoFactorSetup && (
                    <form onSubmit={handleVerify2FA} className="space-y-3 border-t border-slate-200 dark:border-slate-800 pt-3">
                      <p className="text-[11px] text-slate-600 dark:text-slate-300">
                        Add this setup key to Google Authenticator or Authy, then enter the 6-digit verification code:
                      </p>
                      <div className="rounded-md border border-slate-300 bg-slate-100 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 font-mono text-xs font-bold tracking-wider text-slate-900 dark:text-slate-100">
                        {twoFactorSetup.secret}
                      </div>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          inputMode="numeric"
                          maxLength={6}
                          required
                          value={twoFactorCode}
                          onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, ''))}
                          placeholder="6-digit code"
                          className={`${fieldClass} font-mono tracking-widest`}
                        />
                        <button
                          type="submit"
                          disabled={securityBusy}
                          className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500 whitespace-nowrap"
                        >
                          Verify &amp; Enable
                        </button>
                      </div>
                    </form>
                  )}

                  {securityFeedback && (
                    <p className="text-xs text-blue-600 dark:text-blue-400">{securityFeedback}</p>
                  )}
                </div>

                <p className="text-[11px] text-slate-500 dark:text-slate-400">
                  Security Guarantee: Broker API keys, cTrader secrets, and Telegram bot tokens are encrypted and persisted strictly on the Python FastAPI server — never exposed to browser localStorage or plain-text responses.
                </p>
              </div>
            )}

            {/* Export & Backup Panel (6 cols) */}
            <div className="xl:col-span-6 rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-5 space-y-4">
              <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  Export &amp; Backup (JSON)
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Download portable backups or restore your trade journal, strategies, and system settings.
                </p>
              </div>

              <div className="space-y-3">
                {(
                  [
                    {
                      key: 'journal',
                      label: 'Trade Journal & Capital Ledger',
                      desc: 'Closed trades, notes, tags, and deposit/withdrawal records.',
                    },
                    {
                      key: 'strategies',
                      label: 'Strategies & Custom Indicators',
                      desc: 'Strategy definitions, parameters, version history, and grading rules.',
                    },
                    {
                      key: 'settings',
                      label: 'Settings, Risk & Auto-Pause Rules',
                      desc: 'Alert triggers, risk limits, pair toggles, and news blackout window.',
                    },
                  ] as const
                ).map((item) => (
                  <div
                    key={item.key}
                    className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#111824] p-3.5 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                        {item.label}
                      </p>
                      <p className="text-[11px] text-slate-500">{item.desc}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => void handleExportBackup(item.key)}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                      >
                        <Download className="h-3.5 w-3.5" />
                        Export
                      </button>
                      <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-blue-500/40 bg-blue-600/10 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-600/20 dark:text-blue-300">
                        <Upload className="h-3.5 w-3.5" />
                        Import
                        <input
                          type="file"
                          accept=".json,application/json"
                          onChange={(e) => handleImportBackup(item.key, e)}
                          className="hidden"
                        />
                      </label>
                    </div>
                  </div>
                ))}
              </div>

              {backupFeedback && (
                <div className="rounded-lg border border-emerald-500/35 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-700 dark:text-emerald-300">
                  {backupFeedback}
                </div>
              )}
            </div>
          </div>
        )}
      </PanelShell>

      <ConfirmDialog
        open={liveWarningOpen}
        title="Warning: Switch to Live Trading Mode?"
        description="Switching to LIVE mode routes automated bot signals to a real-money cTrader account. Losses are real and irreversible. Ensure your broker credentials, risk limits, and strategies have been verified in Paper/Demo mode first."
        confirmLabel="Confirm Switch to Live"
        variant="danger"
        isProcessing={switchingMode}
        onConfirm={() => commitTradingMode('Live')}
        onCancel={() => setLiveWarningOpen(false)}
      />
    </div>
  );
}
