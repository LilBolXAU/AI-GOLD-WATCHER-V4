"""
Unit tests for MacroTrendDetector (Multi-Timeframe H1 Analysis).
"""

from datetime import datetime, timezone, timedelta
import pytest

from src.data.models import BarData, SymbolSpec
from src.regime.macro_trend import MacroTrendDetector, MacroTrendBias
from src.regime.regime_detector import MarketRegimeState, RegimeType
from src.selector.adaptive_selector import AdaptiveStrategySelector


def _generate_bars(base_price: float, step: float, count: int):
    bars = []
    t0 = datetime(2026, 11, 3, 0, 0, tzinfo=timezone.utc)
    for i in range(count):
        p = base_price + i * step
        bars.append(
            BarData(
                timestamp=t0 + timedelta(hours=i),
                open=p - 0.5,
                high=p + 1.0,
                low=p - 1.0,
                close=p,
                tick_volume=100,
                spread=20,
            )
        )
    return bars


def test_macro_trend_bullish():
    # Rising price from 2600 to 2700 over 30 bars
    bars = _generate_bars(base_price=2600.0, step=3.0, count=30)
    res = MacroTrendDetector.analyze(bars)
    assert res.bias == MacroTrendBias.BULLISH
    assert "Bullish" in res.description
    assert res.h1_close > res.h1_ema50


def test_macro_trend_bearish():
    # Falling price from 2700 to 2600 over 30 bars
    bars = _generate_bars(base_price=2700.0, step=-3.0, count=30)
    res = MacroTrendDetector.analyze(bars)
    assert res.bias == MacroTrendBias.BEARISH
    assert "Bearish" in res.description
    assert res.h1_close < res.h1_ema50


def test_macro_trend_insufficient_bars():
    bars = _generate_bars(base_price=2600.0, step=1.0, count=10)
    res = MacroTrendDetector.analyze(bars)
    assert res.bias == MacroTrendBias.NEUTRAL
    assert "Insufficient" in res.description
