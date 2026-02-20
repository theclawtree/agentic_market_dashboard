"""FastAPI dashboard server."""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

sys.path.insert(0, str(Path(__file__).parent.parent))
from config_loader import get_config
from storage.writer import list_parquet_files

app = FastAPI(title="Prediction Market Platform")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def load_latest(source: str) -> pd.DataFrame:
    cfg = get_config()
    files = list_parquet_files(cfg["storage"]["data_dir"], source, days_back=1)
    if not files:
        return pd.DataFrame()
    return pd.read_parquet(files[-1])


def load_analysis() -> pd.DataFrame:
    cfg = get_config()
    files = list_parquet_files(cfg["storage"]["data_dir"], "analysis", days_back=1)
    if not files:
        return pd.DataFrame()
    return pd.read_parquet(files[-1])


def load_news() -> pd.DataFrame:
    cfg = get_config()
    files = list_parquet_files(cfg["storage"]["data_dir"], "news", days_back=1)
    if not files:
        return pd.DataFrame()
    # Load all today's news
    dfs = [pd.read_parquet(f) for f in files[-5:]]  # last 5 files
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["url"])


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    cfg = get_config()

    poly_df = load_latest("polymarket")
    kalshi_df = load_latest("kalshi")
    news_df = load_news()
    analysis_df = load_analysis()
    analysis_df = analysis_df[analysis_df["question"].notnull()]
    analysis_df = analysis_df.fillna("0")

    print(analysis_df.volume.unique())

    # Build opportunity list from analysis
    opportunities = []

    if not analysis_df.empty:
        # Merge news sentiment into market rankings
        for _, row in analysis_df.iterrows():
            question = row.get("question", "") or row.get("title", "")

            # Find news for this market
            market_news = pd.DataFrame()
            if not news_df.empty and "market_question" in news_df.columns:
                market_news = news_df[
                    news_df["market_question"].str.contains(question, case=False, na=False)
                ]

            has_scores = not market_news.empty and "sentiment_score" in market_news.columns
            avg_sentiment = market_news["sentiment_score"].mean() if has_scores else 0
            dominant = "neutral"
            if avg_sentiment > 0.15:
                dominant = "bullish"
            elif avg_sentiment < -0.15:
                dominant = "bearish"

            spread_val = row.get("spread", None)
            spread_cents_val = row.get("spread_cents", None)
            if row.get("platform") == "kalshi":
                spread_display = (
                    f"{int(spread_cents_val)}¢" if pd.notna(spread_cents_val) else "N/A"
                )
            else:
                spread_display = f"{spread_val:.3f}" if pd.notna(spread_val) else "N/A"

            opportunities.append(
                {
                    "platform": row.get("platform", "?"),
                    "question": question[:80],
                    "yes_price": row.get("yes_price", 0),
                    "volume": float(
                        row.get("volume_24h", 0)
                        if pd.notna(row.get("volume_24h"))
                        else row.get("volume", 0)
                        if pd.notna(row.get("volume"))
                        else 0
                    ),
                    "spread_display": spread_display,
                    "opportunity_score": row.get("opportunity_score", 0),
                    "sentiment": dominant,
                    "news_count": len(market_news),
                }
            )

    # Format news items
    news_items = []
    if not news_df.empty:
        for _, row in news_df.sort_values("relevance", ascending=False).head(30).iterrows():
            news_items.append(
                {
                    "sentiment": row.get("sentiment", "neutral"),
                    "sentiment_score": row.get("sentiment_score", 0) or 0,
                    "relevance": row.get("relevance", 0) or 0,
                    "headline": (row.get("headline", "") or "")[:100],
                    "source": row.get("source", ""),
                    "url": row.get("url", "#"),
                    "market_question": (row.get("market_question", "") or "")[:60],
                }
            )

    # Format market lists
    poly_list = []
    if not poly_df.empty:
        for _, row in poly_df.head(15).iterrows():
            spread = row.get("spread")
            poly_list.append(
                {
                    "question": (row.get("question", "") or "")[:70],
                    "yes_price": float(row.get("yes_price", 0) or 0),
                    "spread_display": f"{spread:.3f}" if pd.notna(spread) else "N/A",
                    "volume_24h": float(row.get("volume_24h", 0) or 0),
                    "liquidity": float(row.get("liquidity", 0) or 0),
                }
            )

    kalshi_list = []
    if not kalshi_df.empty:
        for _, row in kalshi_df.head(15).iterrows():
            kalshi_list.append(
                {
                    "title": (row.get("title", "") or "")[:70],
                    "yes_price": float(row.get("yes_price", 0) or 0),
                    "spread_cents": int(row.get("spread_cents", 0) or 0),
                    "volume": int(row.get("volume", 0) or 0),
                    "open_interest": int(row.get("open_interest", 0) or 0),
                }
            )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "refresh_interval": cfg["dashboard"]["auto_refresh_seconds"],
            "retention_days": cfg["storage"]["retention_days"],
            "llm_backend": cfg["llm"]["backend"],
            "poly_count": len(poly_df),
            "kalshi_count": len(kalshi_df),
            "news_count": len(news_df),
            "opp_count": len(opportunities),
            "opportunities": opportunities,
            "news_items": news_items,
            "poly_markets": poly_list,
            "kalshi_markets": kalshi_list,
        },
    )


@app.get("/api/markets")
async def api_markets():
    poly = load_latest("polymarket")
    kalshi = load_latest("kalshi")
    return {
        "polymarket": poly.to_dict(orient="records") if not poly.empty else [],
        "kalshi": kalshi.to_dict(orient="records") if not kalshi.empty else [],
    }


@app.get("/api/opportunities")
async def api_opportunities():
    analysis = load_analysis()
    return analysis.to_dict(orient="records") if not analysis.empty else []


@app.get("/api/news")
async def api_news():
    news = load_news()
    return news.to_dict(orient="records") if not news.empty else []
