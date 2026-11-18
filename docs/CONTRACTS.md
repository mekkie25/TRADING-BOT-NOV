# Contracts - the fixed formats

## Candle data
Columns: time, open, high, low, close. "time" is UTC.
(TO CHECK: confirm the data loader really uses these names.)

## Time
Everything inside the bot is UTC. South African time (Africa/Johannesburg) is only for the screen and reports.

## Names
File names are lowercase_with_underscores. Imports must match the file names exactly.

## Knowledge files
Candles go in. A clear result comes out: found yes/no, direction, price levels, candle time. No trading decisions.

## Trade record (planned)
strategy, result (WIN/LOSS/BREAKEVEN), money_pnl, date, date_sast, signal_time_sast, mfe_r, mae_pips, failure_reason