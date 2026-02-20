"""Rank markets by return potential — identifies best opportunities."""
import pandas as pd
import numpy as np


def rank_polymarket(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Rank Polymarket markets by composite opportunity score.
    
    Factors:
    - Volume (higher = more liquid, easier to trade)
    - Tight spread (lower = less slippage cost)
    - Mid-range price (20-80¢ = more room for movement)
    - Book depth (deeper = can trade larger size)
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Normalize factors to 0-1 scale
    if "volume_24h" in df.columns:
        vmax = df["volume_24h"].max()
        df["vol_score"] = df["volume_24h"] / vmax if vmax > 0 else 0
    else:
        df["vol_score"] = 0
    
    # Spread score (lower is better, invert)
    if "spread" in df.columns and df["spread"].notna().any():
        df["spread_score"] = 1 - df["spread"].fillna(1.0).clip(0, 0.2) / 0.2
    else:
        df["spread_score"] = 0.5
    
    # Price range score (peaks at 0.5, drops near 0 or 1)
    if "yes_price" in df.columns:
        df["range_score"] = 1 - 4 * (df["yes_price"] - 0.5).pow(2)
        df["range_score"] = df["range_score"].clip(0, 1)
    else:
        df["range_score"] = 0.5
    
    # Depth score
    if "bid_depth_usd" in df.columns and df["bid_depth_usd"].notna().any():
        dmax = df["bid_depth_usd"].dropna().max()
        df["depth_score"] = df["bid_depth_usd"].fillna(0) / dmax if dmax > 0 else 0
    else:
        df["depth_score"] = 0.5
    
    # Composite score (weighted)
    df["opportunity_score"] = (
        0.30 * df["vol_score"] +
        0.25 * df["spread_score"] +
        0.25 * df["range_score"] +
        0.20 * df["depth_score"]
    )
    
    return df.sort_values("opportunity_score", ascending=False).head(top_n).reset_index(drop=True)


def rank_kalshi(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Rank Kalshi markets by opportunity score."""
    if df.empty:
        return df
    
    df = df.copy()
    
    vmax = df["volume"].max()
    df["vol_score"] = df["volume"] / vmax if vmax > 0 else 0
    
    # Spread (cents) — lower is better
    df["spread_score"] = 1 - df["spread_cents"].clip(0, 20) / 20
    
    # Price range
    df["range_score"] = 1 - 4 * (df["yes_price"] - 0.5).pow(2)
    df["range_score"] = df["range_score"].clip(0, 1)
    
    df["opportunity_score"] = (
        0.40 * df["vol_score"] +
        0.30 * df["spread_score"] +
        0.30 * df["range_score"]
    )
    
    return df.sort_values("opportunity_score", ascending=False).head(top_n).reset_index(drop=True)


def extract_search_terms(row: pd.Series) -> str:
    """Extract search-friendly terms from a market question/title."""
    text = row.get("question", "") or row.get("title", "")
    # Remove common filler
    for w in ["Will", "will", "the", "be", "by", "in", "of", "a", "an", "?"]:
        text = text.replace(w, " ")
    # Collapse whitespace, trim
    return " ".join(text.split()[:6]).strip()
