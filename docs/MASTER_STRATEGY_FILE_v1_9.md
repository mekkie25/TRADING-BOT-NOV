# MASTER STRATEGY FILE v1.9

Compiled from six AI-extracted strategy files covering about two years of the mentors' live streams (Chris, Keegan, Bonang, Ed and others). Version 1.9 adds section 11 (operational definitions of hold, rejection, momentum break and volume) and section 12 (stops and targets are tunable, with a calibration design). Version 1.8 renamed "triggers" to "strategies/triggers" throughout, because these are full strategies and not only entry triggers. Version 1.7 added more on boxes, Fridays, Gold timing and the prop news window (section 9g). Version 1.6 added the mentors' "boxes ticked" grading and more SuperTrend rules (section 9f). Version 1.5 corrected the Cracker and adds a fifth round (section 9e). Version 1.4 added a fourth round (section 9d). Version 1.3 added a third round (section 9c) and frequency and number tallies across all 417 videos (section 10). Version 1.2 added a second round of searches (section 9b). Version 1.1 added a search of the full transcript file (417 videos, about 52.8 million characters). Section 9 lists what the search confirmed, what it resolved, and what it did not find. Rules checked against the raw transcripts carry the new tag [CONFIRMED].

---

## 0. How to read this file

**IMPORTANT: every stop and take-profit number in this file is a reference value, not a final one.** They are what the mentors said, and are starting points only. In the bot they will be parameters, tuned by the backtesting panel (section 12). Likewise, words such as "hold", "rejection", "momentum break" and "volume" have no numbers in the transcripts; section 11 defines what each must look like in code, with values to tune.

**Two layers**
1. **Core strategies/triggers** (section 3) are the strategies and entry patterns that can start a trade.
2. **Confluence** (section 2) is the set of levels and indicators that add reasons to a strategy/trigger. Confluence never starts a trade by itself. It raises confidence. This matches how the mentors talk: they stack reasons until the trade looks solid.

**Confidence rule (as you decided):** a core strategy/trigger is required. Extra reasons raise confidence only. How many reasons are enough is left for backtesting.

**Tags on every rule**
- **[SOLID]** stated the same way everywhere I read.
- **[VARIANT]** files disagree; every version is kept, none picked.
- **[ONE FILE]** stated in one file only.
- **[GAP]** not stated; left for backtest.
- **[CONFIRMED]** checked against the raw mentor transcripts (see section 9 for the video).
- **[SUGGESTED]** my own judgement based on how the mentors stack reasons. Not stated as a rule in the files; test it.

**Banter warning.** The mentors joke constantly, so some names and "rules" in the transcripts are not real. Example: the "Teemo Cracker" is a joke on "Temu" (a cheap knock-off Cracker), and "ChatGPT improved cracker" is a gag. Where a rule comes from one jokey exchange, this file now says so, and the bot should not use it.

**Caveats**
- The six source files are AI summaries of the same transcripts, and some were built from each other. Agreement between files is weaker evidence than agreement between independent sessions.
- Time zone is SAST where stated (London open 08:00–10:00; New York open 15:30, which is 13:30 UTC).
- "Close" means a candle **body** close ("bodily closure"), with wicks allowed beyond it. [CONFIRMED: the mentors say "bodily closure" repeatedly in live analysis, section 9b item 3.]

**Left out on purpose (also the "Big Shack" strat, the "Naz players" and a "no stop loss, just TP" idea: named but never explained):** Bonang's value-to-value maths (no formulas given), Iron 2000 / I2K (a proprietary training indicator), Gold Sentinel (a bot), and name-only items with no rules (Heat Seeker, Big Dreamhouse, Triple S, B R A I N, KGO's model, VW Squeeze, VWAP Tick, Santa Rally).

---

## 1. General-case trade checklist (use this order for any setup)

