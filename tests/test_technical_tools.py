"""Tests for technical_tools package."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Test fixtures path
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_prices() -> pd.DataFrame:
    """Load sample price data for testing."""
    df = pd.read_csv(FIXTURES_DIR / "sample_prices.csv", parse_dates=["Date"])
    df = df.set_index("Date")
    return df


@pytest.fixture
def sample_prices_with_sma(sample_prices: pd.DataFrame) -> pd.DataFrame:
    """Sample prices with pre-calculated SMA columns."""
    df = sample_prices.copy()
    df["SMA_5"] = df["Close"].rolling(window=5).mean()
    df["SMA_10"] = df["Close"].rolling(window=10).mean()
    return df


@pytest.fixture
def sample_prices_with_adjustment(sample_prices: pd.DataFrame) -> pd.DataFrame:
    """Sample prices with adjustment columns (simulating J-Quants full columns)."""
    df = sample_prices.copy()
    # Add adjustment columns (same values as originals for testing)
    df["AdjustmentOpen"] = df["Open"]
    df["AdjustmentHigh"] = df["High"]
    df["AdjustmentLow"] = df["Low"]
    df["AdjustmentClose"] = df["Close"]
    df["AdjustmentVolume"] = df["Volume"]
    df["AdjustmentFactor"] = 1.0
    return df


class TestExceptions:
    """Test custom exception classes."""

    def test_technical_tools_error_base(self) -> None:
        """TechnicalToolsError is base exception."""
        from technical_tools.exceptions import TechnicalToolsError

        error = TechnicalToolsError("test error")
        assert str(error) == "test error"

    def test_data_source_error(self) -> None:
        """DataSourceError inherits from TechnicalToolsError."""
        from technical_tools.exceptions import DataSourceError, TechnicalToolsError

        error = DataSourceError("data source error")
        assert isinstance(error, TechnicalToolsError)

    def test_ticker_not_found_error(self) -> None:
        """TickerNotFoundError has ticker and source attributes."""
        from technical_tools.exceptions import TickerNotFoundError

        error = TickerNotFoundError("7203", "jquants")
        assert error.ticker == "7203"
        assert error.source == "jquants"
        assert "7203" in str(error)
        assert "jquants" in str(error)

    def test_insufficient_data_error(self) -> None:
        """InsufficientDataError shows required vs actual."""
        from technical_tools.exceptions import InsufficientDataError

        error = InsufficientDataError(200, 50)
        assert "200" in str(error)
        assert "50" in str(error)


class TestDataSourceBase:
    """Test DataSource abstract base class."""

    def test_data_source_is_abstract(self) -> None:
        """DataSource cannot be instantiated directly."""
        from technical_tools.data_sources.base import DataSource

        with pytest.raises(TypeError):
            DataSource()  # type: ignore


class TestJQuantsSource:
    """Test JQuantsSource data fetching."""

    def test_jquants_source_uses_market_reader(
        self, sample_prices_with_adjustment: pd.DataFrame
    ) -> None:
        """JQuantsSource wraps market_reader DataReader."""
        from technical_tools.data_sources.jquants import JQuantsSource

        with patch("technical_tools.data_sources.jquants.DataReader") as mock_reader:
            mock_instance = MagicMock()
            mock_instance.get_prices.return_value = sample_prices_with_adjustment
            mock_reader.return_value = mock_instance

            source = JQuantsSource()
            df = source.get_prices("7203", start="2024-01-01", end="2024-02-28")

            mock_instance.get_prices.assert_called_once()
            assert not df.empty
            assert "Open" in df.columns
            assert "Close" in df.columns

    def test_jquants_source_ticker_not_found_empty_df(self) -> None:
        """JQuantsSource raises TickerNotFoundError for empty DataFrame."""
        from technical_tools.data_sources.jquants import JQuantsSource
        from technical_tools.exceptions import TickerNotFoundError

        with patch("technical_tools.data_sources.jquants.DataReader") as mock_reader:
            mock_instance = MagicMock()
            mock_instance.get_prices.return_value = pd.DataFrame()
            mock_reader.return_value = mock_instance

            source = JQuantsSource()
            with pytest.raises(TickerNotFoundError) as exc_info:
                source.get_prices("9999")

            assert exc_info.value.ticker == "9999"
            assert exc_info.value.source == "jquants"

    def test_jquants_invalid_period(self) -> None:
        """JQuantsSource raises ValueError for invalid period."""
        from technical_tools.data_sources.jquants import _period_to_dates

        with pytest.raises(ValueError) as exc_info:
            _period_to_dates("invalid")

        assert "Invalid period" in str(exc_info.value)

    def test_jquants_source_normalizes_columns(
        self, sample_prices_with_adjustment: pd.DataFrame
    ) -> None:
        """JQuantsSource returns DataFrame with standard columns using adjusted prices."""
        from technical_tools.data_sources.jquants import JQuantsSource

        with patch("technical_tools.data_sources.jquants.DataReader") as mock_reader:
            mock_instance = MagicMock()
            mock_instance.get_prices.return_value = sample_prices_with_adjustment
            mock_reader.return_value = mock_instance

            source = JQuantsSource()
            df = source.get_prices("7203")

            expected_cols = {"Open", "High", "Low", "Close", "Volume"}
            assert expected_cols.issubset(set(df.columns))

    def test_jquants_source_with_period(
        self, sample_prices_with_adjustment: pd.DataFrame
    ) -> None:
        """JQuantsSource supports period argument."""
        from technical_tools.data_sources.jquants import JQuantsSource

        with patch("technical_tools.data_sources.jquants.DataReader") as mock_reader:
            mock_instance = MagicMock()
            mock_instance.get_prices.return_value = sample_prices_with_adjustment
            mock_reader.return_value = mock_instance

            source = JQuantsSource()
            df = source.get_prices("7203", period="1y")

            # Verify get_prices was called with start/end dates
            call_args = mock_instance.get_prices.call_args
            assert call_args.kwargs.get("start") is not None
            assert call_args.kwargs.get("end") is not None
            assert not df.empty

    def test_jquants_period_to_dates(self) -> None:
        """Period string is correctly converted to date range."""
        from technical_tools.data_sources.jquants import _period_to_dates

        start, end = _period_to_dates("1y")
        # Verify format is YYYY-MM-DD
        assert len(start) == 10
        assert len(end) == 10
        assert start < end


class TestYFinanceSource:
    """Test YFinanceSource data fetching."""

    def test_yfinance_source_with_period(self, sample_prices: pd.DataFrame) -> None:
        """YFinanceSource supports period argument."""
        from technical_tools.data_sources.yfinance import YFinanceSource

        with patch("technical_tools.data_sources.yfinance.yf") as mock_yf:
            mock_yf.download.return_value = sample_prices
            source = YFinanceSource()
            df = source.get_prices("AAPL", period="1y")

            mock_yf.download.assert_called_once()
            assert not df.empty

    def test_yfinance_source_with_date_range(self, sample_prices: pd.DataFrame) -> None:
        """YFinanceSource supports start/end arguments."""
        from technical_tools.data_sources.yfinance import YFinanceSource

        with patch("technical_tools.data_sources.yfinance.yf") as mock_yf:
            mock_yf.download.return_value = sample_prices
            source = YFinanceSource()
            _ = source.get_prices("AAPL", start="2024-01-01", end="2024-02-28")

            mock_yf.download.assert_called_once()

    def test_yfinance_source_japanese_ticker(self, sample_prices: pd.DataFrame) -> None:
        """YFinanceSource handles Japanese tickers (7203.T format)."""
        from technical_tools.data_sources.yfinance import YFinanceSource

        with patch("technical_tools.data_sources.yfinance.yf") as mock_yf:
            mock_yf.download.return_value = sample_prices
            source = YFinanceSource()
            _ = source.get_prices("7203.T", period="1y")

            call_args = mock_yf.download.call_args
            assert "7203.T" in str(call_args)

    def test_yfinance_source_ticker_not_found_empty_df(self) -> None:
        """YFinanceSource raises TickerNotFoundError for empty DataFrame."""
        from technical_tools.data_sources.yfinance import YFinanceSource
        from technical_tools.exceptions import TickerNotFoundError

        with patch("technical_tools.data_sources.yfinance.yf") as mock_yf:
            mock_yf.download.return_value = pd.DataFrame()
            source = YFinanceSource()

            with pytest.raises(TickerNotFoundError) as exc_info:
                source.get_prices("INVALID", period="1y")

            assert exc_info.value.ticker == "INVALID"
            assert exc_info.value.source == "yfinance"

    def test_yfinance_source_ticker_not_found_exception(self) -> None:
        """YFinanceSource raises TickerNotFoundError when yfinance raises exception."""
        from technical_tools.data_sources.yfinance import YFinanceSource
        from technical_tools.exceptions import TickerNotFoundError

        with patch("technical_tools.data_sources.yfinance.yf") as mock_yf:
            mock_yf.download.side_effect = Exception("Network error")
            source = YFinanceSource()

            with pytest.raises(TickerNotFoundError):
                source.get_prices("AAPL", period="1y")

    def test_yfinance_source_multiindex_columns(self) -> None:
        """YFinanceSource handles MultiIndex columns from yfinance."""
        from technical_tools.data_sources.yfinance import YFinanceSource

        # Create DataFrame with MultiIndex columns (as yfinance sometimes returns)
        data = {
            ("Open", "AAPL"): [100.0, 101.0, 102.0],
            ("High", "AAPL"): [105.0, 106.0, 107.0],
            ("Low", "AAPL"): [99.0, 100.0, 101.0],
            ("Close", "AAPL"): [104.0, 105.0, 106.0],
            ("Volume", "AAPL"): [1000000, 1100000, 1200000],
        }
        df_multiindex = pd.DataFrame(data)
        df_multiindex.index = pd.date_range("2024-01-01", periods=3)

        with patch("technical_tools.data_sources.yfinance.yf") as mock_yf:
            mock_yf.download.return_value = df_multiindex
            source = YFinanceSource()
            df = source.get_prices("AAPL", period="1y")

            # Should have flattened columns
            assert "Open" in df.columns
            assert "Close" in df.columns
            assert not isinstance(df.columns, pd.MultiIndex)

    def test_yfinance_source_non_datetime_index(self) -> None:
        """YFinanceSource converts non-datetime index to DatetimeIndex."""
        from technical_tools.data_sources.yfinance import YFinanceSource

        # Create DataFrame with string index
        data = {
            "Open": [100.0, 101.0],
            "High": [105.0, 106.0],
            "Low": [99.0, 100.0],
            "Close": [104.0, 105.0],
            "Volume": [1000000, 1100000],
        }
        df_str_index = pd.DataFrame(data, index=["2024-01-01", "2024-01-02"])

        with patch("technical_tools.data_sources.yfinance.yf") as mock_yf:
            mock_yf.download.return_value = df_str_index
            source = YFinanceSource()
            df = source.get_prices("AAPL", period="1y")

            assert isinstance(df.index, pd.DatetimeIndex)


class TestIndicators:
    """Test technical indicator calculations."""

    def test_add_sma_single_period(self, sample_prices: pd.DataFrame) -> None:
        """SMA calculation for single period."""
        from technical_tools.indicators import add_sma

        df = add_sma(sample_prices.copy(), periods=[5])
        assert "SMA_5" in df.columns
        # First 4 values should be NaN
        assert df["SMA_5"].iloc[:4].isna().all()
        # 5th value should be average of first 5 closes
        expected = sample_prices["Close"].iloc[:5].mean()
        assert abs(df["SMA_5"].iloc[4] - expected) < 0.01

    def test_add_sma_multiple_periods(self, sample_prices: pd.DataFrame) -> None:
        """SMA calculation for multiple periods."""
        from technical_tools.indicators import add_sma

        df = add_sma(sample_prices.copy(), periods=[5, 10, 20])
        assert "SMA_5" in df.columns
        assert "SMA_10" in df.columns
        assert "SMA_20" in df.columns

    def test_add_ema(self, sample_prices: pd.DataFrame) -> None:
        """EMA calculation."""
        from technical_tools.indicators import add_ema

        df = add_ema(sample_prices.copy(), periods=[12])
        assert "EMA_12" in df.columns

    def test_add_rsi_range(self, sample_prices: pd.DataFrame) -> None:
        """RSI values are within 0-100 range."""
        from technical_tools.indicators import add_rsi

        df = add_rsi(sample_prices.copy(), period=14)
        assert "RSI_14" in df.columns
        # Exclude NaN values
        rsi_values = df["RSI_14"].dropna()
        assert (rsi_values >= 0).all()
        assert (rsi_values <= 100).all()

    def test_add_macd(self, sample_prices: pd.DataFrame) -> None:
        """MACD calculation includes line, signal, and histogram."""
        from technical_tools.indicators import add_macd

        df = add_macd(sample_prices.copy(), fast=12, slow=26, signal=9)
        assert "MACD" in df.columns
        assert "MACD_Signal" in df.columns
        assert "MACD_Hist" in df.columns

    def test_add_bollinger_bands(self, sample_prices: pd.DataFrame) -> None:
        """Bollinger bands include upper, middle, lower."""
        from technical_tools.indicators import add_bollinger_bands

        df = add_bollinger_bands(sample_prices.copy(), period=20, std=2.0)
        assert "BB_Upper" in df.columns
        assert "BB_Middle" in df.columns
        assert "BB_Lower" in df.columns
        # Upper > Middle > Lower
        valid_rows = df.dropna(subset=["BB_Upper", "BB_Middle", "BB_Lower"])
        if not valid_rows.empty:
            assert (valid_rows["BB_Upper"] >= valid_rows["BB_Middle"]).all()
            assert (valid_rows["BB_Middle"] >= valid_rows["BB_Lower"]).all()

    def test_calculate_indicators_multiple(self, sample_prices: pd.DataFrame) -> None:
        """Calculate multiple indicators at once."""
        from technical_tools.indicators import calculate_indicators

        df = calculate_indicators(
            sample_prices.copy(), indicators=["sma", "rsi", "macd", "bb"]
        )
        # Should have SMA columns
        sma_cols = [c for c in df.columns if c.startswith("SMA_")]
        assert len(sma_cols) > 0
        # Should have RSI
        assert any(c.startswith("RSI_") for c in df.columns)

    def test_calculate_indicators_with_ema(self, sample_prices: pd.DataFrame) -> None:
        """Calculate indicators including EMA."""
        from technical_tools.indicators import calculate_indicators

        df = calculate_indicators(sample_prices.copy(), indicators=["ema"])
        # Should have EMA columns
        ema_cols = [c for c in df.columns if c.startswith("EMA_")]
        assert len(ema_cols) > 0

    def test_calculate_indicators_unknown_ignored(self, sample_prices: pd.DataFrame) -> None:
        """Unknown indicators are silently ignored."""
        from technical_tools.indicators import calculate_indicators

        df = calculate_indicators(
            sample_prices.copy(), indicators=["sma", "unknown_indicator"]
        )
        # Should still have SMA columns
        sma_cols = [c for c in df.columns if c.startswith("SMA_")]
        assert len(sma_cols) > 0


class TestSignals:
    """Test signal detection."""

    def test_signal_dataclass(self) -> None:
        """Signal dataclass has required fields."""
        from technical_tools.signals import Signal

        signal = Signal(
            date=datetime(2024, 1, 15),
            signal_type="golden_cross",
            price=2560.0,
            short_period=5,
            long_period=25,
        )
        assert signal.date == datetime(2024, 1, 15)
        assert signal.signal_type == "golden_cross"
        assert signal.price == 2560.0

    def test_detect_golden_cross(self, sample_prices_with_sma: pd.DataFrame) -> None:
        """Detect golden cross when short crosses above long."""
        from technical_tools.signals import detect_crosses

        signals = detect_crosses(sample_prices_with_sma, short=5, long=10)
        # Results depend on data - just verify return type and structure
        assert isinstance(signals, list)
        for s in signals:
            assert s.signal_type in ("golden_cross", "dead_cross")

    def test_detect_dead_cross(self, sample_prices_with_sma: pd.DataFrame) -> None:
        """Detect dead cross when short crosses below long."""
        from technical_tools.signals import detect_crosses

        signals = detect_crosses(sample_prices_with_sma, short=5, long=10)
        dead_crosses = [s for s in signals if s.signal_type == "dead_cross"]
        # Results depend on data - just verify structure
        for s in dead_crosses:
            assert s.short_period == 5
            assert s.long_period == 10

    def test_detect_crosses_sorted_by_date(
        self, sample_prices_with_sma: pd.DataFrame
    ) -> None:
        """Signals are sorted by date."""
        from technical_tools.signals import detect_crosses

        signals = detect_crosses(sample_prices_with_sma, short=5, long=10)
        if len(signals) > 1:
            dates = [s.date for s in signals]
            assert dates == sorted(dates)

    def test_detect_crosses_missing_columns(self, sample_prices: pd.DataFrame) -> None:
        """detect_crosses returns empty list if SMA columns are missing."""
        from technical_tools.signals import detect_crosses

        # No SMA columns in sample_prices
        signals = detect_crosses(sample_prices, short=5, long=10)
        assert signals == []

    def test_detect_crosses_multiple_patterns(
        self, sample_prices_with_sma: pd.DataFrame
    ) -> None:
        """detect_crosses_multiple detects crosses for multiple patterns."""
        from technical_tools.signals import detect_crosses_multiple

        # Add additional SMA columns for multiple patterns
        df = sample_prices_with_sma.copy()
        df["SMA_25"] = df["Close"].rolling(window=25).mean()

        signals = detect_crosses_multiple(df, patterns=[(5, 10), (10, 25)])
        assert isinstance(signals, list)
        # Verify signals are sorted by date
        if len(signals) > 1:
            dates = [s.date for s in signals]
            assert dates == sorted(dates)

    def test_detect_crosses_multiple_default_patterns(
        self, sample_prices: pd.DataFrame
    ) -> None:
        """detect_crosses_multiple uses default patterns when None."""
        from technical_tools.signals import detect_crosses_multiple

        # Add SMA columns for default patterns (5, 25) and (25, 75)
        df = sample_prices.copy()
        df["SMA_5"] = df["Close"].rolling(window=5).mean()
        df["SMA_25"] = df["Close"].rolling(window=25).mean()
        df["SMA_75"] = df["Close"].rolling(window=75).mean()

        signals = detect_crosses_multiple(df, patterns=None)
        assert isinstance(signals, list)

    def test_detect_crosses_with_string_index(self) -> None:
        """detect_crosses handles string date index."""
        from technical_tools.indicators import add_sma
        from technical_tools.signals import detect_crosses

        # Create DataFrame with string index that will cause cross
        dates = [f"2024-01-{i:02d}" for i in range(1, 21)]
        # Prices that cause a golden cross around day 10
        prices = [100 + i for i in range(10)] + [100 - i for i in range(10)]
        df = pd.DataFrame(
            {
                "Open": prices,
                "High": [p + 1 for p in prices],
                "Low": [p - 1 for p in prices],
                "Close": prices,
                "Volume": [1000000] * 20,
            },
            index=dates,
        )
        df = add_sma(df, periods=[3, 5])

        signals = detect_crosses(df, short=3, long=5)
        # Should handle string index conversion
        for s in signals:
            assert isinstance(s.date, datetime)


class TestCharts:
    """Test chart generation."""

    def test_create_chart_returns_figure(self, sample_prices: pd.DataFrame) -> None:
        """create_chart returns a plotly Figure."""
        from technical_tools.charts import create_chart

        fig = create_chart(sample_prices, ticker="7203")
        assert fig is not None
        # Check it's a plotly figure
        assert hasattr(fig, "data")
        assert hasattr(fig, "layout")

    def test_create_chart_with_sma(self, sample_prices: pd.DataFrame) -> None:
        """Chart includes SMA lines when requested."""
        from technical_tools.charts import create_chart
        from technical_tools.indicators import add_sma

        df = add_sma(sample_prices.copy(), periods=[5, 10])
        fig = create_chart(df, ticker="7203", show_sma=[5, 10])
        # Should have traces for SMA
        trace_names = [t.name for t in fig.data if hasattr(t, "name") and t.name]
        assert any("SMA" in name or "5" in name for name in trace_names)

    def test_create_chart_with_rsi(self, sample_prices: pd.DataFrame) -> None:
        """Chart includes RSI subplot when requested."""
        from technical_tools.charts import create_chart
        from technical_tools.indicators import add_rsi

        df = add_rsi(sample_prices.copy(), period=14)
        fig = create_chart(df, ticker="7203", show_rsi=True)
        # Should have multiple rows (subplots)
        assert fig.layout.xaxis is not None

    def test_create_chart_with_macd(self, sample_prices: pd.DataFrame) -> None:
        """Chart includes MACD subplot when requested."""
        from technical_tools.charts import create_chart
        from technical_tools.indicators import add_macd

        df = add_macd(sample_prices.copy())
        fig = create_chart(df, ticker="7203", show_macd=True)
        assert fig is not None

    def test_create_chart_with_bollinger_bands(self, sample_prices: pd.DataFrame) -> None:
        """Chart includes Bollinger Bands when requested."""
        from technical_tools.charts import create_chart
        from technical_tools.indicators import add_bollinger_bands

        df = add_bollinger_bands(sample_prices.copy())
        fig = create_chart(df, ticker="7203", show_bb=True)
        # Should have traces for BB
        trace_names = [t.name for t in fig.data if hasattr(t, "name") and t.name]
        assert any("BB" in str(name) for name in trace_names)

    def test_create_chart_with_signals(self, sample_prices: pd.DataFrame) -> None:
        """Chart includes signal markers when provided."""
        from technical_tools.charts import create_chart
        from technical_tools.signals import Signal

        # Create test signals
        signals = [
            Signal(
                date=sample_prices.index[10],
                signal_type="golden_cross",
                price=float(sample_prices["Close"].iloc[10]),
                short_period=5,
                long_period=25,
            ),
            Signal(
                date=sample_prices.index[20],
                signal_type="dead_cross",
                price=float(sample_prices["Close"].iloc[20]),
                short_period=5,
                long_period=25,
            ),
        ]

        fig = create_chart(sample_prices, ticker="7203", signals=signals)
        # Chart should be created without errors
        assert fig is not None
        assert len(fig.data) > 1  # Has candlestick + signal markers

    def test_create_chart_with_rsi_and_macd(self, sample_prices: pd.DataFrame) -> None:
        """Chart with both RSI and MACD subplots."""
        from technical_tools.charts import create_chart
        from technical_tools.indicators import add_macd, add_rsi

        df = add_rsi(sample_prices.copy())
        df = add_macd(df)
        fig = create_chart(df, ticker="7203", show_rsi=True, show_macd=True)
        # Should have 3 rows (main + RSI + MACD)
        assert fig is not None
        # Check layout height is increased for multiple subplots
        assert fig.layout.height == 800

    def test_create_chart_signal_outside_data(self, sample_prices: pd.DataFrame) -> None:
        """Chart handles signals with dates not in DataFrame index."""
        from technical_tools.charts import create_chart
        from technical_tools.signals import Signal

        # Create signal with date not in index
        signals = [
            Signal(
                date=datetime(1999, 1, 1),  # Date not in sample data
                signal_type="golden_cross",
                price=100.0,
                short_period=5,
                long_period=25,
            ),
        ]

        fig = create_chart(sample_prices, ticker="7203", signals=signals)
        # Should not raise error, just skip the invalid signal
        assert fig is not None


class TestIntegration:
    """Test integration with existing analysis results."""

    def test_load_existing_analysis_returns_dict(self, tmp_path: Path) -> None:
        """load_existing_analysis returns dict with expected keys."""
        import sqlite3

        from technical_tools.integration import load_existing_analysis

        # Create a mock database
        db_path = tmp_path / "analysis_results.db"
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE minervini (
                Code TEXT, Date TEXT, score REAL
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE relative_strength (
                Code TEXT, Date TEXT, rsp REAL
            )
        """
        )
        conn.execute(
            "INSERT INTO minervini VALUES ('7203', '2024-01-15', 0.85)"
        )
        conn.execute(
            "INSERT INTO relative_strength VALUES ('7203', '2024-01-15', 75.5)"
        )
        conn.commit()
        conn.close()

        result = load_existing_analysis("7203", db_path=db_path)
        assert "minervini" in result
        assert "relative_strength" in result

    def test_load_existing_analysis_missing_ticker(self, tmp_path: Path) -> None:
        """load_existing_analysis returns None for missing data."""
        import sqlite3

        from technical_tools.integration import load_existing_analysis

        db_path = tmp_path / "analysis_results.db"
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE minervini (Code TEXT, Date TEXT, score REAL)
        """
        )
        conn.execute(
            """
            CREATE TABLE relative_strength (Code TEXT, Date TEXT, rsp REAL)
        """
        )
        conn.commit()
        conn.close()

        result = load_existing_analysis("9999", db_path=db_path)
        assert result["minervini"] is None
        assert result["relative_strength"] is None

    def test_load_existing_analysis_db_not_exists(self, tmp_path: Path) -> None:
        """load_existing_analysis returns empty dict when DB doesn't exist."""
        from technical_tools.integration import load_existing_analysis

        db_path = tmp_path / "nonexistent.db"
        result = load_existing_analysis("7203", db_path=db_path)

        assert result["minervini"] is None
        assert result["relative_strength"] is None

    def test_load_existing_analysis_missing_tables(self, tmp_path: Path) -> None:
        """load_existing_analysis handles missing tables gracefully."""
        import sqlite3

        from technical_tools.integration import load_existing_analysis

        db_path = tmp_path / "analysis_results.db"
        conn = sqlite3.connect(db_path)
        # Create empty database with no tables
        conn.close()

        result = load_existing_analysis("7203", db_path=db_path)
        assert result["minervini"] is None
        assert result["relative_strength"] is None

    def test_load_existing_analysis_5digit_code(self, tmp_path: Path) -> None:
        """load_existing_analysis handles 5-digit stock codes."""
        import sqlite3

        from technical_tools.integration import load_existing_analysis

        db_path = tmp_path / "analysis_results.db"
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE minervini (Code TEXT, Date TEXT, score REAL)"
        )
        conn.execute(
            "CREATE TABLE relative_strength (Code TEXT, Date TEXT, rsp REAL)"
        )
        # Insert with 5-digit code
        conn.execute(
            "INSERT INTO minervini VALUES ('72030', '2024-01-15', 0.85)"
        )
        conn.commit()
        conn.close()

        # Search with 4-digit code should still find it
        result = load_existing_analysis("7203", db_path=db_path)
        assert result["minervini"] is not None
        assert result["minervini"]["Code"] == "72030"


