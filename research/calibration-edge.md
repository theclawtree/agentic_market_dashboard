# Calibration Edge in Prediction Markets

## 1. What Calibration Means

**Calibration** is the correspondence between your stated probabilities and actual outcomes. If you say "70%" to 100 different events, and ~70 of them happen, you're well-calibrated. A **calibration edge** means your probability estimates are systematically closer to reality than the market's.

This is distinct from:
- **Discrimination/resolution**: ability to separate events that happen from those that don't (sharpness)
- **Information edge**: knowing something the market doesn't
- **Speed edge**: reacting to news faster

A calibration edge is quieter — you don't need secret info, you just need to be *less wrong* about base rates, update more rationally, and avoid the systematic biases that plague crowds.

### Why Markets Are Calibrated But Not Perfectly

Prediction markets aggregate information effectively (Hayek's insight), but they're populated by humans with systematic biases, limited liquidity, and structural constraints. The efficient market hypothesis applies loosely — markets are *approximately* calibrated but leave exploitable gaps, especially:

- In thin/illiquid markets
- At extreme probabilities (tails)
- During high-emotion events
- In novel event categories with no historical precedent
- When structural incentives distort participation (e.g., entertainment bettors on sports)

---

## 2. Superforecasting Techniques

Drawing heavily from Philip Tetlock's *Superforecasting* (2015) and the Good Judgment Project:

### 2.1 Reference Class Forecasting

Instead of asking "will X happen?", ask "how often do events like X happen?"

- **Identify the reference class**: What category does this event belong to? (e.g., "incumbent presidents seeking re-election," "Fed rate decisions after 3 consecutive hikes," "Series leads in NBA playoffs")
- **Find the base rate**: What percentage of events in this class had the outcome in question?
- **Adjust from the base rate**: Use case-specific evidence to nudge up or down

**Example**: "Will Country X's leader survive a no-confidence vote?"
→ Reference class: no-confidence votes in parliamentary democracies since 1990
→ Base rate: leaders survive ~65% of the time
→ Adjust for: size of governing coalition, economic conditions, leader approval rating

### 2.2 Base Rate Neglect (and How to Fix It)

Humans chronically underweight base rates in favor of narrative/anecdotal evidence. Superforecasters anchor on base rates first, then adjust.

**Kahneman & Tversky's inside/outside view:**
- Inside view: build a story about this specific case → overconfident, narrative-driven
- Outside view: how often does this type of thing happen? → better calibrated

### 2.3 Bayesian Updating

Start with a prior (ideally the base rate), then update incrementally as new evidence arrives.

```
P(H|E) = P(E|H) × P(H) / P(E)
```

Practical rules:
- **Update often, update small**: Don't anchor and refuse to move, but don't overreact to single data points
- **Consider the diagnosticity of evidence**: How much more likely is this evidence under H vs. not-H?
- **Beware double-counting**: If evidence is already priced into the market, it shouldn't move your estimate further

### 2.4 Granularity and Precision

Superforecasters use more granular probabilities (e.g., 72% instead of "about 70%"). This forces more careful thinking. Tetlock found that forecasters who used finer-grained probabilities performed measurably better.

### 2.5 The Fermi Estimation Approach

Break complex questions into components you can estimate:
- "Will Company X hit earnings?" → What's GDP growth? × sector multiplier × company-specific factors × analyst track record
- Multiply independent probabilities; use ranges and triangulate

### 2.6 Key Superforecaster Traits (from GJP Data)

- **Active open-mindedness**: Willingness to update beliefs
- **Granularity**: Fine-grained probability estimates
- **Dragonfly eye**: Aggregating many perspectives
- **Growth mindset**: Treating forecasting as a skill to improve
- **Probabilistic thinking**: Comfort with uncertainty
- **Distinguishing signal from noise**: Not overreacting to headlines

---

## 3. Building Calibrated Models by Domain

### 3.1 Elections

**Data sources**: Polls, fundamentals models, prediction markets, expert ratings

**Key base rates & patterns:**
- Incumbent advantage: US presidential incumbents win ~67% of the time historically
- "Time for change" model (Abramowitz): GDP growth + approval rating + incumbency fatigue explains ~80% of variance
- Polling averages converge: final polling averages have ~2-3% average error in US presidential races
- State-level correlations matter: if a candidate overperforms in PA, they likely overperform in MI/WI

**Common miscalibrations:**
- Markets overreact to individual polls (especially partisan ones)
- Narrative bias: "momentum" gets overweighted vs. structural factors
- Availability bias: recent elections dominate mental models
- Markets often underweight the probability of the "boring" outcome

**Model approach:**
1. Start with fundamentals model (economy + approval)
2. Blend with polling averages (weight increases closer to election)
3. Apply state correlation structures
4. Monte Carlo simulation for probability distributions
5. Compare to market → trade the gap

### 3.2 Economics (Fed decisions, GDP, inflation)

**Key patterns:**
- Fed funds futures are well-calibrated for near-term meetings but poorly calibrated 6+ months out
- Consensus economic forecasts have known biases: they're slow to forecast recessions and overshoot during recoveries
- Leading indicators (yield curve, PMI, unemployment claims) have well-documented predictive power

**Model approach:**
1. Base rate: what has the Fed done historically given similar macro conditions?
2. Fed communication analysis: parse dot plots, minutes, speeches (systematic, not cherry-picked)
3. Market-implied probabilities from futures vs. your model
4. Look for gaps where the market is extrapolating the current trend too far

**Known biases:**
- Herding in economic forecasts (economists cluster around consensus)
- Recency bias: markets overweight the last data point
- Status quo bias: markets underestimate the probability of regime changes

### 3.3 Sports

**Most developed prediction market domain.** Oddsmakers are very good, but exploitable edges exist:

**Known biases:**
- **Favorite-longshot bias**: Longshots are overbet relative to true probability (bettors overpay for the thrill of big payoffs). Favorites are slightly underbet. This is one of the most robust findings in betting market research.
- **Home field bias**: Markets sometimes over- or under-adjust for home advantage depending on sport/era
- **Recency bias**: Recent performance (last 3-5 games) gets overweighted vs. season-long metrics
- **Star player effect**: Markets overreact to star player absences in some contexts, underreact in others
- **Public money effect**: Lines move toward popular teams on high-profile games

**Model approach:**
1. Build a statistical model (e.g., Elo, regression-based, or Bayesian)
2. Calibrate on historical data with out-of-sample testing
3. Compare model probabilities to market-implied probabilities (from odds)
4. Bet only when edge exceeds the vig/commission (typically need >2-3% edge)

### 3.4 Crypto / Token Prices

**Hardest domain to calibrate.** Markets are:
- Highly reflexive (prices affect sentiment which affects prices)
- Driven by narrative cycles
- Subject to manipulation and insider activity
- Lacking stable base rates (novel asset class)

**Possible approaches:**
- On-chain metrics (active addresses, exchange flows) as leading indicators
- Cycle analysis: BTC halving cycles have shown some regularity (diminishing)
- Correlation structures: crypto markets are highly correlated in downturns
- Sentiment extremes: fear/greed indices at extremes have some mean-reversion signal

**Honest assessment:** Calibration edges in crypto are fragile, regime-dependent, and likely ephemeral. Focus on structural/mechanical edges (e.g., funding rates, basis trades) rather than directional calibration.

---

## 4. Metaculus & Good Judgment Project: Data and Lessons

### 4.1 Good Judgment Project (GJP)

Funded by IARPA's ACE tournament (2011-2015). Key findings:

- **Superforecasters beat intelligence analysts with classified data** by ~30% (Brier score)
- **Top 2%** of forecasters were designated "superforecasters" and maintained edge over time
- **Teaming helps**: Superforecasters in teams outperformed solo superforecasters
- **Training helps modestly**: A 1-hour training on biases improved forecasts by ~10%
- **Updating frequency correlates with accuracy**: Best forecasters updated more often
- **Extremizing helps for aggregation**: If the crowd says 70%, a good algorithm pushes toward 75-80% (because the average of informed opinions underweights shared information)

### 4.2 Metaculus

Community forecasting platform with rich calibration data:

- **Community is reasonably well-calibrated** in aggregate — the Metaculus community prediction tracks the calibration curve fairly well
- **Individual calibration varies enormously** — top forecasters are much sharper than the median
- **Metaculus community tends to be slightly overconfident** at high probabilities (says 95% when reality is ~90%)
- **Long-range forecasts are worse** (obviously) but the community still adds value over naive priors
- **Domain matters**: Metaculus is best on science/tech/geopolitics, weaker on short-term market movements

### 4.3 Key Lessons for Prediction Market Trading

1. **The crowd is a strong baseline** — beating it consistently requires disciplined methodology
2. **Small edges compound** — even 1-2% better calibration, applied consistently, generates significant returns
3. **Diversification across many bets** is essential — any single prediction is noisy
4. **Track your record religiously** — you cannot improve what you don't measure
5. **The best forecasters are perpetual updaters**, not people who "call it" and move on

---

## 5. Statistical Methods for Evaluating Calibration

### 5.1 Brier Score

The most common proper scoring rule for binary outcomes:

```
Brier Score = (1/N) × Σ(forecast_i - outcome_i)²
```

Where forecast is your probability (0-1) and outcome is 0 or 1.

- **Range**: 0 (perfect) to 1 (maximally wrong)
- **Baseline**: Always predicting the base rate gives Brier = p(1-p), e.g., 0.25 for 50/50 events
- **Climatology**: Always predicting the historical base rate
- **Brier Skill Score**: (Brier_climatology - Brier_forecast) / Brier_climatology — measures improvement over always guessing the base rate

**Brier Score Decomposition** (Murphy 1973):

```
Brier = Reliability - Resolution + Uncertainty
```

- **Reliability** (calibration component): How close are your stated probabilities to actual frequencies? Lower = better calibrated.
- **Resolution**: How much do your forecasts vary by outcome? Higher = better discrimination.
- **Uncertainty**: Base rate entropy. Not under forecaster's control.

This decomposition is key — it separates calibration from discrimination. You can be well-calibrated but uninformative (always say 50%), or poorly calibrated but still useful (consistently say 80% when truth is 90% — miscalibrated but discriminating).

### 5.2 Log Score (Logarithmic Scoring Rule)

```
Log Score = (1/N) × Σ[outcome_i × log(forecast_i) + (1-outcome_i) × log(1-forecast_i)]
```

- More heavily penalizes confident wrong predictions than Brier
- Saying 99% when outcome is 0 costs much more than saying 70% when outcome is 0
- **Proper scoring rule**: Your expected score is maximized by reporting your true belief
- Preferred in information-theoretic contexts; relates to cross-entropy/KL divergence

### 5.3 Calibration Plots

Plot predicted probability (x-axis, binned) vs. observed frequency (y-axis). Perfect calibration = 45° line.

- Bin forecasts (e.g., 0-10%, 10-20%, ..., 90-100%)
- Plot the actual outcome rate for each bin
- Deviations from the diagonal reveal systematic miscalibration
- Common patterns: S-curve (overconfident), inverse-S (underconfident)

### 5.4 Comparing to Market Benchmark

Your edge = Market Brier Score - Your Brier Score

In practice, calculate:
- Your Brier score on resolved markets you traded
- The market's implied probability Brier score on those same markets at the time you traded
- The difference is your calibration edge

**Important**: Account for transaction costs (spread, fees). A raw 2% Brier improvement might be eaten by a 5% spread.

### 5.5 Statistical Significance

- Use paired tests (your score vs. market score on same questions)
- Bootstrap confidence intervals on score differences
- Minimum ~100-200 resolved predictions before drawing conclusions
- Beware survivorship bias: don't only count markets where you traded

---

## 6. Identifying Systematically Miscalibrated Markets

### 6.1 Structural Miscalibration Sources

| Source | Mechanism | Where to Look |
|--------|-----------|---------------|
| **Favorite-longshot bias** | Entertainment bettors overbet longshots | Sports, novelty markets |
| **Liquidity constraints** | Prices can't move to true value if nobody can trade enough | Thin prediction markets (Polymarket small markets) |
| **Hedging demand** | Some participants trade for insurance, not information | Financial markets, crypto |
| **Regulatory limits** | Position limits, geographic restrictions reduce informed capital | Kalshi, regulated platforms |
| **Narrative/salience** | Dramatic scenarios overweighted | Geopolitics, pandemic, AI risk |
| **Recency bias** | Recent trends extrapolated too far | All domains |
| **Anchoring** | Market opened at wrong price, insufficient adjustment | New markets |
| **Partisanship** | Motivated reasoning by political bettors | Election markets |

### 6.2 Practical Screens for Miscalibration

1. **Compare platforms**: If Polymarket says 60% and Metaculus says 45%, someone's wrong. Cross-platform divergence flags opportunities.

2. **Historical calibration analysis**: Download resolved market data. Bin by probability. Check calibration curves. If events priced at 80% only resolve YES 65% of the time in a given category, there's a persistent bias.

3. **Base rate comparison**: Compare market price to simple base rate models. If the market says 30% for an event type that historically occurs 50% of the time, investigate why. Maybe the market knows something, or maybe it's biased.

4. **Extreme probability audit**: Markets at 95%+ and 5%- are often poorly calibrated. The tail probabilities are especially where overconfidence appears.

5. **Event clustering**: Markets on correlated events sometimes price them independently when they shouldn't be. (E.g., if "Fed hikes in June" is 80% and "Fed hikes in September" is 70%, but September depends heavily on June, the joint probability may be mispriced.)

6. **Temporal patterns**: Some markets are less efficient at certain times (overnight, weekends, right after market creation, during high-volatility news events).

### 6.3 The Meta-Strategy

The highest-value approach:
1. Build a database of resolved predictions across platforms
2. Categorize by domain, probability range, time horizon
3. Run calibration analysis on each segment
4. Identify segments where markets are persistently miscalibrated
5. Develop specialized models for those segments
6. Trade systematically with bankroll management

---

## 7. Known Biases in Prediction Markets

### 7.1 Favorite-Longshot Bias

**The most robust and well-documented bias in betting markets.**

- Longshots (low probability events) are overpriced; favorites (high probability events) are underpriced
- Documented in horse racing (Griffith 1949, many since), sports betting, and prediction markets
- Magnitude: events at true 1% are often priced at 2-5%; events at true 95% are often priced at 90-93%
- **Explanations**: Risk-loving preferences, utility of gambling, representative heuristic, small-sample overweighting
- **Implication**: Systematically betting on favorites and against longshots has positive expected value (before transaction costs)

### 7.2 Recency Bias

- Recent events are overweighted in probability estimates
- A team that won its last 3 games is overvalued; one that lost its last 3 is undervalued (relative to season-long performance)
- Markets overreact to recent polls, economic data releases, and news
- **Counter-strategy**: Use longer lookback windows, regress to the mean more aggressively

### 7.3 Anchoring

- Market prices anchor on the initial probability and adjust insufficiently
- New markets are especially vulnerable — the first few trades set a price that subsequent traders nudge rather than fundamentally reassess
- **Counter-strategy**: Ignore the current market price when forming your independent estimate, then compare

### 7.4 Overconfidence / Miscalibration at Extremes

- Forecasters and markets are systematically overconfident at high probabilities
- "95% sure" events happen only ~85-90% of the time in many domains
- This creates value in buying cheap "no" positions on high-probability markets
- **GJP data**: Even superforecasters showed mild overconfidence above 90%

### 7.5 Narrative Bias / Availability

- Vivid, easily imagined scenarios are overpriced (terrorism, pandemics, dramatic geopolitical events)
- Boring, gradual outcomes are underpriced (continued stability, slow growth, status quo)
- **Counter-strategy**: Ask "what would have to happen for this NOT to occur?" — inversion forces consideration of the mundane alternative

### 7.6 Partisanship and Motivated Reasoning

- Especially acute in political prediction markets
- Supporters of a candidate systematically overestimate their candidate's chances
- Creates systematic bias proportional to the platform's user base political leaning
- **Data**: PredictIt during 2016-2020 showed Republican-leaning biases on some contracts; Polymarket's demographics may skew differently
- **Counter-strategy**: If you can identify the platform's demographic bias, fade it

### 7.7 Correlation Neglect

- Markets often price correlated events as if they're independent
- Example: "Will AI lab X release a model?" and "Will AI lab Y release a model?" might both be at 40%, but the correlation (driven by shared competitive dynamics) means the joint distribution is mispriced
- **Counter-strategy**: Build correlation-aware portfolios; look for conditional probability mispricings

### 7.8 Status Quo Bias

- Markets underestimate the probability of regime changes, paradigm shifts, and discontinuities
- Slow to price in: war escalation, policy pivots, technological breakthroughs
- **Counter-strategy**: Explicitly model the probability of "things change" vs. "things continue"

---

## 8. Practical Framework: Building Your Calibration Edge

### Step 1: Track Everything
- Log every prediction you make with timestamp, your probability, market probability, and resolution
- Use a spreadsheet or database. Tools: Calibration City, custom tracker, or just a CSV

### Step 2: Specialize
- Pick 2-3 domains. Go deep. Build base rate databases for those domains.
- Generalists can't beat specialists in their domain

### Step 3: Build Base Rate Models
- For each domain, compile reference classes and historical frequencies
- Start simple: logistic regression on a few key variables often beats complex models

### Step 4: Compare to Markets Systematically
- Develop your estimate independently FIRST, then check the market
- Trade only when your estimate diverges significantly (accounting for transaction costs and uncertainty)

### Step 5: Evaluate and Iterate
- After 100+ resolved predictions, run calibration analysis
- Decompose Brier score into calibration and resolution components
- Identify where you're adding value and where you're not
- Kill strategies that don't work; double down on those that do

### Step 6: Bankroll Management
- Kelly criterion or fractional Kelly (¼ to ½ Kelly is standard)
- Never bet more than 5% of bankroll on a single outcome
- Diversify across uncorrelated predictions
- Account for the possibility that your edge estimate is wrong (it probably is, at least partially)

---

## Key References

- Tetlock, P. (2015). *Superforecasting: The Art and Science of Prediction*
- Tetlock, P. (2005). *Expert Political Judgment*
- Kahneman, D. (2011). *Thinking, Fast and Slow* (especially on base rate neglect)
- Manski, C. (2006). "Interpreting the Predictions of Prediction Markets" — on why market prices aren't pure probabilities
- Snowberg & Wolfers (2010). "Explaining the Favorite-Long Shot Bias"
- Satopää et al. (2014). "Combining Multiple Probability Predictions Using a Simple Logit Model" (extremizing)
- Good Judgment Project publications: goodjudgment.com
- Metaculus track record: metaculus.com/questions/track-record/
- Brier, G. (1950). "Verification of Forecasts Expressed in Terms of Probability"
- Murphy, A. (1973). "A New Vector Partition of the Probability Score" (Brier decomposition)
