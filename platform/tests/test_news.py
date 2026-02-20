"""Tests for analysis/news.py."""
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from analysis.news import fetch_news_for_markets, collect_news


class TestFetchNewsForMarkets:
    def test_basic_fetch(self, poly_df, newsapi_response):
        with patch("analysis.news.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = newsapi_response
            mock_get.return_value = mock_resp

            df = fetch_news_for_markets(poly_df.head(1), api_key="test-key", max_articles=5)

        assert len(df) == 2
        assert "headline" in df.columns
        assert "sentiment" in df.columns

    def test_no_api_key(self, poly_df):
        df = fetch_news_for_markets(poly_df, api_key="", max_articles=5)
        assert df.empty

    def test_deduplication(self, poly_df):
        """Same URL from different queries should not appear twice."""
        response = {
            "articles": [
                {"title": "Same Article", "description": "Test", "source": {"name": "Test"},
                 "url": "https://example.com/same", "publishedAt": "2026-02-18T10:00:00Z"},
            ],
        }
        with patch("analysis.news.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = response
            mock_get.return_value = mock_resp

            df = fetch_news_for_markets(poly_df.head(2), api_key="key", max_articles=5)

        urls = df["url"].tolist()
        assert len(urls) == len(set(urls))

    def test_api_error_graceful(self, poly_df):
        with patch("analysis.news.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 429
            mock_get.return_value = mock_resp

            df = fetch_news_for_markets(poly_df, api_key="key")

        assert df.empty

    def test_request_exception(self, poly_df):
        with patch("analysis.news.requests.get", side_effect=Exception("Network error")):
            df = fetch_news_for_markets(poly_df, api_key="key")
        assert df.empty


class TestCollectNews:
    def test_combines_platforms(self, poly_df, kalshi_df, sample_config, newsapi_response):
        with patch("analysis.news.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = newsapi_response
            mock_get.return_value = mock_resp

            df = collect_news(poly_df, kalshi_df, sample_config)

        assert not df.empty

    def test_both_empty(self, sample_config):
        df = collect_news(pd.DataFrame(), pd.DataFrame(), sample_config)
        assert df.empty
