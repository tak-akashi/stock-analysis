"""Tests for backtest signal classes."""

import pandas as pd
import pytest

from technical_tools.backtest_signals import (
    BaseSignal,
    GoldenCrossSignal,
    DeadCrossSignal,
    RSIOversoldSignal,
    RSIOverboughtSignal,
    MACDCrossSignal,
    BollingerBreakoutSignal,
    BollingerSqueezeSignal,
    VolumeSpikeSignal,
    VolumeBreakoutSignal,
    SignalRegistry,
)


@pytest.fixture
def sample_price_data() -> pd.DataFrame:
    """Create sample price data for testing."""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="B")

    # Create simple price series
    prices = [1000 + i * 10 for i in range(100)]

    df = pd.DataFrame(
        {
            "Open": prices,
            "High": [p * 1.02 for p in prices],
            "Low": [p * 0.98 for p in prices],
            "Close": prices,
            "Volume": [1000000] * len(dates),
        },
        index=dates,
    )

    return df


@pytest.fixture
def golden_cross_data() -> pd.DataFrame:
    """Create data that generates a golden cross."""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="B")

    # Downtrend then uptrend (short MA crosses above long MA)
    prices = []
    for i in range(50):
        prices.append(2000 - i * 20)  # Downtrend
    for i in range(50):
        prices.append(1000 + i * 30)  # Strong uptrend

    df = pd.DataFrame(
        {
            "Open": prices,
            "High": [p * 1.02 for p in prices],
            "Low": [p * 0.98 for p in prices],
            "Close": prices,
            "Volume": [1000000] * len(dates),
        },
        index=dates,
    )

    return df


@pytest.fixture
def dead_cross_data() -> pd.DataFrame:
    """Create data that generates a dead cross."""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="B")

    # Uptrend then downtrend (short MA crosses below long MA)
    prices = []
    for i in range(50):
        prices.append(1000 + i * 30)  # Strong uptrend
    for i in range(50):
        prices.append(2500 - i * 20)  # Downtrend

    df = pd.DataFrame(
        {
            "Open": prices,
            "High": [p * 1.02 for p in prices],
            "Low": [p * 0.98 for p in prices],
            "Close": prices,
            "Volume": [1000000] * len(dates),
        },
        index=dates,
    )

    return df


@pytest.fixture
def rsi_oversold_data() -> pd.DataFrame:
    """Create data with RSI dropping below threshold."""
    dates = pd.date_range(start="2023-01-01", periods=50, freq="B")

    # Sharp decline to trigger oversold
    prices = [1000 - i * 15 for i in range(50)]

    df = pd.DataFrame(
        {
            "Open": prices,
            "High": [p * 1.01 for p in prices],
            "Low": [p * 0.99 for p in prices],
            "Close": prices,
            "Volume": [1000000] * len(dates),
        },
        index=dates,
    )

    return df


@pytest.fixture
def rsi_overbought_data() -> pd.DataFrame:
    """Create data with RSI rising above threshold."""
    dates = pd.date_range(start="2023-01-01", periods=50, freq="B")

    # Sharp increase to trigger overbought
    prices = [1000 + i * 20 for i in range(50)]

    df = pd.DataFrame(
        {
            "Open": prices,
            "High": [p * 1.01 for p in prices],
            "Low": [p * 0.99 for p in prices],
            "Close": prices,
            "Volume": [1000000] * len(dates),
        },
        index=dates,
    )

    return df


class TestSignalRegistry:
    """Test SignalRegistry class."""

    def test_get_signal_class(self) -> None:
        """Can get signal class by name."""
        cls = SignalRegistry.get("golden_cross")
        assert cls == GoldenCrossSignal

    def test_get_all_signal_names(self) -> None:
        """Can get all registered signal names."""
        names = SignalRegistry.list_signals()
        assert "golden_cross" in names
        assert "dead_cross" in names
        assert "rsi_oversold" in names
        assert "rsi_overbought" in names
        assert "macd_cross" in names

    def test_get_unknown_signal_returns_none(self) -> None:
        """Getting unknown signal returns None."""
        cls = SignalRegistry.get("unknown_signal")
        assert cls is None


