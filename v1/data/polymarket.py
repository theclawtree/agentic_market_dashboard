"""Polymarket data layer - Gamma API + CLOB client"""
import json
import requests
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import BookParams
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import POLYMARKET_GAMMA_API, POLYMARKET_CLOB_API


@dataclass
class PolyMarket:
    question: str
    condition_id: str
    slug: str
    yes_token: str
    no_token: str
    yes_price: float
    no_price: float
    volume_24h: float
    liquidity: float
    outcomes: List[str]
    category: str = ""
    platform: str = "polymarket"
    spread: float = 0.0
    book_depth_usd: float = 0.0

    @property
    def mid_price(self) -> float:
        return self.yes_price


@dataclass
class OrderBookLevel:
    price: float
    size: float


@dataclass
class OrderBook:
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    spread: float = 0.0
    depth_usd: float = 0.0


class PolymarketClient:
    def __init__(self):
        self.gamma_url = POLYMARKET_GAMMA_API
        self.clob = ClobClient(POLYMARKET_CLOB_API)

    def get_active_markets(self, limit: int = 50, min_volume: float = 10000) -> List[PolyMarket]:
        """Fetch active markets sorted by 24h volume."""
        r = requests.get(
            f"{self.gamma_url}/markets",
            params={
                "limit": limit,
                "active": "true",
                "closed": "false",
                "order": "volume24hr",
                "ascending": "false",
            },
            timeout=15,
        )
        r.raise_for_status()
        markets = []
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
            
            mkt = PolyMarket(
                question=m.get("question", ""),
                condition_id=m.get("conditionId", ""),
                slug=m.get("slug", ""),
                yes_token=tokens[0],
                no_token=tokens[1],
                yes_price=float(prices[0]),
                no_price=float(prices[1]),
                volume_24h=vol,
                liquidity=float(m.get("liquidityClob", 0) or 0),
                outcomes=m.get("outcomes", ["Yes", "No"]),
            )
            markets.append(mkt)
        return markets

    def get_order_book(self, token_id: str) -> Optional[OrderBook]:
        """Fetch full order book for a token."""
        try:
            book = self.clob.get_order_book(token_id)
        except Exception:
            return None

        bids = [OrderBookLevel(float(b.price), float(b.size)) for b in (book.bids or [])]
        asks = [OrderBookLevel(float(a.price), float(a.size)) for a in (book.asks or [])]
        # Sort: bids descending, asks ascending
        bids.sort(key=lambda x: x.price, reverse=True)
        asks.sort(key=lambda x: x.price)

        spread = (asks[0].price - bids[0].price) if bids and asks else 1.0
        # Estimate depth as sum of top 5 levels on each side
        bid_depth = sum(b.price * b.size for b in bids[:5])
        ask_depth = sum(a.price * a.size for a in asks[:5])

        return OrderBook(bids=bids, asks=asks, spread=spread, depth_usd=bid_depth + ask_depth)

    def get_midpoint(self, token_id: str) -> Optional[float]:
        try:
            result = self.clob.get_midpoint(token_id)
            return float(result.get("mid", 0))
        except Exception:
            return None

    def enrich_with_books(self, markets: List[PolyMarket], top_n: int = 20) -> List[PolyMarket]:
        """Add order book data to top N markets."""
        for mkt in markets[:top_n]:
            book = self.get_order_book(mkt.yes_token)
            if book:
                mkt.spread = book.spread
                mkt.book_depth_usd = book.depth_usd
        return markets


if __name__ == "__main__":
    client = PolymarketClient()
    print("Fetching active Polymarket markets...")
    markets = client.get_active_markets(limit=20, min_volume=50000)
    print(f"Found {len(markets)} markets with >$50K 24h volume\n")
    
    for i, m in enumerate(markets[:10]):
        book = client.get_order_book(m.yes_token)
        spread_str = f"{book.spread:.3f}" if book else "N/A"
        depth_str = f"${book.depth_usd:,.0f}" if book else "N/A"
        print(f"{i+1:2}. {m.question[:70]}")
        print(f"    YES: {m.yes_price:.3f}  |  Vol24h: ${m.volume_24h:,.0f}  |  Spread: {spread_str}  |  Depth: {depth_str}")
        print()