class TestTechnicalAnalyzer:
    """Test TechnicalAnalyzer facade class."""

    def test_analyzer_default_source(self) -> None:
        """TechnicalAnalyzer uses jquants source by default."""
        with patch("technical_tools.analyzer.JQuantsSource") as mock_jquants:
            from technical_tools import TechnicalAnalyzer

            _ = TechnicalAnalyzer()
            mock_jquants.assert_called_once()

    def test_analyzer_yfinance_source(self) -> None:
        """TechnicalAnalyzer can use yfinance source."""
        with patch("technical_tools.analyzer.YFinanceSource") as mock_yfinance:
            from technical_tools import TechnicalAnalyzer

            _ = TechnicalAnalyzer(source="yfinance")
            mock_yfinance.assert_called_once()

    def test_analyzer_get_prices_caches_data(
        self, sample_prices: pd.DataFrame
    ) -> None:
        """TechnicalAnalyzer caches price data."""
        with patch("technical_tools.analyzer.JQuantsSource") as mock_jquants:
            mock_source = MagicMock()
            mock_source.get_prices.return_value = sample_prices
            mock_jquants.return_value = mock_source

            from technical_tools import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            _ = analyzer.get_prices("7203")
            _ = analyzer.get_prices("7203")

            # Should only call data source once due to caching
            assert mock_source.get_prices.call_count == 1

    def test_analyzer_plot_chart(self, sample_prices: pd.DataFrame) -> None:
        """TechnicalAnalyzer.plot_chart returns Figure."""
        with patch("technical_tools.analyzer.JQuantsSource") as mock_jquants:
            mock_source = MagicMock()
            mock_source.get_prices.return_value = sample_prices
            mock_jquants.return_value = mock_source

            from technical_tools import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            fig = analyzer.plot_chart("7203")
            assert fig is not None

    def test_analyzer_add_sma(self, sample_prices: pd.DataFrame) -> None:
        """TechnicalAnalyzer.add_sma adds SMA columns."""
        with patch("technical_tools.analyzer.JQuantsSource") as mock_jquants:
            mock_source = MagicMock()
            mock_source.get_prices.return_value = sample_prices
            mock_jquants.return_value = mock_source

            from technical_tools import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            df = analyzer.add_sma("7203", periods=[5, 10])

            assert "SMA_5" in df.columns
            assert "SMA_10" in df.columns

    def test_analyzer_add_ema(self, sample_prices: pd.DataFrame) -> None:
        """TechnicalAnalyzer.add_ema adds EMA columns."""
        with patch("technical_tools.analyzer.JQuantsSource") as mock_jquants:
            mock_source = MagicMock()
            mock_source.get_prices.return_value = sample_prices
            mock_jquants.return_value = mock_source

            from technical_tools import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            df = analyzer.add_ema("7203", periods=[12, 26])

            assert "EMA_12" in df.columns
            assert "EMA_26" in df.columns

    def test_analyzer_add_rsi(self, sample_prices: pd.DataFrame) -> None:
        """TechnicalAnalyzer.add_rsi adds RSI column."""
        with patch("technical_tools.analyzer.JQuantsSource") as mock_jquants:
            mock_source = MagicMock()
            mock_source.get_prices.return_value = sample_prices
            mock_jquants.return_value = mock_source

            from technical_tools import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            df = analyzer.add_rsi("7203", period=14)

            assert "RSI_14" in df.columns

    def test_analyzer_add_macd(self, sample_prices: pd.DataFrame) -> None:
        """TechnicalAnalyzer.add_macd adds MACD columns."""
        with patch("technical_tools.analyzer.JQuantsSource") as mock_jquants:
            mock_source = MagicMock()
            mock_source.get_prices.return_value = sample_prices
            mock_jquants.return_value = mock_source

            from technical_tools import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            df = analyzer.add_macd("7203")

            assert "MACD" in df.columns
            assert "MACD_Signal" in df.columns
            assert "MACD_Hist" in df.columns

    def test_analyzer_add_bollinger_bands(self, sample_prices: pd.DataFrame) -> None:
        """TechnicalAnalyzer.add_bollinger_bands adds BB columns."""
        with patch("technical_tools.analyzer.JQuantsSource") as mock_jquants:
            mock_source = MagicMock()
            mock_source.get_prices.return_value = sample_prices
            mock_jquants.return_value = mock_source

            from technical_tools import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            df = analyzer.add_bollinger_bands("7203")

            assert "BB_Upper" in df.columns
            assert "BB_Middle" in df.columns
            assert "BB_Lower" in df.columns

    def test_analyzer_calculate_indicators(self, sample_prices: pd.DataFrame) -> None:
        """TechnicalAnalyzer.calculate_indicators calculates multiple indicators."""
        with patch("technical_tools.analyzer.JQuantsSource") as mock_jquants:
            mock_source = MagicMock()
            mock_source.get_prices.return_value = sample_prices
            mock_jquants.return_value = mock_source

            from technical_tools import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            df = analyzer.calculate_indicators("7203", indicators=["sma", "rsi"])

            assert any(c.startswith("SMA_") for c in df.columns)
            assert any(c.startswith("RSI_") for c in df.columns)

    def test_analyzer_detect_crosses(self, sample_prices: pd.DataFrame) -> None:
        """TechnicalAnalyzer.detect_crosses detects MA crosses."""
        with patch("technical_tools.analyzer.JQuantsSource") as mock_jquants:
            mock_source = MagicMock()
            mock_source.get_prices.return_value = sample_prices
            mock_jquants.return_value = mock_source

            from technical_tools import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            signals = analyzer.detect_crosses("7203", short=5, long=10)

            assert isinstance(signals, list)

    def test_analyzer_detect_crosses_with_patterns(
        self, sample_prices: pd.DataFrame
    ) -> None:
        """TechnicalAnalyzer.detect_crosses with multiple patterns."""
        with patch("technical_tools.analyzer.JQuantsSource") as mock_jquants:
            mock_source = MagicMock()
            mock_source.get_prices.return_value = sample_prices
            mock_jquants.return_value = mock_source

            from technical_tools import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            signals = analyzer.detect_crosses("7203", patterns=[(5, 10), (10, 25)])

            assert isinstance(signals, list)

    def test_analyzer_plot_chart_with_signals(self, sample_prices: pd.DataFrame) -> None:
        """TechnicalAnalyzer.plot_chart with signal detection."""
        with patch("technical_tools.analyzer.JQuantsSource") as mock_jquants:
            mock_source = MagicMock()
            mock_source.get_prices.return_value = sample_prices
            mock_jquants.return_value = mock_source

            from technical_tools import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            fig = analyzer.plot_chart(
                "7203",
                show_sma=[5, 25],
                show_rsi=True,
                show_macd=True,
                show_signals=True,
            )

            assert fig is not None

    def test_analyzer_load_existing_analysis(self, tmp_path: Path) -> None:
        """TechnicalAnalyzer.load_existing_analysis loads from database."""
        import sqlite3

        db_path = tmp_path / "analysis_results.db"
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE minervini (Code TEXT, Date TEXT, score REAL)"
        )
        conn.execute(
            "CREATE TABLE relative_strength (Code TEXT, Date TEXT, rsp REAL)"
        )
        conn.execute(
            "INSERT INTO minervini VALUES ('7203', '2024-01-15', 0.85)"
        )
        conn.commit()
        conn.close()

        with patch("technical_tools.analyzer.JQuantsSource"):
            with patch(
                "technical_tools.analyzer.load_existing_analysis"
            ) as mock_load:
                mock_load.return_value = {
                    "minervini": {"Code": "7203", "score": 0.85},
                    "relative_strength": None,
                }

                from technical_tools import TechnicalAnalyzer

                analyzer = TechnicalAnalyzer()
                result = analyzer.load_existing_analysis("7203")

                assert result["minervini"] is not None
                mock_load.assert_called_once_with("7203")


class TestPackageExports:
    """Test package-level exports."""

    def test_import_technical_analyzer(self) -> None:
        """TechnicalAnalyzer can be imported from package."""
        from technical_tools import TechnicalAnalyzer

        assert TechnicalAnalyzer is not None

    def test_import_signal(self) -> None:
        """Signal can be imported from package."""
        from technical_tools import Signal

        assert Signal is not None

    def test_import_exceptions(self) -> None:
        """Exceptions can be imported from package."""
        from technical_tools import (
            DataSourceError,
            InsufficientDataError,
            TechnicalToolsError,
            TickerNotFoundError,
        )

        assert TechnicalToolsError is not None
        assert DataSourceError is not None
        assert TickerNotFoundError is not None
        assert InsufficientDataError is not None
