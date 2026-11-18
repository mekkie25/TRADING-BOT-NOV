import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppProvider, useAppContext } from './components/AppContext';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { JournalPage } from './pages/JournalPage';
import { BacktesterPage } from './pages/BacktesterPage';
import { LiveVsBacktestPage } from './pages/LiveVsBacktestPage';
import { StrategiesPage } from './pages/StrategiesPage';
import { StrategyDetailPage } from './pages/StrategyDetailPage';
import { IndicatorsPage } from './pages/IndicatorsPage';
import { PortfolioPage } from './pages/PortfolioPage';
import { RiskManagementPage } from './pages/RiskManagementPage';
import { DataManagerPage } from './pages/DataManagerPage';
import { LogsPage } from './pages/LogsPage';
import { SystemStatusPage } from './pages/SystemStatusPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { EconomicCalendarPage } from './pages/EconomicCalendarPage';

function AppRoutes() {
  const { isAuthenticated } = useAppContext();

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<LoginPage />} />
      </Routes>
    );
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/journal" element={<JournalPage />} />
        <Route path="/backtester" element={<BacktesterPage />} />
        <Route path="/live-vs-backtest" element={<LiveVsBacktestPage />} />
        <Route path="/strategies" element={<StrategiesPage />} />
        <Route path="/strategies/:strategyId" element={<StrategyDetailPage />} />
        <Route path="/indicators" element={<IndicatorsPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/risk" element={<RiskManagementPage />} />
        <Route path="/data-manager" element={<DataManagerPage />} />
        <Route path="/logs" element={<LogsPage />} />
        <Route path="/system-status" element={<SystemStatusPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/economic-calendar" element={<EconomicCalendarPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <AppRoutes />
      </AppProvider>
    </BrowserRouter>
  );
}
