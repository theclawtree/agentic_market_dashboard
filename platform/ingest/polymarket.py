"""Polymarket data collector → returns DataFrames ready for parquet."""

import json
import logging

import pandas as pd
import requests
from py_clob_client.client import ClobClient

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"


def fetch_markets(min_volume: float = 10000, max_markets: int = 100) -> pd.DataFrame:
    """Fetch active Polymarket markets as a DataFrame."""
    params: dict[str, str | int] = {
        "limit": max_markets,
        "active": "true",
        "closed": "false",
        "order": "volume24hr",
        "ascending": "false",
    }
    r = requests.get(
        f"{GAMMA_API}/markets",
        params=params,
        timeout=20,
    )
    r.raise_for_status()

    rows = []
    for m in r.json():
        vol = float(m.get("volume24hr", 0) or 0)
        if vol < min_volume:
            continue
        try:
            tokens = json.loads(m.get("clobTokenIds", "[]"))
            prices = json.loads(m.get("outcomePrices", "[]"))
        except (json.JSONDecodeError, TypeError):
            continue
        if len(tokens) < 2 or len(prices) < 2:
            continue

        rows.append(
            {
                "pull_ts": pd.Timestamp.now("UTC"),
                "platform": "polymarket",
                "question": m.get("question", ""),
                "slug": m.get("slug", ""),
                "condition_id": m.get("conditionId", ""),
                "yes_token": tokens[0],
                "no_token": tokens[1],
                "yes_price": float(prices[0]),
                "no_price": float(prices[1]),
                "volume_24h": vol,
                "liquidity": float(m.get("liquidityClob", 0) or 0),
                "volume_total": float(m.get("volume", 0) or 0),
                "end_date": m.get("endDate", ""),
                "spread": None,
                "bid_depth_usd": None,
                "ask_depth_usd": None,
            }
        )

    return pd.DataFrame(rows)


def enrich_order_books(df: pd.DataFrame, top_n: int = 25) -> pd.DataFrame:
    """Add order book data (spread, depth) to top N markets."""
    if df.empty:
        return df

    clob = ClobClient(CLOB_API)

    for idx in df.head(top_n).index:
        token_id = df.at[idx, "yes_token"]
        try:
            book = clob.get_order_book(token_id)
            bids = [(float(b.price), float(b.size)) for b in (book.bids or [])]
            asks = [(float(a.price), float(a.size)) for a in (book.asks or [])]

            if bids and asks:
                best_bid = max(b[0] for b in bids)
                best_ask = min(a[0] for a in asks)
                df.at[idx, "spread"] = best_ask - best_bid
                df.at[idx, "bid_depth_usd"] = sum(p * s for p, s in bids[:5])
                df.at[idx, "ask_depth_usd"] = sum(p * s for p, s in asks[:5])
        except Exception:
            logging.exception("Failed to enrich order book")
            continue

    return df


def collect(cfg: dict) -> pd.DataFrame:
    """Full collection cycle using config."""
    poly_cfg = cfg["ingest"]["polymarket"]
    if not poly_cfg["enabled"]:
        return pd.DataFrame()

    df = fetch_markets(
        min_volume=poly_cfg["min_volume_24h"],
        max_markets=poly_cfg["max_markets"],
    )

    if poly_cfg.get("enrich_books", False) and not df.empty:
        df = enrich_order_books(df, top_n=poly_cfg.get("book_top_n", 25))

    return df


if __name__ == "__main__":
    df = fetch_markets(min_volume=25000, max_markets=20)
    df = enrich_order_books(df, top_n=10)
    print(f"Fetched {len(df)} markets")
    print(df[["question", "yes_price", "volume_24h", "spread"]].head(10).to_string())
