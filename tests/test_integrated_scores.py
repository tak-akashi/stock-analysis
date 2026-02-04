"""
Tests for IntegratedScoresRepository class.
Tests CRUD operations, ranking logic, and UPSERT behavior.
"""

import pytest
import pandas as pd
import numpy as np
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta


class TestIntegratedScoresRepository:
    """Tests for IntegratedScoresRepository class."""

    @pytest.fixture
    def temp_analysis_db(self):
        """Create a temporary database for testing."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()
        yield temp_db.name
        os.unlink(temp_db.name)

    @pytest.fixture
    def repository(self, temp_analysis_db):
        """Create an IntegratedScoresRepository instance."""
        from market_pipeline.analysis.integrated_scores_repository import (
            IntegratedScoresRepository,
        )

        return IntegratedScoresRepository(db_path=temp_analysis_db)

    @pytest.fixture
    def sample_scores_df(self):
        """Create sample scores DataFrame for testing."""
        return pd.DataFrame(
            {
                "Code": ["1001", "1002", "1003", "1004", "1005"],
                "composite_score": [85.5, 72.3, 90.1, 65.0, 78.8],
                "HlRatio": [92.0, 85.0, 95.0, 70.0, 88.0],
                "RelativeStrengthPercentage": [80.0, 75.0, 88.0, 60.0, 82.0],
            }
        )

    def test_ensure_table_exists(self, repository):
        """Test that table is created automatically."""
        # Table should be created on first operation
        repository._ensure_table_exists()

        conn = sqlite3.connect(repository.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='integrated_scores'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "integrated_scores"

    def test_save_scores_basic(self, repository, sample_scores_df):
        """Test basic save operation."""
        date = "2026-02-01"
        count = repository.save_scores(sample_scores_df, date)

        assert count == 5

        # Verify data was saved
        scores = repository.get_scores(date)
        assert len(scores) == 5
        assert set(scores["Code"].tolist()) == {"1001", "1002", "1003", "1004", "1005"}

    def test_save_scores_with_ranks(self, repository, sample_scores_df):
        """Test that ranks are calculated and saved correctly."""
        date = "2026-02-01"
        repository.save_scores(sample_scores_df, date)

        scores = repository.get_scores(date)

        # Check composite_score_rank
        # Expected ranking: 1003(90.1)=1, 1001(85.5)=2, 1005(78.8)=3, 1002(72.3)=4, 1004(65.0)=5
        code_1003 = scores[scores["Code"] == "1003"].iloc[0]
        assert code_1003["composite_score_rank"] == 1

        code_1004 = scores[scores["Code"] == "1004"].iloc[0]
        assert code_1004["composite_score_rank"] == 5

    def test_save_scores_upsert(self, repository, sample_scores_df):
        """Test UPSERT behavior - same date/code should update."""
        date = "2026-02-01"

        # First save
        repository.save_scores(sample_scores_df, date)

        # Modify scores
        updated_df = sample_scores_df.copy()
        updated_df.loc[updated_df["Code"] == "1001", "composite_score"] = 99.9

        # Second save (should update, not duplicate)
        repository.save_scores(updated_df, date)

        scores = repository.get_scores(date)
        assert len(scores) == 5  # Still 5 records

        # Check updated value
        code_1001 = scores[scores["Code"] == "1001"].iloc[0]
        assert code_1001["composite_score"] == pytest.approx(99.9, rel=0.01)

    def test_get_scores_latest_date(self, repository, sample_scores_df):
        """Test getting scores for latest date when date is None."""
        # Save scores for multiple dates
        repository.save_scores(sample_scores_df, "2026-02-01")

        updated_df = sample_scores_df.copy()
        updated_df["composite_score"] = updated_df["composite_score"] + 1
        repository.save_scores(updated_df, "2026-02-02")

        # Get latest (should return 2026-02-02)
        scores = repository.get_scores(date=None)
        assert len(scores) == 5
        assert scores["Date"].iloc[0] == "2026-02-02"

    def test_get_scores_specific_date(self, repository, sample_scores_df):
        """Test getting scores for a specific date."""
        repository.save_scores(sample_scores_df, "2026-02-01")

        scores = repository.get_scores("2026-02-01")
        assert len(scores) == 5
        assert all(scores["Date"] == "2026-02-01")

    def test_get_scores_no_data(self, repository):
        """Test getting scores when no data exists."""
        scores = repository.get_scores("2099-01-01")
        assert isinstance(scores, pd.DataFrame)
        assert len(scores) == 0

    def test_get_history_basic(self, repository, sample_scores_df):
        """Test getting history for a specific code."""
        # Save multiple days of data
        for i in range(5):
            date = f"2026-02-0{i+1}"
            df = sample_scores_df.copy()
            df["composite_score"] = df["composite_score"] + i
            repository.save_scores(df, date)

        history = repository.get_history("1001", days=30)
        assert len(history) == 5
        assert all(history["Code"] == "1001")

    def test_get_history_limited_days(self, repository, sample_scores_df):
        """Test history with days limit."""
        # Save 10 days of data
        for i in range(10):
            date = (datetime(2026, 2, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
            repository.save_scores(sample_scores_df, date)

        # Request only last 5 days
        history = repository.get_history("1001", days=5)
        assert len(history) == 5

    def test_get_history_no_data(self, repository):
        """Test getting history for non-existent code."""
        history = repository.get_history("9999", days=30)
        assert isinstance(history, pd.DataFrame)
        assert len(history) == 0

    def test_get_latest_date(self, repository, sample_scores_df):
        """Test getting the latest date in the database."""
        repository.save_scores(sample_scores_df, "2026-02-01")
        repository.save_scores(sample_scores_df, "2026-02-05")
        repository.save_scores(sample_scores_df, "2026-02-03")

        latest = repository.get_latest_date()
        assert latest == "2026-02-05"

    def test_get_latest_date_no_data(self, repository):
        """Test getting latest date when no data exists."""
        latest = repository.get_latest_date()
        assert latest is None

    def test_rank_calculation_ties(self, repository):
        """Test ranking with tied scores."""
        df = pd.DataFrame(
            {
                "Code": ["1001", "1002", "1003"],
                "composite_score": [80.0, 80.0, 70.0],
                "HlRatio": [90.0, 90.0, 80.0],
                "RelativeStrengthPercentage": [85.0, 85.0, 75.0],
            }
        )

        repository.save_scores(df, "2026-02-01")
        scores = repository.get_scores("2026-02-01")

        # With ties, both 1001 and 1002 should have rank 1 (min rank)
        tied_ranks = scores[scores["composite_score"] == 80.0][
            "composite_score_rank"
        ].tolist()
        assert all(r == 1 for r in tied_ranks)

    def test_rank_calculation_null_values(self, repository):
        """Test ranking with NULL/NaN values."""
        df = pd.DataFrame(
            {
                "Code": ["1001", "1002", "1003"],
                "composite_score": [80.0, np.nan, 70.0],
                "HlRatio": [90.0, 85.0, np.nan],
                "RelativeStrengthPercentage": [85.0, np.nan, 75.0],
            }
        )

        repository.save_scores(df, "2026-02-01")
        scores = repository.get_scores("2026-02-01")

        # Non-null scores should be ranked; null scores should have null rank
        code_1001 = scores[scores["Code"] == "1001"].iloc[0]
        assert code_1001["composite_score_rank"] == 1

        code_1002 = scores[scores["Code"] == "1002"].iloc[0]
        assert pd.isna(code_1002["composite_score_rank"])

    def test_indexes_created(self, repository):
        """Test that performance indexes are created."""
        repository._ensure_table_exists()

        conn = sqlite3.connect(repository.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA index_list(integrated_scores)")
        indexes = cursor.fetchall()
        conn.close()

        index_names = [idx[1] for idx in indexes]

        # Check for expected indexes
        assert any("date" in name.lower() for name in index_names)
        assert any("code" in name.lower() for name in index_names)

    def test_get_rank_changes_valid_metrics(self, repository, sample_scores_df):
        """Test get_rank_changes with valid metric values."""
        from market_pipeline.analysis.integrated_scores_repository import (
            IntegratedScoresRepository,
        )

        # Save data for multiple dates
        repository.save_scores(sample_scores_df, "2026-02-01")

        modified_df = sample_scores_df.copy()
        modified_df["composite_score"] = [90.0, 65.0, 85.0, 75.0, 70.0]
        repository.save_scores(modified_df, "2026-02-02")

        # Test valid metrics
        for metric in IntegratedScoresRepository.VALID_METRICS:
            result = repository.get_rank_changes(metric=metric, days=1)
            assert isinstance(result, pd.DataFrame)

    def test_get_rank_changes_invalid_metric(self, repository):
        """Test get_rank_changes raises ValueError for invalid metric."""
        with pytest.raises(ValueError) as exc_info:
            repository.get_rank_changes(metric="invalid_metric")

        assert "invalid_metric" in str(exc_info.value)
        assert "VALID_METRICS" in str(exc_info.value) or "composite_score" in str(
            exc_info.value
        )

    def test_get_rank_changes_empty_db(self, repository):
        """Test get_rank_changes with empty database."""
        result = repository.get_rank_changes()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
