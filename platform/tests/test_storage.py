"""Tests for storage/writer.py, reader.py, and cleanup.py."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from storage.cleanup import cleanup
from storage.reader import get_market_history, read_latest, read_range
from storage.writer import list_parquet_files, write_parquet


class TestWriteParquet:
    def test_basic_write(self, tmp_path, poly_df):
        path = write_parquet(poly_df, str(tmp_path), "polymarket")
        assert path != ""
        assert Path(path).exists()
        assert path.endswith(".parquet")

    def test_empty_df_returns_empty(self, tmp_path):
        path = write_parquet(pd.DataFrame(), str(tmp_path), "test")
        assert path == ""

    def test_creates_directories(self, tmp_path, poly_df):
        data_dir = str(tmp_path / "nested" / "data")
        path = write_parquet(poly_df, data_dir, "polymarket")
        assert Path(path).exists()

    def test_roundtrip(self, tmp_path, poly_df):
        path = write_parquet(poly_df, str(tmp_path), "polymarket")
        loaded = pd.read_parquet(path)
        assert len(loaded) == len(poly_df)
        assert set(loaded.columns) == set(poly_df.columns)


class TestListParquetFiles:
    def test_lists_recent_files(self, tmp_path, poly_df):
        write_parquet(poly_df, str(tmp_path), "polymarket")
        files = list_parquet_files(str(tmp_path), "polymarket", days_back=1)
        assert len(files) >= 1

    def test_no_files(self, tmp_path):
        files = list_parquet_files(str(tmp_path), "nonexistent", days_back=7)
        assert files == []

    def test_old_files_excluded(self, tmp_path, poly_df):
        # Create a file in an old date directory
        old_dir = tmp_path / "polymarket" / "2020-01-01"
        old_dir.mkdir(parents=True)
        write_parquet(poly_df, str(tmp_path), "polymarket")  # today
        # Write a fake old file
        poly_df.to_parquet(str(old_dir / "12-00.parquet"))

        files = list_parquet_files(str(tmp_path), "polymarket", days_back=1)
        assert all("2020-01-01" not in f for f in files)


class TestReadLatest:
    def test_reads_latest(self, tmp_path, poly_df):
        write_parquet(poly_df, str(tmp_path), "polymarket")
        df = read_latest(str(tmp_path), "polymarket")
        assert len(df) == len(poly_df)

    def test_no_data(self, tmp_path):
        df = read_latest(str(tmp_path), "nonexistent")
        assert df.empty


class TestReadRange:
    def test_reads_range(self, tmp_path, poly_df):
        write_parquet(poly_df, str(tmp_path), "polymarket")
        df = read_range(str(tmp_path), "polymarket", hours_back=24)
        assert len(df) > 0

    def test_empty_range(self, tmp_path):
        df = read_range(str(tmp_path), "nonexistent", hours_back=24)
        assert df.empty


class TestGetMarketHistory:
    def test_finds_market(self, tmp_path, poly_df):
        write_parquet(poly_df, str(tmp_path), "polymarket")
        df = get_market_history(
            str(tmp_path), "polymarket", "0xabc123", id_col="condition_id", days_back=1
        )
        assert len(df) == 1

    def test_market_not_found(self, tmp_path, poly_df):
        write_parquet(poly_df, str(tmp_path), "polymarket")
        df = get_market_history(
            str(tmp_path), "polymarket", "nonexistent", id_col="condition_id", days_back=1
        )
        assert df.empty


class TestCleanup:
    def test_removes_old_dirs(self, tmp_path):
        # Create old directory
        old_dir = tmp_path / "source" / "2020-01-01"
        old_dir.mkdir(parents=True)
        (old_dir / "test.parquet").write_text("fake")

        # Create recent directory
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        new_dir = tmp_path / "source" / today
        new_dir.mkdir(parents=True)
        (new_dir / "test.parquet").write_text("fake")

        removed = cleanup(str(tmp_path), retention_days=30)

        assert removed == 1
        assert not old_dir.exists()
        assert new_dir.exists()

    def test_no_old_dirs(self, tmp_path):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        new_dir = tmp_path / "source" / today
        new_dir.mkdir(parents=True)

        removed = cleanup(str(tmp_path), retention_days=30)
        assert removed == 0

    def test_nonexistent_dir(self, tmp_path):
        removed = cleanup(str(tmp_path / "nonexistent"), retention_days=30)
        assert removed == 0
