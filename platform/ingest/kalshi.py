"""Kalshi data collector → returns DataFrames ready for parquet."""

import pandas as pd
import requests

KALSHI_API = "https://api.elections.kalshi.com"


def fetch_markets(max_markets: int = 200, min_volume: int = 100) -> pd.DataFrame:
    """Fetch active Kalshi markets via events endpoint."""
    r = requests.get(
        f"{KALSHI_API}/trade-api/v2/events",
        params={"limit": 50, "status": "open", "with_nested_markets": "true"},
        timeout=20,
    )
    r.raise_for_status()

    rows = []
    for e in r.json().get("events", []):
        for m in e.get("markets", []):
            vol = m.get("volume", 0) or 0
            if vol < min_volume:
                continue
            yes_bid = m.get("yes_bid", 0) or 0
            yes_ask = m.get("yes_ask", 0) or 0

            rows.append(
                {
                    "pull_ts": pd.Timestamp.now("UTC"),
                    "platform": "kalshi",
                    "ticker": m.get("ticker", ""),
                    "title": m.get("title", "") or e.get("title", ""),
                    "event_ticker": m.get("event_ticker", ""),
                    "yes_bid": yes_bid,
                    "yes_ask": yes_ask,
                    "yes_price": (yes_bid + yes_ask) / 200.0 if yes_bid and yes_ask else 0,
                    "spread_cents": yes_ask - yes_bid if yes_bid and yes_ask else 100,
                    "volume": vol,
                    "open_interest": m.get("open_interest", 0) or 0,
                    "close_time": m.get("close_time", ""),
                    "category": m.get("category", ""),
                }
            )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("volume", ascending=False).head(max_markets).reset_index(drop=True)
    return df


def collect(cfg: dict) -> pd.DataFrame:
    """Full collection cycle using config."""
    k_cfg = cfg["ingest"]["kalshi"]
    if not k_cfg["enabled"]:
        return pd.DataFrame()
    return fetch_markets(
        max_markets=k_cfg["max_markets"],
        min_volume=k_cfg.get("min_volume", 100),
    )


if __name__ == "__main__":
    df = fetch_markets(max_markets=20, min_volume=500)
    print(f"Fetched {len(df)} markets")
    print(df[["title", "yes_price", "spread_cents", "volume"]].head(10).to_string())
