# Trading Bot - read this first

## The big idea
A forex trading bot that behaves like a STUDENT. It first learns the basics of forex, then learns to read the market, then to trade, protect its money, and learn from its own results. Everything is built as separate parts, each in its own lane.

## The cycle (the order everything follows)
1. FOUNDATION - what the student must know.
   Candlesticks, market structure, sessions, news, fair value gaps, equilibrium, liquidity, leverage, stop loss, break even. These parts only DETECT and REPORT. They never decide to trade.
2. MARKET - reading the market right now.
   Uses the foundation on live or historical price data: "What is the structure? Which session are we in? Is news coming?" Result: a clear picture of the market.
3. STRATEGY - the decision.
   A strategy is only a list of simple checks written with the foundation. Example: "Is the structure bullish? Yes. Are we at the Asia high? No. Requirement not met, strategy abandoned for now."
4. RISK MANAGEMENT - protecting the money.
   Before any trade: how big is the trade, where is the stop loss, what is the most we can lose today. If risk rules say no, there is no trade.
5. EXECUTION - taking the trade.
   Placing the trade, the stop loss and the target. Moving to break even. Closing the trade.
6. JOURNALING - writing down what happened.
   Every trade is recorded with the reason it was taken and its result.
7. TESTING AND REVIEW - learning.
   Backtest (replay history), then a demo-account forward test. Journal results feed back into improving conditions. Then the cycle starts again.

Data (price candles, news calendar) feeds steps 2 and 7.

## Honest status
- The code is not complete. New files will be needed.
- The strategies were written by AI from transcripts of mentor videos. They are NOT confirmed proven. The AI may have mis-transcribed or used its own logic.
- The backtester is NOT verified. Backtest results are NOT trusted. Never present them as facts.

## Backtesting goal
The offline EURUSD H1 backtest prototype is implemented but not verified; its results are untrusted. It must replay history in time order, use only information available at each moment, and track account balance and equity. The goal and current limits are described in `docs/CONTRACTS.md`.

## Golden rules
1. Every part stays in its own lane. A file may use another file, but never copies or tangles its code into it. When something breaks, only that one file should need to change.
2. Plain trading names that anyone with basic trading knowledge understands: bullish_market, ranging_market, stop_loss, break_even, entry_condition_1. No clever or technical names.
3. Do not silently change a strategy's logic. If a strategy looks wrong or does not match the mentor's transcript, TELL ME and wait for my answer.
4. If you find a problem in the backtest, report it. Do not hide it.
5. Before writing code, read docs/CONTRACTS.md and docs/DECISIONS.md.
6. Use the file and function names that already exist. If a new file is really needed, create it, add it to the folder list below, and add a line to docs/DECISIONS.md.
7. Give every changed file as ONE complete file. No partial snippets.
8. Never open or print .env or any key.
9. When finished, add a line to docs/DECISIONS.md.

## Where things live today
(We move toward the cycle layout ONE piece at a time, never all at once.)
- trading-engine/knowledge/ = the foundation (still called "knowledge" for now); `stop_loss.py`, `take_profit.py`, and `break_even.py` report supplied position levels against a quote; `spread.py` reports the bid/ask difference and only converts it when pip or tick size is supplied; `drawdown.py` reports equity decline from a supplied peak; `average_daily_range.py` reports the mean range of completed daily candles; `average_candle_range.py` reports mean range for an explicitly selected supported timeframe; `exponential_moving_average.py` reports completed-candle EMA 20/50/100/200; `pivot_points.py` calculates Traditional levels from supplied previous-period values; `fibonacci_retracement.py` calculates levels between supplied price points; `anchored_vwap.py` calculates VWAP from supplied prices and volume since an anchor; `timeframes.py` describes explicit candle intervals; `multi_timeframe_alignment.py` compares market structure across supplied timeframes; `weekly_bias.py` reports completed weekly structure and its alignment with daily structure; `round_numbers.py` reports configured round-number levels; `break_retest.py` reports a price-level break and later touch without claiming the level held; `previous_day_levels.py` reports the observed prior UTC day's high and low; `previous_week_levels.py` reports the observed prior UTC week's high and low; `economic_calendar.py` reports upcoming events and local snapshot freshness; `time_structure.py` reports exchange-local session and killzone clocks; `support_resistance.py` reports confirmed swing levels as candidates; `supply_demand.py` reports completed swing-candle ranges as candidate zones; `fair_value_gap.py` and `inverse_fvg.py` report configured gap formations and status; `liquidity.py` reports equal-swing pools and sweep status; `equilibrium.py` reports range midpoint, quartiles, and price location; `trend_lines.py` reports candidate lines across supplied timeframes; `daily_bias.py` exists but its scoring rules are unverified.
- trading-engine/strategies/ = strategies
- trading-engine/engine/ = simulator and models (testing)
- trading-engine/risk_management.py = account risk checks using explicitly supplied limits and account state; no orders
- trading-engine/broker/ = costs and fills; `lot_sizing.py` calculates position size; `ctrader_symbol_specs.py` adapts cTrader Forex contract and volume fields without guessing currency conversion
- trading-engine/analytics/ = results and metrics (review)
- trading-engine/data/ = price data, data-quality reports, and shared timeframe lengths for M1, M5, M15, M30, H1, H2, H4, D1, and W1. `knowledge/economic_calendar.py` reports local calendar snapshots; the control center opens the free Forex Factory calendar but does not download its events
- trading-bot-control-center/ = the screen (UI), including `pages/EconomicCalendarPage.tsx` for the yearly event calendar
- Old bot, for reference only: github.com/mekkie25/trading-portal

## The old bot (a source to borrow from)
An earlier version of this bot exists. It has features the new bot lacks. It is on GitHub at github.com/mekkie25/trading-portal, and on this computer in the folder old-bot/ (read only, never edit it).
- Full list of what is worth borrowing: docs/OLD_BOT.md. Read it before building anything new. The feature you are asked to build may already exist there.
- Never copy old code blindly. It may have bugs. Read it, rebuild it to follow this project's rules and docs/CONTRACTS.md, and give it plain names.
- After borrowing something, mark it DONE in docs/OLD_BOT.md and add a line to docs/DECISIONS.md.