**Before the session (pre-trade)**
1. **Bias.** Take daily bias from higher-timeframe structure and the daily candle. Was the day bearish and then flipped on the daily? Note it (see Daily Flip in section 2). [SOLID]
2. **Direction filter.** Price above the 200 EMA: look for longs. Below: look for shorts. The mentors also take counter-trend scalps back to the 200 EMA ("aggressive plays"); treat these as separate and higher-risk. [VARIANT]
3. **Skip conditions.** High-impact news (FOMC, NFP; one mentor trades news for fun), bank holidays, choppy directionless days, price trapped in the middle of the Asia range, and US indices in the London session. [SOLID]
4. **Mark levels.** Asia high and low, EQ (50%), previous daily high and low, Daily Flip (daily open), daily/weekly/monthly pivots, session POC and value area, VWAP, 200 EMA, 4H zones. [SOLID]
5. **Instrument and strategy.** One instrument, one strategy, one session. [SOLID in one mentor's rules]

**At the level (the entry decision)**
6. Identify **which level price is reacting to** and what it did there (swept it, closed back inside, broke and held, retested).
7. Check that a **core strategy/trigger** from section 3 has fired.
8. Count **confluence reasons** from section 2, grouped by type (direction, level alignment, location, timing and volume, candle confirmation).
9. If the strategy/trigger has fired, take the trade. More confluence means more confidence (and, if you choose later, more size). [Your rule]

**During the trade**
10. Stop and size from the strategy's rules. Risk is capped at 2% per trade at most; many sessions use 1% or less. [SOLID]
11. Break-even at 1R, or at 80% of the way to target. [VARIANT: both stated; one mentor says break-even "took away 20 wins"]
12. Partials at the first structural level, runner to the next. [SOLID]

**After the trade (post-trade)**
13. **Daily limit: two trades a day** ("two bullets a session and you call it"). [SOLID]
14. After a loss on the ORB, the two-bullet rule allows one more trade only on the opposite-side breakout. If it fails, stop for the day. [SOLID for ORB]
15. "One trade only, no double dip": win or lose, the first trade is the day's trade (profit factor did not improve with a second). Whether scale-ins count as one trade is not defined. [ONE FILE, VARIANT against the two-trade rule]
16. Journal every trade; one mentor avoids Mondays and leans into Thursdays from his journal. A pattern to test, not a rule. [ONE FILE]
17. **Transcript findings (section 9 item 7):** one or two "bullets" per session; if the market is chopping, "call it a session"; after a loss, do not overtrade or get emotional, come back tomorrow; one mentor says that if you have caught all three trades of the day you are done. [CONFIRMED]
18. **Still not found:** a numeric daily loss limit or a rule for a losing streak, other than the prop-firm limits in section 5. [GAP]

---

## 2. Confluence library (add-ons only)

Each item lists what it adds and the direction rule. None of these starts a trade alone, with the two conditional exceptions marked.

### 2.1 Direction confluence

**200 EMA** [SOLID]
- Price above = bullish backdrop, so supports longs. Price below = supports shorts.
- A pullback that tests and rejects the 200 EMA is a stronger reason than a plain pass.
- Danger zone: chopping across it, or sitting in the corridor between the 200 EMA and the Daily Flip. Confidence drops.
- Settings: Length 200, EMA, offset 0; source OHLC4 in one session, Close elsewhere. [VARIANT]
- Timeframes used: 5M ("50 is 50"), 1M (Cracker), 4H and Daily (bias), 15M/1H (anchored pullbacks). [SOLID]
- Multi-timeframe 200 EMA alignment (several frames agreeing) is mentioned as a stacking reason. [ONE FILE]
- 9/25 EMA crossover with 200 EMA filter: long when 9 crosses above 25 while price is above the 200; min target 2R; trail on the 9. [ONE FILE]

**Daily Flip (daily open) and daily bias** [SOLID as a level, usage by your description]
- The Flip is the daily open price. A day that was bearish then flips above the open, and a flip on the body of the daily candle, helps set daily bias.
- When the daily flips, volume is expected. A flip that breaks a level, retests it, then breaks further counts as stacked reasons.
- Pullbacks to the Flip that hold are a liquidity-grab-and-continue reaction: bullish above the Flip (hold as support), bearish below (hold as resistance). Targets: previous daily high or Asia high (bull), previous daily low or Asia low (bear). [SOLID]
- Flip invalidation: price goes cleanly through it and holds on the other side, so the intraday bias flips. [SOLID]
- Avoid: price chopping across the open with overlapping dojis and no volume. [SOLID]
- Definition: the Flip "is just your daily open level, where price opens up for the day." At the Flip, price either gets driven or sellers add and the candle keeps falling; it is the level where a bearish day can turn bullish. [CONFIRMED, section 9b item 2]
- Open gaps: mentors say a gap "will close" but not on any schedule (it can take days, weeks or months), so do not trade the gap closing as a timed event; the Flip is used to judge whether the gap fills soon or stays open. [CONFIRMED, section 9b item 8]

### 2.2 Level-alignment confluence (the biggest stacking family)

**Asia high / low** [SOLID]
- A key level for sweeps and breaks. Highest and lowest wick of the Asia session.
- Marking: the default is the highest and lowest wick of the session. One mentor says he uses the **body** ("bodilies") as the Asia low when a single wick is massive, and does the same with the previous daily low. [ONE SOURCE, section 9f item 5; test wick vs body]
- Hours: **01:00–06:00 GMT+2 (SAST)**. [CONFIRMED: a mentor states it directly in the transcripts, section 9 item 3.] Other versions in the summary files (00:00–05:00, ending 06:00, 00:00–08:00) are not supported by the transcripts.

**EQ (50% of a range)** [SOLID]
- EQ is the **50% of the previous day's range** (draw a fib from the previous daily high to low and mark 50%). A session EQ can also be used ("up to you"). It is built into the mentors' own indicator. [CONFIRMED, section 9c item 2] Ranges other than the previous day (Asia range, 4H candle) are used by the summaries and can be tested as variants.

**Pivots (daily, weekly, monthly, yearly; P, S1–S3, R1–R4)** [SOLID]
- Standard pivots are used in practice (debate about Fibonacci and Camarilla). [SOLID]
- Used as levels to reject, break and retest, and as targets (next pivot in sequence).
- Higher-timeframe pivots (weekly pivot, monthly S1/R1, yearly R1/R2) are stronger reasons than daily ones. [SUGGESTED]
- **Conditional standalone:** a break and retest of Daily S1 or R1 can be traded, but only with at least one other confluence (see section 3.12). [Your ruling]

**Previous daily high / low (PDH / PDL)** [SOLID]
- Used as sweep levels, targets, and direction confirmation (hold above PDH = bullish hold; hold below PDL = bearish).

**4H zones / key zones / flat-body levels** [SOLID as a concept]
- The 4H candle that broke structure (high, low, EQ), supply and demand "gold" zones, and flat-body support and resistance. [GAP: formal zone rules not stated]

**Stacking example (your intuition, not a file rule)** [SUGGESTED]
- Asia high and the daily pivot sit close together. Price sweeps the Asia high, consolidates between the two, then breaks through both. Breaking two important levels together is a stronger reason to expect the move to continue than breaking one.
- General form: when two or more marked levels are within a tight zone (a few pips on Gold, 20–30 points on indices), price breaking out of the zone counts as multiple confluence reasons at once. The width of "tight" is left for backtest. [GAP]

**Stacking examples the mentors actually use (from the transcripts)** [CONFIRMED, section 9b item 9]
- EQ lines up with the Asia low, then the move continues to the monthly pivot ("almost a double reverse grabber", Asia highs plus previous weekly lows).
- An open gap lines up with Asia lows and EQ, so the gap fill and the level share one zone.
- A retest of monthly R1 lines up with the Asia low retest.
- A zone lines up with the Asia high, so a sell is considered when price taps it.
- Pre-market high or low, daily low and 80% to target together: "no need to keep risk on the table" (break-even).

### 2.3 Location and value confluence

**Session POC and value area (VAH / VAL)** [SOLID]
- POC is the price with the most traded volume in the session profile. Price tends to move away from low-volume areas ("valleys") toward high-volume nodes.
- Rule: never start a new entry while price sits directly on the POC. [SOLID]
- A rejection at VAL or VAH that closes back inside the value area is a reason for a fade toward POC. A clean break and a held retest of VAH/VAL is a reason for continuation. [SOLID]
- POC rejection with CVD absorption is mentioned as a stronger reason. [ONE FILE]
- Weekly POC and VWAP together appear as stacked context on the Asia plays. [ONE FILE]
- **Conditional standalone:** see 3.13.

**VWAP (also spelled VWOP; anchored VWAP; weekly VWAP; London VWAP)** [SOLID]
- Acts as a magnet and a pivot between mean reversion and continuation. In a ranging market, an extended price printing a reversal candle can target VWAP. After a decisive break above or below, a VWAP retest that holds supports a continuation trade.
- DAX rule: if VWAP is inside the opening range, expect reversals; continuations only once VWAP sits outside it. [ONE FILE]
- VWAP is used as the confluence for the 200 EMA ("200 EMA + VWOP convergence") as a key-level framework. [ONE FILE]
- **Standalone status:** in the transcripts VWAP is mostly a break level and a first target ("first target's going to be VWAP"; "wait for the current day's VWAP to break"). The mentors mention a members-only VWAP "playbook" trade but never state its rules. Treat VWAP as an **add-on**, as you decided. The files' stand-alone entry (3.14) stays as an optional test only.

**ADR (20-day Average Daily Range) and standard deviations** [SOLID]
- Used for sizing and targets more than for entry. Stop = ADR × 1.25 (8 sessions) or average bottom wick × 1.5 (1 session). Target = 75% of ADR; second standard deviation (double ADR) on trend days. [VARIANT only on the stop multiplier]
- Do not enter when price is already at or beyond the full ADR. [SOLID]
- Mentors say the ADR levels act as support and resistance similar to pivot levels. If price holds above the first ADR, the move is likely to extend to two standard deviations. [CONFIRMED, section 9c item 6]
- Scale-in module: three equal-size positions at the POC / wick zone, the next level, and the deepest projected wick; average entry; total risk with all fills inside the limit. [SOLID within the ADR material]

### 2.4 Timing and volume confluence

- **Fridays:** "we always expect a Friday pullback" (said in 67 videos), so Friday trends are treated cautiously and the bias is often neutral. [CONFIRMED, section 9g item 2]
- **Gold in London:** one mentor says Gold during London is a no-go ("entire London just absolutely chop") and that Gold started moving at the COMEX open. One mentor only. [ONE SOURCE, section 9g item 3]
- **Month end:** mentors note "month end flows" as a reason for caution and once skipped a Monday because of them. [ONE SOURCE, section 9g item 4]
- **Session window.** London open (08:00–10:00 SAST) and the New York open (15:30; 15:30–16:30 window). Mid-Asia and the dead zones are weak. [SOLID]
- **Volume.** No number is ever given. It is judged visually: a "drive of volume" on the breaking candle, or "volume candles showing direction". Overlapping candles with no directional volume mean no trade. The aggressive entry is the drive-of-volume candle closure; the safer entry waits for a pullback after it. [CONFIRMED, section 9b item 4]
- **CVD absorption.** One file adds it to reversals at value-area edges. [ONE FILE]
- **SuperTrend (factor 1.6).** Used for stop and trailing on ORB, 200 EMA and some Asia plays. A mentor says "I use the SuperTrend, which is basically the ATR" and aims for 1:1 depending on volatility; a flip from bear to bull is also used as a signal. ATR period is still not stated. A **flat SuperTrend line is a low-probability, range-trading signal** and a reason to skip. For a 4-hour play the mentor waits for the 4H candle close and puts the stop at the bullish SuperTrend line. [CONFIRMED for the role; GAP for the period; section 9f item 2]

### 2.5 Candle confirmation confluence

- A solid-bodied candle closing in the trade direction (M5) after a pullback to a level. [ONE FILE]
- An engulfing candle against a sweep (5M for ORB reversal, 15M/30M for candlestick Type 3). [ONE FILE]
- "Flat body" support and resistance (30M candle) for Types 2 and 4. [ONE FILE]
- Bearish or bullish closure of a candle through a level ("candle closure setup") is described as vague. [GAP]

### 2.6a How the mentors actually count reasons: "boxes ticked" [CONFIRMED, section 9f item 1]

The mentors grade a setup by how many boxes are ticked, which is the same idea as your stacking approach:
- "Take your A+ setups rather than the one you think only takes **two boxes and not three**." A+ means all three; two of three is a weaker trade; one box means wait ("one box ticked for the Naz trade, wait for the second").
- Examples of a box in practice: price back inside the opening range; a first rejection; a bounce off London VWAP; then "a candle closure above here"; "we've ticked all the boxes, holding the monthly R2".
- Boxes are often **specific levels**: "getting back above 9800 was the first box we needed to tick", then a second level to hold; taking a trade with "only one box being ticked and not the other" is called aggressive. [CONFIRMED, section 9g item 1]
- The three boxes are never defined. A reasonable reading from these examples (an inference, test it) is: (1) price is at a marked level or zone, (2) there is a reaction there (sweep, rejection or hold), (3) a candle closure confirms in the trade direction. [SUGGESTED]
- In quiet or ranging weeks the mentors say to trade only the all-boxes A+ setups.

### 2.6 Suggested way to count (for backtest, not a file rule) [SUGGESTED]

Group the reasons into five types: direction, level alignment, location/value, timing and volume, candle confirmation. Count how many **types** agree, not the number of items. Two pivots plus an Asia high is one type (level alignment). A 200 EMA hold plus a value-area rejection plus a London-open entry is three types. Backtest minimum counts of 1, 2 and 3 types for each strategy/trigger.

---

## 3. Core strategies/triggers

Each strategy/trigger lists: instruments and timeframes, pre-trade conditions, the entry, suggested confluence from section 2, in-trade rules, exits, and conflicts and gaps. "Suggested confluence" uses the [SUGGESTED] tag throughout.

### 3.1 Grabber (Reverse Grabber / Grabber Kick / EQ Grabber / Vienna Grabber)

**Instruments / timeframes:** US30 and NAS100 most often; Gold, DAX, DXY too. 4H/daily for range and EQ; 15M/5M for sweep, close-back-inside and EQ tap; 1M occasionally. **Sessions:** London and New York.

**Pre-trade:** range-bound or consolidating, or just after a sweep that failed to continue. Skip strong one-way trend days. Asia high/low and EQ marked. [SOLID]

**Entry**
1. Price retests an Asia boundary. [SOLID]
2. Price sweeps beyond the Asia high or low and a candle **closes back inside**. A wick that stays outside does not count. [SOLID]
3. EQ decides the entry:
   - **Standard Grabber:** after an Asia-low sweep, price rises to EQ; if EQ holds as support, go long. Mirror for shorts. [SOLID]
   - **Reverse Grabber / Kick:** after the sweep and close back inside, price rallies toward EQ, rejects underneath it, and you go short immediately. [SOLID]
   - **EQ Grabber (confirmation entry):** wait for the first confirming candle closing away from EQ. [SOLID]
- **Grubber Kick, US30 3-rule box:** 15M structure, 5M execution, Asia range mapped 01:00–06:00 SAST, trade after 06:00; stop 30–35 points beyond EQ. [ONE FILE]
- **Grabber Sell:** equal lows plus a close under EQ. [ONE FILE]

**Suggested confluence:** a 200 EMA that agrees with the direction; the Asia boundary lining up with a pivot or previous daily high/low; a London or NY open timing; POC or value-area edge near the sweep. [SUGGESTED]

**Kill:** price keeps closing outside the range after the sweep; price trades through EQ with no rejection. [SOLID]

**Stop:** beyond the sweep's swing high/low. [SOLID] Size: a mentor says he "normally with the grabber used to go 30", depending on market volatility. [CONFIRMED for 30; others in the summaries: 50–60, 25, 30–40 on indices, 5–10 beyond the wick, VARIANT]

**Exit:** target sequence for a short from the Asia low: Asia low first, then the daily pivot, then EQ, scaled as you like. [CONFIRMED] 1:1 first partial; 1:2 or 1:3 full; opposite Asia extreme, Daily S1/R1, previous daily high/low. Break-even at 1:1 or 80% of the way. Partial at EQ or the first pivot, runner to the opposite boundary. [SOLID]

**Risk:** 1–2% per trade, sized to the stop. [SOLID]

**Targets by direction** [CONFIRMED, section 9d item 3]: a long Grabber (sweep of the lows, EQ holds) targets the Asia highs; if price instead breaks and holds under EQ, look for sells to Daily S1 and possibly the previous daily low.

**Transcript confirmation** [CONFIRMED, section 9b item 5]: a mentor states "three simple rules: 1) Asia highs and lows, 2) a retest, 3) a sweep of the low or high." The sweep is then a liquidity sweep that tests EQ; if EQ holds as support, buy (mirror for sells). **Break-even:** "we get a close above the daily pivot, now we can go break even"; on a 30-pip Grabber "the rule is 1:1, you go break even if you don't close"; elsewhere break-even at 80% to target. All three are stated; test each.

**Gaps:** EQ confirmation timeframe; EQ when several ranges compete; minimum/maximum sweep depth. [GAP]

### 3.2 Asia sweep-and-fade (fakeout / mean reversion)

**Pre-trade:** London open or early New York; not mid-Asia; skip if both Asia extremes are already taken and price is in the middle. [SOLID]

**Entry:** price breaks beyond Asia high or low, sweeps liquidity, fails to hold, a candle closes back inside; enter against the sweep, targeting EQ then the opposite Asia extreme. NotebookLM adds a solid-bodied M5 close back inside and a stop 5–10 pips beyond the wick. Example: NAS long at an Asia-low retest. [VARIANT on stop; entry SOLID]

**Suggested confluence:** sweep occurs at a pivot, previous daily low/high, or 200 EMA; EQ target aligns with VWAP or POC; bias agrees with the daily flip. [SUGGESTED]

**Exit:** EQ, opposite Asia extreme, or daily pivot. Break-even at EQ or 80% of the target. If a trade closes back inside after a breakout entry, exit at once. [SOLID]

**Stop examples:** 30 pips on index scalps, 50 pips Gold, 100 pips Gold in wide ranges. [VARIANT]

*Note: this and 3.3 are opposite styles on the same level (fade 10 sessions, continuation 14 sessions). Code them separately; do not blend.*

**Transcript rule on direction** [CONFIRMED, section 9c item 1]: mentors say that whichever Asia high or low is taken first after the Asia session, price "tends to trade into that direction" for the day, and give a week of examples (Monday, Tuesday, Friday). This supports continuation (3.3) as the main style. A fake-out (a break that is reclaimed) is the exception that gets the fade. For the fade, mentors describe a "normal 25 to 30 pip" trade; a safer entry waits for a second candle to hold the confirmation; first target Asia high (or low), then 1:2, or 3R to the far Asia extreme.

### 3.3 Asia breakout continuation (including OI-OI)

**Entry**
- A candle closes outside the range with volume. Above Asia high: long (or wait for a retest that holds as support). Below Asia low: short (or retest holding as resistance). [SOLID]
- **OI-OI (outside-inside-outside):** candle 1 closes outside, candle 2 closes back inside, candle 3 closes outside again; enter in the direction of candle 3. [ONE FILE]
- Gold range breakout with Asia-high / Asia-low triggers and weekly R2 as a target. [ONE FILE]

**Suggested confluence:** your pivot-stacking example fits here: Asia high and the daily pivot close together, price breaks both, 200 EMA backing it, London open timing. [SUGGESTED]

**Exit:** Daily R1/R2, previous daily high, 75% of ADR. If a breakout candle closes back inside the Asia range, close immediately. [SOLID]

**Stop:** outside the breakout structure (30 / 50 / 100 pips by instrument). [VARIANT]

**Gap:** what counts as "with volume". [GAP]

### 3.4 ORB / Pre-ORB (SuperTrend box)

**Pre-trade:** high-volume days with an expected explosive open (after data or earnings). Skip high-impact news days, holidays, choppy low-volume days. [SOLID]

**Entry**
1. Draw a box around the pre-market range. Duration: 30 minutes (6 sessions), 15 minutes (5), 5 minutes (2); NotebookLM also lists 2M and a 2-candle confirmation. [VARIANT]
2. A candle closes outside the box: above = buy, below = sell. No retest needed. [SOLID]
3. Stop on the SuperTrend line (factor 1.6) or just beyond the opposite box edge. [SOLID]
4. If the breakout candle closes back inside the box, kill the trade. [SOLID]
5. Two-bullet rule: if trade 1 is stopped or killed, take trade 2 only on a breakout to the opposite side; maximum two trades; stop for the day if trade 2 fails. [SOLID]

**If the range is 100 pips or more:** a mentor says he trades the Intra-Range fade (3.10) instead of the breakout; **if it is under 100 pips** he waits for the breakout on the other side. [CONFIRMED, section 9c item 3] The 100-pip figure is a switch between two setups, not a simple cancel.

**No 200 EMA filter** is used on the ORB: "No 200 EMA, none like that. You wait for a breakout of that range, execute on the breakout, your stop on your SuperTrend, and your target is open because you trail your stop." [CONFIRMED, section 9f item 3]

**Kill rules** [CONFIRMED, section 9c item 4]: a candle closing back inside the range kills the trade; after the break you want volume, and if none appears he kills the trade quickly; the last trade is a break to the other side. "One bullet if you win, two bullets if your first one fails." The pre-market ORB is a separate, already automated strategy; the ORB itself is the opening-range breakout.

**Cancel:** price chopping inside the box. [SOLID]

**Exit:** trail behind the SuperTrend each candle close; winners ran 3R to 9R. Risk 1% per trade (0.5–1% per bullet). [SOLID]

**Suggested confluence:** the breakout agrees with 200 EMA direction and the daily bias; the box edge lines up with a pivot, previous daily high/low, or VWAP. [SUGGESTED]

**Gaps:** SuperTrend ATR period; wick or body for the box; the 100-pip cap on indices. [GAP]

### 3.5 Power Ranger (range breakout, then retest)

**Pre-trade:** avoid high-impact news and holidays; price not trapped inside the box; New York session context. [SOLID]

**Entry**
1. Mark the high and low of the first 15 minutes of the open. [CONFIRMED] The mentor says it is also run on the Asian open, not only New York.
2. On the 5M chart, wait for a candle to break out and close outside the range. [SOLID]
3. The next 5M candle retests the broken boundary and closes in the breakout direction. [SOLID]
4. Place a buy stop above the retest candle's high (sell stop below for shorts); NotebookLM: 2 pips past the retest rejection. [SOLID; offset ONE FILE]

**Kill:** closes back inside the range; a 5M candle invalidates the entry (cancel and re-arm at the range extreme); chop with no break. [SOLID]

**Stop:** fixed 40 pips. [CONFIRMED: mentor states a 40 pip stop and 120 pip target on a live trade, section 9 item 4.] Earlier summary figures (60, 70, 94, 150 points) were individual trades.

**Exit:** 120 pip target (1:3). [CONFIRMED] A mentor also mentions taking a Power Ranger at 1.5R on one day (discretionary). The summary "hold till the cows come home" is not supported.

**Suggested confluence:** same as ORB. [SUGGESTED]

**Red / Black Ranger variants:** rules unclear in all files. [GAP]

### 3.6 Cracker (Crack Attack / Sniper Cracker / KBO Cracker / Teemo Cracker)

**Instruments / timeframes:** built for US30; also taken on NAS and Gold in four sessions [VARIANT]. Executed on the 1M, with the 5M for trend alignment.

**Pre-trade:** high-momentum opens, especially the New York open (15:30 SAST). Skip choppy days, days before CPI/NFP, bank holidays, and any day price breaks the pre-market level before the open. [SOLID]

**Entry: versions kept**
- **A ("Teemo" / "Temu" Cracker): joke version, do not use.** One host reads out his own levels and says "if we close above there, sell" while admitting "I don't even know if my cracker is correct". The name is a pun on Temu (a knock-off). [BANTER, section 9e item 1]
- **B (call-based entry, the real Cracker)** [CONFIRMED, section 9e items 2–3]: before the open the strategy gives a **daily call** ("the cracker wants buys" or "wants sells") and **two price levels**. Mentors say "buys above there or buys above there, whichever gets tapped first", so both levels point the same way as the call. After the open, a 1M (or 5M) close through the first level tapped is the entry, in the call's direction. A statement that a close above the 200 EMA is a buy appears once, when the call was buys; whether the 200 EMA is one of the levels is not stated. [SUGGESTED, unverified]
- **Counter-call trades:** mentors sometimes trade against the call for fun ("in theory the cracker wanted buys, we took a sell") and it lost. This is banter, not a rule.
- **When the mentor downgrades or skips the call** [CONFIRMED, section 9e item 3]: Friday (pullbacks) and end of month; a buy call while price is holding under the Asia lows ("a brick wall"); a sell call while price sits under EQ, where you want to see a drive and a 5M close back under, and the trade is in trouble if price gets back above EQ. An A-grade setup is a **momentum break through the level**; otherwise expect chop.
- **Management seen:** 60 stop, then cutting to half risk if it is not running, break-even at 80%, and the 90-second rule. The move often tops near the 200 EMA about 2 minutes in.
- **C (wick):** price closes under the previous 1M candle's bottom wick, so go long. [ONE FILE]
- **D (barrier):** levels set before the open ("buys above here, sells below there"). If price breaks and closes past the level at the open, enter in that direction. [SOLID] [CONFIRMED: mentors post the day's two levels as exact prices (for example "buys above 43119") and the trade often finishes in 1–2 minutes. How the levels are calculated is never stated.]
- **Cracker Extended Edition:** the same entry, but the mentor breaks the 90-second rule and holds. Management only. [SOLID]

**Cancel:** no breakout in the first 5 minutes after the open; the trigger level was invalidated before the open. [SOLID]

**Stop:** fixed 60 pips / points. [CONFIRMED: "the cracker is always a 60".] NotebookLM also lists 20–30 points for a fast Cracker. [ONE FILE]

**Exit:** 1:1 (60) or 1:2 (120); or EQ, Asia low, or closing at 20/50/60. **90-second rule:** if the trade is not in profit within 90 seconds, exit at market. Break-even at 80% of the target. [CONFIRMED: "if you're not in profits after more than 90 seconds, you should be out"; it is clock time, not a candle close.]

**Risk:** 0.5–2% per trade, lot size computed on the 60-pip stop; maximum two trades a day. [SOLID]

**Suggested confluence:** 200 EMA direction on the 5M, bias from the daily flip, pre-market barrier near a pivot or Asia level. [SUGGESTED]

**Conflicts:** C1 (A vs B direction), C2 (instruments), C3 (90 seconds vs a prop firm's 10-minute minimum hold). See section 6.

### 3.7 OES, version A: opening 5-minute candle fade

**Transcript note (section 9 item 1):** OES is a members-only system and the mentor states it has "two entry criteria" without naming them. The criteria below come from the summary files, not from a mentor's explanation, so treat them as unverified. [VARIANT]

**Entry:** mark the high and low of the first 5M candle after the open. Whichever side breaks first, trade the opposite: break of the high, go short; break of the low, go long. [SOLID within this version; 4 sessions]

**Cancel:** the designated candle isn't broken within the session window; price re-enters and closes back inside; volume stalls and candles overlap. [SOLID]

**Stop:** 50 pips (6 sessions; 52–54 on Gold for spread), structural zone placement (5), 100–200 pips (3). [VARIANT]

**Exit:** 1:1 scalp, 1:2 standard, Daily R1/R2/S1/S2 or ADR, 100–200 pips for runners; break-even at 80% or 1:1. [SOLID]

**OES zones are pre-marked and some days have none:** mentors say "there's no five-minute OES zones for us today", and grade a setup that does not fit as not A+. [CONFIRMED, section 9f item 4]

**Verified OES variants** [CONFIRMED, section 9d item 2]: the mentors name a **5-minute OES** and a **4-hour OES** (also an "inverse 4-hour OES"). The 4-hour OES waits for a 4H candle to close (one stream says "it closes at 11, so we just want to wait for that 11"). A worked example gives a 50-pip stop, a first target of 1:2 (100 pips), then 200 pips, then the previous daily high as the full target. These two variants replace the unverified "three-box" idea as the codable OES forms.

### 3.8 OES, version B: 4H zone continuation

**Transcript hint (partial)** [section 9c item 5]: the OES/OBS 4-hour levels are marked before the session and alerts are set. One mentor describes the play as "break out above this, hold there, OBS, and look for continuation" (and the mirror below), and reports price tapping a 4-hour high OBS level "to the pip" then rejecting. This supports version B (4H break, hold, continuation) as the closest match; the exact criteria are still undisclosed.

**Pre-trade:** 4H structure has broken cleanly, or the London/NY open drives price into a key zone. Skip choppy days and holidays. [SOLID]

**Entry**
1. Establish the 4H bias and mark the 4H candle that broke structure (high, low, EQ) and the 4H zones.
2. Price tests the 4H zone or breaks out of the Asia range.
3. A 5M or 15M candle closes outside the range or bounces off the zone: bullish close above the level goes long, bearish below goes short. NotebookLM: full-body 5M close and 5M order-flow confirmation. [SOLID; 12+ sessions]

**Stop / exit:** as 3.7; NotebookLM: break-even at +50 pips.

**Suggested confluence:** zone aligns with Asia high/low, daily pivot, or previous daily high/low; 200 EMA direction. [SUGGESTED]

*Version C (three-box mechanical): in the transcripts the "three boxes" are the mentor's newer, fully mechanical strategy that replaced the Cracker as his main trade. It is not the same thing as OES, and its three boxes are never stated. Cannot be coded.* [GAP]

### 3.9 All-Time High breakout / retest

**Pre-trade:** hyper-bullish, high-volume regime. **Never short an all-time high.** Skip low-volume probes that wick straight back. [SOLID]

**Entry**
- **Breakout momentum:** a 1M or 5M candle closes above the all-time high (above the bodily high) and above Daily R3: go long. [ONE FILE]
- **Break and retest:** the all-time high breaks, price pulls back to retest it, and it holds as support: go long. [SOLID]
- **Rejection fade (opposite):** an ATH at weekly R1 with no volume is faded. [VARIANT: one file]

**Stop:** 30 pips on Gold; 30–40 points on indices; under the breakout structure. **Exit:** 50-pip scalp; runner 150–200 pips or Daily R4. [SOLID]

**Transcript confirmation** [CONFIRMED, section 9d item 4]: holding above the previous daily high is bullish; if price holds weekly R2 and the yearly pivot, it "runs those all-time highs again"; holding under Asia lows instead points bearish. Mentors are cautious at new highs ("is this the last push before we come back in the range?") and wait for a hold before committing.

### 3.10 Intra-Range (range fade)

**Pre-trade:** the opening range must be 100 pips or more; the mentor says "the rule on paper is if the range is 100 pips or more, we can trade intra range" (he has skipped a 97.5-pip range, and admits the number is arbitrary). [CONFIRMED, section 9c item 3]

**Entry:** a candle breaks out and closes back inside the range; the next candle tests and rejects the top; sell at the rejection (bottom is the mirror, implied). **Target:** the bottom of the range. **Stop, risk:** not stated. [ONE FILE; GAP]

### 3.11 Reversal family (sweep then reversal)

- **Session low reversal:** price takes the session low (a minor break of structure), then a bullish engulfing candle; enter on it. Stop not stated. [ONE FILE]
- **PDH / PDL sweep reversal:** price sweeps the previous daily high or low, fails to hold beyond it, and reverses: "See the sweep, there's your entry." The variants file adds a close back inside the previous day's range with CVD buyer/seller injection. [ONE FILE, vague]
- **ORB reversal at value area:** within 08:00–10:00 or 15:30–16:30, with a 15M opening range set, price sweeps an Asia/PDH/PDL/OR extreme at VAH/VAL, POC or 200 EMA; a 5M engulfing candle against the sweep closes back inside the value area with CVD absorption; enter at market. Stop at the wick extreme plus 2–5 pips; TP1 at POC (50%), TP2 at the opposite value-area edge. [ONE FILE]

Mentors describe previous daily high/low as "our fake out": if price gets back above the previous daily low after breaking it in Asia, "all of this was basically the fakeout", and it can then be used as a swing point. [CONFIRMED, section 9b item 10] These share the "sweep, fail, reverse" pattern with the Grabber. **Suggested confluence:** the swept level lines up with a pivot or 200 EMA; EQ/POC as the target. [SUGGESTED]

### 3.12 Pivot break-and-retest (conditional standalone: needs other confluence)

**Entry**
- **Bearish:** price breaks below Daily S1, pulls back and retests from below, S1 holds as resistance: short, target S2. If S2 breaks and holds, hold or re-enter for S3.
- **Bullish:** price breaks above Daily R1, retests from above, R1 holds as support: long, target R2, then R3 and R4. [SOLID]
- **Macro pivot bounce:** a test of a weekly pivot or monthly S1 with a clean reversal candle; enter toward the central pivot or the opposite level. [SOLID]

**Condition (your ruling):** do not trade this on the pivot alone. Require at least one other reason (200 EMA direction, daily flip bias, value-area or VWAP agreement, previous daily high/low).

**Transcript confirmation:** "breaks underneath the daily S1, retest, hold underneath daily S1, where are you going? Daily S2 is your target." [CONFIRMED, section 9b item 7]

**Avoid:** narrow, range-bound days around the central pivot. **Stop:** beyond the retested pivot or swing, 30–60 pips in examples. **Target:** the next pivot. [SOLID]

### 3.13 Value area fade / breakout (conditional standalone)

- **Mean reversion (ranging days):** price tests VAL, rejects, closes back inside: long toward POC then VAH. Mirror at VAH. [SOLID]
- **Breakout (trending days):** price breaks VAH or VAL, retests it, and it holds: enter toward the next volume node. [SOLID]
- **Trade away from POC:** after consolidating on the POC, price breaks out and structure shifts away. [SOLID]
- Never enter while price sits on the POC. [SOLID]

**Stop:** beyond the opposite value-area edge or swing. **Target:** POC first, then VAH/VAL or the next node. **Condition:** needs another reason, as the mentors stack this with 200 EMA, pivots and VWAP. [SUGGESTED]

### 3.14 VWAP (conditional standalone: evidence limited)

- **Mean reversion:** in a range, price stretched from VWAP prints a reversal candle; enter toward VWAP. [SOLID]
- **Break and retest:** price breaks decisively through current-day or London VWAP, retests from the other side and VWAP holds: enter toward the session high/low or the next pivot. [SOLID]
- **Stop:** 47–90 points on the DAX; beyond swing structure or the opening-range box. **Target:** VWAP, session high, previous daily high, or the opposite standard-deviation band; 1:1 common on DAX scalps. [ONE FILE for the numbers]

**Standalone verdict:** the transcripts do not show the rules, so use VWAP as confluence only. Note the mentors separate London VWAP from the current day's VWAP; one waits for the current day's VWAP to break before shorting. [CONFIRMED, section 9b item 1]

### 3.15 First pullback after a trend

After a strong trend, buy the first pullback that holds support (or sell the first pullback in a downtrend); enter on the hold or a candle close. The mentor wants to see "a little bit of a fail" with lows taken and structure changing. **Targets:** Daily R1/R2, session high, or VAH. **Stop:** not stated. [ONE FILE] The transcripts add a use of the Daily Flip: a first pullback into the daily flip, then a continuation in the trend direction. [CONFIRMED, section 9c item 7]

### 3.16 513

- **Version 1 (five-level scale-in):** bias from the daily candle. The five lines are the Daily Flip, POC, Asia high, Asia low and the ADR boundaries. If bearish, wait for price to trade up into the Asia high or POC, then sell on rejection or a close back below; if bullish, wait for a drop into the Asia low or POC, then buy on rejection or a close back above. Add positions 2 and 3 on further pullbacks, same lot size, maximum three. **Stop** beyond the ADR boundary from the first entry (50 pips Gold, 60 points US30, 100 pips Gold, 310 points = ADR × 1.25). **Target** 75% of ADR, or the opposite Asia extreme or POC. **Break-even** at 80% of the way or 1:1. Avoid inside days when both Asia extremes are taken. [VARIANT within its stop sizes; entry SOLID]
- **Version 2 (5/13 EMA cross):** a 5 EMA crossing the 13 EMA with pivot or Daily Flip and 200 EMA confluence; M5 entry; stop 40–60 pips or swing low; target 75% ADR. [ONE FILE, thin]

### 3.17 5M 200 EMA pullback ("50 is 50") (conditional standalone)

**Transcript note (section 9 item 6):** "50 is 50" means a stop of about 50 pips (52 for spread on Gold) and a take profit of 50 pips, so 1:1. "100 is 100" is the same idea at 100 pips. These are fixed-size Gold trades, not a trend-following rule set.

Price clearly above (buys) or below (sells) the 5M 200 EMA; it pulls back to test the 200 EMA, Daily Flip or POC; an M5 candle closes with a solid body away from it. **Stop** 50 pips (100 if ATR is above 4.0); **target** 50 pips or Daily R1/R2; fewer than two trades a day. [ONE FILE; the Playbook gives only a structural stop. VARIANT]

### 3.18 IFVG (Inverse Fair Value Gap)

Price sweeps a session high or low and displaces, leaving a fair value gap; price then closes through the gap, turning it into an IFVG; wait for a retest, then enter on the 2-minute chart at the tap. **Stop:** beyond the order block or IFVG candle extreme (12 or 50 points quoted). **Target:** 1:2, the opposite liquidity pool, or EQ. [ONE FILE; GAP: exact FVG and "violation" definition]

### 3.19 $5 Grids (Gold)

Mark $5 grid lines. When price approaches one and rejects and holds it as support, go long; as resistance, go short. **Stop** beyond the midpoint of the grid interval (max $2.50, about 25–35 pips). **Target** the next $5 line (50 pips); 1:1. [ONE FILE; fully mechanical; "rejection and hold" needs a definition]

### 3.20 Fibonacci quadrants scale-in

Four equal-size positions: market entry at 0%, then 25%, 50% and 75% of the move toward the stop; one stop at the 100% line closes all together. **Stop distances:** 250 points US30, 165 NAS, 50 Gold. **Target:** POC, Asia extreme, Daily Flip, or ADR boundary. [ONE FILE; GAP: how the structural stop is chosen]

### 3.21 Candlestick Types 2–5 / "10 is 10" scalps (one mentor's method)

- **Type 2:** structural breakout, shallow pullback that holds flat-body support or resistance, then enter on the rebreak of the micro high/low.
- **Type 3:** sweep of a key level then a decisive 15M or 30M engulfing close; enter on the close or on a stop order at the extreme.
- **Type 4:** a 30M candle closes beyond flat-body support/resistance; place a pending stop at its low (shorts) or high (longs).
- **Type 5:** a weak pause candle after an aggressive expansion into liquidity; stop order at its low (shorts); enter on the rebreak.
- **Stop:** GBPJPY 30 pips; Gold 55–60 (61 for spread); one session 30 on Gold. **Targets:** TP1 fixed 10 pips ("10 is 10"), TP2 20–48, TP3 30–89, TP4 110–125 or the daily extreme. [ONE FILE; VARIANT on the Gold stop; "flat body" needs a definition]

### 3.22 Trend line third touch / counter-trend line break

- **Third touch:** a trend line with two touches; price pulls back for the third touch; enter with the trend on a rejection candle.
- **Counter-trend line break:** during a pullback, draw a line across the swing highs and enter on a clean break back in the trend direction.
- **Stop:** past the third-touch swing. **Target:** previous swing, daily pivots, or extended Fibonacci levels. [ONE FILE; GAP: draw on bodies or wicks]

---

## 4. Quick reference: stops and targets by strategy/trigger

All values are as stated in the files, with the tag showing agreement. **These are reference values only. They will be replaced by values tuned in the backtest panel (section 12); do not hard-code them.** Use them as the starting point of the search.

| Strategy/trigger | Stop (as stated) | Target (as stated) | Break-even | Tag |
|---|---|---|---|---|
| Grabber | Beyond sweep swing; 30 / 50–60 pips | 1:1 partial, 1:2 / 1:3; opposite Asia extreme, S1/R1 | 1:1 or 80% | VARIANT |
| Asia fade | 30 / 50 / 100 pips; wick + 5–10 | EQ, opposite Asia extreme, pivot | EQ or 80% | VARIANT |
| Asia breakout | Outside structure; 30 / 50 / 100 | R1/R2, previous daily high, 75% ADR | 80% | VARIANT |
| ORB / Pre-ORB | SuperTrend 1.6 or beyond box | Trail, 3R–9R | Trail | SOLID |
| Power Ranger | Below retest; 40 or 60–150 pts | 1:3 (120 pips) | Not stated | VARIANT |
| Cracker | 60 pips (fixed) | 1:1 (60) or 1:2 (120) | 80% | SOLID |
| OES (fade, 4H zone) | 50 (52–54 Gold) / structural / 100–200 | 1:1, 1:2, R1/R2, ADR | 80%, 1:1, or +50 pips | VARIANT |
| ATH | 30 Gold; 30–40 pts indices | 50-pip scalp; runner 150–200 or R4 | Not stated | SOLID |
| Intra-Range | Not stated | Range bottom | Not stated | GAP |
| Pivot break-retest | Beyond pivot; 30–60 pips | Next pivot | Not stated | SOLID |
| Value area | Beyond opposite VA edge | POC, then VAH/VAL | Not stated | SOLID |
| VWAP | 47–90 pts (DAX) | VWAP / session high; 1:1 | Not stated | ONE FILE |
| 513 v1 | ADR-based (310 pts), 50 / 60 / 100 | 75% ADR | 80% or 1:1 | VARIANT |
| "50 is 50" | 50 pips (100 if ATR > 4.0) | 50 pips or R1/R2 | Not stated | ONE FILE |
| IFVG | Beyond OB / IFVG extreme (12 or 50 pts) | 1:2, opposite liquidity, EQ | Not stated | ONE FILE |
| $5 Grids | $2.50 max (25–35 pips) | Next $5 line (50 pips), 1:1 | Not stated | ONE FILE |
| Fibonacci scale-in | 100% line (250 US30 / 165 NAS / 50 Gold) | POC, Asia extreme, Flip, ADR | Not stated | ONE FILE |
| Candlestick Types | GBPJPY 30; Gold 55–60 | TP1 10 pips; up to 125 | Not stated | ONE FILE |

---

## 5. General rules

**Risk and sizing**
- Mentors advise **1% per trade** and a maximum of two trades per session ("if you decided you risk 1%, you stick with that"). The 2% figure is the prop-firm contract cap, not the mentors' recommendation (one mentor says there is no rule that lets you risk 2%). Cracker 0.5–2%; ORB 1%; one mentor 0.5%. [CONFIRMED for 1% as the stated default, section 9b item 6]
- Prop daily loss limit (firm-specific): it moves with equity and resets about 23:00 each night; one prop's only rules are the news rule and the maximum daily loss rule; "flex" accounts have no daily loss limit. [ONE SOURCE, section 9b item 6]
- Lot size is computed from the stop distance. Scale-in strategies use equal lots and total risk across all fills stays inside the limit. [SOLID]
- A 2–5 pip buffer on Gold stops for spread (52–55 pips instead of 50). [ONE FILE]
- ATR-based stop sizing exists as a rule in one file. [ONE FILE]

**Trade limits**
- Two trades a day; "two bullets a session". [SOLID]
- One instrument, one strategy, one session. [SOLID, one mentor's rules]
- "One trade only, no double dip." [ONE FILE; conflicts with the two-trade rule]

**Stops**
- Always use a stop loss; "no stop loss" is a rule violation; a wider stop is equivalent to no stop. [SOLID]

**News**
- Do not trade FOMC or NFP; no London trading on NFP day; sit out high-impact news. One mentor trades news "for fun". [SOLID with that exception]
- Do not trade indices in the London session. [SOLID]

**Prop-firm rules that can break a bot** [ONE FILE each]
- A six-minute news window on one prop (3 minutes either side); a mentor says you may enter 3 minutes after the event, and must close trades before the news or wait.
- Daily drawdown measured on equity at rollover; a daily cap of $2,500 on one firm; a 2.5% profit cap on one firm; a 10-minute minimum hold on one firm; one-sided betting is forbidden (FTMO); soft breaches for over-leverage.

**Sessions (SAST)**
- Asia 01:00–06:00 (most support, see conflict C5); London open 08:00–10:00; London Fix 11:30; NY open 15:30 and the 15:30–16:30 window. [SOLID for NY open; others as noted]

**Not coded:** psychology (emotionless execution, "don't marry a bias"), faith and fasting material, mentor banter, and results claims (such as a 95% hit rate) that are not verified.

---

## 6. Conflict register (nothing resolved; every version kept)

| # | Strategy | Versions | Support | Suggested backtest |
|---|---|---|---|---|
| C1 | Cracker | **RESOLVED**: direction is the day's Cracker call (buys or sells) plus two levels; the "Teemo" sell version is a joke | Transcripts, 9e | Take the call and levels as inputs; test filters from 3.6 |
| C2 | Cracker | US30-only vs also NAS and Gold | 1 report vs 4 sessions | Run on each instrument |
| C3 | Cracker | 90-second exit vs a prop firm's 10-minute minimum hold | One firm's rule | Check the firm's rules before running |
| C4 | Asia | Continuation vs sweep-and-fade | Summaries: 14 vs 10 sessions. **Transcripts: whichever Asia extreme breaks first tends to set the day's direction** | Test continuation first; fade as the fake-out exception |
| C5 | Asia hours | **RESOLVED**: 01:00–06:00 GMT+2, stated by a mentor | Transcripts | Use 01:00–06:00 |
| C6 | Grabber stop | 30 / 50–60 / wick + 5–10 / 30–35 (Kick) | 4 vs 3 sessions; others one file | Test 30, 50, wick+5–10 |
| C7 | Grabber BE | 1:1 vs 80% to target vs close above daily pivot | All three stated by mentors | Test each separately |
| C8 | OES | 5M fade vs 4H zone follow vs three-box | Transcripts: OES criteria are undisclosed; three-box is a different, newer strategy | Code A and B separately as unverified |
| C9 | OES stop | 50 (52–54) / structural / 100–200 | 6 / 5 / 3 sessions | Test all three |
| C10 | ORB range | 30 / 15 / 5 min (also 2M, 2-candle) | 6 / 5 / 2 sessions | Test 30M and 15M first |
| C11 | ORB vs Power Ranger | Enter on first close vs wait for retest | By design | Test both |
| C12 | 513 | Five-level scale-in vs 5/13 EMA cross | Playbook and Variants vs NotebookLM and 1ST_2GS | Code both separately |
| C13 | 513 stop | 50 / 100 / ADR × 1.25 | 3 / 2 / 4 sessions | ADR-based vs fixed |
| C14 | ADR stop | ADR × 1.25 vs wick × 1.5 | 8 vs 1 session | Use ADR × 1.25 first |
| C15 | 200 EMA | Never trade against it vs counter-trend scalps | Rule vs practice | Test with and without |
| C16 | 200 EMA source | OHLC4 vs Close | 1 session vs default | Test both |
| C17 | "50 is 50" | Fixed 50/50 vs structural stop | NotebookLM vs Playbook | Test fixed vs structural |
| C18 | Break-even | Always move vs "took away 20 wins" | One mentor each | Test with and without |
| C19 | General risk | **Mostly resolved**: mentors say 1%; 2% is a prop cap; 0.5% by one mentor | Transcripts | Use 1% as the default |
| C20 | News | Don't trade vs "trade for fun" | Personal choice | Block news by default |
| C21 | ATH | Breakout long vs fade a no-volume ATH at weekly R1 | Playbook/NotebookLM vs MERGED | Test separately |
| C22 | Gold stops | 30 vs 55–60 (61 for spread) | 1 vs 5 sessions | Test 30 and 60 |
| C23 | Targets | "10 is 10" scalps vs 1:2 / 3R | One mentor vs others | Test 10-pip TP separately |
| C24 | Power Ranger | **RESOLVED**: 40 pip stop / 120 pip target | Mentor on a live trade | Test 40/120 |
| C25 | Daily trades | Two trades a day vs one trade only | Two mentors | Test both |

*Intra-Range is its own setup (3.10), not a variant of Power Ranger. The 100-pip number is a minimum range size there and a maximum opening range in ORB.*

---

## 7. Gaps and what to search for in the full transcripts

Priority one (a strategy/trigger cannot be coded without these):

| Gap | Search terms to try in the 52M-character file |
|---|---|
| OES three boxes: what are they? | "three boxes", "boxes ticked", "tick the boxes", "OES" with "box", "one entry system" |
| Cracker direction at the 200 EMA | "Cracker" near "200", "above the 200", "below the 200", "crack attack", "fade" |
| Cracker pre-market barrier lines | "buys above", "sells below", "barrier", "trigger level", "pre-market level" |
| Asia hours | "Asia" near "midnight", "1 to 6", "1:00", "daylight savings", "Asia range" |
| EQ with several ranges | "EQ" near "which range", "50%", "equilibrium", "fib" |
| What "close" means | "body close", "wick close", "bodily", "close above", "close below" |
| Sweep depth | "sweep" near "pips", "how far", "too far", "deep sweep" |
| Grabber confirmation candle timeframe | "Grabber" near "confirm", "first candle", "5 minute", "15 minute" |
| Volume meaning | "volume" near "tick", "relative", "delta", "volume candle" |
| SuperTrend settings | "SuperTrend", "ATR", "period", "1.6", "factor" |
| Stops where "not stated" | "stop loss" near "Power Ranger", "intra range", "first pullback", "session low" |
| VWAP traded alone? | "VWAP" near "just", "only", "enter", "sell off VWAP" |
| Level alignment width | "pivot" near "Asia high", "confluence", "aligned", "stack", "same level" |
| Post-trade rules | "after a loss", "after a win", "revenge", "done for the day", "stop trading", "max loss" |
| Daily Flip as bias | "flip" near "bias", "body", "volume", "flipped" |

Priority two: exact clock times per setup; whether the 90-second rule is clock time or candle close; per-strategy vs per-day trade limits; definitions of "healthy pullback" and "holds"; Red/Black Ranger and Grabber Sell rules.

---

## 8. Alias map (names that mean the same strategy)

| Use this name | Also appears as |
|---|---|
| Grabber | A-Tier Grabber, Grabber Play, EQ Grabber, Vienna Grabber, Reverse Grabber, Grabber Kick, Grubber Kick, Prophetic EQ |
| Cracker | Crack Attack, Sniper Cracker, Cracker Extended, KBO Cracker, Kibonaki ("Teemo/Temu Cracker" is a joke name for a knock-off version), "70-Point Bang" (NotebookLM) |
| OES | OBS, OS, EES, "O yes", OES Special, One Entry System, OES Continuation, 4-Hour Play, 4-Hour Strat/Zones |
| Power Ranger | Ranger break and retest, 15-Minute ORB (NotebookLM) |
| ORB / Pre-ORB | Open Range, Opening Range, SuperTrend Box, TikTok Box, 5M/15M/30M ORB |
| Intra-Range | Intra-Range 100-Pip Range Trade |
| Daily Flip | Daily Open Level, Flip |
| VWAP | VWOP, London VWAP, anchored VWAP |
| 200 EMA rule | 200 EMA filter, "50 is 50", EMA Monster, Genesis Wave (strict moving averages) |
| ADR | Average Daily Range, ADR Strat, AVGLW, Two Standard Deviations Play, 75% ADR Model |
| 513 | 513 Method, 513A, Project 5130, "Five Lines, One Direction, Maximum Three Positions" |

*Source files: 1ST_2GS_STRATEGY_LIST, 2GS_STRATEGIES_FROM_TRANSCRIPTS, MERGED_STRATS_FROM_TRANSCRIPTS, Master_Playbook_All_Strats_Merged, NOTEBOOK_LM_STRATEGY_EXTRACTION, STTRATEGY_LIST.*


---

## 9. Transcript search findings (v1.1)

Source: merged_all.txt, 417 videos. Each reference below gives the YouTube video ID; many video titles repeat, so use the ID (youtube.com/watch?v=ID). Quotes are short and approximate because the transcripts are auto-generated.

### What the search settled

| # | Item | Result | Video IDs |
|---|---|---|---|
| 1 | **OES and the three boxes** | OES is a members-only system ("join Project G and you find out what OES stands for"). The mentor says it has **two entry criteria** and does not name them. The "three boxes" are a different thing: a newer, fully mechanical strategy where "if those boxes get ticked, I enter, stop loss is this side, TP is this size". The mentor says the Cracker "still works" but he moved to the new strategy for a higher win rate. Neither set of rules is disclosed. | ubBoI3uwsgU, Rn5j-kPGM28 |
| 2 | **Cracker direction** | "Cracker is looking for buys... if it closes above the 200, it is a buy." Stop is "always a 60". Entry is taken after a 1-minute or 5-minute close. The sell-side wording was not found; the "close above 200 = sell" version from the summaries is unverified. The mentor also says he will not break down his full entry criteria. | R3-0RI9XGyQ, 6KVsWnhqkvw, du7PRSNMnj8 |
| 3 | **Asia hours** | "The Asia range is from 1:00 GMT+2 to 6:00 GMT+2." | k9ZKoYqSDDE |
| 4 | **Power Ranger** | 15-minute open range; a candle breaks it and closes outside; the next candle retests, rejects and closes; sell stop just beneath; **40 pip stop, 120 pip target**. Also described as "5-minute break and retest of the 15-minute range". | 2Aat5Y4FFLQ, EKmnr4tIj-c |
| 5 | **Grabber** | Stop "normally 30", depends on volatility. Targets in order: Asia low, daily pivot, then EQ. | akZnuaHC4wc |
| 6 | **"50 is 50"** | A stop of about 50 pips (52 for spread on Gold) and a 50 pip target. "100 is 100" is the 100 pip version. | wj5NlP_vYnI, WUJHAa07nc0 |
| 7 | **Post-trade rules** | "One or two bullets a session" (20 bullets across 10 sessions). "If it's chopping, you call it a session." After a loss: "don't overtrade, don't get emotional, come back tomorrow." "If you caught all three trades today, you're done for the day." A Grabber taken earlier in the day can mean "done for the day". | XwDq3mirvLo, Kb4BrnJLuP4, r1aemHSyqXY, N_sNFecB4Hs, gMRfrtecjBc |
| 8 | **90-second rule** | Confirmed as clock time: "if you're not in profits by more than 90 seconds, you should be out". In another live trade the mentor manages by "90 seconds" and also says he kills the trade if a 5-minute candle closes above his zone. | _hHdgOIJyxk, 0DGIkF6VoDo |
| 9 | **ORB durations** | The mentors use 1-minute, 5-minute and 15-minute open ranges and a 15-minute pre-market range. One mentor says most trending strategies right now are some form of range break. So the duration is a choice, not a conflict. | irwpiARue4E, EKmnr4tIj-c |

### What the search did not find (still gaps)

- The two OES entry criteria and the three "boxes" (the mentors do not disclose them in the streams).
- Cracker sell-side rule and the exact pre-market barrier calculation.
- A numeric daily loss limit or a losing-streak rule.
- A single definition of EQ. It is used consistently as a hold-or-reject level, never defined in numbers.
- What "volume" means in "close with volume"; whether a "close" is body or wick.
- Whether VWAP is traded on its own.
- Stops for Intra-Range, first pullback and session low reversal.
- Whether the rest of the summary file's "SOLID" numbers match the raw transcripts. The search covered the main conflicts (items above), not every number.

### Searches not yet run

VWAP standalone, volume metric, "close" definition, Grabber confirmation timeframe, Intra-Range, first pullback, Asia breakout vs fade frequency, pivot-plus-Asia-high confluence wording, and the remaining stops marked "not stated". These can be done next.


---

## 9b. Second transcript search (v1.2)

Video IDs are YouTube IDs (youtube.com/watch?v=ID). Quotes are short and approximate because the transcripts are auto-generated.

| # | Question | Result | Video IDs |
|---|---|---|---|
| 1 | **VWAP standalone?** | Not stated. Used as a break level and first target; one mentor waits for the current day's VWAP (not London VWAP) to break before shorting. A members-only "VWAP trade out of the playbook" exists with no disclosed rules. Verdict: add-on. | twvuXSe7uaE, jsaUWmTLcyY, GLbwtqe6I28 |
| 2 | **Daily Flip meaning** | The daily open level. Price either drives from it or sellers keep it falling; a big level where a candle can go from bearish to bullish. | VTtfhczmZM4, s93dOz25mkQ |
| 3 | **What "close" means** | A body close ("bodily closure"). Rejections with wicks are acceptable; what matters is the body closing beyond a level. | TACSdQ_dukg, C_tCTw-vcnQ, E7ccLI2Bkiw |
| 4 | **What "volume" means** | Judged visually: "drive of volume", "volume candles showing direction". Overlapping candles with no volume means no trade. No numeric volume threshold exists. | 3OVrnsOLV7U, vLcmHQFz-LY, -E7eLYMxIrI |
| 5 | **Grabber rules** | Three rules: Asia high/low; a retest; a sweep that tests EQ and holds. Stop normally 30. Break-even: close above daily pivot, or 1:1 on a 30-pip Grabber, or 80% to target. | HUmsIZAL7gk, TACSdQ_dukg, ycrPQStkraU |
| 6 | **Risk and daily loss** | Default 1% per trade, two trades a session. 2% is the prop cap. Prop daily loss limit moves with equity and resets about 23:00; one prop's only key rules are news and max daily loss. | x_KGdDFsae8, U_bPsqm1-2Q, SFx5s8yZZZY, HwyRLLjCp9w, akZnuaHC4wc |
| 7 | **Pivot break-retest** | "Breaks under daily S1, retest, hold under S1, S2 is your target." Also R1 to R2 for buys. | QHVuC46fhYs, eGEmL1sfFzU |
| 8 | **Gaps** | A gap will close eventually, not on a schedule. Do not trade it as timed. | 6sOFJbCaQJg, HzlaI7GlqTQ |
| 9 | **How the mentors stack reasons** | Several levels sharing one zone (EQ + Asia low, gap + Asia low + EQ, monthly R1 + Asia low retest). See section 2.2. | 2qgig2NtukI, XwDq3mirvLo, oDtoql7AiIY, JkIG3ANqiGo |
| 10 | **Previous daily high/low as a fake-out** | A break of the previous daily low that gets reclaimed makes it "the fakeout", usable as a swing point; same on the high side. | RI0lDHJ0UTc, GnzSJNrPXr8 |
| 11 | **Cracker barrier** | Exact day levels are posted ("buys above 43119"); the method is not disclosed; trades often run 1–2 minutes. | y4c3fj75qAE, ryB4qRhRmsE |

### Remaining gaps after both searches

- The OES two entry criteria, the "three boxes", and the Cracker sell side and barrier calculation: not disclosed in the streams.
- Numeric daily loss limit for the mentors' own trading (only prop-firm limits found).
- Numeric EQ definition (usage is consistent, no formula).
- Stops for Intra-Range, first pullback and session low reversal.
- The members-only VWAP trade and the new mechanical "three boxes" strategy.


---

## 9c. Third transcript search (v1.3)

| # | Question | Result | Video IDs |
|---|---|---|---|
| 1 | **Asia direction rule** | "Whichever Asia high or low it takes first for the day after the Asia session, it tends to trade into that direction." Examples given for several weekdays. Fade entries are called a "normal 25 to 30 pip trade", waiting for a second candle to hold. | WUJHAa07nc0, tx3I58imzr4, rCFVedZGNKE |
| 2 | **EQ definition** | 50% of the previous day (fib from previous daily high to low); a session EQ is optional; built into their indicator. | 7ESmAfgtdpk, Y3NFGZEk7Vw, hbWENXlT4LM |
| 3 | **Intra-Range vs ORB** | Range 100 pips or more: trade intra range. Under 100: wait for the breakout on the other side. | TACSdQ_dukg, QS670yNwWNs |
| 4 | **ORB kill and bullets** | A candle closing back inside the range kills the trade; wait only for a break to the other side; volume needed after the break; one bullet if you win, two if the first fails. The pre-market ORB is a separate, already automated strategy. | 351_u2AbtS4, jdc165epdGM, VQu6vbQ_c7I |
| 5 | **OES / OBS hints** | 4H OBS levels are marked in advance with alerts; "break out above, hold, look for continuation"; price tapped a 4H OBS high "to the pip" and rejected. Criteria still undisclosed. | SwpM1-iCkIY, JkIG3ANqiGo, VoNsVmviE_0 |
| 6 | **ADR levels** | Act as support and resistance like pivots; holding the first ADR leads toward two standard deviations. | U_bPsqm1-2Q, v3VwFq9Ot5I |
| 7 | **First pullback and Daily Flip** | "First pullback into that daily flip, then continue higher." | EZ7g-5raVQk, Q2LFoThBcW0 |
| 8 | **SuperTrend** | "I use the SuperTrend, which is basically the ATR"; aims for 1:1 depending on volatility; flip from bear to bull used as a signal. Period not given. | NoOg6TJa5Gg, -nE6jJV5N4s |

---

## 10. How often things come up (all 417 videos)

Counts are mentions and the number of videos that mention each. Chat banter inflates some counts (the Cracker in particular), so use them for ranking, not as a win rate.

**Strategies and levels (mentions / videos)**

| Item | Mentions | Videos |
|---|---|---|
| Asia high / low | 5,491 | 339 |
| Pivots | 2,874 | 295 |
| Point of control | 2,225 | 210 |
| EQ | 1,822 | 264 |
| Daily Flip | 1,519 | 164 |
| Cracker | 1,310 | 96 |
| Fake out | 1,110 | 247 |
| VWAP | 968 | 113 |
| 200 EMA | 935 | 178 |
| ADR | 755 | 131 |
| Grabber | 618 | 111 |
| ORB / open range | 444 | 76 |
| OES / OBS | 342 | 70 |
| 2 standard deviations | 174 | 65 |
| 513 | 170 | 32 |
| Break and retest | 110 | 51 |
| Power Ranger | 68 | 15 |
| All-time high play | 48 | 16 |
| Intra-range | 8 | 4 |

**Reading this:** the backbone is Asia high/low, pivots, POC, EQ, the Daily Flip and fake-outs. Grabber, Cracker, ORB and OES are the main named strategies/triggers. Power Ranger, the all-time high play, 513 and Intra-Range are niche, so build and backtest them last.

**Instruments (mentions / videos)**

| Instrument | Mentions | Videos |
|---|---|---|
| Gold | 20,766 | 391 |
| NAS / Nasdaq | 7,764 | 377 |
| US30 / Dow | 6,617 | 341 |
| USD / dollar index | 2,596 | 293 |
| DAX | 2,280 | 204 |
| Bitcoin | 1,054 | 171 |
| Oil | 740 | 101 |
| Silver | 218 | 59 |
| S&P / SPX | 120 | 44 |

**Stop and target numbers stated next to each strategy (count of times / videos)**

| Strategy | Stops stated | Targets stated |
|---|---|---|
| Grabber | 30 (6 / 4 videos); 100 (1 / 1) | none stated |
| Cracker | 60 (6 / 2) | 120 (2 / 1); 20 (2 / 1) |
| Power Ranger | 40 (1 / 1); 50 (1 / 1) | 120 (1 / 1); 40 (1 / 1) |
| ORB / open range | 80 (4 / 2); 40 (1 / 1) | 18 (2 / 1) |
| OES / OBS | 50 (3 / 1) | 150 (2 / 1); 100 (2 / 1) |
| ADR | 100 (4 / 2); 115 (2 / 1); 250 (2 / 1) | 150 (1 / 1) |
| Asia plays | 100 (8 / 4); 50 (5 / 4); 30 (2 / 1) | 60 (2 / 1); 50 (2 / 1) |
| Pivot S1 / R1 | 100 (3 / 2); 30 (2 / 1); 50 (1 / 1) | 60 (2 / 1); 300 (1 / 1) |
| All-time high | 40 (2 / 1) | 360 (2 / 1); 40 (1 / 1) |

The counts are small because the mentors rarely say a number close to a strategy name. They support the main figures: Grabber 30, Cracker 60, Power Ranger 40 and 120, OES 50. For Asia plays both 100 and 50 are common (Gold at 100, indices and short plays at 50), so test both.

### Remaining gaps after three rounds

- OES's two entry criteria and the new "three boxes" strategy: not disclosed.
- Cracker sell side and barrier calculation: not disclosed.
- Numeric daily loss limit for the mentors' own trading.
- SuperTrend period; pivot type (standard, Fibonacci, Camarilla).
- Stops for first pullback and session low reversal.
- Targets for the Grabber in numbers (the transcripts give levels, not pips).


---

## 9d. Fourth transcript search (v1.4)

| # | Question | Result | Video IDs |
|---|---|---|---|
| 1 | **Cracker direction (see 9e: the Teemo version is a joke)** | One mentor reads the day's two Cracker levels and says "if we close above there, sell" and "the cracker is looking for sells" (the Teemo Cracker, a collaboration). He says another mentor has "quite a few iterations" and may call it a buy. Separately, another stream says closing above the 200 is a buy. Both directions are real; the day's call and levels set it. | WxDHullMFkw, R3-0RI9XGyQ, LRoN5HuCdjU |
| 2 | **OES variants** | 5-minute OES and 4-hour OES (and an "inverse 4H OES"). 4H OES waits for the 4H candle close. Example: 50-pip stop, 1:2 = 100 pips, then 200 pips, full TP at the previous daily high. | P4VZ-2UjfTs, sDJJwO5sPX4, 6bBwe2Pf09k, OH_OwsPi5Xg |
| 3 | **Grabber targets** | Long Grabber targets Asia highs; sells under EQ target Daily S1 then the previous daily low. | N_sNFecB4Hs, VEuMZDgX7ww |
| 4 | **All-time high** | Hold above the previous daily high is bullish; hold above weekly R2 and the yearly pivot sends price back to the highs; hold under Asia lows is bearish. | 5SHm-_myVPw, uPd2d8bS5WI, 7ESmAfgtdpk |
| 5 | **ORB win rate** | One mentor says the ORB's win rate is only about 48% because winners run 7R to 9R; losers are cut short. | VQu6vbQ_c7I |
| 6 | **Other named strategies** | "Big Shack strat" (not the OES; no rules), the Sentinel, the "Naz players". | CENqPRR1DCw, NoOg6TJa5Gg |

### Remaining gaps

- The two OES entry criteria (the stated rules for the 5M and 4H OES), and the three boxes of the new mechanical strategy.
- How the Cracker levels are calculated, and which version of the Cracker is the mentor's current one.
- A numeric daily loss limit for the mentors' own trading.
- SuperTrend period and pivot type.
- Stops for first pullback and session low reversal.


---

## 9e. Fifth transcript search (v1.5): Cracker corrected

| # | Question | Result | Video IDs |
|---|---|---|---|
| 1 | **"Teemo Cracker"** | A Temu joke: a knock-off Cracker run by another host who says he is not sure his version is right. Also a "ChatGPT improved crack" gag. Do not treat his "close above, sell" as a rule. | WxDHullMFkw, AOPA_Msoy_Q |
| 2 | **The real Cracker** | The lead mentor announces daily "the cracker is looking for buys" or "wants shorts" and posts "your two cracker levels". "Buys above there or buys above there, whichever gets tapped first." Direction follows the call. | R3-0RI9XGyQ, 6KVsWnhqkvw, _IwRV5PoOEQ, AOPA_Msoy_Q, E7ccLI2Bkiw |
| 3 | **Filters on the call** | Not happy buying under Asia lows; Friday and end of month mean pullbacks; sell calls are shaky under EQ unless there is a drive and a 5M close back under; A-grade = momentum break; closed at half risk when not running. | _IwRV5PoOEQ, 39F4U1KklI4 |
| 4 | **Counter-call trade** | A mentor took a sell against a buy call "just cuz I felt like it" and got hit. Banter, not a rule. | E7ccLI2Bkiw |
| 5 | **Cracker vs Grabber** | The Grabber had been "playing nicely the last few weeks" while the Cracker was "battling", a hint that the Cracker is less reliable at times. | 39F4U1KklI4 |

### Remaining gaps

- How the Cracker's two levels are calculated (never disclosed) and whether the 200 EMA is one of them.
- The 5-minute and 4-hour OES entry criteria, and the "three boxes" of the new mechanical strategy.
- A numeric daily loss limit for the mentors' own trading.
- SuperTrend period and pivot type.
- Stops for first pullback and session low reversal.


---

## 9f. Sixth transcript search (v1.6)

| # | Question | Result | Video IDs |
|---|---|---|---|
| 1 | **"Boxes ticked" grading** | A+ = all three boxes; two out of three is weaker; one box means wait. Box examples: back inside the opening range, rejection, bounce off London VWAP, candle closure, holding monthly R2. Boxes themselves are not defined. | WUJHAa07nc0, ubBoI3uwsgU, FdT420k_IZA, omokY9-DOeI, zaXEZLYpYAo |
| 2 | **SuperTrend** | A flat SuperTrend means low probability (range trading). 4H play: wait for the candle close, stop at the bullish SuperTrend. Period not stated. | 351_u2AbtS4, JJGnIdIM94A |
| 3 | **ORB filters** | No 200 EMA used; breakout of the range, stop on the SuperTrend, open target, trail the stop. | VQu6vbQ_c7I |
| 4 | **OES zones** | Marked in advance; some days have none ("no five-minute OES zones for us"); a trade outside them is not A+. | 5lui6kicAVc, P4VZ-2UjfTs |
| 5 | **Asia low by body** | One mentor uses bodies, not the massive wick, as the Asia low and the previous daily low. | TE1nUyyOl60 |
| 6 | **Pivot type** | Pivots are used as daily, weekly, monthly and yearly levels; no mention of Fibonacci or Camarilla types found. | pD9FBEbaTx4, 1hpOP9glNUo |

### Remaining gaps

- The contents of the three boxes and the two OES entry criteria.
- How the Cracker's two levels are calculated.
- A numeric daily loss limit for the mentors' own trading.
- SuperTrend period; pivot calculation type.
- Stops for first pullback and session low reversal.


---

## 9g. Seventh transcript search (v1.7)

| # | Question | Result | Video IDs |
|---|---|---|---|
| 1 | **What a "box" is** | Often a level: "back above 9800 was the first box we needed to tick". A trade with only one box ticked is called aggressive. | Ospdsixmg3Y, XNGCs9vEcG8, FdT420k_IZA |
| 2 | **Friday** | "Friday pullback" is a standing expectation (67 videos). Entire London session chop on one Friday. | MndXNPos8Hw, _KJgWDfLrgE, HwyRLLjCp9w, Hct3c3pkFTs |
| 3 | **Gold in London** | "Gold during London is a no-go for me"; it started moving at the COMEX open. One mentor. | CebP_UW2mdk, Hct3c3pkFTs |
| 4 | **Month end** | "Month end flows" is a reason for caution; one Monday was skipped for it. | KwvUBdZ5_TU, YICsNUbhad8 |
| 5 | **Prop news window** | Six-minute window; entry allowed 3 minutes after the event; close trades before news. | X375KIbYW98, w9V2-2vaFS4 |
| 6 | **Mondays** | One mentor's journal showed Mondays as no-trade days for him. A pattern, not a rule. | 5SHm-_myVPw |

### Remaining gaps

- The contents of the three boxes and the two OES entry criteria.
- How the Cracker's two levels are calculated.
- A numeric daily loss limit for the mentors' own trading.
- SuperTrend period; pivot calculation type.
- Stops for first pullback and session low reversal.


---

## 11. Operational definitions (words with no numbers in the transcripts)

The mentors say hold, rejection, momentum break and volume by eye. The bot needs numbers. Everything below is a **proposal to build and tune** [SUGGESTED]; the values are candidates to test, not final settings. Wherever a definition says "average candle size", use the one defined first.

### 11.1 Average candle size (the yardstick)

| Item | Definition | Parameters to tune |
|---|---|---|
| **ACS (average candle size)** | Average of (high minus low) of the last N candles on the timeframe the entry uses (5M for a 5M entry, 1M for the Cracker, 15M for the opening range, and so on). A true-range version (ATR) can be tested as an alternative. | N: 10, 20, 50 |
| **ACS by time of day** | The same average, but only over candles from the same time slot on previous days (for example, the 15:30 to 15:35 candle compared with that slot's average over the last 20 days). This stops the open candle from always looking "huge" next to quiet-hour candles. | Days: 10, 20, 30 |
| **Average body size** | Average of the absolute (close minus open) over the same N candles. | Same N |
| **ADR** | 20-day average daily range, already used by the mentors (stops, targets, "price already used its ADR"). | 10, 20 days |

All other definitions are expressed in multiples of ACS, so they adapt to the instrument and the volatility of the day without hard-coded pips.

### 11.2 Volume (deduced from candle size)

Your approach: volume is "there" when candles are large relative to their usual size. Tick volume can be tested as a second version if the data has it.

| Term | Proposed definition | Parameters to tune |
|---|---|---|
| **Volume present on a candle** | Candle range is at least kv times ACS, and the body is at least a fraction b of the range. | kv: 1.2, 1.5, 2.0; b: 0.5, 0.6, 0.7 |
| **Drive of volume** (the mentors' phrase for a strong break) | At least m consecutive candles in the same direction, each with volume present. | m: 1, 2, 3 |
| **No volume / chop** (a reason to skip) | The last m candles each have a range below kc times ACS and overlap each other by more than a fraction o. | m: 5, 8; kc: 0.7, 0.8; o: 0.5 |
| **Relative tick volume** (optional second test) | Candle tick volume divided by the average tick volume of the same time slot. | Threshold: 1.3, 1.5, 2.0 |

Used by: ORB and Power Ranger breakouts, Asia breakout "with volume", all-time-high breaks, Cracker "momentum" call, OES, and the "no volume, kill the trade quickly" rule.

### 11.3 Hold (price holds a level)

A level L (pivot, Asia high, EQ, POC, Daily Flip, previous daily high and so on). For a long, after price has broken above L:

| Term | Proposed definition | Parameters to tune |
|---|---|---|
| **Break** | A candle closes (body close) beyond L by at least d. | d: 0.0, 0.1, 0.25 ACS |
| **Hold above L** | After the break, price retests L and no candle closes below L for m consecutive candles on the confirmation timeframe. The wick may go below L by at most w. | m: 1, 2, 3; w: 0.1, 0.25, 0.5 ACS |
| **Hold fails** | A candle closes back below L by at least d. | same d |

For shorts, mirror this. The mentors' "bodily closure" rule supports a body close; a wick-tolerant version (w above) is the alternative to test against a strict "wick must not cross" version (w = 0).

### 11.4 Rejection

For a long at support L (mirror for shorts):

| Term | Proposed definition | Parameters to tune |
|---|---|---|
| **Touch** | Price comes within t of L (or crosses it). | t: 0.1, 0.25, 0.5 ACS |
| **Wick rejection** | The candle's wick beyond or at L is at least r of its total range, and the candle closes back on the original side of L. | r: 0.4, 0.5, 0.6 |
| **Close-back rejection** (sweep and reclaim, as in the Grabber and fake-out) | Price trades beyond L by between s_min and s_max, then a candle closes back inside within n candles. | s_min: 0.1 ACS; s_max: 1.0, 2.0 ACS; n: 1, 2, 3 |
| **Confirmation** | The next candle closes in the trade direction (the mentors' "second candle holds"). Test with and without. | on / off |

### 11.5 Momentum break

| Term | Proposed definition | Parameters to tune |
|---|---|---|
| **Momentum break of L** | The breaking candle closes beyond L by at least d, its range is at least km times ACS, its body is at least b of its range, and it closes in the outer fraction q of its range (close near the high for a long). | km: 1.3, 1.5, 2.0; b: 0.6; q: 0.25 |
| **A-grade version** (the mentors call the Cracker momentum break A-grade) | Momentum break plus no overlap in the previous m candles (not choppy). | m: 3, 5 |

### 11.6 Other terms that need numbers

| Term | Proposed definition | Parameters to tune |
|---|---|---|
| **Sweep** | Price exceeds the level by at least s_min and at most s_max (11.4). The depth is a stated gap in the Grabber and Asia fades. | as 11.4 |
| **Aligned levels / tight zone** (the Asia high near the daily pivot) | Two or more levels within z of each other. | z: 0.5, 1.0 ACS (5M) or 0.05, 0.1 ADR |
| **Chop** | SuperTrend flat for m candles, or the overlap test in 11.2. | m: 5, 8 |
| **Close** | Body close (confirmed from the transcripts). | fixed |
| **EQ** | 50% of the previous day's high-low range. | fixed (with session EQ as a test) |
| **Asia high / low** | Wick high and low from 01:00 to 06:00 SAST; body version as a test (one mentor). | wick / body |
| **First pullback, healthy pullback** | Not stated numerically. Candidate: a pullback of 30% to 60% of the last impulse leg, with no close beyond the level that started the move. | depth: 0.3 to 0.6 |

---

## 12. Stops and targets are tunable parameters (calibration design)

**Rule for the bot:** no stop-loss or take-profit number in this file is hard-coded. Each strategy exposes SL and TP as parameters, and the backtest panel finds what fits best.

### 12.1 Three ways to express SL and TP (test all three)

| Mode | How it is set | Example |
|---|---|---|
| **Volatility-scaled (main idea)** | SL = a times ACS; TP = b times ACS, measured at entry on the strategy's timeframe. | If the average candle is 10 pips, a = 2 and b = 2 give SL 20 and TP 20 (1:1); b = 4 gives TP 40 (1:2). |
| **Fixed** | Pips or points as the mentors stated (reference values from section 4). | Grabber 30, Cracker 60, Power Ranger 40 / 120. |
| **Structural** | Beyond the swing, sweep or zone extreme, plus a buffer (in ACS). TP at the next level (pivot, EQ, Asia extreme, POC, previous daily high/low). | Stop beyond the sweep wick plus 0.25 ACS. |

ADR-based versions (stop = ADR times 1.25, TP = 75% of ADR) are a fourth option from the 513 and ADR material.

### 12.2 What the backtest panel should show

For each strategy, instrument and session, over your two years of data:
1. A **grid of results** across SL multiples (for example a = 1, 1.5, 2, 3, 4) and TP multiples (b = 1, 1.5, 2, 3, 4, 6) with expectancy per trade, win rate, profit factor, average R, maximum drawdown and number of trades. A heat map is the easiest way to read it.
2. A comparison of the three modes (volatility-scaled, fixed, structural) side by side.
3. A **relationship view**: for each day or each trade, the best-fitting SL and TP plotted against the ACS at the time. If the best TP rises with ACS in a straight line, a single multiple (b) is a good rule. If it does not, volatility scaling is not helping for that strategy and the fixed or structural mode wins.
4. The same grid by **ACS length (N)**, by **time-of-day ACS** on and off, and by session (London, New York, Asia).
5. A **stability check**: prefer a broad plateau of good cells over the single best cell, and show results on a held-out period (for example, tune on the first 15 months and test on the last 9) so the tuned numbers are not just fitted to the same data. The size of the held-out split is yours to choose.

### 12.3 Other parameters to expose

Break-even rule (1:1, 80% of the way, or after a close beyond a level), partial-profit levels, the 90-second Cracker exit (seconds), trade limits per day, and every threshold in section 11. Each one is a test variable, not a rule.

### 12.4 Process suggestion

Tune the **definitions in section 11 first** (what counts as a hold, rejection, momentum break), then the **SL and TP multiples** for each strategy, then the **confluence count** (how many boxes or reasons are enough). Changing everything at once makes the results hard to read.
