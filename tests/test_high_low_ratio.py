import pytest
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

from market_pipeline.analysis.high_low_ratio import (
    init_hl_ratio_db,
    calc_hl_ratio_for_all,
    calc_ratios_vectorized,
)

@pytest.fixture
def setup_source_db(tmp_path):
    """Provides a temporary database file path with a populated 'daily_quotes' table."""
    db_path = tmp_path / "test_source.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE daily_quotes (
            Date TEXT, Code TEXT, High REAL, Low REAL, AdjustmentClose REAL
        )
    """)
    
    end_date = datetime(2023, 12, 31)
    for i in range(280):
        date = (end_date - timedelta(days=i)).strftime('%Y-%m-%d')
        price = 100 + i
        cursor.execute(
            "INSERT INTO daily_quotes VALUES (?, '1301', ?, ?, ?)",
            (date, price + 5, price - 5, price)
        )
    conn.commit()
    conn.close()
    
    yield db_path

def test_init_hl_ratio_db(tmp_path):
    """Tests that the hl_ratio table is created correctly in a file database."""
    db_path = tmp_path / "test_dest.db"
    init_hl_ratio_db(db_path=str(db_path))
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hl_ratio'")
    assert cursor.fetchone() is not None, "The 'hl_ratio' table was not created."
    
    # Check that MedianRatio column exists
    cursor.execute("PRAGMA table_info(hl_ratio)")
    columns = [row[1] for row in cursor.fetchall()]
    assert 'MedianRatio' in columns, "MedianRatio column was not created."
    conn.close()

def test_calc_hl_ratio_for_all(setup_source_db):
    """
    Tests that calc_hl_ratio_for_all correctly calculates the ratio
    and returns a DataFrame, using a file-based database.
    """
    db_path = setup_source_db
    end_date = '2023-12-31'
    weeks = 52

    results_df = calc_hl_ratio_for_all(db_path=str(db_path), end_date=end_date, weeks=weeks)

    assert isinstance(results_df, pd.DataFrame)
    assert not results_df.empty
    row = results_df[results_df['Code'] == '1301'].iloc[0]
    assert 0.0 <= row['HlRatio'] <= 100.0
    assert 0.0 <= row['MedianRatio'] <= 100.0
    assert 'MedianRatio' in results_df.columns

def test_calc_ratios_vectorized():
    """Unit test for the vectorized ratio calculation logic."""
    end_date = datetime(2023, 12, 31)
    dates = [end_date - timedelta(days=i) for i in range(260)]
    prices = [100 + i for i in range(260)]
    price_df = pd.DataFrame({
        'Date': [d.strftime('%Y-%m-%d') for d in dates],
        'Code': ['1301'] * 260,
        'High': [p + 5 for p in prices],
        'Low': [p - 5 for p in prices],
        'AdjustmentClose': prices
    })

    result_df = calc_ratios_vectorized(price_df, weeks=52)

    assert isinstance(result_df, pd.DataFrame)
    assert 'HlRatio' in result_df.columns
    assert 'MedianRatio' in result_df.columns

    # Check that the ratio values are within expected range
    if not result_df.empty:
        assert 0.0 <= result_df['HlRatio'].iloc[0] <= 100.0
        assert 0.0 <= result_df['MedianRatio'].iloc[0] <= 100.0