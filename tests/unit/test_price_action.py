"""
Unit tests for Price Action & Market Structure (SMC) Engine.
Verifies:
1. Fractal swing high / swing low detection.
2. Market Structure Shift (BOS / CHoCH) and structural bias.
3. Candlestick pattern recognition (Pinbar rejection wicks, Engulfing expansion).
4. SmartMoneyStructureStrategy signal generation and Scalp vs Swing adaptation.
"""

from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd
import pytest

from src.data.models import SymbolSpec
from src.indicators.indicator_engine import SharedIndicatorEngine
from src.indicators.price_action import (
    detect_swing_pivots,
    compute_market_structure,
    compute_candlestick_patterns,
)
from src.strategies.base_strategy import OrderSide
from src.strategies.smc_structure import SmartMoneyStructureStrategy


@pytest.fixture
def dummy_spec() -> SymbolSpec:
    return SymbolSpec(
        name="XAUUSDm",
        digits=2,
        point=0.01,
        contract_size=100.0,
        volume_min=0.01,
        volume_max=10.0,
        volume_step=0.01,
        stops_level=0,
    )


def test_detect_swing_pivots():
    """Verify that clear V-tops and V-bottoms are identified as swing points."""
    # Construct a series with an obvious swing high at index 2 (left=2, right=2)
    # and swing low at index 6
    highs = [100.0, 102.0, 105.0, 103.0, 101.0, 99.0, 98.0, 99.0, 101.0]
    lows = [98.0, 99.0, 101.0, 100.0, 97.0, 95.0, 93.0, 96.0, 98.0]
    opens = [99.0, 100.0, 102.0, 104.0, 102.0, 100.0, 96.0, 97.0, 99.0]
    closes = [100.0, 101.0, 103.0, 102.0, 100.0, 96.0, 95.0, 98.0, 100.0]

    df = pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes},
        index=pd.date_range("2026-01-01", periods=9, freq="5min"),
    )

    sh, sl = detect_swing_pivots(df, left_bars=2, right_bars=2)

    # Index 2 has high=105.0 which is > 100, 102 and > 103, 101
    assert bool(sh.iloc[2]) is True
    assert bool(sh.iloc[0]) is False
    assert bool(sh.iloc[1]) is False

    # Index 6 has low=93.0 which is < 97, 95 and < 96, 98
    assert bool(sl.iloc[6]) is True
    assert bool(sl.iloc[5]) is False


def test_compute_market_structure():
    """Verify structure bias and CHoCH detection upon breaking structural highs/lows."""
    # 20 bars of synthetic price action
    # First makes a swing high at bar 3 (high=105), drops, then bar 10 breaks 105.0
    dates = pd.date_range("2026-01-01", periods=15, freq="5min")
    highs = [100.0, 102.0, 105.0, 103.0, 101.0, 99.0, 98.0, 100.0, 102.0, 106.0, 107.0, 104.0, 102.0, 100.0, 99.0]
    lows = [98.0, 99.0, 102.0, 100.0, 98.0, 96.0, 95.0, 97.0, 99.0, 103.0, 104.0, 101.0, 99.0, 97.0, 96.0]
    opens = [99.0, 100.0, 103.0, 104.0, 100.0, 98.0, 96.0, 98.0, 100.0, 103.0, 105.0, 103.0, 101.0, 99.0, 98.0]
    closes = [100.0, 101.0, 104.0, 102.0, 99.0, 97.0, 97.0, 99.0, 102.0, 106.0, 106.0, 102.0, 100.0, 98.0, 97.0]

    df = pd.DataFrame({"open": opens, "high": highs, "low": lows, "close": closes}, index=dates)
    struct = compute_market_structure(df)

    assert "structure_bias" in struct.columns
    assert "structure_shift" in struct.columns
    assert "last_swing_high" in struct.columns
    assert "last_swing_low" in struct.columns

    # Bar 9 has close=106.0 which breaks past swing high (105.0) -> Bullish CHoCH
    assert struct["structure_shift"].iloc[9] == 1
    assert struct["structure_bias"].iloc[9] == 1


def test_candlestick_patterns():
    """Verify Pinbar rejection wicks and Engulfing patterns."""
    dates = pd.date_range("2026-01-01", periods=4, freq="5min")
    # Bar 0: Normal
    # Bar 1: Bullish Pinbar (open=102, close=102.5, high=103, low=98) -> range=5, lower wick=4 (80% rejection)
    # Bar 2: Bearish bar (open=103, close=101)
    # Bar 3: Bullish Engulfing (open=100.5, close=104, high=104.2, low=100)
    df = pd.DataFrame(
        {
            "open": [100.0, 102.0, 103.0, 100.5],
            "high": [101.0, 103.0, 103.5, 104.2],
            "low": [99.0, 98.0, 100.8, 100.0],
            "close": [100.5, 102.5, 101.0, 104.0],
        },
        index=dates,
    )

    pa = compute_candlestick_patterns(df)

    # Check Bar 1 is Bullish Pinbar
    assert bool(pa["is_pinbar_bull"].iloc[1]) is True
    assert bool(pa["is_pinbar_bear"].iloc[1]) is False

    # Check Bar 3 is Bullish Engulfing
    assert bool(pa["is_engulfing_bull"].iloc[3]) is True


def test_smc_strategy_evaluation(dummy_spec):
    """Verify SmartMoneyStructureStrategy triggers BUY on bullish CHoCH and adapts R:R."""
    # Generate 40 bars
    dates = pd.date_range("2026-01-01", periods=40, freq="5min")
    closes = np.linspace(2600.0, 2630.0, 40)
    highs = closes + 1.0
    lows = closes - 1.0
    opens = closes - 0.5

    df = pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "volume": 100},
        index=dates,
    )

    # Add required technical columns
    df["atr_14"] = 1.20
    df["rsi_14"] = 55.0
    df["adx_14"] = 28.0  # High momentum -> SWING mode
    df["efficiency_ratio_10"] = 0.60
    df["structure_bias"] = 1
    df["structure_shift"] = 1  # Bullish CHoCH on last bar
    df["last_swing_high"] = 2628.0
    df["last_swing_low"] = 2625.0
    df["is_pinbar_bull"] = False
    df["is_pinbar_bear"] = False
    df["is_engulfing_bull"] = False
    df["is_engulfing_bear"] = False

    strat = SmartMoneyStructureStrategy(max_sl_usd=2.00, swing_rr_target=2.5, scalp_rr_target=1.5)
    sig = strat.evaluate(df, dummy_spec)

    assert sig is not None
    assert sig.strategy_id == "SMC_STRUCTURE_PRICE_ACTION"
    assert sig.side == OrderSide.BUY
    assert sig.stop_loss < sig.entry_price
    assert sig.take_profit > sig.entry_price
    # Check Swing RR target (2.5) applied due to high ADX + ER
    sl_dist = sig.entry_price - sig.stop_loss
    tp_dist = sig.take_profit - sig.entry_price
    assert pytest.approx(tp_dist / sl_dist, abs=0.15) == 2.5
