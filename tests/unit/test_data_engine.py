"""
Unit tests for Data Engine, Bar Models, and Data Validation.
"""

from datetime import datetime, timezone
import pytest
from src.data.models import BarData, SymbolSpec, Timeframe, DataError
from src.data.data_validator import DataValidator
from src.data.symbol_specs import DEFAULT_EXNESS_XAUUSD, validate_broker_symbol
from src.data.mt5_client import MockMT5Client
from src.data.data_engine import MT5DataEngine


def test_bar_data_invariants_valid():
    bar = BarData(
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        open=2650.0,
        high=2655.0,
        low=2648.0,
        close=2652.0,
        tick_volume=150,
        spread=18,
    )
    assert bar.high >= bar.low
    assert bar.high >= bar.open
    assert bar.low <= bar.close
    assert bar.timestamp.tzinfo is not None


def test_bar_data_invariants_invalid_high_low():
    with pytest.raises(ValueError, match="cannot be lower than Low"):
        BarData(
            timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
            open=2650.0,
            high=2640.0,  # Invalid: high < low!
            low=2645.0,
            close=2642.0,
            tick_volume=100,
            spread=15,
        )


def test_bar_data_naive_timezone_rejected():
    with pytest.raises(ValueError, match="must be timezone-aware UTC"):
        BarData(
            timestamp=datetime(2026, 1, 1, 12, 0),  # Naive datetime
            open=2650.0,
            high=2655.0,
            low=2648.0,
            close=2652.0,
            tick_volume=100,
            spread=15,
        )


def test_symbol_spec_validation(symbol_spec: SymbolSpec):
    validated_spec = validate_broker_symbol(symbol_spec)
    assert validated_spec.name == "XAUUSDm"
    assert validated_spec.contract_size == 100.0
    assert validated_spec.point == 0.01
    assert validated_spec.digits == 2


def test_closed_bar_discipline(mock_mt5_client: MockMT5Client):
    engine = MT5DataEngine(client=mock_mt5_client, symbol="XAUUSDm")
    assert engine.initialize() is True

    # When closed_only=True, returned count matches exactly
    bars = engine.fetch_bars(Timeframe.M5, count=50, closed_only=True)
    assert len(bars) == 50

    # Ensure monotonic chronological order
    for i in range(len(bars) - 1):
        assert bars[i].timestamp < bars[i + 1].timestamp


def test_validator_spike_filter():
    t0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    bar0 = BarData(timestamp=t0, open=2650.0, high=2652.0, low=2649.0, close=2651.0, tick_volume=100, spread=15)
    t1 = datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc)
    # Huge spike candle (high spikes 20 dollars above prev close, next open returns)
    bar1 = BarData(timestamp=t1, open=2651.0, high=2675.0, low=2650.0, close=2652.0, tick_volume=100, spread=15)
    t2 = datetime(2026, 1, 1, 12, 10, tzinfo=timezone.utc)
    bar2 = BarData(timestamp=t2, open=2652.0, high=2653.0, low=2650.0, close=2651.0, tick_volume=100, spread=15)

    spikes = DataValidator.detect_bad_spikes([bar0, bar1, bar2], threshold_pts=300.0)
    assert 1 in spikes