class TestGoldenCrossSignal:
    """Test GoldenCrossSignal class."""

    def test_init_with_default_params(self) -> None:
        """Can initialize with default parameters."""
        signal = GoldenCrossSignal()
        assert signal.short == 5
        assert signal.long == 25

    def test_init_with_custom_params(self) -> None:
        """Can initialize with custom parameters."""
        signal = GoldenCrossSignal(short=10, long=50)
        assert signal.short == 10
        assert signal.long == 50

    def test_detect_returns_series(self, sample_price_data: pd.DataFrame) -> None:
        """detect() returns a boolean Series."""
        signal = GoldenCrossSignal()
        result = signal.detect(sample_price_data)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_detect_finds_golden_cross(self, golden_cross_data: pd.DataFrame) -> None:
        """detect() finds golden cross signal."""
        signal = GoldenCrossSignal(short=5, long=20)
        result = signal.detect(golden_cross_data)

        # Should have at least one True value
        assert result.sum() >= 1

    def test_name_property(self) -> None:
        """name property returns 'golden_cross'."""
        signal = GoldenCrossSignal()
        assert signal.name == "golden_cross"


class TestDeadCrossSignal:
    """Test DeadCrossSignal class."""

    def test_init_with_default_params(self) -> None:
        """Can initialize with default parameters."""
        signal = DeadCrossSignal()
        assert signal.short == 5
        assert signal.long == 25

    def test_detect_returns_series(self, sample_price_data: pd.DataFrame) -> None:
        """detect() returns a boolean Series."""
        signal = DeadCrossSignal()
        result = signal.detect(sample_price_data)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_detect_finds_dead_cross(self, dead_cross_data: pd.DataFrame) -> None:
        """detect() finds dead cross signal."""
        signal = DeadCrossSignal(short=5, long=20)
        result = signal.detect(dead_cross_data)

        # Should have at least one True value
        assert result.sum() >= 1

    def test_name_property(self) -> None:
        """name property returns 'dead_cross'."""
        signal = DeadCrossSignal()
        assert signal.name == "dead_cross"


class TestRSIOversoldSignal:
    """Test RSIOversoldSignal class."""

    def test_init_with_default_threshold(self) -> None:
        """Can initialize with default threshold."""
        signal = RSIOversoldSignal()
        assert signal.threshold == 30
        assert signal.period == 14

    def test_init_with_custom_threshold(self) -> None:
        """Can initialize with custom threshold."""
        signal = RSIOversoldSignal(threshold=25, period=7)
        assert signal.threshold == 25
        assert signal.period == 7

    def test_detect_returns_series(self, sample_price_data: pd.DataFrame) -> None:
        """detect() returns a boolean Series."""
        signal = RSIOversoldSignal()
        result = signal.detect(sample_price_data)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_detect_finds_oversold(self, rsi_oversold_data: pd.DataFrame) -> None:
        """detect() finds oversold condition."""
        signal = RSIOversoldSignal(threshold=30)
        result = signal.detect(rsi_oversold_data)

        # Should have at least one True value
        assert result.sum() >= 1

    def test_name_property(self) -> None:
        """name property returns 'rsi_oversold'."""
        signal = RSIOversoldSignal()
        assert signal.name == "rsi_oversold"


class TestRSIOverboughtSignal:
    """Test RSIOverboughtSignal class."""

    def test_init_with_default_threshold(self) -> None:
        """Can initialize with default threshold."""
        signal = RSIOverboughtSignal()
        assert signal.threshold == 70
        assert signal.period == 14

    def test_init_with_custom_threshold(self) -> None:
        """Can initialize with custom threshold."""
        signal = RSIOverboughtSignal(threshold=80, period=7)
        assert signal.threshold == 80
        assert signal.period == 7

    def test_detect_returns_series(self, sample_price_data: pd.DataFrame) -> None:
        """detect() returns a boolean Series."""
        signal = RSIOverboughtSignal()
        result = signal.detect(sample_price_data)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_detect_finds_overbought(self, rsi_overbought_data: pd.DataFrame) -> None:
        """detect() finds overbought condition."""
        signal = RSIOverboughtSignal(threshold=70)
        result = signal.detect(rsi_overbought_data)

        # Should have at least one True value
        assert result.sum() >= 1

    def test_name_property(self) -> None:
        """name property returns 'rsi_overbought'."""
        signal = RSIOverboughtSignal()
        assert signal.name == "rsi_overbought"


class TestMACDCrossSignal:
    """Test MACDCrossSignal class."""

    def test_init_with_default_params(self) -> None:
        """Can initialize with default parameters."""
        signal = MACDCrossSignal()
        assert signal.fast == 12
        assert signal.slow == 26
        assert signal.signal_period == 9

    def test_init_with_custom_params(self) -> None:
        """Can initialize with custom parameters."""
        signal = MACDCrossSignal(fast=8, slow=21, signal_period=5)
        assert signal.fast == 8
        assert signal.slow == 21
        assert signal.signal_period == 5

    def test_detect_returns_series(self, sample_price_data: pd.DataFrame) -> None:
        """detect() returns a boolean Series."""
        signal = MACDCrossSignal()
        result = signal.detect(sample_price_data)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_name_property(self) -> None:
        """name property returns 'macd_cross'."""
        signal = MACDCrossSignal()
        assert signal.name == "macd_cross"


