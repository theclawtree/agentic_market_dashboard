"""Parquet writer — date/time partitioned storage."""
import os
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def write_parquet(df: pd.DataFrame, data_dir: str, source: str) -> str:
    """
    Write DataFrame to parquet, partitioned by date and time.
    
    Layout: {data_dir}/{source}/{YYYY-MM-DD}/{HH-MM}.parquet
    
    Returns the path written.
    """
    if df.empty:
        return ""
    
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M")
    
    out_dir = Path(data_dir) / source / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_path = out_dir / f"{time_str}.parquet"
    
    # Convert timestamps to UTC if present
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)  # pyarrow wants tz-naive or explicit
    
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, str(out_path), compression="snappy")
    
    return str(out_path)


def list_parquet_files(data_dir: str, source: str, days_back: int = 7) -> list:
    """List parquet files for a source within recent days."""
    source_dir = Path(data_dir) / source
    if not source_dir.exists():
        return []
    
    cutoff = datetime.now(timezone.utc).date()
    files = []
    for date_dir in sorted(source_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        try:
            dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d").date()
        except ValueError:
            continue
        if (cutoff - dir_date).days > days_back:
            break
        for f in sorted(date_dir.glob("*.parquet")):
            files.append(str(f))
    
    return files
