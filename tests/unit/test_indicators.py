"""
Unit tests for Technical Indicator calculations.
"""

import numpy as np
import pandas as pd
import pytest

from src.indicators.trend_indicators import calc_ema, calc_ema_slope, check_ema_alignment
from src.indicators.volatility_indicators import calc_atr, calc_bollinger_bands, calc_rolling_volatility
from src.indicators.momentum_indicators import calc_rsi, calc_adx_dmi, calc_efficiency_ratio
from src.indicators.indicator_engine import SharedIndicatorEngine, calc_swing_points


def test_calc_ema(trending_up_df: pd.DataFrame):
    close = trending_up_df["close"]
    ema20 = calc_ema(close, period=20)
    assert len(ema20) == len(close)
    # In an uptrend, EMA20 should be monotonically increasing in the latter half
    assert ema20.iloc[-1] > ema20.iloc[-20]


def test_calc_atr(trending_up_df: pd.DataFrame):
    atr = calc_atr(trending_up_df["high"], trending_up_df["low"], trending_up_df["close"], period=14)
    assert len(atr) == len(trending_up_df)
    # ATR must be strictly positive
    valid_atr = atr.dropna()
    assert (valid_atr > 0).all()


def test_calc_bollinger_bands(ranging_df: pd.DataFrame):
    mid, up, low, w = calc_bollinger_bands(ranging_df["close"], period=20, num_std=2.0)
    assert (up.dropna() >= mid.dropna()).all()
    assert (mid.dropna() >= low.dropna()).all()
    assert (w.dropna() >= 0).all()


def test_calc_rsi_bounds(trending_up_df: pd.DataFrame, trending_down_df: pd.DataFrame):
    rsi_up = calc_rsi(trending_up_df["close"], period=14).dropna()
    rsi_down = calc_rsi(trending_down_df["close"], period=14).dropna()

    # RSI must be strictly between 0 and 100
    assert (rsi_up >= 0.0).all() and (rsi_up <= 100.0).all()
    assert (rsi_down >= 0.0).all() and (rsi_down <= 100.0).all()

    # Uptrend RSI should be higher than downtrend RSI
    assert rsi_up.iloc[-1] > 60.0
    assert rsi_down.iloc[-1] < 40.0


def test_calc_adx_dmi(trending_up_df: pd.DataFrame):
    plus_di, minus_di, adx = calc_adx_dmi(
        trending_up_df["high"], trending_up_df["low"], trending_up_df["close"], period=14
    )
    valid_adx = adx.dropna()
    assert (valid_adx >= 0.0).all() and (valid_adx <= 100.0).all()
    # Strong uptrend: +DI should exceed -DI and ADX should be elevated
    assert plus_di.iloc[-1] > minus_di.iloc[-1]
    assert valid_adx.iloc[-1] > 20.0


def test_calc_efficiency_ratio(trending_up_df: pd.DataFrame, ranging_df: pd.DataFrame):
    er_trend = calc_efficiency_ratio(trending_up_df["close"], period=10).dropna()
    er_range = calc_efficiency_ratio(ranging_df["close"], period=10).dropna()

    # ER in a perfect trend is close to 1.0; in range it should be low
    assert er_trend.iloc[-1] > er_range.mean()


def test_shared_indicator_engine(trending_up_df: pd.DataFrame):
    enriched = SharedIndicatorEngine.compute_all(trending_up_df)
    expected_cols = [
        "ema_9", "ema_20", "ema_50", "ema_200",
        "atr_14", "bb_middle", "bb_upper", "bb_lower", "bb_width",
        "rsi_14", "plus_di", "minus_di", "adx_14", "efficiency_ratio_10",
        "ema_20_slope", "ema_aligned_bull", "ema_aligned_bear",
        "swing_high_5", "swing_low_5",
    ]
    for col in expected_cols:
        assert col in enriched.columns, f"Expected column {col} in enriched DataFrame"
