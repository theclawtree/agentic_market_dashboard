"""Tests for ingest/kalshi.py."""

from unittest.mock import MagicMock, patch

import pytest

from ingest.kalshi import collect, fetch_markets


class TestFetchMarkets:
    def test_basic_fetch(self, kalshi_api_response):
        with patch("ingest.kalshi.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = kalshi_api_response
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            df = fetch_markets(max_markets=200, min_volume=100)

        assert len(df) == 1
        assert df.iloc[0]["ticker"] == "FED-26MAR-T4.50"
        assert df.iloc[0]["platform"] == "kalshi"

    def test_min_volume_filter(self, kalshi_api_response):
        with patch("ingest.kalshi.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = kalshi_api_response
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            df = fetch_markets(min_volume=100000)

        assert len(df) == 0

    def test_spread_calculation(self, kalshi_api_response):
        with patch("ingest.kalshi.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = kalshi_api_response
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            df = fetch_markets()

        assert df.iloc[0]["spread_cents"] == 3
        assert df.iloc[0]["yes_price"] == pytest.approx(0.635)

    def test_empty_events(self):
        with patch("ingest.kalshi.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"events": []}
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            df = fetch_markets()

        assert df.empty

    def test_max_markets_limit(self):
        events = {
            "events": [
                {
                    "title": f"Event {i}",
                    "markets": [
                        {
                            "ticker": f"TICK-{i}",
                            "title": f"Market {i}",
                            "event_ticker": f"EVT-{i}",
                            "yes_bid": 50,
                            "yes_ask": 55,
                            "volume": 1000 + i,
                            "open_interest": 100,
                            "close_time": "2026-03-01",
                            "category": "Test",
                        }
                    ],
                }
                for i in range(10)
            ],
        }
        with patch("ingest.kalshi.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = events
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            df = fetch_markets(max_markets=5)

        assert len(df) == 5


class TestCollect:
    def test_disabled(self, sample_config):
        sample_config["ingest"]["kalshi"]["enabled"] = False
        assert collect(sample_config).empty

    def test_enabled(self, sample_config, kalshi_api_response):
        with patch("ingest.kalshi.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = kalshi_api_response
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            df = collect(sample_config)

        assert not df.empty
