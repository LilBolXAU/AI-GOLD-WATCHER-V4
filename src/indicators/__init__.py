"""Indicators package for AI GOLD WATCHER V4."""
from src.indicators.trend_indicators import calc_ema, calc_ema_slope, check_ema_alignment
from src.indicators.volatility_indicators import (
    calc_atr,
    calc_bollinger_bands,
    calc_rolling_volatility,
    calc_true_range,
)
from src.indicators.momentum_indicators import (
    calc_rsi,
    calc_adx_dmi,
    calc_efficiency_ratio,
    calc_normalized_roc,
)
from src.indicators.indicator_engine import SharedIndicatorEngine, calc_swing_points

__all__ = [
    "calc_ema",
    "calc_ema_slope",
    "check_ema_alignment",
    "calc_atr",
    "calc_bollinger_bands",
    "calc_rolling_volatility",
    "calc_true_range",
    "calc_rsi",
    "calc_adx_dmi",
    "calc_efficiency_ratio",
    "calc_normalized_roc",
    "SharedIndicatorEngine",
    "calc_swing_points",
]
