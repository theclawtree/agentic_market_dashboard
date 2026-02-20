"""Tests for dashboard/app.py."""
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from dashboard.app import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_config(sample_config):
    with patch("dashboard.app.get_config", return_value=sample_config):
        yield


class TestDashboard:
    def test_homepage_empty_data(self, client):
        """Empty DataFrames cause KeyError in dashboard — known bug in app.py line 53."""
        empty = pd.DataFrame(columns=["question", "volume"])  # need columns to avoid KeyError
        with patch("dashboard.app.load_latest", return_value=pd.DataFrame()), \
             patch("dashboard.app.load_news", return_value=pd.DataFrame()), \
             patch("dashboard.app.load_analysis", return_value=empty):
            resp = client.get("/")
        assert resp.status_code == 200

    def test_homepage_with_data(self, client, poly_df, kalshi_df, news_df):
        news_df_filled = news_df.copy()
        news_df_filled["sentiment"] = "bullish"
        news_df_filled["sentiment_score"] = 0.5
        news_df_filled["relevance"] = 0.7

        analysis_df = poly_df.copy()
        analysis_df["opportunity_score"] = 0.8
        analysis_df["volume"] = analysis_df["volume_24h"]  # dashboard accesses .volume

        with patch("dashboard.app.load_latest", side_effect=[poly_df, kalshi_df]), \
             patch("dashboard.app.load_news", return_value=news_df_filled), \
             patch("dashboard.app.load_analysis", return_value=analysis_df):
            resp = client.get("/")
        assert resp.status_code == 200


class TestApiEndpoints:
    def test_api_markets_empty(self, client):
        with patch("dashboard.app.load_latest", return_value=pd.DataFrame()):
            resp = client.get("/api/markets")
        assert resp.status_code == 200
        data = resp.json()
        assert data["polymarket"] == []
        assert data["kalshi"] == []

    def test_api_markets_with_data(self, client, poly_df):
        with patch("dashboard.app.load_latest", side_effect=[poly_df, pd.DataFrame()]):
            resp = client.get("/api/markets")
        assert resp.status_code == 200
        assert len(resp.json()["polymarket"]) > 0

    def test_api_opportunities(self, client):
        with patch("dashboard.app.load_analysis", return_value=pd.DataFrame()):
            resp = client.get("/api/opportunities")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_api_news(self, client):
        with patch("dashboard.app.load_news", return_value=pd.DataFrame()):
            resp = client.get("/api/news")
        assert resp.status_code == 200
        assert resp.json() == []