class TestBaseSignal:
    """Test BaseSignal abstract class."""

    def test_cannot_instantiate_directly(self) -> None:
        """Cannot instantiate BaseSignal directly."""
        with pytest.raises(TypeError):
            BaseSignal()  # type: ignore


class TestBollingerBreakoutSignal:
    """Test BollingerBreakoutSignal class."""

    @pytest.fixture
    def bollinger_breakout_data(self) -> pd.DataFrame:
        """Create data that generates a Bollinger breakout."""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="B")

        # Stable prices then sharp breakout
        prices = []
        for i in range(80):
            prices.append(1000 + (i % 5) * 2)  # Small fluctuation
        for i in range(20):
            prices.append(1010 + i * 15)  # Strong upward breakout

        df = pd.DataFrame(
            {
                "Open": prices,
                "High": [p * 1.02 for p in prices],
                "Low": [p * 0.98 for p in prices],
                "Close": prices,
                "Volume": [1000000] * len(dates),
            },
            index=dates,
        )

        return df

    def test_init_with_default_params(self) -> None:
        """Can initialize with default parameters."""
        signal = BollingerBreakoutSignal()
        assert signal.period == 20
        assert signal.std_dev == 2.0
        assert signal.direction == "up"

    def test_init_with_custom_params(self) -> None:
        """Can initialize with custom parameters."""
        signal = BollingerBreakoutSignal(period=30, std_dev=2.5, direction="down")
        assert signal.period == 30
        assert signal.std_dev == 2.5
        assert signal.direction == "down"

    def test_detect_returns_series(self, sample_price_data: pd.DataFrame) -> None:
        """detect() returns a boolean Series."""
        signal = BollingerBreakoutSignal()
        result = signal.detect(sample_price_data)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_detect_finds_breakout(self, bollinger_breakout_data: pd.DataFrame) -> None:
        """detect() finds Bollinger breakout signal."""
        signal = BollingerBreakoutSignal(period=20, std_dev=2.0)
        result = signal.detect(bollinger_breakout_data)

        # Should have at least one True value
        assert result.sum() >= 1

    def test_name_property(self) -> None:
        """name property returns 'bollinger_breakout'."""
        signal = BollingerBreakoutSignal()
        assert signal.name == "bollinger_breakout"

    def test_registry_contains_bollinger_breakout(self) -> None:
        """Signal is registered in SignalRegistry."""
        cls = SignalRegistry.get("bollinger_breakout")
        assert cls == BollingerBreakoutSignal


class TestBollingerSqueezeSignal:
    """Test BollingerSqueezeSignal class."""

    def test_init_with_default_params(self) -> None:
        """Can initialize with default parameters."""
        signal = BollingerSqueezeSignal()
        assert signal.period == 20
        assert signal.std_dev == 2.0
        assert signal.squeeze_threshold == 0.03

    def test_init_with_custom_params(self) -> None:
        """Can initialize with custom parameters."""
        signal = BollingerSqueezeSignal(period=30, std_dev=2.5, squeeze_threshold=0.05)
        assert signal.period == 30
        assert signal.std_dev == 2.5
        assert signal.squeeze_threshold == 0.05

    def test_detect_returns_series(self, sample_price_data: pd.DataFrame) -> None:
        """detect() returns a boolean Series."""
        signal = BollingerSqueezeSignal()
        result = signal.detect(sample_price_data)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_name_property(self) -> None:
        """name property returns 'bollinger_squeeze'."""
        signal = BollingerSqueezeSignal()
        assert signal.name == "bollinger_squeeze"

    def test_registry_contains_bollinger_squeeze(self) -> None:
        """Signal is registered in SignalRegistry."""
        cls = SignalRegistry.get("bollinger_squeeze")
        assert cls == BollingerSqueezeSignal


