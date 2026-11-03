"""
Unit tests for Adaptive Strategy Selector and Regime Routing.
"""

from datetime import datetime, timezone
import pandas as pd
import pytest

from src.data.models import SymbolSpec
from src.regime.regime_detector import MarketRegimeState, RegimeType
from src.selector.strategy_eligibility import get_eligible_strategies
from src.selector.adaptive_selector import AdaptiveStrategySelector
from src.indicators.indicator_engine import SharedIndicatorEngine


def test_strategy_eligibility_mapping():
    assert "TREND_FOLLOWING" in get_eligible_strategies(RegimeType.BULL_TRENDING)
    assert "PULLBACK_CONTINUATION" in get_eligible_strategies(RegimeType.BULL_TRENDING)
    assert "RANGE_REVERSAL" not in get_eligible_strategies(RegimeType.BULL_TRENDING)

    assert "RANGE_REVERSAL" in get_eligible_strategies(RegimeType.MEAN_REVERTING_RANGING)
    assert "TREND_FOLLOWING" not in get_eligible_strategies(RegimeType.MEAN_REVERTING_RANGING)

    assert "VOLATILITY_BREAKOUT" in get_eligible_strategies(RegimeType.HIGH_VOLATILITY)
    assert len(get_eligible_strategies(RegimeType.UNSTABLE)) == 0


def test_selector_abstain_on_unstable_regime(trending_up_df: pd.DataFrame, symbol_spec: SymbolSpec):
    enriched = SharedIndicatorEngine.compute_all(trending_up_df)
    selector = AdaptiveStrategySelector()

    unstable_state = MarketRegimeState(
        timestamp=datetime.now(timezone.utc),
        regime=RegimeType.UNSTABLE,
        confidence=0.3,
        raw_candidate=RegimeType.UNSTABLE,
        reasons=["High uncertainty"],
    )

    # Must abstain (return None) in UNSTABLE regime
    candidate = selector.evaluate(enriched, unstable_state, symbol_spec)
    assert candidate is None


def test_selector_evaluates_eligible_only(trending_up_df: pd.DataFrame, symbol_spec: SymbolSpec):
    enriched = SharedIndicatorEngine.compute_all(trending_up_df)
    selector = AdaptiveStrategySelector()

    bull_state = MarketRegimeState(
        timestamp=datetime.now(timezone.utc),
        regime=RegimeType.BULL_TRENDING,
        confidence=0.85,
        raw_candidate=RegimeType.BULL_TRENDING,
        reasons=["Confirmed bull trend"],
    )

    candidate = selector.evaluate(enriched, bull_state, symbol_spec)
    if candidate is not None:
        assert candidate.strategy_id in ["TREND_FOLLOWING", "PULLBACK_CONTINUATION", "VOLATILITY_BREAKOUT"]
