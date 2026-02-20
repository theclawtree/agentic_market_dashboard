#!/usr/bin/env python3
"""Start the dashboard server."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader import get_config
from dashboard.app import app
import uvicorn

if __name__ == "__main__":
    cfg = get_config()
    port = cfg["dashboard"]["port"]
    host = cfg["dashboard"]["host"]
    print(f"🌐 Dashboard starting at http://localhost:{port}")
    uvicorn.run(app, host=host, port=port)
