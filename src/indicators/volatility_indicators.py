"""
Volatility indicators for AI GOLD WATCHER V4.
True Wilder formulation for ATR, Bollinger Bands, and relative volatility.
"""

from typing import Tuple
import numpy as np
import pandas as pd


def calc_true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """True Range: max(High - Low, abs(High - Close_prev), abs(Low - Close_prev))."""
    prev_close = close.shift(1)
    hl = high - low
    h_pc = (high - prev_close).abs()
    l_pc = (low - prev_close).abs()
    tr = pd.concat([hl, h_pc, l_pc], axis=1).max(axis=1)
    return tr


def calc_atr(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """
    Wilder's Average True Range (ATR 1978).
    Accumulation smoothing: ATR_t = (ATR_{t-1} * (period - 1) + TR_t) / period.
    """
    if len(close) < period:
        return pd.Series(np.nan, index=close.index)

    tr = calc_true_range(high, low, close)
    # Wilder's exponential smoothing equivalent: alpha = 1 / period
    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    return atr


def calc_bollinger_bands(
    close: pd.Series, period: int = 20, num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands (Middle, Upper, Lower, Bandwidth).
    Bandwidth = (Upper - Lower) / Middle.
    """
    if len(close) < period:
        nan_s = pd.Series(np.nan, index=close.index)
        return nan_s, nan_s, nan_s, nan_s

    middle = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    bandwidth = (upper - lower) / middle.replace(0, np.nan)

    return middle, upper, lower, bandwidth


def calc_rolling_volatility(close: pd.Series, window: int = 20) -> pd.Series:
    """Annualized rolling volatility of log returns (bar-scaled for intraday)."""
    log_ret = np.log(close / close.shift(1))
    return log_ret.rolling(window=window).std()
