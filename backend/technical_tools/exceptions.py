"""Custom exceptions for technical_tools package."""


class TechnicalToolsError(Exception):
    """Base exception for technical_tools package."""

    pass


class DataSourceError(TechnicalToolsError):
    """Error occurred while fetching data."""

    pass


class TickerNotFoundError(DataSourceError):
    """Specified ticker was not found."""

    def __init__(self, ticker: str, source: str) -> None:
        self.ticker = ticker
        self.source = source
        super().__init__(f"Ticker '{ticker}' not found in {source}")


class InsufficientDataError(TechnicalToolsError):
    """Not enough data for calculation."""

    def __init__(self, required: int, actual: int) -> None:
        self.required = required
        self.actual = actual
        super().__init__(f"Insufficient data: required {required} rows, got {actual}")
