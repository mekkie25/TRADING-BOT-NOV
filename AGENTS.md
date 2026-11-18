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
- trading-engine/knowledge/ = the foundation (still called "knowledge" for now)
- trading-engine/strategies/ = strategies
- trading-engine/engine/ = simulator and models (testing)
- trading-engine/broker/ = costs and fills (execution)
- trading-engine/analytics/ = results and metrics (review)
- trading-engine/data/ = price data. trading-engine/news_feed/ = news calendar
- trading-bot-control-center/ = the screen (UI)
- Old bot, for reference only: github.com/mekkie25/trading-portal