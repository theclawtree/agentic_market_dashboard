"""Shared fixtures for the prediction market platform test suite."""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure platform package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_config(tmp_path):
    """Minimal valid config dict with tmp_path for storage."""
    return {
        "ingest": {
            "interval_minutes": 15,
            "polymarket": {
                "enabled": True,
                "min_volume_24h": 10000,
                "max_markets": 100,
                "enrich_books": False,
                "book_top_n": 25,
            },
            "kalshi": {
                "enabled": True,
                "max_markets": 200,
                "min_volume": 100,
            },
        },
        "storage": {
            "data_dir": str(tmp_path / "data"),
            "retention_days": 30,
            "cleanup_interval_hours": 24,
        },
        "analysis": {
            "top_n_markets": 20,
            "ranking_method": "composite",
            "news_queries_per_market": 1,
        },
        "news": {
            "api_key": "test-key-123",
            "max_articles_per_query": 5,
            "language": "en",
        },
        "llm": {
            "backend": "keyword",
            "api_base": "https://api.openai.com/v1",
            "api_key": "",
            "model": "gpt-4o-mini",
            "ollama_url": "http://localhost:11434",
            "ollama_model": "llama3.2:3b",
            "temperature": 0.1,
            "max_tokens": 300,
        },
        "dashboard": {
            "host": "0.0.0.0",  # noqa: S104
            "port": 8051,
            "auto_refresh_seconds": 300,
        },
        "trading": {
            "bankroll": 50000,
            "fee_rate": 0.02,
            "kelly_fraction": 0.25,
            "max_position_pct": 0.10,
            "min_edge": 0.03,
        },
    }


@pytest.fixture
def poly_df():
    """Sample Polymarket DataFrame."""
    return pd.DataFrame(
        [
            {
                "pull_ts": pd.Timestamp.now("UTC"),
                "platform": "polymarket",
                "question": "Will Bitcoin exceed $100k by March 2026?",
                "slug": "bitcoin-100k-march",
                "condition_id": "0xabc123",
                "yes_token": "token_yes_1",
                "no_token": "token_no_1",
                "yes_price": 0.65,
                "no_price": 0.35,
                "volume_24h": 150000.0,
                "liquidity": 500000.0,
                "volume_total": 2000000.0,
                "end_date": "2026-03-31",
                "spread": 0.02,
                "bid_depth_usd": 5000.0,
                "ask_depth_usd": 4500.0,
            },
            {
                "pull_ts": pd.Timestamp.now("UTC"),
                "platform": "polymarket",
                "question": "Will the Fed cut rates in March 2026?",
                "slug": "fed-rate-cut-march",
                "condition_id": "0xdef456",
                "yes_token": "token_yes_2",
                "no_token": "token_no_2",
                "yes_price": 0.45,
                "no_price": 0.55,
                "volume_24h": 80000.0,
                "liquidity": 300000.0,
                "volume_total": 1000000.0,
                "end_date": "2026-03-15",
                "spread": 0.03,
                "bid_depth_usd": 3000.0,
                "ask_depth_usd": 2800.0,
            },
            {
                "pull_ts": pd.Timestamp.now("UTC"),
                "platform": "polymarket",
                "question": "Will ETH flip BTC market cap?",
                "slug": "eth-flip-btc",
                "condition_id": "0xghi789",
                "yes_token": "token_yes_3",
                "no_token": "token_no_3",
                "yes_price": 0.08,
                "no_price": 0.92,
                "volume_24h": 20000.0,
                "liquidity": 100000.0,
                "volume_total": 500000.0,
                "end_date": "2026-12-31",
                "spread": 0.05,
                "bid_depth_usd": 800.0,
                "ask_depth_usd": 700.0,
            },
        ]
    )


