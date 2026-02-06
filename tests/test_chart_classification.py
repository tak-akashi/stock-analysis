"""
Pytest tests for chart_classification.py
"""

import os
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from market_pipeline.analysis.chart_classification import (
    ChartClassifier,
    OptimizedChartClassifier,
    BatchDataLoader,
    BatchResultsProcessor,
    DatabaseManager,
    get_all_tickers,
    get_adaptive_windows,
    init_results_db,
    save_result_to_db,
    main_sample,
    main,
)

# --- Fixtures ---


@pytest.fixture
def mock_db_connections(mocker):
    """Mocks all database interactions (read and write)."""
    # Mock for sqlite3.connect
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.return_value = None  # Ensure execute returns something
    mock_conn.commit.return_value = None  # Mock commit as well

    # Explicitly set __enter__ and __exit__ for the context manager
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False  # Indicate no exception was handled

    mocker.patch("sqlite3.connect", return_value=mock_conn)

    # Mock for pandas.read_sql_query
    mock_df_stock = pd.DataFrame(
        {
            "Date": pd.to_datetime(pd.date_range(start="2024-01-01", periods=300)),
            "AdjustmentClose": np.linspace(100, 150, 300),
        }
    )
    mock_df_master = pd.DataFrame({"jquants_code": ["101", "102", "103"]})

    def mock_read_sql_query(query, conn, params=None, parse_dates=None):
        if "FROM daily_quotes" in query:
            return mock_df_stock
        elif "FROM stocks_master" in query:
            return mock_df_master
        return pd.DataFrame()  # Default empty dataframe

    mocker.patch("pandas.read_sql_query", side_effect=mock_read_sql_query)

    return mock_conn


@pytest.fixture
def classifier_instance(mock_db_connections):
    """Returns a standard ChartClassifier instance for testing."""
    # The mock_db_connections fixture already sets up the necessary mocks
    return ChartClassifier(ticker="99999", window=30)


# --- Test Cases ---


def test_chart_classifier_initialization(classifier_instance):
    """Test if the ChartClassifier initializes correctly."""
    assert classifier_instance.ticker == "99999"
    assert classifier_instance.window == 30
    assert len(classifier_instance.price_data) > 0
    assert len(classifier_instance.templates_manual) == 9
    assert "上昇" in classifier_instance.templates_manual


def test_initialization_not_enough_data(mock_db_connections):
    """Test that initialization raises ValueError if there is not enough data."""
    # Override the mock_df_stock for this specific test
    # We need to patch pandas.read_sql_query specifically for this test
    with patch(
        "pandas.read_sql_query",
        return_value=pd.DataFrame(
            {
                "Date": pd.to_datetime(pd.date_range(start="2024-01-01", periods=10)),
                "AdjustmentClose": np.linspace(100, 150, 10),
            }
        ),
    ):
        with pytest.raises(ValueError, match="Not enough data for ticker"):
            ChartClassifier(ticker="12345", window=20)


def test_normalize():
    """Test the static _normalize method."""
    arr = np.array([10, 20, 30, 40, 50])
    normalized = ChartClassifier._normalize(arr)
    assert np.isclose(normalized.min(), 0.0)
    assert np.isclose(normalized.max(), 1.0)
    assert np.allclose(normalized, np.array([0.0, 0.25, 0.5, 0.75, 1.0]))


def test_classify_latest(classifier_instance):
    """Test the classification of the latest window of data."""
    # Create price data that perfectly matches the '上昇' pattern with date index
    perfect_rise = np.linspace(100, 200, 30)
    date_index = pd.date_range(start="2024-01-01", periods=30)
    classifier_instance.price_data = pd.Series(perfect_rise, index=date_index)

    label, score, latest_date = classifier_instance.classify_latest()

    assert label == "上昇"
    assert np.isclose(score, 1.0)
    assert latest_date == "2024-01-30"


