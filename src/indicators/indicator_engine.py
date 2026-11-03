"""
Shared Indicator Engine for AI GOLD WATCHER V4.
Computes technical indicators across timeframes with zero lookahead bias.
"""

from typing import Tuple
import pandas as pd
import numpy as np

from src.indicators.trend_indicators import calc_ema, calc_ema_slope, check_ema_alignment
from src.indicators.volatility_indicators import (
    calc_atr,
    calc_bollinger_bands,
    calc_rolling_volatility,
)
from src.indicators.momentum_indicators import (
    calc_rsi,
    calc_adx_dmi,
    calc_efficiency_ratio,
    calc_normalized_roc,
)
from src.indicators.price_action import compute_market_structure, compute_candlestick_patterns


def calc_swing_points(
    high: pd.Series, low: pd.Series, window: int = 5
) -> Tuple[pd.Series, pd.Series]:
    """
    Causal structural swing high and low detection using backward-looking window.
    Swing high is the highest high over the past `window` bars.
    Swing low is the lowest low over the past `window` bars.
    """
    swing_high = high.shift(1).rolling(window=window).max()
    swing_low = low.shift(1).rolling(window=window).min()
    return swing_high, swing_low


class SharedIndicatorEngine:
    """
    Centralized indicator computation engine.
    Ensures all 4 strategies share identical, cached mathematical features.
    """

    @classmethod
    def compute_all(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute full indicator feature matrix from OHLCV DataFrame.
        Returns a fresh DataFrame containing all indicator columns.
        """
        if df.empty or len(df) < 20:
            return df.copy()

        out = df.copy()

        # 1. EMAs
        out["ema_9"] = calc_ema(out["close"], 9)
        out["ema_20"] = calc_ema(out["close"], 20)
        out["ema_50"] = calc_ema(out["close"], 50)
        out["ema_200"] = calc_ema(out["close"], 200)

        # 2. Volatility (ATR, Bollinger Bands)
        out["atr_14"] = calc_atr(out["high"], out["low"], out["close"], period=14)
        bb_mid, bb_up, bb_low, bb_w = calc_bollinger_bands(out["close"], period=20, num_std=2.0)
        out["bb_middle"] = bb_mid
        out["bb_upper"] = bb_up
        out["bb_lower"] = bb_low
        out["bb_width"] = bb_w
        out["rolling_vol_20"] = calc_rolling_volatility(out["close"], window=20)

        # 3. Momentum (RSI, ADX, DMI, ROC, ER)
        out["rsi_14"] = calc_rsi(out["close"], period=14)
        plus_di, minus_di, adx = calc_adx_dmi(out["high"], out["low"], out["close"], period=14)
        out["plus_di"] = plus_di
        out["minus_di"] = minus_di
        out["adx_14"] = adx
        out["efficiency_ratio_10"] = calc_efficiency_ratio(out["close"], period=10)
        out["roc_atr_5"] = calc_normalized_roc(out["close"], out["atr_14"], period=5)

        # 4. Normalized Slope & Alignment
        out["ema_20_slope"] = calc_ema_slope(out["ema_20"], out["atr_14"], lookback=3)
        bull_align, bear_align = check_ema_alignment(out["ema_20"], out["ema_50"], out["ema_200"])
        out["ema_aligned_bull"] = bull_align
        out["ema_aligned_bear"] = bear_align

        # 5. Market Structure (Swing Highs/Lows & Donchian)
        sw_high, sw_low = calc_swing_points(out["high"], out["low"], window=5)
        out["swing_high_5"] = sw_high
        out["swing_low_5"] = sw_low
        out["donchian_high_20"] = out["high"].shift(1).rolling(window=20).max()
        out["donchian_low_20"] = out["low"].shift(1).rolling(window=20).min()

        # 6. Institutional Price Action & Smart Money Market Structure
        ms_df = compute_market_structure(out)
        for col in ms_df.columns:
            out[col] = ms_df[col]

        pa_df = compute_candlestick_patterns(out)
        for col in pa_df.columns:
            out[col] = pa_df[col]

        return out
