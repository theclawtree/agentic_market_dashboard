"""Tests for analysis/ranking.py."""
import pandas as pd
import pytest

from analysis.ranking import rank_polymarket, rank_kalshi, extract_search_terms


class TestRankPolymarket:
    def test_basic_ranking(self, poly_df):
        result = rank_polymarket(poly_df, top_n=3)
        assert len(result) == 3
        assert "opportunity_score" in result.columns
        # Scores should be between 0 and 1
        assert (result["opportunity_score"] >= 0).all()
        assert (result["opportunity_score"] <= 1).all()

    def test_sorted_descending(self, poly_df):
        result = rank_polymarket(poly_df)
        scores = result["opportunity_score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_top_n_limit(self, poly_df):
        result = rank_polymarket(poly_df, top_n=1)
        assert len(result) == 1

    def test_empty_df(self):
        assert rank_polymarket(pd.DataFrame()).empty

    def test_mid_range_price_preferred(self):
        """Markets at 0.50 should score higher on range_score than 0.05 or 0.95."""
        df = pd.DataFrame([
            {"yes_price": 0.50, "volume_24h": 100000, "spread": 0.02, "bid_depth_usd": 5000},
            {"yes_price": 0.95, "volume_24h": 100000, "spread": 0.02, "bid_depth_usd": 5000},
            {"yes_price": 0.05, "volume_24h": 100000, "spread": 0.02, "bid_depth_usd": 5000},
        ])
        result = rank_polymarket(df, top_n=3)
        # First result should be the 0.50 price market
        assert result.iloc[0]["yes_price"] == 0.50

    def test_no_spread_column(self):
        df = pd.DataFrame([
            {"yes_price": 0.50, "volume_24h": 100000},
        ])
        result = rank_polymarket(df)
        assert len(result) == 1
        assert result.iloc[0]["spread_score"] == 0.5  # default


class TestRankKalshi:
    def test_basic_ranking(self, kalshi_df):
        result = rank_kalshi(kalshi_df, top_n=2)
        assert len(result) == 2
        assert "opportunity_score" in result.columns

    def test_empty_df(self):
        assert rank_kalshi(pd.DataFrame()).empty

    def test_tight_spread_preferred(self):
        df = pd.DataFrame([
            {"yes_price": 0.50, "volume": 10000, "spread_cents": 1},
            {"yes_price": 0.50, "volume": 10000, "spread_cents": 15},
        ])
        result = rank_kalshi(df, top_n=2)
        assert result.iloc[0]["spread_cents"] == 1


class TestExtractSearchTerms:
    def test_removes_filler(self):
        row = pd.Series({"question": "Will the Fed be raising rates by March?"})
        terms = extract_search_terms(row)
        assert "Will" not in terms
        assert "the" not in terms
        assert "Fed" in terms

    def test_title_fallback(self):
        row = pd.Series({"title": "S&P 500 above 6000?"})
        terms = extract_search_terms(row)
        assert "S&P" in terms

    def test_max_6_words(self):
        row = pd.Series({"question": "Will a very long question with many words exceed limit?"})
        terms = extract_search_terms(row)
        assert len(terms.split()) <= 6

    def test_empty_question(self):
        row = pd.Series({"question": ""})
        terms = extract_search_terms(row)
        assert terms == ""
