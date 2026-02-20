# Prediction Market Arbitrage Strategies

*Research document — February 2026*

---

## Table of Contents

1. [Overview](#overview)
2. [Cross-Platform Arbitrage](#cross-platform-arbitrage)
3. [Intra-Platform Arbitrage](#intra-platform-arbitrage)
4. [Identifying & Calculating Arb Opportunities](#identifying--calculating-arb-opportunities)
5. [Execution Challenges](#execution-challenges)
6. [Historical Examples](#historical-examples)
7. [Data Requirements & Monitoring](#data-requirements--monitoring)

---

## Overview

Arbitrage in prediction markets exploits price discrepancies for equivalent (or logically related) outcomes across or within platforms. Because prediction markets are fragmented, relatively illiquid, and populated by retail participants, mispricings are more frequent than in traditional financial markets — but execution is harder.

**Key platforms (as of early 2026):**

| Platform | Type | Currency | Fees | Geography |
|----------|------|----------|------|-----------|
| **Polymarket** | Crypto (Polygon) | USDC | ~2% on winnings (no trading fee since 2024) | Non-US (officially) |
| **Kalshi** | CFTC-regulated | USD | Varies by market, typically 1-7¢/contract | US only |
| **PredictIt** | CFTC no-action letter (wound down 2023) | USD | 10% profit fee + 5% withdrawal | US (was) |
| **Metaculus** | Reputation-based | N/A | N/A | Global |
| **Betfair Exchange** | Betting exchange | GBP/EUR | 2-5% commission on net winnings | UK/EU/AUS |
| **Manifold** | Play money / Mana | Mana | Minimal | Global |
| **Insight Prediction** | Crypto | USDC | ~1% | Non-US |

True monetary arbitrage requires platforms where you can deposit/withdraw real value. The practical arb universe is primarily: **Polymarket ↔ Kalshi ↔ Betfair** (and smaller crypto prediction markets).

---

## Cross-Platform Arbitrage

### The Core Concept

When the same event is priced differently on two platforms, you can buy YES on the cheaper platform and NO (or sell YES) on the more expensive one. If the prices sum to less than $1.00 (after fees), you lock in a guaranteed profit.

### Example

> **"Will the Fed cut rates in March 2026?"**
> - Kalshi: YES @ 35¢ / NO @ 67¢
> - Polymarket: YES @ 42¢ / NO @ 60¢
>
> **Arb:** Buy YES on Kalshi (35¢) + Buy NO on Polymarket (60¢) = 95¢ total cost
> One of these pays $1.00 → **5¢ guaranteed profit per pair (before fees)**

### Why Cross-Platform Arbs Exist

1. **Different user bases** — Kalshi skews US retail/institutional; Polymarket skews crypto-native/international. Different information sets and biases.
2. **Deposit/withdrawal friction** — Moving capital between platforms takes time (especially fiat ↔ crypto), so arbitrageurs can't instantly equalize prices.
3. **Market definition differences** — Subtle differences in resolution criteria. "Will X happen by end of Q1?" may resolve differently if platforms define Q1 differently, or use different oracle/resolution sources.
4. **Liquidity asymmetry** — A large buy on Polymarket may not be matched by someone willing to sell on Kalshi at the corresponding price.
5. **Regulatory barriers** — US users can't (legally) use Polymarket; non-US users can't use Kalshi. This structurally segments the arbitrage pool.

### Cross-Platform Pairs to Monitor

- **US Elections** — Historically the fattest cross-platform arbs (Polymarket vs Kalshi vs Betfair)
- **Fed/Macro decisions** — Rate cuts, inflation prints, GDP
- **Crypto-specific events** — Bitcoin ETF approvals, protocol upgrades (bigger on Polymarket)
- **Sports/entertainment** — Betfair vs Polymarket (where both offer markets)
- **Geopolitical** — Ukraine/Russia, China/Taiwan (thin markets, wide spreads, but arbs exist)

---

## Intra-Platform Arbitrage

### Types

#### 1. Complementary Contract Arbitrage (YES + NO < $1.00)

On a single binary market, if you can buy YES + NO for less than $1.00, one must pay out and you profit the difference. This is rare on well-functioning platforms but can appear momentarily during volatile moves or with wide bid-ask spreads.

**Important:** Most platforms price YES and NO as complements (NO = 1 - YES), so this arb is typically unavailable on the *mid* price. But on **order books**, the ask for YES + ask for NO can briefly sum to < $1.00.

#### 2. Multi-Outcome Market Arbitrage

When a market has multiple mutually exclusive, collectively exhaustive outcomes, the prices should sum to $1.00 (or the number of shares per outcome). If they sum to less, buy all outcomes.

**Example:**
> **"Who will win the 2028 Democratic primary?"**
> - Candidate A: 30¢
> - Candidate B: 25¢
> - Candidate C: 15¢
> - Candidate D: 10¢
> - Field/Other: 12¢
> - **Total: 92¢** → Buy all five for 92¢, guaranteed $1.00 payout = 8¢ profit

In practice, multi-outcome markets frequently overprice (sum > $1.00) because platforms embed overround/vig. But during rapid price movements, they can temporarily underprice.

#### 3. Correlated Market Arbitrage

Exploit logical relationships between markets that aren't directly linked:

- **"Will X happen before Y?"** + **"Will Y happen before X?"** — should sum to ~100% (if one must happen first)
- **Conditional markets** — "Will A win the election?" and "Will A win state X?" (A winning state X but losing the election creates a constraint)
- **Temporal nesting** — "Will inflation be >3% in Q1?" vs "Will inflation be >3% in 2026?" (annual ≥ quarterly by definition)

#### 4. Calendar/Temporal Arbitrage

If "Will X happen by March?" is priced higher than "Will X happen by June?", that's a logical impossibility (anything that happens by March also happens by June). Buy June, sell March.

---

## Identifying & Calculating Arb Opportunities

### The Math

#### Binary Cross-Platform Arb

```
Platform A: YES @ price_a
Platform B: NO  @ price_b

Cost = price_a + price_b
Gross profit = $1.00 - cost (if cost < $1.00)

After fees:
Net profit = (1 - fee_rate_winner) × $1.00 - cost
```

Where `fee_rate_winner` is the fee on the winning platform's payout.

#### Multi-Outcome Arb

```
n outcomes, prices p_1 ... p_n (mutually exclusive, exhaustive)
Cost = Σ p_i
Gross profit = $1.00 - Σ p_i (if sum < $1.00)
```

#### Adjusted for Fees

Each platform's fee structure matters enormously:

- **Polymarket**: ~2% on net profit (winnings minus cost basis). No fee on losing side.
- **Kalshi**: Per-contract fee on both entry and exit (varies, often 1-3¢ per contract per side).
- **Betfair**: Commission on net winnings per market (2-5%, depends on account).

**Effective arb threshold**: The raw price gap must exceed total fees on both platforms. For Polymarket + Kalshi, you typically need at least a **4-7¢ gap** to profit after all fees.

### Screening Formula

For a cross-platform binary arb:

```
arb_exists = (best_yes_A + best_no_B) < (1 - total_fee_rate)
```

Where `total_fee_rate` accounts for worst-case fees on both sides.

### Capital Efficiency

Arb returns are typically **2-8% per instance** on capital deployed, but capital is locked until resolution. For a market resolving in 3 months, a 5% arb = ~20% annualized — attractive, but with significant opportunity cost and risk.

**Capital-weighted approach:**
```
Annualized return = (profit / capital_deployed) × (365 / days_to_resolution)
```

---

## Execution Challenges

### 1. Latency & Execution Risk

- **Leg risk**: You execute one side of the arb, but the other side moves before you can execute. This is the #1 killer of arb strategies.
- **Polymarket** runs on Polygon blockchain — transactions take 2-5 seconds. Kalshi is centralized — effectively instant. This asymmetry means prices can move during execution.
- **Mitigation**: Use APIs for both platforms. Polymarket has a CLOB (central limit order book) accessible via API; Kalshi has a REST API. Minimize human-in-the-loop.

### 2. Fee Structures

| Platform | Entry Fee | Exit Fee | Winner Fee | Net Impact |
|----------|-----------|----------|------------|------------|
| Polymarket | 0% | 0% | ~2% on profit | Low for large wins |
| Kalshi | 1-7¢/contract | 0-1¢ | Built into spread | Moderate |
| Betfair | 0% | 0% | 2-5% of net win | Moderate |

Fees can eat the entire arb. **Always calculate net of ALL fees before executing.**

### 3. Liquidity

- Most prediction markets are thin. You might see a 5¢ arb on the top-of-book, but only 50 contracts available at that price.
- Slippage is real: a $1,000 arb order might move the price 3-5¢, destroying the edge.
- **Check depth of book**, not just top-of-book prices.

### 4. Settlement & Resolution Risk

This is the most underappreciated risk:

- **Different resolution sources**: Polymarket uses UMA oracle (decentralized dispute resolution); Kalshi uses internal resolution with CFTC oversight. They can resolve the same real-world event **differently**.
- **Ambiguity**: "Will Biden run for re-election?" — what counts as "running"? Filing FEC paperwork? Announcing? Each platform has its own fine print.
- **Timing**: One platform may resolve days or weeks before the other, affecting capital lockup.
- **Edge case: both sides lose**: If Platform A resolves YES and Platform B also resolves YES (when you bought NO there), your "arb" becomes a double loss. This can happen with ambiguous markets.

**Mitigation**: Read resolution criteria for BOTH platforms carefully. Only arb markets with near-identical resolution criteria.

### 5. Capital Requirements & Lockup

- Capital is locked until market resolution (could be days to months).
- Cross-platform arbs require funded accounts on multiple platforms.
- Opportunity cost of locked capital is significant.
- Polymarket requires USDC on Polygon; Kalshi requires USD. Bridging between these has costs and delays.

### 6. Regulatory Risk

- Using Polymarket from the US violates their ToS and potentially CFTC regulations.
- Kalshi markets are CFTC-regulated; Polymarket operates offshore.
- Regulatory action against either platform could freeze funds.
- Tax treatment differs (Kalshi issues 1099s; Polymarket is DeFi — self-reported).

### 7. Counterparty Risk

- Polymarket: Smart contract risk (though audited), Polygon chain risk.
- Kalshi: Counterparty risk is low (CFTC-regulated, funds held at regulated banks).
- Smaller platforms: Significant counterparty risk.

---

## Historical Examples

### 1. 2024 US Presidential Election (Polymarket vs Kalshi)

The biggest prediction market event in history. Throughout 2024:
- Polymarket consistently priced Trump higher than Kalshi (sometimes by 5-10¢).
- This was partly due to whale activity on Polymarket (the "French trader" who bet ~$30M on Trump).
- Cross-platform arbs of 3-8¢ existed for weeks, but were hard to exploit because US users couldn't legally access Polymarket.
- Post-election, both resolved identically (Trump won), so the arb was real and profitable for those who executed it.

### 2. PredictIt Overround Arbs (2020-2023)

PredictIt's 850-trader limit per market created persistent mispricings:
- Multi-outcome markets (e.g., "Which state will have the closest margin?") frequently summed to 120-140¢ instead of 100¢ — meaning sellers of all outcomes could lock in 20-40% returns.
- The 10% profit fee and 5% withdrawal fee ate into this, but net arbs of 5-15% were common.
- PredictIt's wind-down in 2023 created additional pricing chaos.

### 3. Fed Rate Decision Markets (2023-2025)

Fed funds rate markets exist on both Kalshi and Polymarket:
- Before each FOMC meeting, prices would diverge by 3-8¢ between platforms.
- Arbs were most pronounced 1-2 weeks before the meeting and collapsed to near-zero the day before.
- These were relatively clean arbs — same resolution criteria (Fed announces rate), same timing.

### 4. COVID-era Arbs (2020-2021)

Early COVID prediction markets (mostly on smaller platforms) had massive mispricings:
- "Will there be a vaccine by end of 2020?" was priced at 15-20¢ on some platforms while betting markets implied 40%+.
- Resolution ambiguity (EUA vs full approval vs "available to public") created both opportunities and traps.

### 5. Crypto-Specific Markets

- "Will Bitcoin reach $100K by end of 2024?" — priced wildly differently across Polymarket, Insight, and Manifold (though Manifold is play money, it signaled relative sentiment).
- ETF approval markets in late 2023 showed 10-15¢ gaps between platforms.

### 6. Multi-Outcome Underpricing (Polymarket 2024)

During the 2024 Democratic primary speculation period:
- Multi-outcome markets for the Democratic nominee briefly summed to <90¢ when Biden dropped out and the field was in flux.
- Fast actors who bought all outcomes locked in guaranteed returns.

---

## Data Requirements & Monitoring

### Required Data Feeds

#### Per Platform:
1. **Order book data** (full depth, not just top-of-book)
   - Polymarket: WebSocket via CLOB API (`wss://clob.polymarket.com`)
   - Kalshi: REST API (`api.elections.kalshi.com`) + WebSocket for live updates
   - Betfair: Exchange Stream API (requires API key + subscription)

2. **Market metadata**
   - Resolution criteria text
   - Resolution date/time
   - Resolution source/oracle

3. **Historical prices** — for backtesting and identifying typical arb windows

#### Cross-Platform:
4. **Market matching/mapping** — The hardest part. You need to identify which markets on Platform A correspond to which markets on Platform B. This requires:
   - NLP/fuzzy matching on market titles
   - Manual curation for high-value markets
   - A maintained mapping table

### Monitoring Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Polymarket  │    │   Kalshi    │    │   Betfair   │
│  WebSocket   │    │  REST/WS    │    │  Stream API │
└──────┬───────┘    └──────┬──────┘    └──────┬──────┘
       │                   │                   │
       └─────────┬─────────┴─────────┬─────────┘
                 │                   │
          ┌──────▼──────┐    ┌───────▼───────┐
          │  Normalizer  │    │ Market Mapper │
          │  (prices to  │    │ (which mkts   │
          │  common fmt) │    │  are equiv?)  │
          └──────┬───────┘    └───────┬───────┘
                 │                    │
                 └────────┬───────────┘
                          │
                  ┌───────▼────────┐
                  │  Arb Scanner   │
                  │  (fee-adjusted │
                  │   comparison)  │
                  └───────┬────────┘
                          │
              ┌───────────▼──────────┐
              │  Alert / Execution   │
              │  (notify or auto-    │
              │   execute if > X%)   │
              └──────────────────────┘
```

### Key Metrics to Track

- **Gross spread**: Raw price difference before fees
- **Net spread**: After all fees on both sides
- **Available size**: Minimum liquidity on either side (your max arb size)
- **Resolution date**: Days until lockup ends → annualized return
- **Resolution match score**: How similar are the resolution criteria? (1.0 = identical, <0.9 = risky)
- **Historical spread**: What's the typical spread for this market pair? (helps assess mean-reversion vs true arb)

### Tools & APIs

| Tool | Purpose |
|------|---------|
| **Polymarket API** | CLOB order book, market data, trade execution |
| **Kalshi API** | REST API for prices, positions, order placement |
| **Betfair API-NG** | Exchange data and execution |
| **CCXT** | Crypto exchange library (useful if prediction market tokens trade on DEXs) |
| **Custom scripts** | Market mapping, arb calculation, alerting |
| **Grafana/Prometheus** | Real-time dashboards for spread monitoring |

### Practical Implementation Notes

1. **Start with manual monitoring** of 5-10 high-volume market pairs across 2 platforms. Get a feel for typical spreads, fee impacts, and execution logistics.

2. **Build a spreadsheet first** before coding anything:
   - Columns: Market name, Platform A price, Platform B price, gross spread, fees A, fees B, net spread, size available, days to resolution, annualized return
   - Update 2-3x daily for your tracked markets

3. **Graduate to API-based monitoring** once you've validated the strategy manually. Python + asyncio for WebSocket feeds from multiple platforms.

4. **Execution automation is optional and dangerous** — leg risk from automated execution gone wrong can be worse than missing arbs. Consider semi-automated: alerts + one-click execution.

5. **Track all trades meticulously** — you need to reconcile positions across platforms, track locked capital, and calculate actual vs expected P&L.

---

## Key Takeaways

1. **Cross-platform arbs exist and are persistent** due to regulatory segmentation, different user bases, and capital friction. The 2024 election proved this at scale.

2. **Fees are the arb killer.** A 5¢ raw spread often becomes 0-1¢ after fees. Always calculate net.

3. **Resolution risk is the hidden danger.** The same real-world event can resolve differently across platforms. Read the fine print.

4. **Liquidity limits scale.** You might find a 10¢ arb, but only be able to execute $200 of it before slippage eats the edge.

5. **Capital lockup is the opportunity cost.** A 5% arb on a 6-month market is only 10% annualized — decent but not amazing, especially given the risks.

6. **Intra-platform arbs in multi-outcome markets** are the cleanest form (same platform, same resolution) but also the rarest and shortest-lived.

7. **The best arbs require being on both sides of the regulatory fence** (US + non-US accounts), which creates legal risk.

8. **Automation helps but isn't required.** The best arbs persist for hours or days, not milliseconds. A well-monitored spreadsheet can capture most of the value.

---

*Next steps: Build a monitoring tool that tracks Polymarket ↔ Kalshi spreads for the top 20 markets by volume. See `/research/tools/` for implementation notes.*
