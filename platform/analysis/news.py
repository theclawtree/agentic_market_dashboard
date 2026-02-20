"""NewsAPI integration — query news for top-ranked markets."""

import logging
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from analysis.ranking import extract_search_terms

NEWSAPI_URL = "https://newsapi.org/v2/everything"


def fetch_news_for_markets(
    top_markets: pd.DataFrame, api_key: str, max_articles: int = 5
) -> pd.DataFrame:
    """
    For each top market, query NewsAPI and return a DataFrame of articles.
    """
    if not api_key:
        return pd.DataFrame()

    all_rows = []
    seen_urls = set()

    for _, row in top_markets.iterrows():
        query = extract_search_terms(row)
        if not query or len(query) < 3:
            continue

        try:
            r = requests.get(
                NEWSAPI_URL,
                params={
                    "apiKey": api_key,
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": max_articles,
                },
                timeout=10,
            )
            if r.status_code != 200:
                continue

            articles = r.json().get("articles", [])
            for a in articles:
                url = a.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                all_rows.append(
                    {
                        "pull_ts": pd.Timestamp.now("UTC"),
                        "market_question": row.get("question", "") or row.get("title", ""),
                        "market_platform": row.get("platform", "unknown"),
                        "search_query": query,
                        "headline": a.get("title", ""),
                        "description": a.get("description", "") or "",
                        "source": a.get("source", {}).get("name", ""),
                        "url": url,
                        "published_at": a.get("publishedAt", ""),
                        "sentiment": None,  # filled by sentiment.py
                        "sentiment_score": None,
                        "relevance": None,
                    }
                )

            time.sleep(0.2)  # rate limit courtesy

        except Exception:
            logging.exception("Failed to fetch news for market")
            continue

    return pd.DataFrame(all_rows)


def collect_news(top_poly: pd.DataFrame, top_kalshi: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Collect news for top markets from both platforms."""
    api_key = cfg["news"]["api_key"]
    max_articles = cfg["news"]["max_articles_per_query"]

    frames = []
    if not top_poly.empty:
        frames.append(fetch_news_for_markets(top_poly, api_key, max_articles))
    if not top_kalshi.empty:
        frames.append(fetch_news_for_markets(top_kalshi, api_key, max_articles))

    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()
