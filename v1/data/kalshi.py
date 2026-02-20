"""Kalshi data layer - public REST API"""
import requests
from dataclasses import dataclass
from typing import List, Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import KALSHI_API


@dataclass
class KalshiMarket:
    ticker: str
    title: str
    event_ticker: str
    yes_bid: int  # cents
    yes_ask: int  # cents
    volume: int
    open_interest: int
    category: str = ""
    platform: str = "kalshi"

    @property
    def yes_price(self) -> float:
        return (self.yes_bid + self.yes_ask) / 200.0 if self.yes_bid and self.yes_ask else 0

    @property
    def spread(self) -> float:
        return (self.yes_ask - self.yes_bid) / 100.0 if self.yes_bid and self.yes_ask else 1.0

    @property
    def spread_cents(self) -> int:
        return self.yes_ask - self.yes_bid if self.yes_bid and self.yes_ask else 100


class KalshiClient:
    def __init__(self):
        self.base = KALSHI_API

    def _get(self, path: str, params: dict = None) -> dict:
        r = requests.get(f"{self.base}/trade-api/v2{path}", params=params or {}, timeout=15)
        r.raise_for_status()
        return r.json()

    def get_events(self, limit: int = 50, status: str = "open") -> List[dict]:
        data = self._get("/events", {"limit": limit, "status": status, "with_nested_markets": "true"})
        return data.get("events", [])

    def get_markets(self, limit: int = 100, status: str = "open") -> List[KalshiMarket]:
        """Fetch active markets."""
        data = self._get("/markets", {"limit": limit, "status": "open"})
        markets = []
        for m in data.get("markets", []):
            mkt = KalshiMarket(
                ticker=m.get("ticker", ""),
                title=m.get("title", ""),
                event_ticker=m.get("event_ticker", ""),
                yes_bid=m.get("yes_bid", 0) or 0,
                yes_ask=m.get("yes_ask", 0) or 0,
                volume=m.get("volume", 0) or 0,
                open_interest=m.get("open_interest", 0) or 0,
            )
            if mkt.volume > 0:
                markets.append(mkt)
        markets.sort(key=lambda x: x.volume, reverse=True)
        return markets

    def get_markets_from_events(self, limit: int = 30) -> List[KalshiMarket]:
        """Fetch markets via events endpoint (often gives richer data)."""
        events = self.get_events(limit=limit)
        markets = []
        for e in events:
            for m in e.get("markets", []):
                mkt = KalshiMarket(
                    ticker=m.get("ticker", ""),
                    title=m.get("title", "") or e.get("title", ""),
                    event_ticker=m.get("event_ticker", ""),
                    yes_bid=m.get("yes_bid", 0) or 0,
                    yes_ask=m.get("yes_ask", 0) or 0,
                    volume=m.get("volume", 0) or 0,
                    open_interest=m.get("open_interest", 0) or 0,
                )
                if mkt.volume > 0:
                    markets.append(mkt)
        markets.sort(key=lambda x: x.volume, reverse=True)
        return markets

    def get_orderbook(self, ticker: str) -> dict:
        """Get order book for a market (may need auth for full depth)."""
        try:
            data = self._get(f"/markets/{ticker}/orderbook")
            return data.get("orderbook", {})
        except Exception:
            return {}


if __name__ == "__main__":
    client = KalshiClient()
    print("Fetching active Kalshi markets...")
    markets = client.get_markets_from_events(limit=30)
    print(f"Found {len(markets)} markets with volume\n")
    
    for i, m in enumerate(markets[:15]):
        print(f"{i+1:2}. [{m.ticker}] {m.title[:65]}")
        print(f"    Yes: {m.yes_bid}¢/{m.yes_ask}¢  |  Spread: {m.spread_cents}¢  |  Vol: {m.volume:,}  |  OI: {m.open_interest:,}")
        print()
