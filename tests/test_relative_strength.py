import pytest
import numpy as np
import pandas as pd
import sqlite3
import tempfile
import os

from market_pipeline.analysis.relative_strength import (
    relative_strength_percentage_vectorized,
    init_results_db,
)


class TestRelativeStrength:
    @pytest.fixture
    def temp_database(self):
        """Create a temporary database for testing"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()

        conn = sqlite3.connect(temp_db.name)

        # Create tables
        conn.execute("""
        CREATE TABLE daily_quotes (
            Date TEXT,
            Code TEXT,
            AdjustmentClose REAL
        )
        """)

        conn.execute("""
        CREATE TABLE relative_strength (
            Date TEXT,
            Code TEXT,
            RelativeStrengthPercentage REAL,
            RelativeStrengthIndex REAL,
            PRIMARY KEY (Date, Code)
        )
        """)

        # Insert sample data
        dates = pd.date_range("2023-01-01", periods=300, freq="D")
        np.random.seed(42)

        codes = ["1001", "1002", "1003"]

        for code in codes:
            base_price = np.random.uniform(50, 200)
            current_price = base_price

            for date in dates:
                change = np.random.normal(0.001, 0.02)  # Small trend with volatility
                current_price *= 1 + change

                conn.execute(
                    """
                INSERT INTO daily_quotes (Date, Code, AdjustmentClose)
                VALUES (?, ?, ?)
                """,
                    (date.strftime("%Y-%m-%d"), code, current_price),
                )

        conn.commit()
        conn.close()

        yield temp_db.name

        # Clean up
        os.unlink(temp_db.name)

    @pytest.fixture
    def temp_results_database(self):
        """Create a temporary results database"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()

        yield temp_db.name

        # Clean up
        os.unlink(temp_db.name)

    def test_relative_strength_percentage_vectorized(self):
        """Test vectorized RSP calculation"""
        # Create sample price data
        dates = pd.date_range("2023-01-01", periods=300, freq="D")
        np.random.seed(42)

        data = []
        codes = ["1001", "1002", "1003"]

        for code in codes:
            base_price = 100.0
            current_price = base_price

            for date in dates:
                change = np.random.normal(0.001, 0.02)
                current_price *= 1 + change

                data.append(
                    {
                        "Date": date.strftime("%Y-%m-%d"),
                        "Code": code,
                        "AdjustmentClose": current_price,
                    }
                )

        df = pd.DataFrame(data)

        result = relative_strength_percentage_vectorized(df, period=200)

        assert isinstance(result, pd.DataFrame)
        assert "RelativeStrengthPercentage" in result.columns
        assert len(result) > 0

    def test_init_results_db(self, temp_results_database):
        """Test initialization of results database"""
        init_results_db(temp_results_database)

        # Check that table was created
        conn = sqlite3.connect(temp_results_database)
        tables = conn.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='relative_strength'
        """).fetchall()
        assert len(tables) == 1

        # Check table structure
        columns = conn.execute("PRAGMA table_info(relative_strength)").fetchall()
        column_names = [col[1] for col in columns]
        expected_columns = [
            "Date",
            "Code",
            "RelativeStrengthPercentage",
            "RelativeStrengthIndex",
        ]
        assert all(col in column_names for col in expected_columns)

        conn.close()


if __name__ == "__main__":
    pytest.main([__file__])
