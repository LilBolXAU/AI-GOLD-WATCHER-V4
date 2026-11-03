"""
Momentum and directional indicators for AI GOLD WATCHER V4.
Implements exact Wilder's RSI, Wilder's ADX/DMI, and Kaufman Efficiency Ratio.
"""

from typing import Tuple
import numpy as np
import pandas as pd
from src.indicators.volatility_indicators import calc_true_range


def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Wilder's Relative Strength Index (RSI 1978).
    Smoothed using exponential moving average with alpha = 1 / period.
    """
    if len(close) < period + 1:
        return pd.Series(np.nan, index=close.index)

    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    # Handle pure zero loss edge cases
    rsi = rsi.fillna(100.0).where(avg_loss != 0, 100.0)
    rsi = rsi.where((avg_gain != 0) | (avg_loss != 0), 50.0)
    return rsi


def calc_adx_dmi(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Wilder's Directional Movement System (1978): +DI, -DI, and ADX.
    Returns: (plus_di, minus_di, adx).
    """
    if len(close) < period * 2:
        nan_s = pd.Series(np.nan, index=close.index)
        return nan_s, nan_s, nan_s

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=close.index,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=close.index,
    )

    tr = calc_true_range(high, low, close)

    # Wilder accumulation smoothing: alpha = 1 / period
    tr_smooth = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    plus_dm_smooth = plus_dm.ewm(alpha=1.0 / period, adjust=False).mean()
    minus_dm_smooth = minus_dm.ewm(alpha=1.0 / period, adjust=False).mean()

    plus_di = (100.0 * plus_dm_smooth / tr_smooth.replace(0, np.nan)).fillna(0.0)
    minus_di = (100.0 * minus_dm_smooth / tr_smooth.replace(0, np.nan)).fillna(0.0)

    di_sum = plus_di + minus_di
    dx = (100.0 * (plus_di - minus_di).abs() / di_sum.replace(0, np.nan)).fillna(0.0)
    adx = dx.ewm(alpha=1.0 / period, adjust=False).mean()

    return plus_di, minus_di, adx


def calc_efficiency_ratio(close: pd.Series, period: int = 10) -> pd.Series:
    """
    Kaufman Efficiency Ratio (KER): Directional net change / Total path movement.
    Bounded in [0.0, 1.0]. Near 1.0 = clean linear trend, near 0.0 = choppy noise.
    """
    if len(close) < period + 1:
        return pd.Series(np.nan, index=close.index)

    net_change = (close - close.shift(period)).abs()
    path = close.diff().abs().rolling(window=period).sum()
    er = net_change / path.replace(0, np.nan)
    return er.fillna(0.0)


def calc_normalized_roc(close: pd.Series, atr: pd.Series, period: int = 5) -> pd.Series:
    """Rate of Change normalized by ATR: (Close_t - Close_{t-k}) / ATR_t."""
    roc = (close - close.shift(period)) / atr.replace(0, np.nan)
    return roc
