"""Load and validate platform configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | None = None) -> dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        path: Optional path to config file. If not provided, uses config.yaml in the same directory as this module.
        
    Returns:
        Dictionary containing the configuration.
    """
    CONFIG_PATH = Path(__file__).parent / "config.yaml"
    p = Path(path) if path else CONFIG_PATH
    with open(p) as f:
        cfg: dict[str, Any] = yaml.safe_load(f)

    # Override secrets from environment
    if os.environ.get("NEWSAPI_KEY"):
        cfg["news"]["api_key"] = os.environ["NEWSAPI_KEY"]
    if os.environ.get("LLM_API_KEY"):
        cfg["llm"]["api_key"] = os.environ["LLM_API_KEY"]

    # Resolve data_dir to absolute
    data_dir = cfg["storage"]["data_dir"]
    if not os.path.isabs(data_dir):
        cfg["storage"]["data_dir"] = str(Path(__file__).parent / data_dir)

    return cfg


# Singleton
_cfg: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    global _cfg
    if _cfg is None:
        _cfg = load_config()
    return _cfg
