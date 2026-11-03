"""
Trend indicators for AI GOLD WATCHER V4.
Strictly causal: past and present closed bars only. Zero lookahead bias.
"""

from typing import Tuple
import numpy as np
import pandas as pd


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA).
    adjust=False gives the recursive formulation: EMA_t = alpha * P_t + (1 - alpha) * EMA_{t-1}.
    """
    if len(series) == 0:
        return pd.Series(np.nan, index=series.index)
    return series.ewm(span=period, adjust=False).mean()


def calc_ema_slope(ema: pd.Series, atr: pd.Series, lookback: int = 3) -> pd.Series:
    """
    Calculate EMA slope normalized by ATR: (EMA_t - EMA_{t-k}) / (k * ATR_t).
    Dimensionless metric representing trend steepness.
    """
    delta_ema = ema.diff(lookback)
    normalized_slope = delta_ema / (lookback * atr.replace(0, np.nan))
    return normalized_slope


def check_ema_alignment(
    ema_fast: pd.Series, ema_mid: pd.Series, ema_slow: pd.Series
) -> Tuple[pd.Series, pd.Series]:
    """
    Check EMA multi-period alignment:
    Bullish: fast > mid > slow (or fast > mid if slow is not yet established)
    Bearish: fast < mid < slow (or fast < mid if slow is not yet established)
    Returns: (is_bull_aligned, is_bear_aligned) as boolean Series.
    """
    bull = (ema_fast > ema_mid) & (ema_mid >= ema_slow)
    bear = (ema_fast < ema_mid) & (ema_mid <= ema_slow)
    return bull, bear
