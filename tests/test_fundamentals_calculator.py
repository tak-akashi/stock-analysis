"""
Tests for Fundamentals Calculator.
"""

import os
import pytest
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock

from backend.jquants.fundamentals_calculator import FundamentalsCalculator


@pytest.fixture
def temp_statements_db():
    """Create a temporary statements database with test data."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name

    with sqlite3.connect(db_path) as conn:
        # Create financial_statements table
        conn.execute('''
            CREATE TABLE financial_statements (
                local_code TEXT NOT NULL,
                disclosed_date TEXT NOT NULL,
                type_of_current_period TEXT NOT NULL,
                net_sales REAL,
                operating_profit REAL,
                ordinary_profit REAL,
                profit REAL,
                earnings_per_share REAL,
                total_assets REAL,
                equity REAL,
                equity_to_asset_ratio REAL,
                book_value_per_share REAL,
                cf_operating REAL,
                cf_investing REAL,
                cf_financing REAL,
                result_dividend_per_share_annual REAL,
                forecast_earnings_per_share REAL,
                number_of_shares REAL,
                payout_ratio_annual REAL,
                current_fiscal_year_end_date TEXT,
                PRIMARY KEY (local_code, disclosed_date, type_of_current_period)
            )
        ''')

        # Create calculated_fundamentals table
        conn.execute('''
            CREATE TABLE calculated_fundamentals (
                code TEXT PRIMARY KEY,
                company_name TEXT,
                sector_33 TEXT,
                sector_17 TEXT,
                market_segment TEXT,
                latest_period TEXT,
                latest_fiscal_year_end TEXT,
                latest_disclosed_date TEXT,
                market_cap REAL,
                per REAL,
                forward_per REAL,
                pbr REAL,
                dividend_yield REAL,
                roe REAL,
                roa REAL,
                equity_ratio REAL,
                operating_margin REAL,
                profit_margin REAL,
                eps REAL,
                bps REAL,
                dps REAL,
                total_assets REAL,
                equity REAL,
                operating_cf REAL,
                free_cash_flow REAL,
                net_sales REAL,
                operating_profit REAL,
                ordinary_profit REAL,
                profit REAL,
                payout_ratio REAL,
                reference_price REAL,
                reference_date TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert test data - FY statement
        conn.execute('''
            INSERT INTO financial_statements (
                local_code, disclosed_date, type_of_current_period,
                net_sales, operating_profit, ordinary_profit, profit,
                earnings_per_share, total_assets, equity, equity_to_asset_ratio,
                book_value_per_share, cf_operating, cf_investing, cf_financing,
                result_dividend_per_share_annual, forecast_earnings_per_share,
                number_of_shares, payout_ratio_annual, current_fiscal_year_end_date
            ) VALUES (
                '72030', '2024-05-10', 'FY',
                45000000000000, 3000000000000, 3200000000000, 2500000000000,
                180.5, 80000000000000, 35000000000000, 43.75,
                2500.0, 5000000000000, -2000000000000, -1000000000000,
                60.0, 200.0,
                14000000000, 33.24, '2024-03-31'
            )
        ''')

        # Insert test data - Quarterly statement (should not be preferred over FY)
        conn.execute('''
            INSERT INTO financial_statements (
                local_code, disclosed_date, type_of_current_period,
                net_sales, operating_profit, profit,
                earnings_per_share, total_assets, equity,
                book_value_per_share, number_of_shares
            ) VALUES (
                '72030', '2024-08-01', '1Q',
                12000000000000, 800000000000, 650000000000,
                45.0, 82000000000000, 36000000000000,
                2550.0, 14000000000
            )
        ''')

        # Insert test data - Another company with only quarterly data
        conn.execute('''
            INSERT INTO financial_statements (
                local_code, disclosed_date, type_of_current_period,
                net_sales, operating_profit, profit,
                earnings_per_share, total_assets, equity,
                book_value_per_share, result_dividend_per_share_annual,
                number_of_shares
            ) VALUES (
                '99840', '2024-08-15', '2Q',
                3000000000000, 250000000000, 200000000000,
                225.0, 6000000000000, 2500000000000,
                2800.0, 22.0,
                900000000
            )
        ''')

        conn.commit()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_jquants_db():
    """Create a temporary jquants database with price data."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name

    with sqlite3.connect(db_path) as conn:
        conn.execute('''
            CREATE TABLE daily_quotes (
                Code TEXT,
                Date TEXT,
                Open REAL,
                High REAL,
                Low REAL,
                Close REAL,
                AdjustmentClose REAL,
                Volume INTEGER,
                PRIMARY KEY (Code, Date)
            )
        ''')

        # Insert price data for test stocks
        conn.execute('''
            INSERT INTO daily_quotes (Code, Date, Open, High, Low, Close, AdjustmentClose, Volume)
            VALUES ('72030', '2024-08-20', 2850, 2900, 2800, 2880, 2880, 10000000)
        ''')

        conn.execute('''
            INSERT INTO daily_quotes (Code, Date, Open, High, Low, Close, AdjustmentClose, Volume)
            VALUES ('99840', '2024-08-20', 8500, 8600, 8400, 8550, 8550, 5000000)
        ''')

        conn.commit()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_cache():
    """Mock the cache manager."""
    with patch('backend.jquants.fundamentals_calculator.get_cache') as mock:
        cache_instance = MagicMock()
        # Return listed info when cache.get is called
        cache_instance.get.return_value = [
            {'Code': '72030', 'CompanyName': 'トヨタ自動車', 'Sector33CodeName': '輸送用機器', 'Sector17CodeName': '自動車・輸送機', 'MarketCodeName': 'プライム'},
            {'Code': '99840', 'CompanyName': 'ソフトバンクグループ', 'Sector33CodeName': '情報・通信業', 'Sector17CodeName': '情報通信・サービスその他', 'MarketCodeName': 'プライム'},
        ]
        mock.return_value = cache_instance
        yield cache_instance


