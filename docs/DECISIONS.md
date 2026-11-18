# Decisions log - newest at the bottom
Format: date | decision | why | status (ACTIVE / ABANDONED / TODO)

2026-10-08 | Strategies are never changed, only their conditions | Experienced traders proved them | ACTIVE
2026-11-17 | Knowledge built as separate files, one per concept | Reuse in every strategy | ACTIVE
2026-11-17 | Four import lines in knowledge/ still use wrong file names | Blocks the knowledge folder from loading | TODO
2026-11-17 | .env was on GitHub; replace all keys and tokens | Old file stays in GitHub history | TODO
2026-11-18 | Port from old bot: first the advisor/optimiser, then the backtest panel, then the risk manager | Old bot had more features | ACTIVE
2026-11-18 | Small tasks only, one file or feature per AI prompt, commit before each AI change | Stops the mess | ACTIVE
2026-11-18 | Strategies are NOT confirmed proven; they came from AI summaries of transcripts | May contain AI mistakes | TODO check against the transcripts
2026-11-18 | Backtester is NOT verified yet | Results cannot be trusted | TODO verify before acting on any result
2026-11-18 | The "improvement tips" port waits until the backtest is verified | Tips from a wrong backtest would mislead us | ACTIVE
2026-11-18 | Cycle: foundation, market, strategy, risk management, execution, journaling, testing and review | Clear order, each part in its own lane | ACTIVE