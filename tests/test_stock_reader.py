"""
Tests for stock_reader package.

Tests cover:
- Code normalization (4-digit/5-digit conversion)
- Date validation
- Single/multiple stock price retrieval
- Column selection (simple/full/list)
- Default date handling
- Error handling (strict/non-strict modes)
"""

import sqlite3
import warnings
from datetime import datetime

import pandas as pd
import pytest


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def stock_reader_database(tmp_path):
    """Create a test database with full daily_quotes schema for stock_reader tests."""
    db_path = tmp_path / "test_jquants.db"
    conn = sqlite3.connect(db_path)

    # Create daily_quotes table with full schema
    conn.execute("""
    CREATE TABLE IF NOT EXISTS daily_quotes (
        Date TEXT,
        Code TEXT,
        Open REAL,
        High REAL,
        Low REAL,
        Close REAL,
        UpperLimit TEXT,
        LowerLimit TEXT,
        Volume REAL,
        TurnoverValue REAL,
        AdjustmentFactor REAL,
        AdjustmentOpen REAL,
        AdjustmentHigh REAL,
        AdjustmentLow REAL,
        AdjustmentClose REAL,
        AdjustmentVolume REAL
    )
    """)

    # Create indexes
    conn.execute("CREATE INDEX idx_code ON daily_quotes (Code)")
    conn.execute("CREATE INDEX idx_date ON daily_quotes (Date)")
    conn.execute("CREATE UNIQUE INDEX idx_code_date ON daily_quotes (Code, Date)")

    # Insert test data for Toyota (7203) - stored as 72030 in DB
    toyota_data = [
        ("2024-01-04", "72030", 2500.0, 2550.0, 2480.0, 2520.0, "2700", "2300",
         1000000.0, 2520000000.0, 1.0, 2500.0, 2550.0, 2480.0, 2520.0, 1000000.0),
        ("2024-01-05", "72030", 2520.0, 2600.0, 2510.0, 2580.0, "2720", "2320",
         1200000.0, 3096000000.0, 1.0, 2520.0, 2600.0, 2510.0, 2580.0, 1200000.0),
        ("2024-01-08", "72030", 2580.0, 2620.0, 2560.0, 2600.0, "2780", "2380",
         1100000.0, 2860000000.0, 1.0, 2580.0, 2620.0, 2560.0, 2600.0, 1100000.0),
        ("2024-01-09", "72030", 2600.0, 2650.0, 2590.0, 2640.0, "2800", "2400",
         1300000.0, 3432000000.0, 1.0, 2600.0, 2650.0, 2590.0, 2640.0, 1300000.0),
        ("2024-01-10", "72030", 2640.0, 2680.0, 2620.0, 2660.0, "2840", "2440",
         1150000.0, 3059000000.0, 1.0, 2640.0, 2680.0, 2620.0, 2660.0, 1150000.0),
    ]

    # Insert test data for SoftBank (9984) - stored as 99840 in DB
    softbank_data = [
        ("2024-01-04", "99840", 8000.0, 8100.0, 7950.0, 8050.0, "8500", "7500",
         500000.0, 4025000000.0, 1.0, 8000.0, 8100.0, 7950.0, 8050.0, 500000.0),
        ("2024-01-05", "99840", 8050.0, 8200.0, 8000.0, 8150.0, "8550", "7550",
         600000.0, 4890000000.0, 1.0, 8050.0, 8200.0, 8000.0, 8150.0, 600000.0),
        ("2024-01-08", "99840", 8150.0, 8250.0, 8100.0, 8200.0, "8650", "7650",
         550000.0, 4510000000.0, 1.0, 8150.0, 8250.0, 8100.0, 8200.0, 550000.0),
        ("2024-01-09", "99840", 8200.0, 8300.0, 8150.0, 8250.0, "8700", "7700",
         650000.0, 5362500000.0, 1.0, 8200.0, 8300.0, 8150.0, 8250.0, 650000.0),
        ("2024-01-10", "99840", 8250.0, 8350.0, 8200.0, 8300.0, "8750", "7750",
         580000.0, 4814000000.0, 1.0, 8250.0, 8350.0, 8200.0, 8300.0, 580000.0),
    ]

    conn.executemany(
        """
        INSERT INTO daily_quotes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        toyota_data + softbank_data,
    )

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def empty_database(tmp_path):
    """Create an empty test database with schema but no data."""
    db_path = tmp_path / "empty_jquants.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS daily_quotes (
        Date TEXT,
        Code TEXT,
        Open REAL,
        High REAL,
        Low REAL,
        Close REAL,
        UpperLimit TEXT,
        LowerLimit TEXT,
        Volume REAL,
        TurnoverValue REAL,
        AdjustmentFactor REAL,
        AdjustmentOpen REAL,
        AdjustmentHigh REAL,
        AdjustmentLow REAL,
        AdjustmentClose REAL,
        AdjustmentVolume REAL
    )
    """)
    conn.commit()
    conn.close()
    return db_path


