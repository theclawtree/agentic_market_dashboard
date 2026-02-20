"""Performance and scalability tests."""
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psutil
import pytest

from storage.writer import write_parquet, list_parquet_files
from storage.reader import read_latest, read_range
from analysis.ranking import rank_polymarket, rank_kalshi
from analysis.sentiment import _keyword_fallback


def _make_large_poly_df(n: int) -> pd.DataFrame:
    """Generate a large Polymarket-like DataFrame."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "pull_ts": pd.Timestamp.now("UTC"),
        "platform": "polymarket",
        "question": [f"Market question {i}?" for i in range(n)],
        "slug": [f"market-{i}" for i in range(n)],
        "condition_id": [f"0x{i:08x}" for i in range(n)],
        "yes_token": [f"tok_y_{i}" for i in range(n)],
        "no_token": [f"tok_n_{i}" for i in range(n)],
        "yes_price": rng.uniform(0.01, 0.99, n),
        "no_price": rng.uniform(0.01, 0.99, n),
        "volume_24h": rng.uniform(1000, 500000, n),
        "liquidity": rng.uniform(10000, 1000000, n),
        "volume_total": rng.uniform(100000, 10000000, n),
        "end_date": "2026-12-31",
        "spread": rng.uniform(0.001, 0.1, n),
        "bid_depth_usd": rng.uniform(100, 50000, n),
        "ask_depth_usd": rng.uniform(100, 50000, n),
    })


def _make_large_kalshi_df(n: int) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "pull_ts": pd.Timestamp.now("UTC"),
        "platform": "kalshi",
        "ticker": [f"TICK-{i}" for i in range(n)],
        "title": [f"Kalshi market {i}?" for i in range(n)],
        "event_ticker": [f"EVT-{i}" for i in range(n)],
        "yes_bid": rng.integers(10, 90, n),
        "yes_ask": rng.integers(10, 90, n),
        "yes_price": rng.uniform(0.1, 0.9, n),
        "spread_cents": rng.integers(1, 20, n),
        "volume": rng.integers(100, 100000, n),
        "open_interest": rng.integers(100, 50000, n),
        "close_time": "2026-12-31",
        "category": "Test",
    })


@pytest.mark.performance
class TestWritePerformance:
    def test_write_10k_rows(self, tmp_path):
        df = _make_large_poly_df(10000)
        start = time.time()
        path = write_parquet(df, str(tmp_path), "polymarket")
        elapsed = time.time() - start

        assert Path(path).exists()
        assert elapsed < 5.0, f"Write 10k rows took {elapsed:.2f}s (expected <5s)"
        # Check file size is reasonable (snappy compressed)
        size_mb = Path(path).stat().st_size / (1024 * 1024)
        assert size_mb < 10, f"File size {size_mb:.1f}MB too large"

    def test_write_50k_rows(self, tmp_path):
        df = _make_large_poly_df(50000)
        start = time.time()
        path = write_parquet(df, str(tmp_path), "polymarket")
        elapsed = time.time() - start

        assert elapsed < 15.0, f"Write 50k rows took {elapsed:.2f}s (expected <15s)"


@pytest.mark.performance
class TestReadPerformance:
    def test_read_10k_rows(self, tmp_path):
        df = _make_large_poly_df(10000)
        write_parquet(df, str(tmp_path), "polymarket")

        start = time.time()
        result = read_latest(str(tmp_path), "polymarket")
        elapsed = time.time() - start

        assert len(result) == 10000
        assert elapsed < 3.0, f"Read 10k rows took {elapsed:.2f}s (expected <3s)"

    def test_list_many_files(self, tmp_path):
        """Test listing performance with many date directories."""
        df = _make_large_poly_df(10)
        for day in range(30):
            date_str = f"2026-02-{day + 1:02d}"
            out_dir = tmp_path / "polymarket" / date_str
            out_dir.mkdir(parents=True, exist_ok=True)
            df.to_parquet(str(out_dir / "12-00.parquet"))

        start = time.time()
        files = list_parquet_files(str(tmp_path), "polymarket", days_back=30)
        elapsed = time.time() - start

        assert len(files) >= 20
        assert elapsed < 1.0


@pytest.mark.performance
class TestRankingPerformance:
    def test_rank_10k_polymarket(self):
        df = _make_large_poly_df(10000)
        start = time.time()
        result = rank_polymarket(df, top_n=100)
        elapsed = time.time() - start

        assert len(result) == 100
        assert elapsed < 2.0, f"Ranking 10k took {elapsed:.2f}s"

    def test_rank_10k_kalshi(self):
        df = _make_large_kalshi_df(10000)
        start = time.time()
        result = rank_kalshi(df, top_n=100)
        elapsed = time.time() - start

        assert len(result) == 100
        assert elapsed < 2.0


@pytest.mark.performance
class TestSentimentPerformance:
    def test_keyword_fallback_1000_articles(self):
        """Keyword fallback should handle 1000 articles quickly."""
        start = time.time()
        for i in range(1000):
            _keyword_fallback(
                f"Article headline {i} about market surge and gains",
                f"Description {i} with positive momentum and growth",
                "Will the market rise?",
            )
        elapsed = time.time() - start

        assert elapsed < 2.0, f"1000 keyword analyses took {elapsed:.2f}s"


@pytest.mark.performance
class TestMemoryUsage:
    def test_large_df_memory(self):
        """50k row DataFrame should use less than 100MB."""
        process = psutil.Process()
        mem_before = process.memory_info().rss

        df = _make_large_poly_df(50000)
        _ = rank_polymarket(df, top_n=100)

        mem_after = process.memory_info().rss
        mem_delta_mb = (mem_after - mem_before) / (1024 * 1024)

        assert mem_delta_mb < 100, f"Used {mem_delta_mb:.1f}MB (expected <100MB)"
