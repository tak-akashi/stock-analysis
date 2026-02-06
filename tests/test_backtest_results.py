"""Tests for BacktestResults class."""

import pandas as pd
import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from technical_tools.backtest_results import BacktestResults, Trade


@pytest.fixture
def sample_trades() -> list[Trade]:
    """Create sample trades for testing."""
    return [
        Trade(
            symbol="7203",
            entry_date=datetime(2023, 1, 10),
            entry_price=1000.0,
            exit_date=datetime(2023, 1, 20),
            exit_price=1100.0,
            shares=100,
            pnl=10000.0,
            return_pct=0.10,
            holding_days=10,
            exit_reason="take_profit",
        ),
        Trade(
            symbol="7203",
            entry_date=datetime(2023, 2, 1),
            entry_price=1200.0,
            exit_date=datetime(2023, 2, 15),
            exit_price=1080.0,
            shares=100,
            pnl=-12000.0,
            return_pct=-0.10,
            holding_days=14,
            exit_reason="stop_loss",
        ),
        Trade(
            symbol="9984",
            entry_date=datetime(2023, 3, 1),
            entry_price=5000.0,
            exit_date=datetime(2023, 3, 20),
            exit_price=5500.0,
            shares=20,
            pnl=10000.0,
            return_pct=0.10,
            holding_days=19,
            exit_reason="take_profit",
        ),
    ]


@pytest.fixture
def sample_equity_curve() -> pd.Series:
    """Create sample equity curve for testing."""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="B")
    equity = [1000000 + i * 1000 for i in range(100)]
    return pd.Series(equity, index=dates)


