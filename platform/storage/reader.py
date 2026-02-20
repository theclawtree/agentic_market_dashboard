"""Parquet reader — load and query stored market data."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from storage.writer import list_parquet_files


def read_latest(data_dir: str, source: str) -> pd.DataFrame:
    """Read the most recent parquet file for a source."""
    files = list_parquet_files(data_dir, source, days_back=1)
    if not files:
        return pd.DataFrame()
    return pd.read_parquet(files[-1])


def read_range(data_dir: str, source: str, hours_back: int = 24) -> pd.DataFrame:
    """Read all parquet files within the last N hours."""
    days_back = (hours_back // 24) + 1
    files = list_parquet_files(data_dir, source, days_back=days_back)
    if not files:
        return pd.DataFrame()

    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)

    if "pull_ts" in df.columns:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        df["pull_ts"] = pd.to_datetime(df["pull_ts"], utc=True)
        df = df[df["pull_ts"] >= cutoff]

    return df


def get_market_history(
    data_dir: str, source: str, market_id: str, id_col: str = "condition_id", days_back: int = 7
) -> pd.DataFrame:
    """Get price history for a specific market."""
    files = list_parquet_files(data_dir, source, days_back=days_back)
    if not files:
        return pd.DataFrame()

    dfs = []
    for f in files:
        df = pd.read_parquet(f)
        if id_col in df.columns:
            match = df[df[id_col] == market_id]
            if not match.empty:
                dfs.append(match)

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