@pytest.fixture
def kalshi_df():
    """Sample Kalshi DataFrame."""
    return pd.DataFrame(
        [
            {
                "pull_ts": pd.Timestamp.now("UTC"),
                "platform": "kalshi",
                "ticker": "FED-26MAR-T4.50",
                "title": "Fed funds rate above 4.50% on March 19?",
                "event_ticker": "FED-26MAR",
                "yes_bid": 62,
                "yes_ask": 65,
                "yes_price": 0.635,
                "spread_cents": 3,
                "volume": 50000,
                "open_interest": 12000,
                "close_time": "2026-03-19T18:00:00Z",
                "category": "Economics",
            },
            {
                "pull_ts": pd.Timestamp.now("UTC"),
                "platform": "kalshi",
                "ticker": "INXD-26FEB28-B5800",
                "title": "S&P 500 above 5800 on Feb 28?",
                "event_ticker": "INXD-26FEB28",
                "yes_bid": 70,
                "yes_ask": 73,
                "yes_price": 0.715,
                "spread_cents": 3,
                "volume": 30000,
                "open_interest": 8000,
                "close_time": "2026-02-28T21:00:00Z",
                "category": "Financials",
            },
        ]
    )


@pytest.fixture
def news_df():
    """Sample news DataFrame."""
    return pd.DataFrame(
        [
            {
                "pull_ts": pd.Timestamp.now("UTC"),
                "market_question": "Will Bitcoin exceed $100k by March 2026?",
                "market_platform": "polymarket",
                "search_query": "Bitcoin exceed 100k March 2026",
                "headline": "Bitcoin Surges Past $95k Amid Institutional Buying",
                "description": (
                    "Major institutions increase Bitcoin holdings"
                    " as price approaches all-time highs."
                ),
                "source": "CoinDesk",
                "url": "https://coindesk.com/article1",
                "published_at": "2026-02-18T10:00:00Z",
                "sentiment": None,
                "sentiment_score": None,
                "relevance": None,
            },
            {
                "pull_ts": pd.Timestamp.now("UTC"),
                "market_question": "Will the Fed cut rates in March 2026?",
                "market_platform": "polymarket",
                "search_query": "Fed cut rates March 2026",
                "headline": "Fed Officials Signal No Rate Cuts Until Inflation Falls",
                "description": (
                    "Multiple Fed governors oppose rate cuts, saying inflation remains too high."
                ),
                "source": "Reuters",
                "url": "https://reuters.com/article2",
                "published_at": "2026-02-18T08:00:00Z",
                "sentiment": None,
                "sentiment_score": None,
                "relevance": None,
            },
        ]
    )


@pytest.fixture
def gamma_api_response():
    """Mock Gamma API response for Polymarket."""
    return [
        {
            "question": "Will Bitcoin hit $100k?",
            "slug": "btc-100k",
            "conditionId": "0xabc",
            "clobTokenIds": '["tok_yes", "tok_no"]',
            "outcomePrices": '["0.65", "0.35"]',
            "volume24hr": "150000",
            "liquidityClob": "500000",
            "volume": "2000000",
            "endDate": "2026-03-31",
        },
        {
            "question": "Will ETH hit $10k?",
            "slug": "eth-10k",
            "conditionId": "0xdef",
            "clobTokenIds": '["tok_yes2", "tok_no2"]',
            "outcomePrices": '["0.30", "0.70"]',
            "volume24hr": "5000",  # Below min_volume
            "liquidityClob": "50000",
            "volume": "200000",
            "endDate": "2026-06-30",
        },
    ]


@pytest.fixture
def kalshi_api_response():
    """Mock Kalshi API response."""
    return {
        "events": [
            {
                "title": "Fed March Meeting",
                "markets": [
                    {
                        "ticker": "FED-26MAR-T4.50",
                        "title": "Fed rate above 4.50%?",
                        "event_ticker": "FED-26MAR",
                        "yes_bid": 62,
                        "yes_ask": 65,
                        "volume": 50000,
                        "open_interest": 12000,
                        "close_time": "2026-03-19T18:00:00Z",
                        "category": "Economics",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def newsapi_response():
    """Mock NewsAPI response."""
    return {
        "status": "ok",
        "totalResults": 2,
        "articles": [
            {
                "title": "Bitcoin Surges Past $95k",
                "description": "Institutional buying increases as BTC nears all-time highs.",
                "source": {"name": "CoinDesk"},
                "url": "https://coindesk.com/btc-surge",
                "publishedAt": "2026-02-18T10:00:00Z",
            },
            {
                "title": "Crypto Market Rally Continues",
                "description": "Positive sentiment across digital assets.",
                "source": {"name": "CryptoNews"},
                "url": "https://cryptonews.com/rally",
                "publishedAt": "2026-02-18T09:00:00Z",
            },
        ],
    }
