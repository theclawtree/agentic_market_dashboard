"""V1 Informed Trading Bot - Configuration"""
import os

# ─── API Endpoints ────────────────────────────────────────────────────────────
POLYMARKET_GAMMA_API = "https://gamma-api.polymarket.com"
POLYMARKET_CLOB_API = "https://clob.polymarket.com"
KALSHI_API = "https://api.elections.kalshi.com"

# ─── Trading Parameters (from backtest) ──────────────────────────────────────
BANKROLL = 50_000
FEE_RATE = 0.02           # 2% on profits (Polymarket)
KELLY_FRACTION = 0.25     # Quarter-Kelly
MAX_POSITION_PCT = 0.10   # 10% of bankroll per trade
MIN_EDGE = 0.03           # 3% minimum edge to trade
BASE_SLIPPAGE = 0.005     # 0.5% base slippage

# ─── API Keys (from environment) ─────────────────────────────────────────────
POLYMARKET_PRIVATE_KEY = os.environ.get("POLYMARKET_PRIVATE_KEY", "")
KALSHI_API_KEY_ID = os.environ.get("KALSHI_API_KEY_ID", "")
KALSHI_PRIVATE_KEY_PATH = os.environ.get("KALSHI_PRIVATE_KEY_PATH", "")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN", "")
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "30109bb118a449519989b2058ae37c07")

# ─── Signal Categories ───────────────────────────────────────────────────────
CATEGORIES = {
    "fed_decisions": {
        "name": "Fed Decisions",
        "keywords": [
            "federal reserve", "fomc", "fed rate", "interest rate", "rate cut",
            "rate hike", "powell", "monetary policy", "basis points", "bps",
            "dovish", "hawkish", "tightening", "easing", "quantitative",
            "fed funds", "treasury yield", "inflation target"
        ],
        "signal_accuracy": 0.80,
        "avg_adjustment_min": 20,
    },
    "elections": {
        "name": "Elections",
        "keywords": [
            "election", "poll", "ballot", "candidate", "primary", "caucus",
            "electoral", "swing state", "approval rating", "campaign",
            "democrat", "republican", "congress", "senate", "governor",
            "endorsement", "debate", "nomination", "convention"
        ],
        "signal_accuracy": 0.75,
        "avg_adjustment_min": 45,
    },
    "crypto_regulatory": {
        "name": "Crypto Regulatory",
        "keywords": [
            "sec crypto", "bitcoin etf", "crypto regulation", "cftc",
            "stablecoin", "defi regulation", "crypto ban", "cbdc",
            "gensler", "crypto enforcement", "token security",
            "crypto legislation", "digital asset", "blockchain regulation"
        ],
        "signal_accuracy": 0.70,
        "avg_adjustment_min": 30,
    },
    "geopolitical": {
        "name": "Geopolitical",
        "keywords": [
            "war", "ceasefire", "sanctions", "military", "troops",
            "invasion", "peace talks", "nato", "nuclear", "missile",
            "strike", "conflict", "alliance", "treaty", "diplomacy",
            "tariff", "trade war", "embargo"
        ],
        "signal_accuracy": 0.65,
        "avg_adjustment_min": 60,
    },
}
