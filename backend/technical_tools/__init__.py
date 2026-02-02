"""technical_tools - Technical analysis tools for Jupyter Notebook.

A unified interface for Japanese and US stock technical analysis,
providing:
- Data fetching from J-Quants (via market_reader) and yfinance
- Technical indicator calculation (SMA, EMA, RSI, MACD, Bollinger Bands)
- Signal detection (Golden Cross, Dead Cross)
- Interactive chart generation with plotly

Example:
    >>> from technical_tools import TechnicalAnalyzer
    >>> analyzer = TechnicalAnalyzer(source="jquants")
    >>> fig = analyzer.plot_chart("7203", show_sma=[25, 75], show_rsi=True)
    >>> fig.show()
"""

from .analyzer import TechnicalAnalyzer
from .exceptions import (
    DataSourceError,
    InsufficientDataError,
    TechnicalToolsError,
    TickerNotFoundError,
)
from .signals import Signal

__all__ = [
    "TechnicalAnalyzer",
    "Signal",
    "TechnicalToolsError",
    "DataSourceError",
    "TickerNotFoundError",
    "InsufficientDataError",
]

__version__ = "0.1.0"
