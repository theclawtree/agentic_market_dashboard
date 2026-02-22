#!/usr/bin/env python3
"""
Prediction Market Platform — Full Pipeline
Ingest → Store → Rank → News → Sentiment → Dashboard

Usage:
    python3 platform/main.py              # Run once
    python3 platform/main.py --loop       # Run continuously
    python3 platform/main.py --dashboard  # Run once + start dashboard
"""
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import get_config
from ingest.polymarket import collect as collect_poly
from ingest.kalshi import collect as collect_kalshi
from storage.writer import write_parquet
from storage.cleanup import cleanup
from analysis.ranking import rank_polymarket, rank_kalshi
from analysis.news import collect_news
from analysis.sentiment import analyze_news_df


def run_pipeline(cfg: dict = None) -> dict:
    """Run full pipeline once. Returns summary stats."""
    cfg = cfg or get_config()
    data_dir = cfg["storage"]["data_dir"]
    now = datetime.now(timezone.utc)
    
    print(f"\n{'='*70}")
    print(f"  Pipeline Run: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*70}")
    
    # ── 1. Ingest ─────────────────────────────────────────────────────────────
    print("\n📊 [1/5] Ingesting market data...")
    
    poly_df = collect_poly(cfg)
    poly_path = write_parquet(poly_df, data_dir, "polymarket")
    print(f"   Polymarket: {len(poly_df)} markets → {poly_path}")
    
    kalshi_df = collect_kalshi(cfg)
    kalshi_path = write_parquet(kalshi_df, data_dir, "kalshi")
    print(f"   Kalshi:     {len(kalshi_df)} markets → {kalshi_path}")
    
    # ── 2. Rank ───────────────────────────────────────────────────────────────
    print("\n🏆 [2/5] Ranking markets by opportunity...")
    top_n = cfg["analysis"]["top_n_markets"]
    
    top_poly = rank_polymarket(poly_df, top_n=top_n)
    top_kalshi = rank_kalshi(kalshi_df, top_n=top_n)
    
    # Save ranked analysis
    analysis_frames = []
    if not top_poly.empty:
        analysis_frames.append(top_poly)
    if not top_kalshi.empty:
        analysis_frames.append(top_kalshi)
    
    if analysis_frames:
        import pandas as pd
        # Unify columns for combined analysis file
        combined = pd.concat(analysis_frames, ignore_index=True)
        write_parquet(combined, data_dir, "analysis")
    
    print(f"   Top Polymarket: {len(top_poly)} markets")
    print(f"   Top Kalshi:     {len(top_kalshi)} markets")
    
    if not top_poly.empty:
        print(f"\n   Polymarket Top 5:")
        for _, r in top_poly.head(5).iterrows():
            q = (r.get("question", "") or "")[:55]
            print(f"     {r.get('opportunity_score', 0):.2f}  {q}  YES={r.get('yes_price', 0):.3f}")
    
    # ── 3. News ───────────────────────────────────────────────────────────────
    print("\n📰 [3/5] Fetching news for top markets...")
    news_df = collect_news(top_poly, top_kalshi, cfg)
    print(f"   Articles found: {len(news_df)}")
    
    # ── 4. Sentiment ──────────────────────────────────────────────────────────
    print(f"\n🧠 [4/5] Running sentiment analysis ({cfg['llm']['backend']})...")
    if not news_df.empty:
        news_df = analyze_news_df(news_df, cfg)
        news_path = write_parquet(news_df, data_dir, "news")
        
        bullish = (news_df["sentiment"] == "bullish").sum()
        bearish = (news_df["sentiment"] == "bearish").sum()
        neutral = (news_df["sentiment"] == "neutral").sum()
        print(f"   Results: 🟢 {bullish} bullish | 🔴 {bearish} bearish | ⚪ {neutral} neutral")
        print(f"   Saved → {news_path}")
        
        # Show top sentiment signals
        high_rel = news_df[news_df["relevance"] > 0.2].sort_values("relevance", ascending=False)
        if not high_rel.empty:
            print(f"\n   Top signals:")
            for _, r in high_rel.head(5).iterrows():
                emoji = "🟢" if r["sentiment"] == "bullish" else "🔴" if r["sentiment"] == "bearish" else "⚪"
                print(f"     {emoji} [{r.get('source', ''):15}] {r.get('headline', '')[:65]}")
    else:
        print("   No articles to analyze.")
    
    # ── 5. Cleanup ────────────────────────────────────────────────────────────
    print(f"\n🗑️  [5/5] Cleanup (retention: {cfg['storage']['retention_days']}d)...")
    removed = cleanup(data_dir, cfg["storage"]["retention_days"])
    print(f"   Removed {removed} old directories.")
    
    # ── Summary ───────────────────────────────────────────────────────────────
    summary = {
        "timestamp": now.isoformat(),
        "polymarket_markets": len(poly_df),
        "kalshi_markets": len(kalshi_df),
        "news_articles": len(news_df),
        "opportunities": len(top_poly) + len(top_kalshi),
    }
    
    print(f"\n{'='*70}")
    print(f"  ✅ Pipeline complete | {summary['polymarket_markets']} poly | {summary['kalshi_markets']} kalshi | {summary['news_articles']} news")
    print(f"{'='*70}")
    
    return summary


def run_loop(cfg: dict = None):
    """Run pipeline continuously at configured interval."""
    cfg = cfg or get_config()
    interval = cfg["ingest"]["interval_minutes"] * 60
    
    print(f"Starting continuous pipeline (every {cfg['ingest']['interval_minutes']} min)...")
    print(f"Dashboard: http://localhost:{cfg['dashboard']['port']}")
    
    while True:
        try:
            run_pipeline(cfg)
            print(f"\n⏰ Next run in {cfg['ingest']['interval_minutes']} min... (Ctrl+C to stop)\n")
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 Shutting down.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print("Retrying in 60s...")
            time.sleep(60)


if __name__ == "__main__":
    cfg = get_config()
    
    if "--loop" in sys.argv:
        run_loop(cfg)
    elif "--dashboard" in sys.argv:
        run_pipeline(cfg)
        import uvicorn
        from dashboard.app import app
        print(f"\n🌐 Starting dashboard at http://localhost:{cfg['dashboard']['port']}")
        uvicorn.run(app, host=cfg["dashboard"]["host"], port=cfg["dashboard"]["port"])
    else:
        run_pipeline(cfg)
