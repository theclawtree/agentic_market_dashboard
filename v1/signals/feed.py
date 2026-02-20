"""News signal feed - aggregates signals from multiple sources."""
import time
import requests
from dataclasses import dataclass
from typing import List, Callable
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEWSAPI_KEY, TWITTER_BEARER_TOKEN


@dataclass
class RawNewsItem:
    text: str
    source: str
    url: str = ""
    timestamp: float = 0.0


class FedRSSFeed:
    """Monitor Federal Reserve press releases (free, no auth)."""
    URL = "https://www.federalreserve.gov/feeds/press_all.xml"
    
    def __init__(self):
        self.seen_urls = set()
    
    def fetch(self) -> List[RawNewsItem]:
        try:
            import xml.etree.ElementTree as ET
            r = requests.get(self.URL, timeout=10)
            root = ET.fromstring(r.content)
            items = []
            for entry in root.findall(".//item")[:15]:
                title = entry.findtext("title", "")
                link = entry.findtext("link", "")
                if link in self.seen_urls:
                    continue
                self.seen_urls.add(link)
                desc = entry.findtext("description", "")
                items.append(RawNewsItem(
                    text=f"{title}. {desc}".strip(),
                    source="federal_reserve",
                    url=link,
                    timestamp=time.time(),
                ))
            return items
        except Exception as e:
            return []


class NewsAPIFeed:
    """NewsAPI.org headlines (free tier: 100 req/day)."""
    URL = "https://newsapi.org/v2/top-headlines"
    
    def __init__(self):
        self.seen_urls = set()
    
    def fetch(self, query: str = None, category: str = "business") -> List[RawNewsItem]:
        if not NEWSAPI_KEY:
            return []
        params = {"apiKey": NEWSAPI_KEY, "language": "en", "pageSize": 20}
        if query:
            params["q"] = query
        else:
            params["category"] = category
            params["country"] = "us"
        try:
            r = requests.get(self.URL, params=params, timeout=10)
            data = r.json()
            items = []
            for a in data.get("articles", []):
                url = a.get("url", "")
                if url in self.seen_urls:
                    continue
                self.seen_urls.add(url)
                title = a.get("title", "")
                desc = a.get("description", "") or ""
                source_name = a.get("source", {}).get("name", "newsapi")
                items.append(RawNewsItem(
                    text=f"{title}. {desc}".strip(),
                    source=source_name.lower().replace(" ", "_"),
                    url=url,
                    timestamp=time.time(),
                ))
            return items
        except Exception:
            return []


class FREDFeed:
    """FRED economic data releases (free, no auth needed for basic)."""
    URL = "https://api.stlouisfed.org/fred"
    
    def fetch_latest(self, series_id: str = "FEDFUNDS") -> List[RawNewsItem]:
        """Fetch latest value of a FRED series."""
        # Note: FRED API needs a key for most endpoints. 
        # Without key, we can still scrape release calendar.
        return []


class SignalFeed:
    """Unified signal feed combining all sources."""
    
    def __init__(self):
        self.fed_rss = FedRSSFeed()
        self.news_api = NewsAPIFeed()
        self.callbacks: List[Callable] = []
    
    def on_signal(self, callback: Callable):
        self.callbacks.append(callback)
    
    def poll_all(self) -> List[RawNewsItem]:
        """Poll all sources once and return new items."""
        items = []
        
        # Fed RSS
        items.extend(self.fed_rss.fetch())
        
        # NewsAPI (if key available)
        if NEWSAPI_KEY:
            items.extend(self.news_api.fetch(category="business"))
            for q in [
                "federal reserve OR FOMC OR rate cut OR rate hike",
                "election OR poll OR primary OR candidate",
                "SEC crypto OR bitcoin ETF OR crypto regulation",
                "Iran OR Ukraine OR ceasefire OR sanctions OR tariff",
            ]:
                items.extend(self.news_api.fetch(query=q))
        
        for item in items:
            for cb in self.callbacks:
                cb(item)
        
        return items


if __name__ == "__main__":
    feed = SignalFeed()
    print("Polling signal sources...\n")
    
    items = feed.poll_all()
    print(f"Fed RSS: {len(feed.fed_rss.seen_urls)} items")
    print(f"NewsAPI: {'configured' if NEWSAPI_KEY else 'no key (set NEWSAPI_KEY)'}")
    print(f"Total new items: {len(items)}\n")
    
    for item in items[:10]:
        print(f"[{item.source}] {item.text[:100]}...")
        print()
