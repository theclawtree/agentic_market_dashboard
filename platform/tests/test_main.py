"""Tests for main.py pipeline orchestration."""
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from main import run_pipeline


class TestRunPipeline:
    def test_full_pipeline_mocked(self, sample_config, poly_df, kalshi_df, news_df):
        news_df_filled = news_df.copy()
        news_df_filled["sentiment"] = "bullish"
        news_df_filled["sentiment_score"] = 0.5
        news_df_filled["relevance"] = 0.7

        with patch("main.collect_poly", return_value=poly_df), \
             patch("main.collect_kalshi", return_value=kalshi_df), \
             patch("main.write_parquet", return_value="/fake/path.parquet"), \
             patch("main.rank_polymarket", return_value=poly_df), \
             patch("main.rank_kalshi", return_value=kalshi_df), \
             patch("main.collect_news", return_value=news_df), \
             patch("main.analyze_news_df", return_value=news_df_filled), \
             patch("main.cleanup", return_value=0):

            summary = run_pipeline(sample_config)

        assert summary["polymarket_markets"] == 3
        assert summary["kalshi_markets"] == 2
        assert summary["news_articles"] == 2
        assert "timestamp" in summary

    def test_pipeline_empty_data(self, sample_config):
        empty = pd.DataFrame()
        with patch("main.collect_poly", return_value=empty), \
             patch("main.collect_kalshi", return_value=empty), \
             patch("main.write_parquet", return_value=""), \
             patch("main.rank_polymarket", return_value=empty), \
             patch("main.rank_kalshi", return_value=empty), \
             patch("main.collect_news", return_value=empty), \
             patch("main.analyze_news_df", return_value=empty), \
             patch("main.cleanup", return_value=0):

            summary = run_pipeline(sample_config)

        assert summary["polymarket_markets"] == 0
        assert summary["kalshi_markets"] == 0
