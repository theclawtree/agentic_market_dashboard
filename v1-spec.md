# V1 Informed Trading Bot - Spec

## Goal
Automated informed trading on Polymarket (and later Kalshi) targeting the 78% annual return from our backtest. Read-only data layer first, then execution.

## Architecture

```
v1/
├── config.py          # API endpoints, constants, env vars
├── data/
│   ├── polymarket.py  # Polymarket Gamma API + CLOB client (read-only)
│   ├── kalshi.py      # Kalshi public market data API (read-only)
│   └── news.py        # News signal ingestion (Twitter/RSS/govt feeds stubs)
├── signals/
│   ├── feed.py        # Unified signal feed (combines all news sources)
│   └── classifier.py  # NLP signal classifier (keyword + LLM hybrid)
├── strategy/
│   ├── engine.py      # Core strategy: match signals to markets, calc edge
│   └── sizing.py      # Kelly criterion position sizing
├── execution/
│   ├── polymarket.py  # Polymarket order placement (needs wallet key)
│   └── paper.py       # Paper trading simulator
├── risk/
│   └── manager.py     # Position limits, kill switch, max loss
├── monitor/
│   └── dashboard.py   # CLI dashboard showing markets, signals, P&L
└── main.py            # Entry point - ties everything together
```

## Phase 1 (Build Now - No Auth Needed)
1. **Polymarket data layer** - fetch active markets, order books, prices via Gamma API + py-clob-client
2. **Kalshi data layer** - fetch events, markets, prices via public REST API
3. **Market scanner** - find high-volume, liquid markets across both platforms
4. **Signal classifier stub** - keyword-based signal scoring for Fed/elections/crypto
5. **Paper trading engine** - simulate trades with realistic slippage/fees
6. **CLI monitor** - show top markets, spreads, signals in terminal

## Phase 2 (Needs User Input)
- Polymarket wallet private key for trading
- Kalshi API key (RSA key pair) for authenticated endpoints
- News API keys (Twitter API, NewsAPI.org, etc.)

## Key Parameters (from backtest)
- Fee rate: 2% on profits
- Kelly fraction: 0.25
- Max position: 10% of bankroll
- Min edge threshold: 3%
- Target categories: Fed decisions (best), elections, crypto regulatory
- Speed target: <1 minute signal-to-trade

## Dependencies (already installed)
- py-clob-client (Polymarket CLOB)
- requests, aiohttp, websockets
- Standard lib: json, asyncio, dataclasses

## Important API Details

### Polymarket
- Gamma API (market discovery): `https://gamma-api.polymarket.com/markets`
- CLOB API (order books/trading): `https://clob.polymarket.com`
- Token IDs are JSON arrays in `clobTokenIds` field - must json.loads() them
- Read-only: no auth needed. Trading: needs Polygon wallet private key + USDC

### Kalshi
- Base URL: `https://api.elections.kalshi.com`
- Events: `GET /trade-api/v2/events?status=open&with_nested_markets=true`
- Markets: `GET /trade-api/v2/markets`
- Read-only: no auth needed. Trading: needs RSA key pair from account settings
- Auth: KALSHI-ACCESS-KEY + KALSHI-ACCESS-TIMESTAMP + KALSHI-ACCESS-SIGNATURE headers