@pytest.fixture
def calculator(temp_statements_db, temp_jquants_db, mock_cache):
    """Create a FundamentalsCalculator instance for testing."""
    return FundamentalsCalculator(
        statements_db_path=temp_statements_db,
        jquants_db_path=temp_jquants_db
    )


class TestCalculationMethods:
    """Test individual calculation methods."""

    def test_calculate_per_normal(self):
        """Test PER calculation with normal values."""
        assert FundamentalsCalculator.calculate_per(1000, 50) == 20.0
        assert FundamentalsCalculator.calculate_per(2880, 180.5) == pytest.approx(15.96, rel=0.01)

    def test_calculate_per_zero_eps(self):
        """Test PER calculation with zero EPS."""
        assert FundamentalsCalculator.calculate_per(1000, 0) is None

    def test_calculate_per_negative_eps(self):
        """Test PER calculation with negative EPS."""
        assert FundamentalsCalculator.calculate_per(1000, -50) == -20.0

    def test_calculate_per_none_values(self):
        """Test PER calculation with None values."""
        assert FundamentalsCalculator.calculate_per(None, 50) is None
        assert FundamentalsCalculator.calculate_per(1000, None) is None

    def test_calculate_pbr_normal(self):
        """Test PBR calculation with normal values."""
        assert FundamentalsCalculator.calculate_pbr(1000, 500) == 2.0
        assert FundamentalsCalculator.calculate_pbr(2880, 2500) == pytest.approx(1.15, rel=0.01)

    def test_calculate_pbr_zero_bps(self):
        """Test PBR calculation with zero BPS."""
        assert FundamentalsCalculator.calculate_pbr(1000, 0) is None

    def test_calculate_roe_normal(self):
        """Test ROE calculation."""
        # ROE = Profit / Equity * 100
        assert FundamentalsCalculator.calculate_roe(100000, 1000000) == 10.0
        # Toyota: 2.5T / 35T = 7.14%
        assert FundamentalsCalculator.calculate_roe(2500000000000, 35000000000000) == pytest.approx(7.14, rel=0.01)

    def test_calculate_roe_zero_equity(self):
        """Test ROE calculation with zero equity."""
        assert FundamentalsCalculator.calculate_roe(100000, 0) is None

    def test_calculate_roa_normal(self):
        """Test ROA calculation."""
        # ROA = Profit / TotalAssets * 100
        assert FundamentalsCalculator.calculate_roa(100000, 2000000) == 5.0

    def test_calculate_dividend_yield_normal(self):
        """Test dividend yield calculation."""
        # Yield = DPS / Price * 100
        assert FundamentalsCalculator.calculate_dividend_yield(60, 2880) == pytest.approx(2.08, rel=0.01)

    def test_calculate_dividend_yield_zero_price(self):
        """Test dividend yield with zero price."""
        assert FundamentalsCalculator.calculate_dividend_yield(60, 0) is None

    def test_calculate_market_cap_normal(self):
        """Test market cap calculation."""
        # Market Cap = Price * Shares
        assert FundamentalsCalculator.calculate_market_cap(2880, 14000000000) == 2880 * 14000000000

    def test_calculate_operating_margin_normal(self):
        """Test operating margin calculation."""
        # Operating Margin = OperatingProfit / NetSales * 100
        assert FundamentalsCalculator.calculate_operating_margin(3000000000000, 45000000000000) == pytest.approx(6.67, rel=0.01)

    def test_calculate_profit_margin_normal(self):
        """Test profit margin calculation."""
        # Profit Margin = Profit / NetSales * 100
        assert FundamentalsCalculator.calculate_profit_margin(2500000000000, 45000000000000) == pytest.approx(5.56, rel=0.01)

    def test_calculate_free_cash_flow_normal(self):
        """Test free cash flow calculation."""
        # FCF = Operating CF + Investing CF
        assert FundamentalsCalculator.calculate_free_cash_flow(5000000000000, -2000000000000) == 3000000000000

    def test_calculate_free_cash_flow_none(self):
        """Test free cash flow with None values."""
        assert FundamentalsCalculator.calculate_free_cash_flow(None, -2000000000000) is None
        assert FundamentalsCalculator.calculate_free_cash_flow(5000000000000, None) is None


