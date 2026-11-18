# Old bot - what is worth borrowing
Old bot folder: old-bot/ (names below are paths inside it)
Status of each item: NOT STARTED / IN PROGRESS / DONE

## Finding the best conditions (best times, days, stops, targets)
- backtest/advisor.py - plain-English improvement tips from trade results | NOT STARTED
- backtest/settings_optimizer.py - searches for better settings | NOT STARTED
- backtest/entry_analysis.py, backtest/export_advice.py | NOT STARTED

## Screens (user interface)
- src/components/views/BacktestView.tsx and BacktestResearchPanel.tsx - backtest panel | NOT STARTED
- DashboardView, TradeJournalView, LiveSimReplay, SettingsView | NOT STARTED
- EconomicCalendarView.tsx - event calendar screen | DONE (rebuilt as a free Forex Factory link; the app does not import unverified calendar data)
- HeaderClocks.tsx - session clocks | NOT STARTED

## Risk management
- risk/risk_manager.py and AdvancedLimitsView.tsx - trade and loss limits | NOT STARTED

## Testing
- backtest/replay_engine.py - chronological historical replay | IN PROGRESS (rebuilt as an offline prototype; not verified)
- backtest/live_sim.py - live simulation like historical replay | NOT STARTED
- backtest/compare_engines.py - checks two engines agree | NOT STARTED
- backtest/data_quality.py - checks price data for gaps and bad candles | DONE (rebuilt as an H1 report; suspicious moves are flagged for review, not rejected)

## Warning
Everything above was listed from file names only. The code has not been reviewed and may contain bugs.