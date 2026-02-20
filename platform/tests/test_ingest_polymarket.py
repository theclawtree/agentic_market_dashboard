"""Tests for ingest/polymarket.py."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from ingest.polymarket import collect, enrich_order_books, fetch_markets


class TestFetchMarkets:
    def test_basic_fetch(self, gamma_api_response):
        with patch("ingest.polymarket.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = gamma_api_response
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            df = fetch_markets(min_volume=10000, max_markets=100)

        assert len(df) == 1  # Only one above 10k volume
        assert df.iloc[0]["question"] == "Will Bitcoin hit $100k?"
        assert df.iloc[0]["yes_price"] == 0.65
        assert df.iloc[0]["platform"] == "polymarket"

    def test_low_volume_filtered(self, gamma_api_response):
        with patch("ingest.polymarket.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = gamma_api_response
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            df = fetch_markets(min_volume=200000)

        assert len(df) == 0

    def test_malformed_tokens_skipped(self):
        data = [
            {
                "question": "Bad market",
                "clobTokenIds": "not-json",
                "outcomePrices": "[0.5, 0.5]",
                "volume24hr": "50000",
            }
        ]
        with patch("ingest.polymarket.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = data
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            df = fetch_markets(min_volume=1000)

        assert len(df) == 0

    def test_empty_response(self):
        with patch("ingest.polymarket.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = []
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            df = fetch_markets()

        assert df.empty


class TestEnrichOrderBooks:
    def test_enrichment_adds_spread(self, poly_df):
        mock_book = MagicMock()
        bid = MagicMock()
        bid.price = "0.64"
        bid.size = "100"
        ask = MagicMock()
        ask.price = "0.66"
        ask.size = "100"
        mock_book.bids = [bid]
        mock_book.asks = [ask]

        with patch("ingest.polymarket.ClobClient") as MockClob:
            MockClob.return_value.get_order_book.return_value = mock_book
            result = enrich_order_books(poly_df, top_n=1)

        assert result.at[0, "spread"] == pytest.approx(0.02)

    def test_empty_df_returns_empty(self):
        df = pd.DataFrame()
        result = enrich_order_books(df)
        assert result.empty

    def test_api_error_graceful(self, poly_df):
        with patch("ingest.polymarket.ClobClient") as MockClob:
            MockClob.return_value.get_order_book.side_effect = Exception("timeout")
            result = enrich_order_books(poly_df, top_n=1)

        # Should not crash, original data preserved
        assert len(result) == len(poly_df)


class TestCollect:
    def test_disabled_returns_empty(self, sample_config):
        sample_config["ingest"]["polymarket"]["enabled"] = False
        df = collect(sample_config)
        assert df.empty

    def test_enabled_calls_fetch(self, sample_config, gamma_api_response):
        with patch("ingest.polymarket.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = gamma_api_response
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            df = collect(sample_config)

        assert not df.empty