def test_save_classification_plot(mocker, classifier_instance):
    """Test that the plot saving function calls the correct file system and plotting methods."""
    mock_makedirs = mocker.patch("os.makedirs")
    mock_savefig = mocker.patch("matplotlib.pyplot.savefig")
    mocker.patch("matplotlib.pyplot.close")  # Don't need to test this, just mock it

    output_dir = "/tmp/test_output"
    classifier_instance.save_classification_plot("上昇", 0.95, output_dir)

    mock_makedirs.assert_called_once_with(output_dir, exist_ok=True)
    expected_path = os.path.join(output_dir, "99999_window30_上昇.png")
    mock_savefig.assert_called_once_with(expected_path)


# --- Test Database and Main Functions ---


def test_get_all_tickers(mock_db_connections):
    """Test fetching all tickers from the master DB."""
    # mock_db_connections already sets up pandas.read_sql_query for master DB
    tickers = get_all_tickers("dummy/master.db")
    assert tickers == ["101", "102", "103"]


def test_init_results_db(mock_db_connections):
    """Test the initialization of the results database."""
    init_results_db("dummy/results.db")
    cursor = mock_db_connections.cursor()
    # Check that the CREATE TABLE query was executed
    cursor.execute.assert_called_once()
    assert "CREATE TABLE IF NOT EXISTS" in cursor.execute.call_args[0][0]


def test_save_result_to_db(mock_db_connections):
    """Test saving a single result to the database."""
    save_result_to_db("dummy/results.db", "2024-07-11", "12345", 60, "調整", 0.88)
    cursor = mock_db_connections.cursor()
    cursor.execute.assert_called_once()
    sql, params = cursor.execute.call_args[0]
    assert "INSERT OR REPLACE INTO" in sql
    assert params == ("2024-07-11", "12345", 60, "調整", 0.88)


@patch("market_pipeline.analysis.chart_classification.OptimizedChartClassifier")
def test_main_sample(MockClassifier, mock_db_connections):
    """Test the main_sample function to ensure it loops and calls correctly."""
    # Mock the instance methods
    mock_instance = MagicMock()
    mock_instance.classify_latest.return_value = ("上昇", 0.99, "2024-01-01")
    MockClassifier.return_value = mock_instance

    main_sample()

    # Check if the classifier was instantiated for all tickers and windows
    tickers = ["74530", "99840", "67580"]
    windows = [20, 60, 120, 240]
    assert MockClassifier.call_count == len(tickers) * len(windows)

    # Check if the plot saving method was called for each
    assert mock_instance.save_classification_plot.call_count == len(tickers) * len(
        windows
    )


@pytest.mark.skip(
    reason="main_full_run has been replaced by main_full_run_optimized with different architecture"
)
def test_main_full_run(mock_db_connections):
    """Test the main_full_run function - SKIPPED due to architecture change."""
    pass


@pytest.mark.parametrize(
    "mode, expected_func",
    [
        ("sample", "main_sample"),
        ("sample-adaptive", "main_sample_adaptive"),
        ("full", "main_full_run_optimized"),
        ("full-optimized", "main_full_run_optimized"),
    ],
)
def test_main_argparse_dispatch(mocker, mode, expected_func):
    """Test that the correct main function is called based on the --mode arg."""
    # Patch the actual main functions that `main()` will call
    mock_main_sample = mocker.patch(
        "market_pipeline.analysis.chart_classification.main_sample"
    )
    mock_main_sample_adaptive = mocker.patch(
        "market_pipeline.analysis.chart_classification.main_sample_adaptive"
    )
    mock_main_full_run_optimized = mocker.patch(
        "market_pipeline.analysis.chart_classification.main_full_run_optimized"
    )

    # Simulate command-line arguments
    mocker.patch("sys.argv", ["script_name", "--mode", mode])

    # Call the top-level main function that parses args and dispatches
    main()

    if expected_func == "main_sample":
        mock_main_sample.assert_called_once()
        mock_main_sample_adaptive.assert_not_called()
        mock_main_full_run_optimized.assert_not_called()
    elif expected_func == "main_sample_adaptive":
        mock_main_sample.assert_not_called()
        mock_main_sample_adaptive.assert_called_once()
        mock_main_full_run_optimized.assert_not_called()
    else:  # main_full_run_optimized (for both 'full' and 'full-optimized')
        mock_main_sample.assert_not_called()
        mock_main_sample_adaptive.assert_not_called()
        mock_main_full_run_optimized.assert_called_once()


