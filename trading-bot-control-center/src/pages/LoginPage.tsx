import { useState, type FormEvent } from 'react';
import { Lock, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import { useAppContext } from '../components/AppContext';

export function LoginPage() {
  const { loginSession, operatorUsername } = useAppContext();

  const [username, setUsername] = useState(operatorUsername || 'operator@desk');
  const [password, setPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [requiresTwoFactor, setRequiresTwoFactor] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await api.login(
        username,
        password || 'demo-operator',
        requiresTwoFactor ? otpCode : undefined
      );
      if (res.requiresTwoFactor && !res.authenticated) {
        setRequiresTwoFactor(true);
      } else if (res.authenticated) {
        loginSession(res.username);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#0B0F17] px-4">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#111824] p-6 sm:p-8 shadow-2xl space-y-6">
        <div className="space-y-1.5 text-center">
          <div className="mx-auto inline-flex h-11 w-11 items-center justify-center rounded-xl border border-blue-500/30 bg-blue-600/10 text-blue-600 dark:text-blue-400">
            <Lock className="h-5 w-5" />
          </div>
          <h1 className="font-display text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Trading Bot Control Center
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Operator authentication · Protected session
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Operator Username / Email
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password (any value in mock mode)"
              className="w-full rounded-lg border border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {requiresTwoFactor && (
            <div className="rounded-lg border border-blue-500/35 bg-blue-600/10 p-3 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-700 dark:text-blue-300">
                <ShieldCheck className="h-4 w-4" />
                <span>Two-Factor Authentication Required</span>
              </div>
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                required
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                placeholder="6-digit authenticator code"
                className="w-full rounded-lg border border-slate-300 bg-white dark:border-slate-700 dark:bg-[#0B0F17] px-3 py-2 font-mono text-sm tracking-widest text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:outline-none"
              />
            </div>
          )}

          {error && (
            <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50 transition-colors"
          >
            {submitting
              ? 'Verifying...'
              : requiresTwoFactor
              ? 'Verify 2FA & Unlock'
              : 'Sign In to Control Center'}
          </button>
        </form>

        <div className="rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#0B0F17] p-3 text-[11px] text-slate-500 dark:text-slate-400 text-center">
          Broker API keys and cTrader secrets are encrypted server-side and are never transmitted to or stored in the browser.
        </div>
      </div>
    </div>
  );
}