class TestBacktestResultsInit:
    """Test BacktestResults initialization."""

    def test_init_with_trades(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """BacktestResults can be initialized with trades."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        assert results is not None
        assert len(results._trades) == 3

    def test_init_empty_trades(self, sample_equity_curve: pd.Series) -> None:
        """BacktestResults can be initialized with empty trades."""
        results = BacktestResults(
            trades=[],
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        assert results is not None
        assert len(results._trades) == 0


class TestBacktestResultsSummary:
    """Test summary method."""

    def test_summary_returns_dict(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """summary() returns a dictionary with metrics."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        summary = results.summary()

        assert isinstance(summary, dict)

    def test_summary_contains_trade_count(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """summary() contains trade count."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        summary = results.summary()

        assert "total_trades" in summary
        assert summary["total_trades"] == 3

    def test_summary_contains_win_rate(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """summary() contains win rate."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        summary = results.summary()

        assert "win_rate" in summary
        # 2 wins out of 3 trades = 66.67%
        assert abs(summary["win_rate"] - 0.6667) < 0.01

    def test_summary_contains_avg_return(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """summary() contains average return."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        summary = results.summary()

        assert "avg_return" in summary
        # (0.10 + -0.10 + 0.10) / 3 = 0.0333
        assert abs(summary["avg_return"] - 0.0333) < 0.01

    def test_summary_contains_max_return(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """summary() contains maximum return."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        summary = results.summary()

        assert "max_return" in summary
        assert summary["max_return"] == 0.10

    def test_summary_contains_max_loss(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """summary() contains maximum loss."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        summary = results.summary()

        assert "max_loss" in summary
        assert summary["max_loss"] == -0.10

    def test_summary_contains_profit_factor(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """summary() contains profit factor."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        summary = results.summary()

        assert "profit_factor" in summary
        # Total profit: 20000, Total loss: 12000
        # PF = 20000 / 12000 = 1.67
        assert abs(summary["profit_factor"] - 1.67) < 0.1


class TestBacktestResultsRiskMetrics:
    """Test risk metrics calculation."""

    def test_summary_contains_max_drawdown(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """summary() contains maximum drawdown."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        summary = results.summary()

        assert "max_drawdown" in summary

    def test_summary_contains_sharpe_ratio(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """summary() contains Sharpe ratio."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        summary = results.summary()

        assert "sharpe_ratio" in summary

    def test_summary_contains_avg_holding_period(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """summary() contains average holding period."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        summary = results.summary()

        assert "avg_holding_days" in summary
        # (10 + 14 + 19) / 3 = 14.33
        assert abs(summary["avg_holding_days"] - 14.33) < 0.1


class TestBacktestResultsTrades:
    """Test trades method."""

    def test_trades_returns_dataframe(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """trades() returns a DataFrame."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        trades_df = results.trades()

        assert isinstance(trades_df, pd.DataFrame)
        assert len(trades_df) == 3

    def test_trades_contains_required_columns(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """trades() DataFrame contains required columns."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        trades_df = results.trades()

        required_columns = [
            "symbol",
            "entry_date",
            "entry_price",
            "exit_date",
            "exit_price",
            "shares",
            "pnl",
            "return_pct",
            "holding_days",
            "exit_reason",
        ]
        for col in required_columns:
            assert col in trades_df.columns


class TestBacktestResultsPlot:
    """Test plot method."""

    def test_plot_returns_figure(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """plot() returns a plotly Figure."""
        import plotly.graph_objects as go

        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        fig = results.plot()

        assert isinstance(fig, go.Figure)


class TestBacktestResultsEmptyTrades:
    """Test behavior with empty trades."""

    def test_summary_with_empty_trades(self, sample_equity_curve: pd.Series) -> None:
        """summary() works with empty trades."""
        results = BacktestResults(
            trades=[],
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        summary = results.summary()

        assert summary["total_trades"] == 0
        assert summary["win_rate"] == 0.0
        assert summary["avg_return"] == 0.0

    def test_trades_with_empty_trades(self, sample_equity_curve: pd.Series) -> None:
        """trades() returns empty DataFrame with correct columns."""
        results = BacktestResults(
            trades=[],
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        trades_df = results.trades()

        assert len(trades_df) == 0
        assert len(trades_df.columns) > 0


class TestBacktestResultsExport:
    """Test export method."""

    def test_export_csv(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """export() can create CSV file."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.csv"
            result_path = results.export(output_path)

            assert result_path.exists()
            assert result_path.suffix == ".csv"

            # Verify content
            df = pd.read_csv(result_path)
            assert len(df) == 3

    def test_export_excel(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """export() can create Excel file."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.xlsx"
            result_path = results.export(output_path)

            assert result_path.exists()
            assert result_path.suffix == ".xlsx"

            # Verify sheets
            excel = pd.ExcelFile(result_path)
            assert "Summary" in excel.sheet_names
            assert "Trades" in excel.sheet_names

    def test_export_html(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """export() can create HTML file."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.html"
            result_path = results.export(output_path)

            assert result_path.exists()
            assert result_path.suffix == ".html"

            # Verify content
            content = result_path.read_text()
            assert "<html" in content
            assert "バックテストレポート" in content

    def test_export_infers_format_from_extension(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """export() infers format from file extension."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # Test CSV inference
            csv_path = results.export(Path(tmpdir) / "report.csv")
            assert csv_path.suffix == ".csv"

            # Test Excel inference
            xlsx_path = results.export(Path(tmpdir) / "report.xlsx")
            assert xlsx_path.suffix == ".xlsx"

            # Test HTML inference
            html_path = results.export(Path(tmpdir) / "report.html")
            assert html_path.suffix == ".html"

    def test_export_with_explicit_format(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """export() respects explicit format parameter."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report"
            result_path = results.export(output_path, format="csv")

            assert result_path.suffix == ".csv"


class TestBacktestResultsBySymbol:
    """Test by_symbol method."""

    def test_by_symbol_returns_dataframe(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """by_symbol() returns a DataFrame."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.by_symbol()

        assert isinstance(df, pd.DataFrame)

    def test_by_symbol_groups_correctly(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """by_symbol() groups trades by symbol."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.by_symbol()

        # Should have 2 symbols: 7203 and 9984
        assert len(df) == 2
        assert "7203" in df["symbol"].values
        assert "9984" in df["symbol"].values

    def test_by_symbol_calculates_correct_metrics(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """by_symbol() calculates correct metrics."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.by_symbol()

        # Check 7203 (2 trades: 1 win, 1 loss)
        row_7203 = df[df["symbol"] == "7203"].iloc[0]
        assert row_7203["trades"] == 2
        assert abs(row_7203["win_rate"] - 0.5) < 0.01  # 50% win rate

        # Check 9984 (1 trade: 1 win)
        row_9984 = df[df["symbol"] == "9984"].iloc[0]
        assert row_9984["trades"] == 1
        assert abs(row_9984["win_rate"] - 1.0) < 0.01  # 100% win rate

    def test_by_symbol_with_empty_trades(self, sample_equity_curve: pd.Series) -> None:
        """by_symbol() works with empty trades."""
        results = BacktestResults(
            trades=[],
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.by_symbol()

        assert len(df) == 0


class TestBacktestResultsBySector:
    """Test by_sector method."""

    def test_by_sector_returns_dataframe(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """by_sector() returns a DataFrame."""
        sector_map = {"7203": "Automotive", "9984": "Technology"}
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.by_sector(sector_map)

        assert isinstance(df, pd.DataFrame)

    def test_by_sector_groups_correctly(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """by_sector() groups trades by sector."""
        sector_map = {"7203": "Automotive", "9984": "Technology"}
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.by_sector(sector_map)

        assert len(df) == 2
        assert "Automotive" in df["sector"].values
        assert "Technology" in df["sector"].values

    def test_by_sector_without_map_returns_empty(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """by_sector() without sector_map returns empty DataFrame."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.by_sector()

        assert len(df) == 0


class TestBacktestResultsMonthlyReturns:
    """Test monthly_returns method."""

    def test_monthly_returns_returns_dataframe(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """monthly_returns() returns a DataFrame."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.monthly_returns()

        assert isinstance(df, pd.DataFrame)

    def test_monthly_returns_groups_by_month(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """monthly_returns() groups trades by month."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.monthly_returns()

        # Sample trades span Jan, Feb, Mar 2023
        assert len(df) == 3

    def test_monthly_returns_contains_required_columns(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """monthly_returns() DataFrame contains required columns."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.monthly_returns()

        assert "year_month" in df.columns
        assert "trades" in df.columns
        assert "avg_return" in df.columns
        assert "total_pnl" in df.columns

    def test_monthly_returns_with_empty_trades(
        self, sample_equity_curve: pd.Series
    ) -> None:
        """monthly_returns() works with empty trades."""
        results = BacktestResults(
            trades=[],
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.monthly_returns()

        assert len(df) == 0


class TestBacktestResultsYearlyReturns:
    """Test yearly_returns method."""

    def test_yearly_returns_returns_dataframe(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """yearly_returns() returns a DataFrame."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.yearly_returns()

        assert isinstance(df, pd.DataFrame)

    def test_yearly_returns_groups_by_year(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """yearly_returns() groups trades by year."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.yearly_returns()

        # All sample trades are in 2023
        assert len(df) == 1
        assert df.iloc[0]["year"] == 2023

    def test_yearly_returns_contains_required_columns(
        self, sample_trades: list[Trade], sample_equity_curve: pd.Series
    ) -> None:
        """yearly_returns() DataFrame contains required columns."""
        results = BacktestResults(
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.yearly_returns()

        assert "year" in df.columns
        assert "trades" in df.columns
        assert "win_rate" in df.columns
        assert "avg_return" in df.columns
        assert "total_pnl" in df.columns

    def test_yearly_returns_with_empty_trades(
        self, sample_equity_curve: pd.Series
    ) -> None:
        """yearly_returns() works with empty trades."""
        results = BacktestResults(
            trades=[],
            equity_curve=sample_equity_curve,
            initial_cash=1000000,
        )
        df = results.yearly_returns()

        assert len(df) == 0
