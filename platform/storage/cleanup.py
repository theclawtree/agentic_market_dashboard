"""Auto-delete parquet files older than retention period."""

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config_loader import get_config


def cleanup(data_dir: str | None = None, retention_days: int | None = None) -> int:
    """Delete date-partitioned directories older than retention_days."""
    cfg = get_config()
    if cfg:
        data_dir = cfg["storage"]["data_dir"]
        retention_days = cfg["storage"]["retention_days"]
        
    if not data_dir or not retention_days:
        raise ValueError("data_dir and retention_days must be provided")
    
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