# --- Test get_adaptive_windows function ---


class TestGetAdaptiveWindows:
    """Tests for the get_adaptive_windows utility function."""

    def test_short_data_returns_base_windows(self):
        """Data less than 960 days should return only base windows."""
        windows = get_adaptive_windows(500)
        assert windows == [20, 60, 120, 240]

    def test_medium_data_includes_960(self):
        """Data between 960 and 1200 days should include 960-day window."""
        windows = get_adaptive_windows(1000)
        assert windows == [20, 60, 120, 240, 960]

    def test_long_data_includes_1200(self):
        """Data >= 1200 days should include 1200-day window."""
        windows = get_adaptive_windows(1200)
        assert windows == [20, 60, 120, 240, 1200]

    def test_very_long_data(self):
        """Data > 1200 days should still use 1200-day window."""
        windows = get_adaptive_windows(2000)
        assert windows == [20, 60, 120, 240, 1200]

    def test_boundary_960(self):
        """Test exact boundary at 960 days."""
        windows = get_adaptive_windows(960)
        assert 960 in windows
        assert 1200 not in windows

    def test_boundary_1199(self):
        """Test just below 1200 boundary."""
        windows = get_adaptive_windows(1199)
        assert 960 in windows
        assert 1200 not in windows


# --- Test normalize edge cases ---


class TestNormalizeEdgeCases:
    """Tests for _normalize method edge cases."""

    def test_normalize_empty_array_raises(self):
        """Empty array should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot normalize empty array"):
            OptimizedChartClassifier._normalize(np.array([]))

    def test_normalize_single_value(self):
        """Single value should normalize to 0.5."""
        result = OptimizedChartClassifier._normalize(np.array([42]))
        assert len(result) == 1
        assert result[0] == 0.5


# --- Test BatchDataLoader ---


class TestBatchDataLoader:
    """Tests for the BatchDataLoader class."""

    def test_load_all_ticker_data(self, mocker, tmp_path):
        """Test batch loading of ticker data."""
        from datetime import datetime, timedelta

        # Create a temporary database
        db_path = tmp_path / "test.db"
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE daily_quotes (
                Code TEXT, Date TEXT, AdjustmentClose REAL
            )
        """)
        # Insert test data with recent dates
        today = datetime.today()
        for i in range(100):
            date = (today - timedelta(days=100 - i)).strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT INTO daily_quotes VALUES (?, ?, ?)", ("1001", date, 100 + i)
            )
            cursor.execute(
                "INSERT INTO daily_quotes VALUES (?, ?, ?)", ("1002", date, 200 + i)
            )
        conn.commit()
        conn.close()

        logger = mocker.MagicMock()
        loader = BatchDataLoader(str(db_path), logger)
        result = loader.load_all_ticker_data(["1001", "1002"], days=150)

        assert "1001" in result
        assert "1002" in result
        assert len(result["1001"]) > 0
        assert len(result["1002"]) > 0

    def test_load_empty_ticker_list(self, mocker, tmp_path):
        """Test with empty ticker list."""
        db_path = tmp_path / "test.db"
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE daily_quotes (
                Code TEXT, Date TEXT, AdjustmentClose REAL
            )
        """)
        conn.commit()
        conn.close()

        logger = mocker.MagicMock()
        loader = BatchDataLoader(str(db_path), logger)
        result = loader.load_all_ticker_data([], days=100)

        assert result == {}

    def test_load_missing_ticker(self, mocker, tmp_path):
        """Test loading a ticker that doesn't exist in the database."""
        db_path = tmp_path / "test.db"
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE daily_quotes (
                Code TEXT, Date TEXT, AdjustmentClose REAL
            )
        """)
        conn.commit()
        conn.close()

        logger = mocker.MagicMock()
        loader = BatchDataLoader(str(db_path), logger)
        result = loader.load_all_ticker_data(["9999"], days=100)

        assert "9999" in result
        assert result["9999"].empty

    def test_long_term_data_loading(self, mocker, tmp_path):
        """Test loading data with days > 1000 (long-term analysis mode)."""
        db_path = tmp_path / "test.db"
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE daily_quotes (
                Code TEXT, Date TEXT, AdjustmentClose REAL
            )
        """)
        # Insert minimal test data
        cursor.execute(
            "INSERT INTO daily_quotes VALUES (?, ?, ?)", ("1001", "2024-01-01", 100)
        )
        conn.commit()
        conn.close()

        logger = mocker.MagicMock()
        loader = BatchDataLoader(str(db_path), logger)
        loader.load_all_ticker_data(
            ["1001"], days=1500
        )  # Result not needed, testing logging

        # Should log "Loading ALL available data" message
        assert any(
            "ALL available data" in str(call) for call in logger.info.call_args_list
        )


