"""Tests for config_loader.py."""

import os

import pytest
import yaml

from config_loader import get_config, load_config


@pytest.fixture
def config_file(tmp_path):
    """Write a minimal config.yaml to tmp_path and return its path."""
    cfg = {
        "ingest": {
            "interval_minutes": 10,
            "polymarket": {"enabled": True},
            "kalshi": {"enabled": True},
        },
        "storage": {"data_dir": "./data", "retention_days": 7},
        "news": {"api_key": "default-key"},
        "llm": {"api_key": ""},
        "analysis": {"top_n_markets": 10},
        "dashboard": {"host": "0.0.0.0", "port": 8051, "auto_refresh_seconds": 60},  # noqa: S104
    }
    p = tmp_path / "config.yaml.example"
    p.write_text(yaml.dump(cfg))
    return str(p)


def test_load_config_basic(config_file):
    cfg = load_config(config_file)
    assert cfg["ingest"]["interval_minutes"] == 10
    assert cfg["storage"]["retention_days"] == 7


def test_load_config_resolves_relative_data_dir(config_file):
    cfg = load_config(config_file)
    # data_dir should be absolute after loading
    assert os.path.isabs(cfg["storage"]["data_dir"])


def test_load_config_absolute_data_dir_unchanged(tmp_path):
    cfg_data = {
        "ingest": {
            "interval_minutes": 5,
            "polymarket": {"enabled": True},
            "kalshi": {"enabled": True},
        },
        "storage": {"data_dir": "/absolute/path", "retention_days": 3},
        "news": {"api_key": ""},
        "llm": {"api_key": ""},
        "analysis": {},
        "dashboard": {},
    }
    p = tmp_path / "config.yaml.example"
    p.write_text(yaml.dump(cfg_data))
    cfg = load_config(str(p))
    assert cfg["storage"]["data_dir"] == "/absolute/path"


def test_env_override_newsapi(config_file, monkeypatch):
    monkeypatch.setenv("NEWSAPI_KEY", "env-news-key")
    cfg = load_config(config_file)
    assert cfg["news"]["api_key"] == "env-news-key"


def test_env_override_llm_key(config_file, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "env-llm-key")
    cfg = load_config(config_file)
    assert cfg["llm"]["api_key"] == "env-llm-key"


def test_get_config_singleton(monkeypatch):
    """get_config returns cached singleton."""
    import config_loader

    monkeypatch.setattr(config_loader, "_cfg", None)
    # Will load from default CONFIG_PATH — just verify it doesn't crash
    # and returns a dict
    cfg = get_config()
    assert isinstance(cfg, dict)
    # Second call should return same object
    cfg2 = get_config()
    assert cfg is cfg2
    # Reset
    monkeypatch.setattr(config_loader, "_cfg", None)