# =============================================================================
# Tests for utils.py - normalize_code
# =============================================================================


class TestNormalizeCode:
    """Tests for normalize_code function."""

    def test_normalize_code_4digit(self):
        """4-digit code should remain unchanged."""
        from market_reader.utils import normalize_code

        assert normalize_code("7203") == "7203"
        assert normalize_code("9984") == "9984"
        assert normalize_code("1234") == "1234"

    def test_normalize_code_5digit(self):
        """5-digit code ending with 0 should be converted to 4-digit."""
        from market_reader.utils import normalize_code

        assert normalize_code("72030") == "7203"
        assert normalize_code("99840") == "9984"
        assert normalize_code("12340") == "1234"

    def test_normalize_code_5digit_non_zero(self):
        """5-digit code not ending with 0 should remain unchanged."""
        from market_reader.utils import normalize_code

        assert normalize_code("72031") == "72031"
        assert normalize_code("99845") == "99845"


# =============================================================================
# Tests for utils.py - validate_date
# =============================================================================


class TestValidateDate:
    """Tests for validate_date function."""

    def test_validate_date_valid(self):
        """Valid date string should be converted to datetime."""
        from market_reader.utils import validate_date

        result = validate_date("2024-01-01")
        assert isinstance(result, datetime)
        assert result == datetime(2024, 1, 1)

    def test_validate_date_none(self):
        """None input should return None."""
        from market_reader.utils import validate_date

        assert validate_date(None) is None

    def test_validate_date_invalid_format(self):
        """Invalid date format should raise ValueError."""
        from market_reader.utils import validate_date

        with pytest.raises(ValueError):
            validate_date("01-01-2024")  # Wrong format

    def test_validate_date_invalid_value(self):
        """Invalid date value should raise ValueError."""
        from market_reader.utils import validate_date

        with pytest.raises(ValueError):
            validate_date("2024-13-01")  # Invalid month

        with pytest.raises(ValueError):
            validate_date("2024-02-30")  # Invalid day


# =============================================================================
# Tests for DataReader - get_prices single code
# =============================================================================


class TestGetPricesSingleCode:
    """Tests for get_prices with single stock code."""

    def test_get_prices_single_code(self, stock_reader_database):
        """Single code should return DataFrame with Date index."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database)
        df = reader.get_prices("7203", start="2024-01-04", end="2024-01-10")

        assert isinstance(df, pd.DataFrame)
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.name == "Date"
        assert len(df) == 5  # 5 trading days

    def test_get_prices_5digit_code(self, stock_reader_database):
        """5-digit code should be normalized and work correctly."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database)
        df = reader.get_prices("72030", start="2024-01-04", end="2024-01-10")

        assert len(df) == 5

    def test_get_prices_date_index_type(self, stock_reader_database):
        """DataFrame index should be datetime type."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database)
        df = reader.get_prices("7203", start="2024-01-04", end="2024-01-10")

        assert pd.api.types.is_datetime64_any_dtype(df.index)


# =============================================================================
# Tests for DataReader - get_prices multiple codes
# =============================================================================


class TestGetPricesMultipleCodes:
    """Tests for get_prices with multiple stock codes."""

    def test_get_prices_multiple_codes(self, stock_reader_database):
        """Multiple codes should return MultiIndex DataFrame."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database)
        df = reader.get_prices(
            ["7203", "9984"], start="2024-01-04", end="2024-01-10"
        )

        assert isinstance(df, pd.DataFrame)
        assert isinstance(df.index, pd.MultiIndex)
        assert df.index.names == ["Date", "Code"]

    def test_get_prices_multiindex_access(self, stock_reader_database):
        """MultiIndex DataFrame should support date/code access."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database)
        df = reader.get_prices(
            ["7203", "9984"], start="2024-01-04", end="2024-01-10"
        )

        # Access by date and code
        jan4_data = df.loc["2024-01-04"]
        assert len(jan4_data) == 2  # 2 stocks

    def test_get_prices_code_normalized_in_output(self, stock_reader_database):
        """Output DataFrame should have 4-digit codes."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database)
        df = reader.get_prices(
            ["7203", "9984"], start="2024-01-04", end="2024-01-10"
        )

        codes = df.index.get_level_values("Code").unique()
        assert "7203" in codes
        assert "9984" in codes
        assert "72030" not in codes
        assert "99840" not in codes


# =============================================================================
# Tests for DataReader - column selection
# =============================================================================


