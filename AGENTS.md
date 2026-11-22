# Trading Bot - read this first

## Strategy build rules
1) The spec is docs/MASTER_STRATEGY_FILE_v1_9.md and must be read before building any strategy.
2) One file per strategy in trading-engine/strategies/, one test file each. Do not create a folder per strategy.
3) Never rewrite or delete an existing file. Extend it.
4) Build one strategy at a time, then stop and report.
5) Keep stops and targets tunable (spec Section 12) and keep every spec variant selectable.
6) If two things in the spec conflict, tell me. Do not change the spec's meaning.

-## Token-saving rules (free AI plans have small rate limits, so send as little as possible)
1) Do NOT read the whole spec file (it is about 82 KB). Read only: the section of the strategy being built, plus Section 0 (lines 7-35), Section 11 (lines 829-900) and Section 12 (line 901 to the end). Use line ranges, not the whole file.
2) Spec line ranges for v1.9 (if the file changes, find the headings instead): 3.1 Grabber 181-212; 3.2 Asia fade 213-228; 3.3 Asia breakout 229-243; 3.4 ORB 244-268; 3.5 Power Ranger 269-288; 3.6 Cracker 289-316; 3.7 OES A 317-332; 3.8 OES B 333-349; 3.9 ATH 350-362; 3.10 Intra-Range 363-368; 3.11 Reversal 369-376; 3.12 Pivot break-retest 377-389; 3.13 Value area 390-398; 3.14 VWAP 399-406; 3.15 First pullback 407-410; 3.16 513 411-415; 3.17 5M 200 EMA 416-421; 3.18 IFVG 422-425; 3.19 Grids 426-429; 3.20 Fibonacci 430-433; 3.21 Candlestick types 434-441; 3.22 Trend line 442-449.
3) Read only the files the task names, plus AGENTS.md. Do not scan the whole repository.
4) Never read these unless I ask: agy_backup/, venv/, node_modules/, repomix-port-context.xml, astpack-output.md, trading-bot-control-center.zip, trading-bot-control-center/.
5) Run only the tests for the files you changed, not the whole test suite. Do not run tests/news_feed (it has a known unrelated import error).
6) Keep replies short. Do not paste whole files back in the chat. Report: what changed, the test result, and the list of changed files.
7) If you get a rate-limit error (429 or "quota"), STOP and tell me. Do not retry in a loop.
8) Do not do extra work I did not ask for. One strategy per chat, then stop.

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
10. No pending orders. Never use buy stops, sell stops, limit orders or any order placed ahead of price. Every entry is taken only after a candle has CLOSED and the entry conditions are confirmed on that close, because a wick through a level can be a liquidity grab. Where the master file describes a stop or pending entry (3.5 Power Ranger step 4, and 3.21 Types 3 to 5), the master file stays unchanged, but the code enters on the confirming candle close instead. This rule overrides strategy build rule 5 for pending-order variants: do not build them. Tell me wherever a strategy differs from the master file because of this rule.
11. Stops and targets are starting values. The fixed numbers in the master file (for example Cracker 60, Power Ranger 40 and 120) are only defaults. Every strategy keeps its stop and target tunable, and the volatility-scaled mode (a multiple of the average candle range, with the average daily range as a second yardstick, master file Sections 11.1 and 12) must stay selectable. The long-term goal is to set stops and targets from current volatility, so a target is reachable and a stop is not squeezed by normal movement, whatever the year or the instrument. Never hard-code a stop or target number that cannot be changed.

