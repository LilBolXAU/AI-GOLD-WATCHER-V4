"""
Unit tests for Market Regime Detection, Hysteresis, and Volatility Override.
"""

import pandas as pd
import pytest

from src.indicators.indicator_engine import SharedIndicatorEngine
from src.regime.regime_detector import MarketRegimeDetector, RegimeType
from src.regime.regime_features import extract_regime_features


def test_regime_bull_trend_detection(trending_up_df: pd.DataFrame):
    enriched = SharedIndicatorEngine.compute_all(trending_up_df)
    detector = MarketRegimeDetector(hysteresis_bars=1)  # 1 bar for direct check
    state = detector.update(enriched)

    assert state.regime == RegimeType.BULL_TRENDING
    assert state.confidence > 0.60


def test_regime_bear_trend_detection(trending_down_df: pd.DataFrame):
    enriched = SharedIndicatorEngine.compute_all(trending_down_df)
    detector = MarketRegimeDetector(hysteresis_bars=1)
    state = detector.update(enriched)

    assert state.regime == RegimeType.BEAR_TRENDING
    assert state.confidence > 0.60


def test_regime_ranging_detection(ranging_df: pd.DataFrame):
    enriched = SharedIndicatorEngine.compute_all(ranging_df)
    detector = MarketRegimeDetector(hysteresis_bars=1)
    state = detector.update(enriched)

    assert state.regime == RegimeType.MEAN_REVERTING_RANGING


def test_volatility_shock_immediate_override(shock_df: pd.DataFrame):
    enriched = SharedIndicatorEngine.compute_all(shock_df)
    # Use standard 3-bar hysteresis
    detector = MarketRegimeDetector(hysteresis_bars=3, volatility_z_threshold=1.5)
    state = detector.update(enriched)

    # Volatility shock must bypass hysteresis immediately
    assert state.regime == RegimeType.HIGH_VOLATILITY
    assert any("IMMEDIATE OVERRIDE" in r for r in state.reasons)


def test_hysteresis_delay(trending_up_df: pd.DataFrame, ranging_df: pd.DataFrame):
    detector = MarketRegimeDetector(hysteresis_bars=3)

    # Confirm bull trend initially
    enriched_bull = SharedIndicatorEngine.compute_all(trending_up_df)
    for _ in range(4):
        state = detector.update(enriched_bull)
    assert state.regime == RegimeType.BULL_TRENDING

    # Now feed only 1 bar of ranging data; regime should NOT switch yet
    enriched_range = SharedIndicatorEngine.compute_all(ranging_df)
    state_after_1 = detector.update(enriched_range)
    assert state_after_1.regime == RegimeType.BULL_TRENDING, "Regime switched prematurely before hysteresis satisfied"
