"""Auto-delete parquet files older than retention period."""
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config_loader import get_config


def cleanup(data_dir: str = None, retention_days: int = None):
    """Delete date-partitioned directories older than retention_days."""
    cfg = get_config()
    data_dir = data_dir or cfg["storage"]["data_dir"]
    retention_days = retention_days or cfg["storage"]["retention_days"]
    
    cutoff = datetime.now(timezone.utc).date()
    removed = 0
    
    root = Path(data_dir)
    if not root.exists():
        return 0
    
    for source_dir in root.iterdir():
        if not source_dir.is_dir():
            continue
        for date_dir in source_dir.iterdir():
            if not date_dir.is_dir():
                continue
            try:
                dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d").date()
            except ValueError:
                continue
            age = (cutoff - dir_date).days
            if age > retention_days:
                shutil.rmtree(date_dir)
                removed += 1
                print(f"  Removed: {date_dir} (age: {age} days)")
    
    return removed


if __name__ == "__main__":
    print(f"Running cleanup (retention: {get_config()['storage']['retention_days']} days)...")
    n = cleanup()
    print(f"Removed {n} directories.")