## Where things live today
(We move toward the cycle layout ONE piece at a time, never all at once.)
- trading-engine/knowledge/ = the foundation (still called "knowledge" for now); `stop_loss.py`, `take_profit.py`, and `break_even.py` report supplied position levels against a quote; `spread.py` reports the bid/ask difference and only converts it when pip or tick size is supplied; `drawdown.py` reports equity decline from a supplied peak; `average_daily_range.py` reports the mean range of completed daily candles; `average_candle_range.py` reports mean range for an explicitly selected supported timeframe; `timeframes.py` describes explicit candle intervals; `multi_timeframe_alignment.py` compares market structure across supplied timeframes; `weekly_bias.py` reports completed weekly structure and its alignment with daily structure; `round_numbers.py` reports configured round-number levels; `break_retest.py` reports a price-level break and later touch without claiming the level held; `previous_day_levels.py` reports the observed prior UTC day's high and low; `previous_week_levels.py` reports the observed prior UTC week's high and low; `economic_calendar.py` reports upcoming events and local snapshot freshness; `time_structure.py` reports exchange-local session and killzone clocks; `support_resistance.py` reports confirmed swing levels as candidates; `supply_demand.py` reports completed swing-candle ranges as candidate zones; `fair_value_gap.py` and `inverse_fvg.py` report configured gap formations and status; `liquidity.py` reports equal-swing pools and sweep status; `equilibrium.py` reports range midpoint, quartiles, and price location; `trend_lines.py` reports candidate lines across supplied timeframes; `daily_bias.py` exists but its scoring rules are unverified.
- trading-engine/market/ = read-only market snapshots built after each completed M1 candle from available M1/M5 reports; no entry checks or trade decisions.
- trading-engine/indicators/ = reusable calculations for exponential moving averages, pivot points, Fibonacci levels, and anchored VWAP; they report values only and do not produce trade decisions.
- trading-engine/tests/ = tests grouped by area in `tests/knowledge/`, `tests/indicators/`, `tests/market/`, `tests/data/`, `tests/broker/`, `tests/engine/`, `tests/news_feed/`, `tests/integration/`, `tests/risk_management/`, and `tests/strategies/`; do not place test files beside production modules.
- New shared strategy foundations: `knowledge/operational_definitions.py`, `knowledge/strategy_sessions.py`, `knowledge/asia_levels.py`, `knowledge/daily_flip.py`, and `knowledge/volume_profile.py`; `strategies/confluence.py` counts confluence without starting trades; `broker/instrument_specs.py` converts configured instrument units; `data/source.py` is the replaceable candle-source interface.
- trading-engine/strategies/ = independent strategy checks; `strategies/pivot_break_retest/` evaluates the daily S1/R1 break-and-retest trigger without placing orders
- trading-engine/engine/ = simulator and models (testing)
- trading-engine/risk_management.py = account risk checks using explicitly supplied limits and account state, capped at 2% risk per trade and two trades per day; no orders
- trading-engine/broker/ = costs and fills; `lot_sizing.py` calculates position size; `ctrader_symbol_specs.py` adapts cTrader Forex contract and volume fields without guessing currency conversion
- trading-engine/analytics/ = results and metrics (review)
- trading-engine/data/ = price data, data-quality reports, and shared timeframe lengths for M1, M5, M15, M30, H1, H2, H4, D1, and W1; the live feed retains up to 10,080 completed M1 and M5 candles in memory after connection. `knowledge/economic_calendar.py` reports local calendar snapshots; the control center opens the free Forex Factory calendar but does not download its events
- trading-bot-control-center/ = the screen (UI), including `pages/EconomicCalendarPage.tsx` for the yearly event calendar and `components/MarketSnapshotPanel.tsx` for separately displayed M1/M5 market and indicator reports
- Old bot, for reference only: github.com/mekkie25/trading-portal

## The old bot (a source to borrow from)
An earlier version of this bot exists. It has features the new bot lacks. It is on GitHub at github.com/mekkie25/trading-portal, and on this computer in the folder old-bot/ (read only, never edit it).
- Full list of what is worth borrowing: docs/OLD_BOT.md. Read it before building anything new. The feature you are asked to build may already exist there.
- Never copy old code blindly. It may have bugs. Read it, rebuild it to follow this project's rules and docs/CONTRACTS.md, and give it plain names.
- After borrowing something, mark it DONE in docs/OLD_BOT.md and add a line to docs/DECISIONS.md.
-