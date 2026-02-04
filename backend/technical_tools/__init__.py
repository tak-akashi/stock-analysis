"""technical_tools - Technical analysis tools for Jupyter Notebook.

A unified interface for Japanese and US stock technical analysis,
providing:
- Data fetching from J-Quants (via market_reader) and yfinance
- Technical indicator calculation (SMA, EMA, RSI, MACD, Bollinger Bands)
- Signal detection (Golden Cross, Dead Cross)
- Interactive chart generation with plotly
- Stock screening with integrated analysis data

Example:
    >>> from technical_tools import TechnicalAnalyzer, StockScreener, ScreenerFilter
    >>> analyzer = TechnicalAnalyzer(source="jquants")
    >>> fig = analyzer.plot_chart("7203", show_sma=[25, 75], show_rsi=True)
    >>> fig.show()

    >>> screener = StockScreener()
    >>> results = screener.filter(composite_score_min=70.0, hl_ratio_min=80)

    # Using ScreenerFilter for structured parameter handling
    >>> config = ScreenerFilter(composite_score_min=70.0, market_cap_min=100_000_000_000)
    >>> results = screener.filter(config)
"""

from .analyzer import TechnicalAnalyzer
from .exceptions import (
    DataSourceError,
    InsufficientDataError,
    TechnicalToolsError,
    TickerNotFoundError,
)
from .screener import ScreenerFilter, StockScreener
from .signals import Signal

__all__ = [
    "TechnicalAnalyzer",
    "StockScreener",
    "ScreenerFilter",
    "Signal",
    "TechnicalToolsError",
    "DataSourceError",
    "TickerNotFoundError",
    "InsufficientDataError",
]

__version__ = "0.1.0"