# --- Test BatchResultsProcessor ---


class TestBatchResultsProcessor:
    """Tests for the BatchResultsProcessor class."""

    def test_add_and_flush_results(self, mocker, tmp_path):
        """Test adding results and flushing to database."""
        db_path = tmp_path / "results.db"
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE classification_results (
                date TEXT, ticker TEXT, window INTEGER,
                pattern_label TEXT, score REAL,
                PRIMARY KEY (date, ticker, window)
            )
        """)
        conn.commit()
        conn.close()

        logger = mocker.MagicMock()
        processor = BatchResultsProcessor(str(db_path), logger, batch_size=10)

        # Add results
        processor.add_result("2024-01-01", "1001", 20, "上昇", 0.95)
        processor.add_result("2024-01-01", "1002", 20, "下落", 0.88)

        # Manually flush
        processor.flush_results()

        # Verify data was saved
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM classification_results")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2

    def test_auto_flush_on_batch_full(self, mocker, tmp_path):
        """Test auto-flush when batch size is reached."""
        db_path = tmp_path / "results.db"
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE classification_results (
                date TEXT, ticker TEXT, window INTEGER,
                pattern_label TEXT, score REAL,
                PRIMARY KEY (date, ticker, window)
            )
        """)
        conn.commit()
        conn.close()

        logger = mocker.MagicMock()
        processor = BatchResultsProcessor(str(db_path), logger, batch_size=3)

        # Add 3 results - should trigger auto-flush
        processor.add_result("2024-01-01", "1001", 20, "上昇", 0.95)
        processor.add_result("2024-01-01", "1002", 20, "下落", 0.88)
        processor.add_result("2024-01-01", "1003", 20, "調整", 0.75)

        # Verify data was saved (auto-flushed)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM classification_results")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 3
        assert len(processor.pending_results) == 0

    def test_context_manager_flushes_on_exit(self, mocker, tmp_path):
        """Test that context manager flushes pending results on exit."""
        db_path = tmp_path / "results.db"
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE classification_results (
                date TEXT, ticker TEXT, window INTEGER,
                pattern_label TEXT, score REAL,
                PRIMARY KEY (date, ticker, window)
            )
        """)
        conn.commit()
        conn.close()

        logger = mocker.MagicMock()

        with BatchResultsProcessor(str(db_path), logger, batch_size=100) as processor:
            processor.add_result("2024-01-01", "1001", 20, "上昇", 0.95)

        # Verify data was flushed on exit
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM classification_results")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1

    def test_flush_empty_results(self, mocker, tmp_path):
        """Test flushing with no pending results does nothing."""
        db_path = tmp_path / "results.db"

        logger = mocker.MagicMock()
        processor = BatchResultsProcessor(str(db_path), logger)

        # Should not raise error
        processor.flush_results()
        assert len(processor.pending_results) == 0


# --- Test DatabaseManager ---


class TestDatabaseManager:
    """Tests for the DatabaseManager context manager."""

    def test_context_manager_opens_and_closes(self, tmp_path):
        """Test that context manager properly opens and closes connection."""
        db_path = tmp_path / "test.db"

        with DatabaseManager(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test (id INTEGER)")
            conn.commit()

        # Verify file was created
        assert db_path.exists()

    def test_pragma_settings_applied(self, tmp_path):
        """Test that PRAGMA optimizations are applied."""
        db_path = tmp_path / "test.db"

        with DatabaseManager(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            # WAL mode should be set
            assert journal_mode.lower() == "wal"


# --- Test find_best_match edge cases ---


class TestFindBestMatchEdgeCases:
    """Tests for _find_best_match edge cases."""

    def test_length_mismatch_warning(self, mocker, capsys):
        """Test that length mismatch triggers warning and skips template."""
        # Create classifier with window=30
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mocker.patch("sqlite3.connect", return_value=mock_conn)

        date_index = pd.date_range(start="2024-01-01", periods=30)
        price_data = pd.Series(np.linspace(100, 200, 30), index=date_index)

        classifier = OptimizedChartClassifier(
            ticker="9999", window=30, price_data=price_data
        )

        # Manually add a template with wrong length
        classifier.templates_manual["wrong_length"] = np.array([1, 2, 3])

        # This should print a warning but not crash
        label, score = classifier._find_best_match(
            price_data.values, classifier.templates_manual
        )

        # Should still return a valid match from correct templates
        assert label is not None
        assert score > -np.inf

        captured = capsys.readouterr()
        assert "Warning: Length mismatch" in captured.out


# --- Test check_ticker_data_length ---


class TestCheckTickerDataLength:
    """Tests for BatchDataLoader.check_ticker_data_length method."""

    def test_check_ticker_data_length(self, mocker, tmp_path):
        """Test checking data length for a single ticker."""
        from datetime import datetime, timedelta

        db_path = tmp_path / "test.db"
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE daily_quotes (
                Code TEXT, Date TEXT, AdjustmentClose REAL
            )
        """)
        # Insert 50 days of data
        today = datetime.today()
        for i in range(50):
            date = (today - timedelta(days=50 - i)).strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT INTO daily_quotes VALUES (?, ?, ?)", ("1001", date, 100 + i)
            )
        conn.commit()
        conn.close()

        logger = mocker.MagicMock()
        loader = BatchDataLoader(str(db_path), logger)
        count = loader.check_ticker_data_length("1001")

        assert count == 50

    def test_check_ticker_data_length_empty(self, mocker, tmp_path):
        """Test checking data length for non-existent ticker."""
        db_path = tmp_path / "test.db"
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE daily_quotes (
                Code TEXT, Date TEXT, AdjustmentClose REAL
            )
        """)
        conn.commit()
        conn.close()

        logger = mocker.MagicMock()
        loader = BatchDataLoader(str(db_path), logger)
        count = loader.check_ticker_data_length("9999")

        assert count == 0


# --- Test get_all_tickers error handling ---


class TestGetAllTickersErrors:
    """Tests for get_all_tickers error handling."""

    def test_get_all_tickers_db_error(self, mocker, tmp_path):
        """Test error handling when database read fails."""
        # Create an invalid database path
        result = get_all_tickers("/nonexistent/path/master.db")
        assert result == []


# --- Test OptimizedChartClassifier additional cases ---


class TestOptimizedChartClassifierAdditional:
    """Additional tests for OptimizedChartClassifier."""

    def test_no_price_data_raises(self, mocker):
        """Test that classify_latest raises when no data available."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mocker.patch("sqlite3.connect", return_value=mock_conn)

        # Create classifier with empty price data
        date_index = pd.DatetimeIndex([])

        classifier = OptimizedChartClassifier(
            ticker="9999",
            window=30,
            price_data=pd.Series([], index=date_index, dtype=float),
        )

        with pytest.raises(ValueError, match="No price data available"):
            classifier.classify_latest()

    def test_nan_score_handled(self, mocker):
        """Test that NaN correlation scores are converted to 0."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mocker.patch("sqlite3.connect", return_value=mock_conn)

        # Create constant data that would produce NaN correlation
        date_index = pd.date_range(start="2024-01-01", periods=30)
        constant_data = pd.Series([100.0] * 30, index=date_index)

        classifier = OptimizedChartClassifier(
            ticker="9999", window=30, price_data=constant_data
        )

        # Should not raise - NaN scores should be handled
        label, score, _ = classifier.classify_latest()
        assert label is not None
        assert not np.isnan(score)