class TestVolumeSpikeSignal:
    """Test VolumeSpikeSignal class."""

    @pytest.fixture
    def volume_spike_data(self) -> pd.DataFrame:
        """Create data with volume spike."""
        dates = pd.date_range(start="2023-01-01", periods=50, freq="B")

        prices = [1000 + i * 5 for i in range(50)]
        volumes = [1000000] * 45 + [5000000] * 5  # Volume spike at end

        df = pd.DataFrame(
            {
                "Open": prices,
                "High": [p * 1.02 for p in prices],
                "Low": [p * 0.98 for p in prices],
                "Close": prices,
                "Volume": volumes,
            },
            index=dates,
        )

        return df

    def test_init_with_default_params(self) -> None:
        """Can initialize with default parameters."""
        signal = VolumeSpikeSignal()
        assert signal.period == 20
        assert signal.threshold == 2.0
        assert signal.price_direction is None

    def test_init_with_custom_params(self) -> None:
        """Can initialize with custom parameters."""
        signal = VolumeSpikeSignal(period=30, threshold=3.0, price_direction="up")
        assert signal.period == 30
        assert signal.threshold == 3.0
        assert signal.price_direction == "up"

    def test_detect_returns_series(self, sample_price_data: pd.DataFrame) -> None:
        """detect() returns a boolean Series."""
        signal = VolumeSpikeSignal()
        result = signal.detect(sample_price_data)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_detect_finds_volume_spike(self, volume_spike_data: pd.DataFrame) -> None:
        """detect() finds volume spike signal."""
        signal = VolumeSpikeSignal(period=20, threshold=2.0)
        result = signal.detect(volume_spike_data)

        # Should have at least one True value
        assert result.sum() >= 1

    def test_detect_handles_missing_volume(self) -> None:
        """detect() handles missing Volume column gracefully."""
        dates = pd.date_range(start="2023-01-01", periods=50, freq="B")
        df = pd.DataFrame(
            {
                "Open": [1000] * 50,
                "High": [1010] * 50,
                "Low": [990] * 50,
                "Close": [1000] * 50,
            },
            index=dates,
        )

        signal = VolumeSpikeSignal()
        result = signal.detect(df)

        assert isinstance(result, pd.Series)
        assert result.sum() == 0  # No signals without volume

    def test_name_property(self) -> None:
        """name property returns 'volume_spike'."""
        signal = VolumeSpikeSignal()
        assert signal.name == "volume_spike"

    def test_registry_contains_volume_spike(self) -> None:
        """Signal is registered in SignalRegistry."""
        cls = SignalRegistry.get("volume_spike")
        assert cls == VolumeSpikeSignal


class TestVolumeBreakoutSignal:
    """Test VolumeBreakoutSignal class."""

    @pytest.fixture
    def volume_breakout_data(self) -> pd.DataFrame:
        """Create data with volume-confirmed breakout."""
        dates = pd.date_range(start="2023-01-01", periods=50, freq="B")

        # Prices consolidate then break out
        prices = [1000] * 30 + [1000 + i * 20 for i in range(20)]
        highs = [1005] * 30 + [1005 + i * 20 for i in range(20)]
        volumes = [1000000] * 30 + [3000000] * 20  # Higher volume on breakout

        df = pd.DataFrame(
            {
                "Open": prices,
                "High": highs,
                "Low": [p * 0.99 for p in prices],
                "Close": prices,
                "Volume": volumes,
            },
            index=dates,
        )

        return df

    def test_init_with_default_params(self) -> None:
        """Can initialize with default parameters."""
        signal = VolumeBreakoutSignal()
        assert signal.price_period == 20
        assert signal.volume_period == 20
        assert signal.volume_threshold == 1.5

    def test_init_with_custom_params(self) -> None:
        """Can initialize with custom parameters."""
        signal = VolumeBreakoutSignal(
            price_period=30, volume_period=15, volume_threshold=2.0
        )
        assert signal.price_period == 30
        assert signal.volume_period == 15
        assert signal.volume_threshold == 2.0

    def test_detect_returns_series(self, sample_price_data: pd.DataFrame) -> None:
        """detect() returns a boolean Series."""
        signal = VolumeBreakoutSignal()
        result = signal.detect(sample_price_data)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_detect_finds_volume_breakout(
        self, volume_breakout_data: pd.DataFrame
    ) -> None:
        """detect() finds volume-confirmed breakout."""
        signal = VolumeBreakoutSignal(price_period=20, volume_threshold=1.5)
        result = signal.detect(volume_breakout_data)

        # Should have at least one True value
        assert result.sum() >= 1

    def test_name_property(self) -> None:
        """name property returns 'volume_breakout'."""
        signal = VolumeBreakoutSignal()
        assert signal.name == "volume_breakout"

    def test_registry_contains_volume_breakout(self) -> None:
        """Signal is registered in SignalRegistry."""
        cls = SignalRegistry.get("volume_breakout")
        assert cls == VolumeBreakoutSignal


class TestSignalRegistryPhase2:
    """Test SignalRegistry includes Phase 2 signals."""

    def test_all_phase2_signals_registered(self) -> None:
        """All Phase 2 signals are registered."""
        names = SignalRegistry.list_signals()
        assert "bollinger_breakout" in names
        assert "bollinger_squeeze" in names
        assert "volume_spike" in names
        assert "volume_breakout" in names
