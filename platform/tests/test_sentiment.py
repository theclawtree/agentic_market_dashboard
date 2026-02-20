"""Tests for analysis/sentiment.py."""

from unittest.mock import MagicMock, patch

import pandas as pd

from analysis.sentiment import (
    _keyword_fallback,
    analyze_news_df,
    analyze_with_api,
    analyze_with_ollama,
)


class TestKeywordFallback:
    def test_bullish_keywords(self):
        result = _keyword_fallback("Price surge and gains", "Markets rise", "Will BTC go up?")
        assert result["sentiment"] == "bullish"
        assert result["sentiment_score"] > 0

    def test_bearish_keywords(self):
        result = _keyword_fallback(
            "Market crash and decline", "Prices drop sharply", "Will BTC go up?"
        )
        assert result["sentiment"] == "bearish"
        assert result["sentiment_score"] < 0

    def test_neutral_no_keywords(self):
        result = _keyword_fallback(
            "Weather forecast today", "Sunny skies expected", "Will BTC go up?"
        )
        assert result["sentiment"] == "neutral"
        assert result["sentiment_score"] == 0.0

    def test_relevance_calculation(self):
        result = _keyword_fallback("Bitcoin price rises", "BTC gains", "Will Bitcoin go up?")
        assert result["relevance"] > 0

    def test_all_fields_present(self):
        result = _keyword_fallback("test", "test", "test")
        assert "sentiment" in result
        assert "sentiment_score" in result
        assert "relevance" in result


class TestAnalyzeWithApi:
    def test_successful_api_call(self):
        api_response = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"sentiment": "bullish", "sentiment_score": 0.7, "relevance": 0.8}'
                        )
                    }
                }
            ]
        }
        with patch("analysis.sentiment.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = api_response
            mock_post.return_value = mock_resp

            result = analyze_with_api(
                "BTC surges",
                "Big gains",
                "Will BTC rise?",
                "https://api.test.com/v1",
                "test-key",
                "gpt-4o-mini",
            )

        assert result["sentiment"] == "bullish"

    def test_no_api_key_falls_back(self):
        result = analyze_with_api(
            "headline", "desc", "question", "https://api.test.com/v1", "", "model"
        )
        # Should use keyword fallback
        assert "sentiment" in result

    def test_api_error_falls_back(self):
        with patch("analysis.sentiment.requests.post", side_effect=Exception("timeout")):
            result = analyze_with_api(
                "headline", "desc", "question", "https://api.test.com/v1", "key", "model"
            )
        assert "sentiment" in result

    def test_json_in_code_block(self):
        api_response = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '```json\n{"sentiment": "bearish",'
                            ' "sentiment_score": -0.5, "relevance": 0.6}\n```'
                        )
                    }
                }
            ]
        }
        with patch("analysis.sentiment.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = api_response
            mock_post.return_value = mock_resp

            result = analyze_with_api(
                "test", "test", "test", "https://api.test.com/v1", "key", "model"
            )

        assert result["sentiment"] == "bearish"


class TestAnalyzeWithOllama:
    def test_successful_call(self):
        ollama_response = {
            "message": {
                "content": '{"sentiment": "neutral", "sentiment_score": 0.0, "relevance": 0.5}'
            }
        }
        with patch("analysis.sentiment.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = ollama_response
            mock_post.return_value = mock_resp

            result = analyze_with_ollama(
                "headline", "desc", "question", "http://localhost:11434", "llama3.2:3b"
            )

        assert result["sentiment"] == "neutral"

    def test_ollama_error_falls_back(self):
        with patch("analysis.sentiment.requests.post", side_effect=Exception("connection refused")):
            result = analyze_with_ollama(
                "headline", "desc", "question", "http://localhost:11434", "model"
            )
        assert "sentiment" in result


class TestAnalyzeNewsDf:
    def test_keyword_backend(self, news_df, sample_config):
        sample_config["llm"]["backend"] = "keyword"
        result = analyze_news_df(news_df, sample_config)

        assert "sentiment" in result.columns
        assert "sentiment_score" in result.columns
        assert "relevance" in result.columns
        assert not result["sentiment"].isna().any()

    def test_empty_df(self, sample_config):
        result = analyze_news_df(pd.DataFrame(), sample_config)
        assert result.empty

    def test_openai_backend_with_key(self, news_df, sample_config):
        sample_config["llm"]["backend"] = "openai_compatible"
        sample_config["llm"]["api_key"] = "test-key"

        api_response = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"sentiment": "bullish", "sentiment_score": 0.5, "relevance": 0.7}'
                        )
                    }
                }
            ]
        }
        with patch("analysis.sentiment.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = api_response
            mock_post.return_value = mock_resp

            result = analyze_news_df(news_df, sample_config)

        assert (result["sentiment"] == "bullish").all()
