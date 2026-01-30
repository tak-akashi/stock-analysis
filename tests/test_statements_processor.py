"""
Tests for J-Quants Statements Processor.
"""

import os
import pytest
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock

from market_pipeline.jquants.statements_processor import JQuantsStatementsProcessor

# テスト用の固定値を設定
TEST_REFRESH_TOKEN = "test_refresh_token"
TEST_ID_TOKEN = "test_id_token"


@pytest.fixture
def mock_api_responses():
    """Mock API responses for statements tests."""
    return {
        'statements': [
            {
                'LocalCode': '72030',
                'DisclosedDate': '2024-05-10',
                'TypeOfCurrentPeriod': 'FY',
                'TypeOfDocument': '有価証券報告書',
                'NetSales': 45000000000000,
                'OperatingProfit': 3000000000000,
                'OrdinaryProfit': 3200000000000,
                'Profit': 2500000000000,
                'EarningsPerShare': 180.5,
                'TotalAssets': 80000000000000,
                'Equity': 35000000000000,
                'EquityToAssetRatio': 43.75,
                'BookValuePerShare': 2500.0,
                'CashFlowsFromOperatingActivities': 5000000000000,
                'CashFlowsFromInvestingActivities': -2000000000000,
                'CashFlowsFromFinancingActivities': -1000000000000,
                'ResultDividendPerShareAnnual': 60.0,
                'NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock': 14000000000,
            },
            {
                'LocalCode': '99840',
                'DisclosedDate': '2024-05-15',
                'TypeOfCurrentPeriod': 'FY',
                'TypeOfDocument': '有価証券報告書',
                'NetSales': 6000000000000,
                'OperatingProfit': 500000000000,
                'Profit': 400000000000,
                'EarningsPerShare': 450.0,
                'TotalAssets': 12000000000000,
                'Equity': 5000000000000,
                'BookValuePerShare': 5600.0,
                'ResultDividendPerShareAnnual': 44.0,
            }
        ]
    }


@pytest.fixture
def mock_requests():
    """Mock requests.post and requests.get for authentication."""
    with patch('backend.jquants.statements_processor.requests.post') as mock_post, \
         patch('backend.jquants.statements_processor.requests.get') as mock_get:
        # auth_user のレスポンス
        def post_side_effect(url, data=None, params=None, headers=None):
            if "auth_user" in url:
                return MagicMock(
                    status_code=200,
                    json=lambda: {'refreshToken': TEST_REFRESH_TOKEN}
                )
            elif "auth_refresh" in url:
                return MagicMock(
                    status_code=200,
                    json=lambda: {'idToken': TEST_ID_TOKEN}
                )
            return MagicMock(status_code=404)

        mock_post.side_effect = post_side_effect

        # listed/info のレスポンス
        def get_side_effect(url, params=None, headers=None):
            if "listed/info" in url:
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        'info': [
                            {'Code': '72030', 'CompanyName': 'トヨタ自動車', 'Sector33CodeName': '輸送用機器'},
                            {'Code': '99840', 'CompanyName': 'ソフトバンクグループ', 'Sector33CodeName': '情報・通信業'},
                        ]
                    }
                )
            return MagicMock(status_code=404)

        mock_get.side_effect = get_side_effect
        yield mock_post, mock_get


@pytest.fixture
def mock_env_vars():
    """Set up required environment variables."""
    original_email = os.environ.get("EMAIL")
    original_password = os.environ.get("PASSWORD")

    os.environ["EMAIL"] = "test@example.com"
    os.environ["PASSWORD"] = "test_password"

    yield

    # Cleanup
    if original_email:
        os.environ["EMAIL"] = original_email
    else:
        os.environ.pop("EMAIL", None)
    if original_password:
        os.environ["PASSWORD"] = original_password
    else:
        os.environ.pop("PASSWORD", None)