class TestDataRetrieval:
    """Test data retrieval methods."""

    def test_get_latest_price(self, calculator, temp_jquants_db):
        """Test getting latest price for a stock."""
        price, date = calculator.get_latest_price('72030')
        assert price == 2880
        assert date == '2024-08-20'

    def test_get_latest_price_not_found(self, calculator):
        """Test getting price for non-existent stock."""
        price, date = calculator.get_latest_price('99999')
        assert price is None
        assert date is None

    def test_get_latest_prices_batch(self, calculator):
        """Test batch retrieval of latest prices."""
        prices = calculator.get_latest_prices_batch()
        assert '72030' in prices
        assert prices['72030'][0] == 2880

    def test_get_latest_statement_prefers_fy(self, calculator):
        """Test that FY statements are preferred over quarterly."""
        statement = calculator.get_latest_statement('72030')
        assert statement is not None
        assert statement['type_of_current_period'] == 'FY'
        assert statement['earnings_per_share'] == 180.5

    def test_get_latest_statement_falls_back_to_quarterly(self, calculator):
        """Test fallback to quarterly when no FY available."""
        statement = calculator.get_latest_statement('99840')
        assert statement is not None
        assert statement['type_of_current_period'] == '2Q'

    def test_get_all_latest_statements(self, calculator):
        """Test batch retrieval of latest statements."""
        df = calculator.get_all_latest_statements()
        assert not df.empty
        assert len(df) == 2  # Two unique codes


class TestFundamentalsCalculation:
    """Test full fundamentals calculation."""

    def test_calculate_all_fundamentals(self, calculator, mock_cache):
        """Test calculating all fundamentals for a single stock."""
        statement = calculator.get_latest_statement('72030')
        listed_info = {'CompanyName': 'トヨタ自動車', 'Sector33CodeName': '輸送用機器', 'Sector17CodeName': '自動車', 'MarketCodeName': 'プライム'}

        fundamentals = calculator.calculate_all_fundamentals(
            code='72030',
            statement=statement,
            price=2880,
            price_date='2024-08-20',
            listed_info=listed_info
        )

        assert fundamentals['code'] == '72030'
        assert fundamentals['company_name'] == 'トヨタ自動車'
        assert fundamentals['sector_33'] == '輸送用機器'
        assert fundamentals['reference_price'] == 2880
        assert fundamentals['per'] is not None
        assert fundamentals['pbr'] is not None
        assert fundamentals['roe'] is not None
        assert fundamentals['free_cash_flow'] is not None

    def test_update_all_fundamentals(self, calculator, temp_statements_db, mock_cache):
        """Test updating all fundamentals and saving to database."""
        processed = calculator.update_all_fundamentals(temp_statements_db)

        assert processed == 2  # Two stocks with prices

        # Verify data was saved
        with sqlite3.connect(temp_statements_db) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM calculated_fundamentals")
            count = cursor.fetchone()[0]
            assert count == 2

            # Check specific values
            cursor = conn.execute(
                "SELECT per, pbr, roe FROM calculated_fundamentals WHERE code = '72030'"
            )
            row = cursor.fetchone()
            assert row is not None
            per, pbr, roe = row
            assert per is not None
            assert pbr is not None
            assert roe is not None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_price_data(self, temp_statements_db, mock_cache):
        """Test handling of missing price data."""
        # Create a jquants db without the stock
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            empty_db_path = f.name

        with sqlite3.connect(empty_db_path) as conn:
            conn.execute('''
                CREATE TABLE daily_quotes (
                    Code TEXT, Date TEXT, AdjustmentClose REAL,
                    PRIMARY KEY (Code, Date)
                )
            ''')

        try:
            calculator = FundamentalsCalculator(
                statements_db_path=temp_statements_db,
                jquants_db_path=empty_db_path
            )
            processed = calculator.update_all_fundamentals(temp_statements_db)
            # Should process 0 stocks since no price data
            assert processed == 0
        finally:
            os.unlink(empty_db_path)

    def test_missing_statement_fields(self, calculator):
        """Test handling of missing statement fields."""
        partial_statement = {
            'local_code': '12345',
            'disclosed_date': '2024-01-01',
            'type_of_current_period': 'FY',
            # Most fields missing
        }

        fundamentals = calculator.calculate_all_fundamentals(
            code='12345',
            statement=partial_statement,
            price=1000,
            price_date='2024-01-01',
            listed_info=None
        )

        assert fundamentals['code'] == '12345'
        assert fundamentals['per'] is None  # No EPS
        assert fundamentals['pbr'] is None  # No BPS
        assert fundamentals['company_name'] is None  # No listed info
