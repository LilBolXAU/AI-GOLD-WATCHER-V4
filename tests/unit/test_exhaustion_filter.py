"""
Unit tests for ExhaustionFilter (Chống Bán Đuổi Đáy / Mua Đuổi Đỉnh).
Verifies:
1. Oversold climax blocks directional SELL.
2. Overbought climax blocks directional BUY.
3. Band hyper-extension triggers VETO.
4. Absorption rejection wicks trigger VETO.
5. Mean-reverting strategies (RANGE_REVERSAL, ASIAN_RANGE_SCALPER) are exempted.
6. Normal non-exhausted conditions pass smoothly.
"""

import pandas as pd
import pytest

from src.regime.exhaustion_filter import ExhaustionFilter
from src.strategies.base_strategy import OrderSide


def create_synthetic_df(
    close: float,
    open_p: float,
    high: float,
    low: float,
    rsi: float = 50.0,
    atr: float = 1.0,
    ema_20: float = 2650.0,
    bb_lower: float = 2645.0,
    bb_upper: float = 2655.0,
) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "open": [open_p] * 10,
            "high": [high] * 10,
            "low": [low] * 10,
            "close": [close] * 10,
            "rsi_14": [rsi] * 10,
            "atr_14": [atr] * 10,
            "ema_20": [ema_20] * 10,
            "bb_lower": [bb_lower] * 10,
            "bb_upper": [bb_upper] * 10,
        },
        index=pd.date_range("2026-01-01", periods=10, freq="5min"),
    )
    return df


def test_oversold_rsi_blocks_sell():
    """RSI < 33.0 must block trend-following SELL."""
    df = create_synthetic_df(close=3901.0, open_p=3903.0, high=3904.0, low=3900.5, rsi=28.5)
    is_exh, reason = ExhaustionFilter.is_exhausted(df, OrderSide.SELL, "TREND_FOLLOWING")
    assert is_exh is True
    assert "oversold exhaustion" in reason


def test_overbought_rsi_blocks_buy():
    """RSI > 67.0 must block trend-following BUY."""
    df = create_synthetic_df(close=3955.0, open_p=3952.0, high=3956.0, low=3951.0, rsi=72.0)
    is_exh, reason = ExhaustionFilter.is_exhausted(df, OrderSide.BUY, "TREND_FOLLOWING")
    assert is_exh is True
    assert "overbought exhaustion" in reason


def test_stretched_band_blocks_sell():
    """Price > 2.0 ATR below EMA20 and below lower band must block SELL."""
    # EMA20 = 3920.0, ATR = 1.5 -> EMA - 2*ATR = 3917.0. Close = 3915.0, bb_lower = 3916.0
    df = create_synthetic_df(
        close=3915.0,
        open_p=3918.0,
        high=3919.0,
        low=3914.0,
        rsi=40.0,
        atr=1.5,
        ema_20=3920.0,
        bb_lower=3916.0,
    )
    is_exh, reason = ExhaustionFilter.is_exhausted(df, OrderSide.SELL, "VOLATILITY_BREAKOUT")
    assert is_exh is True
    assert "stretched" in reason


def test_rejection_wick_blocks_sell():
    """Lower rejection wick >= 45% of candle range must block SELL."""
    # Range: high 3910.0, low 3900.0 (range=10.0). Open 3908.0, Close 3907.0 -> lower wick = 3907 - 3900 = 7.0 (70%)
    df = create_synthetic_df(
        close=3907.0,
        open_p=3908.0,
        high=3910.0,
        low=3900.0,
        rsi=45.0,
        ema_20=3915.0,
    )
    is_exh, reason = ExhaustionFilter.is_exhausted(df, OrderSide.SELL, "PULLBACK_CONTINUATION")
    assert is_exh is True
    assert "rejection wick" in reason


def test_exempt_strategies_pass():
    """RANGE_REVERSAL and ASIAN_RANGE_SCALPER must be exempt to buy oversold / sell overbought."""
    df = create_synthetic_df(close=3901.0, open_p=3903.0, high=3904.0, low=3900.5, rsi=25.0)
    # Even with RSI=25, RANGE_REVERSAL is exempt
    is_exh_rr, _ = ExhaustionFilter.is_exhausted(df, OrderSide.BUY, "RANGE_REVERSAL")
    assert is_exh_rr is False

    is_exh_asia, _ = ExhaustionFilter.is_exhausted(df, OrderSide.BUY, "ASIAN_RANGE_SCALPER")
    assert is_exh_asia is False


def test_normal_conditions_pass():
    """Normal balanced momentum without climax must pass freely."""
    df = create_synthetic_df(
        close=3925.0,
        open_p=3924.0,
        high=3926.0,
        low=3923.0,
        rsi=52.0,
        atr=1.2,
        ema_20=3924.0,
        bb_lower=3920.0,
        bb_upper=3928.0,
    )
    is_exh, reason = ExhaustionFilter.is_exhausted(df, OrderSide.BUY, "TREND_FOLLOWING")
    assert is_exh is False
    assert reason == ""


def test_climax_rebound_blocks_sell():
    """Recent RSI < 30 followed by a rebound > 0.8 ATR must block SELL."""
    df = create_synthetic_df(close=3905.0, open_p=3900.0, high=3906.0, low=3895.0, rsi=38.0, atr=2.0)
    # Set bar 2 bars ago to have RSI = 25.0
    df.loc[df.index[-3], "rsi_14"] = 25.0
    df.loc[df.index[-3], "low"] = 3895.0
    # Current close is 3905.0, bounce = 3905 - 3895 = 10.0 > 0.8 * 2.0 = 1.6
    is_exh, reason = ExhaustionFilter.is_exhausted(df, OrderSide.SELL, "TREND_FOLLOWING")
    assert is_exh is True
    assert "Climax bottom rebound" in reason

