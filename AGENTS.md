# Trading Bot - read this first

## What this is
A forex trading bot, still being built. The code is not complete, and new files will be needed.

## Honest status
- The strategies were written by AI from transcripts of mentor videos. They are NOT confirmed proven. The AI may have mis-transcribed something or used its own logic.
- The backtester has NOT been verified yet. Backtest results are NOT trusted. Never present them as facts.

## Golden rules
1. Do not silently change a strategy's logic. If a strategy looks wrong or does not match the mentor's transcript, TELL ME and wait for my answer.
2. If you find a problem in the backtest, report it. Do not hide it.
3. Before writing code, read docs/CONTRACTS.md and docs/DECISIONS.md.
4. Use the file names and function names that already exist. If a new file is really needed, create it, then add it to the folder list below and add a line to docs/DECISIONS.md.
5. Give every changed file as ONE complete file. No partial snippets.
6. Never open or print .env or any key.
7. When finished, add a line to docs/DECISIONS.md.

## Folders
- trading-engine/ = the bot (Python)
  - knowledge/ = one file per trading concept. They only DETECT and REPORT. They never decide to trade.
  - strategies/ = the trading strategies. They use knowledge/ as building blocks.
  - engine/ = simulator and models. data/ = price data. broker/ = costs and fills. analytics/ = metrics. news_feed/ = news calendar.
- trading-bot-control-center/ = the screen (UI)
- The old bot (reference only): github.com/mekkie25/trading-portal