@pytest.fixture
def processor(mock_requests, mock_env_vars):
    """Create a JQuantsStatementsProcessor instance for testing."""
    return JQuantsStatementsProcessor(
        max_concurrent_requests=2,
        batch_size=10,
        request_delay=0.01
    )


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestJQuantsStatementsProcessor:
    """Test class for JQuantsStatementsProcessor."""

    def test_init_success(self, processor):
        """Test that processor initializes successfully."""
        assert processor._refresh_token == TEST_REFRESH_TOKEN
        assert processor._id_token == TEST_ID_TOKEN
        assert processor.max_concurrent_requests == 2
        assert processor.batch_size == 10

    def test_headers_property(self, processor):
        """Test that headers property returns correct authorization header."""
        headers = processor._headers
        assert 'Authorization' in headers
        assert headers['Authorization'] == f'Bearer {TEST_ID_TOKEN}'

    def test_initialize_database(self, processor, temp_db):
        """Test database initialization creates required tables."""
        processor._initialize_database(temp_db)

        with sqlite3.connect(temp_db) as conn:
            # Check financial_statements table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='financial_statements'"
            )
            assert cursor.fetchone() is not None

            # Check calculated_fundamentals table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='calculated_fundamentals'"
            )
            assert cursor.fetchone() is not None

            # Check indexes exist
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_statements_code'"
            )
            assert cursor.fetchone() is not None

    def test_map_statement_to_record(self, processor, mock_api_responses):
        """Test mapping API response to database record."""
        statement = mock_api_responses['statements'][0]
        record = processor._map_statement_to_record(statement)

        assert record['local_code'] == '72030'
        assert record['disclosed_date'] == '2024-05-10'
        assert record['type_of_current_period'] == 'FY'
        assert record['net_sales'] == 45000000000000
        assert record['earnings_per_share'] == 180.5
        assert record['book_value_per_share'] == 2500.0

    def test_save_statements_batch(self, processor, temp_db, mock_api_responses):
        """Test batch saving of statements to database."""
        processor._initialize_database(temp_db)

        statements_data = [
            ('72030', mock_api_responses['statements'][:1]),
            ('99840', mock_api_responses['statements'][1:2]),
        ]

        records_saved = processor.save_statements_batch(temp_db, statements_data)
        assert records_saved == 2

        # Verify data was saved
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM financial_statements")
            count = cursor.fetchone()[0]
            assert count == 2

    def test_get_listed_info_cached(self, processor, mock_requests):
        """Test that listed info is fetched and returns a DataFrame."""
        df = processor.get_listed_info_cached()

        assert not df.empty
        # Verify expected columns exist
        assert 'Code' in df.columns

    def test_database_stats(self, processor, temp_db, mock_api_responses):
        """Test getting database statistics."""
        processor._initialize_database(temp_db)

        statements_data = [
            ('72030', mock_api_responses['statements'][:1]),
        ]
        processor.save_statements_batch(temp_db, statements_data)

        stats = processor.get_database_stats(temp_db)
        assert 'statement_record_count' in stats
        assert stats['statement_record_count'] == 1


class TestStatementMapping:
    """Test statement field mapping."""

    def test_all_fields_mapped(self, processor):
        """Test that all expected fields are mapped."""
        full_statement = {
            'LocalCode': '12345',
            'DisclosedDate': '2024-01-01',
            'TypeOfCurrentPeriod': 'FY',
            'DisclosureNumber': '12345',
            'TypeOfDocument': '有価証券報告書',
            'NetSales': 1000000,
            'OperatingProfit': 100000,
            'OrdinaryProfit': 110000,
            'Profit': 80000,
            'EarningsPerShare': 100.0,
            'TotalAssets': 5000000,
            'Equity': 2000000,
            'BookValuePerShare': 500.0,
            'CashFlowsFromOperatingActivities': 200000,
            'CashFlowsFromInvestingActivities': -100000,
            'CashFlowsFromFinancingActivities': -50000,
            'ResultDividendPerShareAnnual': 20.0,
        }

        record = processor._map_statement_to_record(full_statement)

        assert record['local_code'] == '12345'
        assert record['net_sales'] == 1000000
        assert record['profit'] == 80000
        assert record['cf_operating'] == 200000
        assert record['cf_investing'] == -100000

    def test_missing_fields_return_none(self, processor):
        """Test that missing fields are handled gracefully."""
        partial_statement = {
            'LocalCode': '12345',
            'DisclosedDate': '2024-01-01',
            'TypeOfCurrentPeriod': 'FY',
        }

        record = processor._map_statement_to_record(partial_statement)

        assert record['local_code'] == '12345'
        assert record['net_sales'] is None
        assert record['earnings_per_share'] is None
