# Prediction Market Market Making: Deep Research

*Last updated: 2026-02-17*

---

## Table of Contents

1. [How Market Making Works on Prediction Markets](#1-how-market-making-works)
2. [Spread Mechanics, Inventory Risk & Order Book Dynamics](#2-spread-mechanics)
3. [Algorithms & Approaches](#3-algorithms)
4. [Data Requirements](#4-data-requirements)
5. [Edge Cases & Risks](#5-risks)
6. [Real Examples & Practical Notes](#6-real-examples)
7. [Implementation Considerations](#7-implementation)

---

## 1. How Market Making Works on Prediction Markets {#1-how-market-making-works}

### The Basic Idea

A market maker (MM) provides liquidity by simultaneously posting **bid** and **ask** orders on a prediction market contract. The contract pays $1 if an event occurs, $0 otherwise. The MM profits from the **bid-ask spread** — buying at (say) $0.48 and selling at $0.52.

### Prediction Market vs. Traditional MM

| Aspect | Traditional Equities | Prediction Markets |
|--------|--------------------|--------------------|
| Asset lifetime | Indefinite | Finite (resolves to 0 or 1) |
| Fair value | Continuous, uncertain | Converges to 0 or 1 at expiry |
| Liquidity | Deep | Often thin |
| Information asymmetry | Moderate | Can be extreme (insiders) |
| Hedging | Options, correlated assets | Very limited |
| Regulation | Heavy | Light (crypto) or moderate (Kalshi) |

### Platform Specifics

**Polymarket (CLOB on Polygon)**
- Central Limit Order Book (CLOB) using the CTF Exchange smart contract
- Orders are signed off-chain, matched by an operator, settled on-chain
- Binary outcome tokens: YES and NO shares for each market
- NO fees for makers (as of 2024-2025), taker fees ~1-2%
- API access for programmatic trading via REST + WebSocket
- Complementary pricing: YES price + NO price = $1.00 (minus spread)

**Kalshi (Regulated CFTC exchange)**
- Traditional CLOB, regulated as a Designated Contract Market
- Event contracts regulated as swaps
- API available for institutional/programmatic access
- Fees apply to both makers and takers
- More structured market data

### The MM's Core Loop

```
1. Estimate fair probability p* of the event
2. Post BID at p* - δ (buy YES shares)
3. Post ASK at p* + δ (sell YES shares / buy NO shares)
4. When filled, update p* based on new information
5. Manage inventory (net YES/NO position)
6. Repeat until market resolves
```

---

## 2. Spread Mechanics, Inventory Risk & Order Book Dynamics {#2-spread-mechanics}

### Spread Determination

The spread (2δ) must compensate for:

1. **Adverse selection cost** — informed traders pick you off
2. **Inventory risk** — holding directional exposure
3. **Volatility** — probability can swing fast on news
4. **Time to resolution** — closer to event = more binary movement

**Minimum viable spread formula (simplified):**

```
spread ≥ adverse_selection_cost + inventory_risk_premium + volatility_cost
```

In practice, on thin prediction markets, spreads of **2-8 cents** (on a $1 contract) are common. During high-information periods, spreads widen to 10-20+ cents.

### Inventory Risk

This is the central challenge. Unlike equities where you can hedge, prediction market positions are largely **unhedgeable**.

**Inventory accumulation scenario:**
- You're making a market at 50¢ bid / 54¢ ask
- Informed traders keep buying YES (hitting your ask)
- You accumulate a short YES / long NO position
- If the event happens, you lose $1 per share minus the premium collected
- Your spread profits (~4¢/share) are dwarfed by directional loss ($1/share)

**Inventory management techniques:**
1. **Skew quotes** — shift bid/ask in direction that reduces inventory
   - Long 100 YES → lower both bid and ask to encourage selling to you
2. **Position limits** — hard caps on directional exposure
3. **Decay quotes** — reduce size as inventory grows
4. **Cross-market hedging** — if correlated markets exist (e.g., "Will X win?" and "Will X win by >5%?"), hedge across them
5. **Complementary token trading** — buy/sell NO tokens to offset YES exposure

### Order Book Dynamics on Prediction Markets

Prediction market order books are characteristically:

- **Thin** — often <$10K on each side for most markets
- **Lumpy** — a few large orders dominate
- **Event-driven** — liquidity appears/disappears around news
- **Asymmetric** — more interest on one side (e.g., heavy YES buying on popular outcomes)

**Key observation:** The order book is much more informative on prediction markets than on equities. A large resting bid at 65¢ in a political market often reflects a genuine probability estimate, not just a market-making algo.

**Queue priority matters:** On Polymarket's CLOB, price-time priority applies. Getting to the front of the queue at key price levels is valuable. MMs compete for queue position.

### The Complementarity Constraint

On binary markets: `P(YES) + P(NO) = 1`

This means the MM can equivalently:
- Sell YES at 55¢, OR
- Buy NO at 45¢

Both create the same economic exposure. Smart MMs quote in **both** YES and NO books simultaneously to maximize fill opportunities. This also means arbitrage between YES and NO tokens keeps the books in sync.

---

## 3. Algorithms & Approaches {#3-algorithms}

### 3.1 Avellaneda-Stoikov (AS) Framework

The gold standard for market making, adapted from the 2008 paper *"High-frequency trading in a limit order book"*.

**Core idea:** Optimal bid/ask quotes depend on:
- Current inventory `q`
- Time remaining `T - t`
- Volatility `σ`
- Risk aversion `γ`

**Key formulas:**

**Reservation price** (where the MM is indifferent to trading):
```
r(s, q, t) = s - q * γ * σ² * (T - t)
```
Where:
- `s` = current mid-price (fair probability)
- `q` = inventory (positive = long YES)
- `γ` = risk aversion parameter
- `σ` = volatility of the probability
- `T - t` = time to resolution

**Optimal spread:**
```
δ(t) = γ * σ² * (T - t) + (2/γ) * ln(1 + γ/κ)
```
Where `κ` is a parameter related to order arrival intensity.

**Adaptation for prediction markets:**
- `s` is the estimated true probability (0 to 1)
- `σ` is the volatility of probability changes (not price returns)
- `T` is the market resolution time (known!)
- The bounded nature of prices [0, 1] requires modification — standard AS assumes unbounded prices
- Near resolution, `σ` should spike (probability converges to 0 or 1)

**Practical parameter tuning:**
- `γ` (risk aversion): Start high (conservative), decrease as you gain confidence. Typical: 0.1–1.0
- `σ` estimation: Use recent realized volatility of mid-price changes, or implied from order flow
- `κ` (arrival rate): Estimate from historical fill rates at various distances from mid

### 3.2 Bayesian Market Making

Instead of treating fair value as a continuous process, model the underlying event as a Bernoulli random variable and update beliefs:

```
Prior: p ~ Beta(α, β)
Observation: order flow signals
Posterior: p ~ Beta(α', β')
```

**Order flow as information:**
- Net buying pressure → increase estimated probability
- Large aggressive orders → high information content
- Small passive fills → low information content

This approach naturally handles the **information asymmetry** problem. Each trade updates your estimate of the true probability, and your quotes adjust accordingly.

### 3.3 Simple Spread-Based Strategies

For practitioners starting out:

**Fixed spread around an estimate:**
```python
def simple_mm(fair_price, spread=0.04, size=100):
    bid = fair_price - spread/2
    ask = fair_price + spread/2
    return {
        'bid': {'price': round(bid, 2), 'size': size},
        'ask': {'price': round(ask, 2), 'size': size}
    }
```

**Inventory-adjusted spread:**
```python
def inventory_adjusted_mm(fair_price, inventory, max_inventory=500, 
                           base_spread=0.04, skew_factor=0.02):
    inventory_ratio = inventory / max_inventory  # -1 to 1
    skew = inventory_ratio * skew_factor
    
    bid = fair_price - base_spread/2 - skew
    ask = fair_price + base_spread/2 - skew
    
    # Reduce size on the side that would increase inventory
    bid_size = max(10, 100 * (1 - max(0, inventory_ratio)))
    ask_size = max(10, 100 * (1 + max(0, inventory_ratio)))
    
    return {
        'bid': {'price': round(bid, 2), 'size': int(bid_size)},
        'ask': {'price': round(ask, 2), 'size': int(ask_size)}
    }
```

### 3.4 Model-Based Edge + Market Making

The most profitable approach combines **edge** (a better probability estimate) with market making:

1. Build a model that estimates P(event) better than the market
2. Center your quotes around your model's estimate, not the market mid
3. Your spread captures both the MM spread AND the model's edge

**Example:** You model an election at 62% while the market trades at 58%. You bid at 59¢ and ask at 63¢. You earn spread AND capture the 4¢ mispricing on your bid side.

This is where **most real money is made** in prediction market making. Pure spread capture on thin, informationally-loaded markets is marginal at best.

### 3.5 Multi-Market / Portfolio Market Making

When making markets across multiple related contracts:

- **Correlated events** (e.g., "Dem wins presidency" + "Dem wins Senate") — hedge across them
- **Multi-outcome markets** (e.g., "Who wins the primary?" with 10 candidates) — the sum of all probabilities = 100%. An overpriced candidate means others are underpriced.
- **Temporal markets** (e.g., "Will X happen by March?" and "Will X happen by June?") — the March contract bounds the June contract from below.

Portfolio-level inventory management across correlated markets significantly reduces risk.

---

## 4. Data Requirements {#4-data-requirements}

### Essential Data

| Data Type | Source | Use |
|-----------|--------|-----|
| **Order book snapshots** | Exchange API (WebSocket) | Fair value estimation, spread determination |
| **Trade tape** | Exchange API | Volume analysis, order flow toxicity |
| **Historical prices** | Exchange API / scrapers | Volatility estimation, backtesting |
| **Event-specific data** | News, polls, models | Fair probability estimation |
| **Resolution schedule** | Exchange | Time-to-expiry calculations |

### Order Book Data (Critical)

**What you need in real-time:**
- Full depth of book (all resting orders with price + size)
- Best bid/ask (BBO) updates
- Order additions, cancellations, modifications
- Trade executions (aggressor side, size, price)

**Polymarket specifics:**
- WebSocket API provides real-time book updates
- REST API for snapshots
- On-chain data as backup/verification
- Token IDs for YES/NO positions

**Derived metrics to compute:**
- **Mid-price:** `(best_bid + best_ask) / 2`
- **Micro-price:** `(best_bid × ask_size + best_ask × bid_size) / (bid_size + ask_size)` — better fair value estimate
- **Spread:** `best_ask - best_bid`
- **Book imbalance:** `(bid_volume - ask_volume) / (bid_volume + ask_volume)` — predictive of short-term price moves
- **VPIN (Volume-synchronized PIN):** Estimates probability of informed trading

### Volume & Liquidity Metrics

- **Daily volume** — determines if a market is worth making
- **Average trade size** — calibrate your order sizes
- **Fill rate** — how often your resting orders get hit
- **Time between trades** — determines how often to update quotes

**Rule of thumb:** Don't bother market-making on markets with <$5K daily volume unless you have strong model edge. The spread capture won't cover operational costs.

### Volatility Estimation

Prediction market volatility is **not** like equity volatility:

- **Regime-dependent:** Quiet periods punctuated by information shocks
- **Resolution-dependent:** Volatility structure depends on time to resolution
- **Bounded:** Prices are in [0, 1], so volatility naturally decreases near boundaries
- **Event-clustered:** Debates, primaries, data releases cause volatility spikes

**Practical volatility estimation:**
```python
# Simple realized volatility of mid-price changes
import numpy as np

def estimate_volatility(mid_prices, window=100):
    returns = np.diff(mid_prices)
    return np.std(returns[-window:])

# Better: use exponentially weighted
def ewma_volatility(mid_prices, halflife=50):
    returns = np.diff(mid_prices)
    weights = np.exp(-np.log(2) * np.arange(len(returns))[::-1] / halflife)
    weights /= weights.sum()
    return np.sqrt(np.sum(weights * returns**2))
```

### External Data for Fair Value

The MM's edge comes from better probability estimates. Useful sources:

- **Polls & poll aggregators** (elections)
- **Weather models** (weather markets)
- **Economic data feeds** (macro markets)
- **News sentiment** (general)
- **Other prediction markets** (cross-platform arbitrage / signals)
- **Social media signals** (Twitter/X, Reddit)
- **Betting odds** (sports/elections)

---

## 5. Edge Cases & Risks {#5-risks}

### 5.1 Adverse Selection (The #1 Risk)

**The problem:** Someone knows the outcome (or has much better information) and trades against your resting orders before you can update.

**Real scenario:** A political market is quoting 50¢. An insider knows the candidate is about to drop out. They buy 10,000 NO shares at your 50¢ bid. Within minutes, the market moves to 10¢. You're stuck holding worthless YES shares.

**Detection & mitigation:**
- Monitor **trade size distribution** — unusually large trades signal informed flow
- Track **consecutive fills on one side** — 5+ consecutive buys = potential adverse selection
- Measure **realized spread** vs. **quoted spread** — if realized is consistently negative, you're being adversely selected
- Use **quote fade** — cancel and requote after each fill (adds latency risk)
- Implement **order flow toxicity metrics** (VPIN, Kyle's Lambda)
- **Widen spreads** during high-information periods (debates, announcements)

### 5.2 Event Resolution Spikes

**The problem:** Near resolution, the contract price moves violently from mid-range to 0 or 1. Any remaining inventory takes a large P&L hit.

**Example:** An election night market. At 8 PM, price is 55¢. By 11 PM, it's 95¢ as results come in. By midnight, it resolves at $1.00. If you were short YES at 55¢, you lose 45¢/share.

**Mitigation:**
- **Reduce position size** as resolution approaches
- **Widen spreads dramatically** (10-20¢+) near known information events
- **Pull quotes entirely** during live events (debates, vote counts)
- **Time-decay your maximum inventory** proportional to `T - t`
- Set **hard stop-losses** on directional exposure

### 5.3 Thin Market / Illiquidity Traps

**The problem:** You provide most of the liquidity. When you need to unwind, there's no one to trade with.

**Scenario:** You're the only MM on a niche market. You accumulate 5,000 YES shares. You want to reduce. The book has 200 shares on the bid. You can't exit without crashing the price.

**Mitigation:**
- Never hold more than you can unwind in a reasonable time
- Track your own share of book depth — if you're >50% of liquidity, scale down
- Maintain positions small relative to daily volume

### 5.4 Platform / Smart Contract Risk

**Polymarket-specific:**
- Smart contract bugs (CTF Exchange)
- Oracle manipulation (UMA oracle for resolution)
- Operator risk (centralized order matching)
- Disputed resolutions (has happened — e.g., ambiguous market wording)
- Gas spikes on Polygon (rare but possible)

**Kalshi-specific:**
- Exchange downtime
- Regulatory changes (CFTC could restrict markets)
- Settlement delays

### 5.5 Correlation Risk in Multi-Outcome Markets

In a market like "Who wins the Republican primary?" with 8 candidates:

- If you're making markets on all 8, your positions are **implicitly correlated**
- The sum must equal ~100%. If one candidate surges, all others drop simultaneously
- A single news event can move ALL your positions against you at once

**Mitigation:** Track your **net portfolio delta** across all related contracts, not just individual positions.

### 5.6 The "Rug Pull" / Ambiguous Resolution

Some markets have ambiguous resolution criteria. The MM's nightmare:
- You've been making a market for weeks, earning spread
- The event occurs but resolution is disputed
- The oracle/exchange rules against your position on a technicality
- All accumulated spread is wiped out by resolution loss

**Mitigation:** Read resolution criteria obsessively. Avoid markets with ambiguous wording. Monitor UMA oracle disputes (Polymarket).

### 5.7 Latency Disadvantage

On Polymarket, the operator matches orders. Sophisticated players may:
- Have lower-latency connections to the operator
- See your orders and react faster
- Front-run your quote updates

This is less of an issue than in traditional HFT, but still relevant during fast-moving events.

---

## 6. Real Examples & Practical Notes {#6-real-examples}

### Example 1: 2024 US Presidential Election (Polymarket)

The 2024 presidential election markets on Polymarket saw enormous volume ($3B+). Market makers in these markets faced:

- **Extreme adverse selection** around debates, polling releases, and major news events
- **Massive inventory risk** — the market swung from 50/50 to strongly favoring Trump over months
- **Deep liquidity** — at peak, tens of millions of dollars on the book
- **Professional MM participation** — firms reportedly used sophisticated models combining poll aggregation with order flow analysis
- Spreads were often 1-2¢ on the main market, competitive with traditional exchanges
- Some MMs reportedly earned 7-15% annualized return on deployed capital during stable periods, but faced significant drawdowns during volatile moves

### Example 2: Small "Novelty" Markets

Markets like "Will X tweet about Y?" or niche events:
- Extremely thin (<$1K daily volume)
- Spreads of 5-15¢ common
- Almost impossible to profitably market-make without a strong model edge
- Adverse selection from insiders (e.g., the tweeter themselves!) is severe
- Best avoided for pure MM; only viable with informational edge

### Example 3: Weather / Economic Data Markets (Kalshi)

- Resolution based on objective data (temperature, CPI, etc.)
- Model edge is achievable (weather models, economic nowcasts)
- More predictable volatility patterns (data release schedule is known)
- Less adverse selection risk (no "insiders" for weather)
- Good candidates for algorithmic MM

### Practical P&L Breakdown

A realistic MM operation on prediction markets:

```
Revenue:
  Spread capture:           +$X per contract traded
  Model edge (when right):  +$Y per position
  Rebates (if any):         +$Z

Costs:
  Adverse selection losses: -$A (the big one)
  Inventory loss at resolution: -$B
  Gas/transaction fees:     -$C
  Infrastructure costs:     -$D
  Opportunity cost of capital: -$E

Typical outcome:
  Pure spread MM on thin markets:    -5% to +5% (marginal/negative)
  Model-edge + MM on liquid markets: +10% to +30% annualized (good)
  MM during extreme events:          -50% to +100% (high variance)
```

---

## 7. Implementation Considerations {#7-implementation}

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Data Feed   │────▶│  Strategy    │────▶│  Order Manager │
│  (WebSocket) │     │  Engine      │     │  (REST API)    │
└─────────────┘     └──────────────┘     └────────────────┘
       │                    │                      │
       ▼                    ▼                      ▼
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Book State  │     │  Risk Mgmt   │     │  Position      │
│  Manager     │     │  Module       │     │  Tracker       │
└─────────────┘     └──────────────┘     └────────────────┘
```

### Key Implementation Details

1. **Quote update frequency:** Every 1-5 seconds for active markets, less for sleepy ones
2. **Order management:** Always know your resting orders. Cancel-before-replace to avoid double fills
3. **Position tracking:** Reconcile with on-chain state (Polymarket) regularly
4. **Failsafes:**
   - Kill switch to cancel all orders instantly
   - Maximum position limits (hard-coded, not configurable at runtime)
   - Maximum loss limits per market and globally
   - Heartbeat monitoring — if strategy process dies, cancel all orders

### Technology Stack (Practical)

- **Language:** Python (prototyping), Rust/C++ (production latency-sensitive)
- **Data:** WebSocket feeds, PostgreSQL/TimescaleDB for historical
- **Hosting:** Co-located if latency matters, cloud otherwise
- **Wallet management:** Secure key storage, separate hot/cold wallets
- **Monitoring:** Grafana dashboards for P&L, inventory, spread, fill rates

### Getting Started Checklist

- [ ] Set up API access (Polymarket CLOB API or Kalshi API)
- [ ] Build order book reconstruction from WebSocket feed
- [ ] Implement basic fair value estimation (start with micro-price)
- [ ] Build simple MM with fixed spread + inventory skew
- [ ] Paper trade for 2+ weeks, measure realized spread vs. quoted spread
- [ ] Analyze adverse selection: which markets/times are toxic?
- [ ] Add model-based fair value for specific markets
- [ ] Implement risk limits and kill switch
- [ ] Go live with minimal capital ($500-$2K)
- [ ] Scale slowly as you understand the dynamics

---

## Key Takeaways

1. **Pure spread capture is marginal** on prediction markets. The real money is in **model edge + market making**.
2. **Adverse selection is the dominant risk** — one informed trader can wipe out weeks of spread profits.
3. **Inventory management is critical** because positions are unhedgeable and resolve to 0 or 1.
4. **Avellaneda-Stoikov adapts well** but needs modification for bounded [0,1] prices and known resolution times.
5. **Start with liquid, objective-resolution markets** (weather, economic data) — less adverse selection than political/social markets.
6. **Risk management > alpha.** The kill switch and position limits matter more than the quoting algorithm.
7. **The complementarity constraint** (YES + NO = $1) creates unique opportunities for quoting both sides efficiently.

---

## Further Reading

- Avellaneda & Stoikov (2008) — "High-frequency trading in a limit order book"
- Guéant, Lehalle & Fernandez-Tapia (2012) — "Optimal Portfolio Liquidation with Limit Orders"
- Polymarket CLOB API documentation — https://docs.polymarket.com
- Kalshi API documentation — https://trading-api.readme.io
- Kyle (1985) — "Continuous Auctions and Insider Trading" (foundational adverse selection model)
- Glosten & Milgrom (1985) — "Bid, ask and transaction prices" (information-based spread model)
