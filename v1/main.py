#!/usr/bin/env python3
"""
V1 Informed Trading Bot - Main Entry Point
Paper trading mode by default. Scans markets, processes signals, generates trades.
"""
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.polymarket import PolymarketClient
from data.kalshi import KalshiClient
from signals.feed import SignalFeed
from signals.classifier import SignalClassifier
from strategy.engine import StrategyEngine
from execution.paper import PaperTrader
from risk.manager import RiskManager
from config import BANKROLL


def print_header():
    print("""
    V1 Informed Trading Bot - Paper Mode
    Polymarket + Kalshi Market Scanner  
    """)


def scan_markets():
    """Scan both platforms and return top markets."""
    print("📊 Scanning Polymarket...")
    poly_client = PolymarketClient()
    poly_markets = poly_client.get_active_markets(limit=30, min_volume=25000)
    poly_markets = poly_client.enrich_with_books(poly_markets, top_n=15)
    print(f"   Found {len(poly_markets)} active markets")

    print("📊 Scanning Kalshi...")
    kalshi_client = KalshiClient()
    kalshi_markets = kalshi_client.get_markets_from_events(limit=30)
    print(f"   Found {len(kalshi_markets)} active markets")

    return poly_markets, kalshi_markets


def print_market_table(poly_markets, kalshi_markets):
    """Print top markets from both platforms."""
    print(f"\n{'─'*30}")
    print(f"  TOP POLYMARKET MARKETS (by 24h volume)")
    print(f"{'─'*30}")
    print(f"  {'#':>2}  {'Market':<20} {'YES':>6} {'Spread':>7} {'Vol24h':>12}")
    print(f"  {'─'*2}  {'─'*55} {'─'*6} {'─'*7} {'─'*12}")
    
    for i, m in enumerate(poly_markets[:12]):
        q = m.question[:55]
        spread = f"{m.spread:.3f}" if m.spread > 0 else "N/A"
        print(f"  {i+1:2}  {q:<20} {m.yes_price:6.3f} {spread:>7} ${m.volume_24h:>10,.0f}")

    print(f"\n{'─'*30}")
    print(f"  TOP KALSHI MARKETS (by volume)")
    print(f"{'─'*30}")
    print(f"  {'#':>2}  {'Market':<20} {'Yes':>6} {'Spread':>7} {'Volume':>10}")
    print(f"  {'─'*2}  {'─'*55} {'─'*6} {'─'*7} {'─'*10}")
    
    for i, m in enumerate(kalshi_markets[:12]):
        t = m.title[:55]
        print(f"  {i+1:2}  {t:<20} {m.yes_price:6.2f} {m.spread_cents:>5}¢  {m.volume:>10,}")


def print_signals(signals):
    """Print detected signals."""
    if not signals:
        print("\n  📭 No signals detected (Fed RSS only without API keys)")
        return
    
    print(f"\n{'─'*30}")
    print(f"  ACTIVE SIGNALS")
    print(f"{'─'*30}")
    for s in signals[:10]:
        arrow = "🟢↑" if s.direction > 0 else "🔴↓" if s.direction < 0 else "⚪→"
        print(f"  {arrow} [{s.category_name}] conf={s.confidence:.2f} dir={s.direction:+.2f}")
        print(f"     {s.text[:85]}...")
        print()


def print_decisions(decisions):
    """Print trade decisions."""
    if not decisions:
        print("\n  📭 No trade opportunities found (need stronger signals)")
        return
    
    print(f"\n{'─'*30}")
    print(f"  TRADE DECISIONS (paper mode)")
    print(f"{'─'*30}")
    for d in decisions[:5]:
        arrow = "🟢 BUY YES" if d.direction == "buy_yes" else "🔴 BUY NO"
        print(f"  {arrow}: ${d.size_usd:,.0f}")
        print(f"     Market: {d.market_question[:70]}")
        print(f"     Price: {d.market_price:.3f} → Est: {d.estimated_prob:.3f} | Edge: {d.edge:+.2%} | Slippage: {d.slippage:.3f}")
        print()


def run_once():
    """Run one full cycle: scan → signals → decisions → paper trade."""
    print_header()
    
    # 1. Scan markets
    poly_markets, kalshi_markets = scan_markets()
    print_market_table(poly_markets, kalshi_markets)
    
    # 2. Gather signals
    print("\n📡 Polling signal feeds...")
    feed = SignalFeed()
    raw_items = feed.poll_all()
    print(f"   Raw news items: {len(raw_items)}")
    
    # 3. Classify signals
    classifier = SignalClassifier()
    all_signals = []
    for item in raw_items:
        signals = classifier.classify(item.text, item.source)
        all_signals.extend(signals)
    print(f"   Classified signals: {len(all_signals)}")
    print_signals(all_signals)
    
    # 4. Generate trade decisions
    engine = StrategyEngine(bankroll=BANKROLL)
    decisions = engine.generate_decisions(all_signals, poly_markets)
    print_decisions(decisions)
    
    # 5. Paper execute
    risk = RiskManager()
    paper = PaperTrader()
    executed = 0
    
    for d in decisions:
        approved, reason = risk.check_trade(d, paper.bankroll)
        if approved:
            paper.execute(d)
            risk.record_trade(d)
            executed += 1
        else:
            print(f"  ⚠️  Blocked: {reason} | {d.market_question[:50]}")
    
    if executed:
        print(f"\n  ✅ Executed {executed} paper trades")
    
    paper.print_summary()
    
    # Status
    print(f"  Risk Status: {risk.status()}")
    print(f"\n  💡 To improve signals, set these env vars:")
    print(f"     NEWSAPI_KEY=<your-key>        (newsapi.org, free tier)")
    print(f"     TWITTER_BEARER_TOKEN=<token>  (developer.twitter.com, $100/mo)")
    print()
    
    return poly_markets, kalshi_markets, all_signals, decisions


def run_loop(interval_sec: int = 300):
    """Run continuously, polling every interval."""
    print(f"Starting continuous loop (polling every {interval_sec}s)...")
    while True:
        try:
            run_once()
            print(f"\n⏰ Next scan in {interval_sec}s... (Ctrl+C to stop)")
            time.sleep(interval_sec)
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down gracefully.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print(f"   Retrying in 60s...")
            time.sleep(60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--loop":
        run_loop()
    else:
        run_once()