class TestGetPricesColumns:
    """Tests for column selection in get_prices."""

    def test_get_prices_columns_simple(self, stock_reader_database):
        """columns='simple' should return 6 columns."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database)
        df = reader.get_prices(
            "7203", start="2024-01-04", end="2024-01-10", columns="simple"
        )

        expected_columns = [
            "Open", "High", "Low", "Close", "Volume", "AdjustmentClose"
        ]
        assert list(df.columns) == expected_columns

    def test_get_prices_columns_full(self, stock_reader_database):
        """columns='full' should return all 16 columns."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database)
        df = reader.get_prices(
            "7203", start="2024-01-04", end="2024-01-10", columns="full"
        )

        # Full columns (Date and Code are in index, not columns)
        expected_column_count = 14  # 16 total - Date (index) - Code (not in single)
        assert len(df.columns) == expected_column_count

    def test_get_prices_columns_list(self, stock_reader_database):
        """columns as list should return specified columns only."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database)
        df = reader.get_prices(
            "7203",
            start="2024-01-04",
            end="2024-01-10",
            columns=["Open", "Close"],
        )

        assert list(df.columns) == ["Open", "Close"]

    def test_get_prices_columns_invalid(self, stock_reader_database):
        """Invalid column name should raise ValueError."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database)

        with pytest.raises(ValueError) as exc_info:
            reader.get_prices(
                "7203",
                start="2024-01-04",
                end="2024-01-10",
                columns=["Open", "InvalidColumn"],
            )

        assert "InvalidColumn" in str(exc_info.value)


# =============================================================================
# Tests for DataReader - default dates
# =============================================================================


class TestGetPricesDefaultDates:
    """Tests for default date handling in get_prices."""

    def test_get_prices_default_end_date(self, stock_reader_database):
        """Omitting end date should use latest date in DB."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database)
        df = reader.get_prices("7203", start="2024-01-04")

        # Latest date in test data is 2024-01-10
        assert df.index.max() == pd.Timestamp("2024-01-10")

    def test_get_prices_default_start_date(self, stock_reader_database):
        """Omitting start date should use 5 years before end date."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database)
        # Since test data only has 5 days, this tests the mechanism
        df = reader.get_prices("7203", end="2024-01-10")

        # Should return all available data (start is before our test data)
        assert len(df) == 5

    def test_get_prices_empty_database_error(self, empty_database):
        """Empty database should raise ValueError for default dates."""
        from market_reader import DataReader

        reader = DataReader(db_path=empty_database)

        # No end date specified on empty DB should raise error
        with pytest.raises(ValueError) as exc_info:
            reader.get_prices("7203")

        assert "No data found" in str(exc_info.value)


# =============================================================================
# Tests for DataReader - strict mode
# =============================================================================


class TestStrictModeStockNotFound:
    """Tests for strict=True with non-existent stock."""

    def test_strict_mode_stock_not_found(self, stock_reader_database):
        """strict=True should raise StockNotFoundError for non-existent code."""
        from market_reader import DataReader
        from market_reader.exceptions import StockNotFoundError

        reader = DataReader(db_path=stock_reader_database, strict=True)

        with pytest.raises(StockNotFoundError) as exc_info:
            reader.get_prices("9999", start="2024-01-04", end="2024-01-10")

        assert exc_info.value.code == "9999"


class TestNonStrictModeStockNotFound:
    """Tests for strict=False with non-existent stock."""

    def test_non_strict_mode_stock_not_found(self, stock_reader_database):
        """strict=False should return empty DataFrame with UserWarning."""
        from market_reader import DataReader

        reader = DataReader(db_path=stock_reader_database, strict=False)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            df = reader.get_prices("9999", start="2024-01-04", end="2024-01-10")

            assert len(df) == 0
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "9999" in str(w[0].message)


# =============================================================================
# Tests for DataReader - invalid date range
# =============================================================================


class TestInvalidDateRange:
    """Tests for invalid date range handling."""

    def test_invalid_date_range(self, stock_reader_database):
        """Start date after end date should raise InvalidDateRangeError."""
        from market_reader import DataReader
        from market_reader.exceptions import InvalidDateRangeError

        reader = DataReader(db_path=stock_reader_database, strict=True)

        with pytest.raises(InvalidDateRangeError):
            reader.get_prices("7203", start="2024-12-31", end="2024-01-01")


# =============================================================================
# Tests for DataReader - database connection error
# =============================================================================


class TestDatabaseConnectionError:
    """Tests for database connection error handling."""

    def test_database_connection_error(self, tmp_path):
        """Invalid DB path should raise DatabaseConnectionError."""
        from market_reader import DataReader
        from market_reader.exceptions import DatabaseConnectionError

        invalid_path = tmp_path / "nonexistent" / "db.db"

        with pytest.raises(DatabaseConnectionError):
            DataReader(db_path=invalid_path)
