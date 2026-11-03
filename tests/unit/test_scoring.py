"""
Unit tests for Multi-Factor Confidence Scoring Engine.
"""

from datetime import datetime, timezone
import pytest

from src.strategies.base_strategy import SignalCandidate, OrderSide
from src.regime.regime_detector import MarketRegimeState, RegimeType
from src.scoring.confidence_engine import ConfidenceEngine
from src.scoring.signal_quality import ScoredSignal


def test_confidence_scoring_bull_aligned():
    engine = ConfidenceEngine(threshold=65.0, max_spread_pts=35)

    candidate = SignalCandidate(
        strategy_id="TREND_FOLLOWING",
        timestamp=datetime.now(timezone.utc),
        symbol="XAUUSDm",
        side=OrderSide.BUY,
        entry_price=2650.0,
        stop_loss=2649.0,  # 1.00 risk ($1.00 = 100 pts)
        take_profit=2652.5,  # 2.5 reward (2.5 R:R)
        raw_confidence=0.85,
        reasons=["EMA bull cross"],
    )

    regime_state = MarketRegimeState(
        timestamp=datetime.now(timezone.utc),
        regime=RegimeType.BULL_TRENDING,
        confidence=0.90,
        raw_candidate=RegimeType.BULL_TRENDING,
        reasons=["Strong bull DMI"],
    )

    scored = engine.score(candidate, regime_state, current_spread=15)
    assert isinstance(scored, ScoredSignal)
    assert 0.0 <= scored.total_score <= 100.0
    assert scored.confidence_score == scored.total_score
    assert scored.passes_threshold is True


def test_confidence_scoring_spread_penalty():
    engine = ConfidenceEngine(threshold=65.0, max_spread_pts=35)

    candidate = SignalCandidate(
        strategy_id="TREND_FOLLOWING",
        timestamp=datetime.now(timezone.utc),
        symbol="XAUUSDm",
        side=OrderSide.BUY,
        entry_price=2650.0,
        stop_loss=2649.0,
        take_profit=2652.5,
        raw_confidence=0.85,
    )

    regime_state = MarketRegimeState(
        timestamp=datetime.now(timezone.utc),
        regime=RegimeType.BULL_TRENDING,
        confidence=0.90,
        raw_candidate=RegimeType.BULL_TRENDING,
    )

    # Spread 60 points exceeds 35 points limit -> fails threshold
    scored = engine.score(candidate, regime_state, current_spread=60)
    assert scored.passes_threshold is False
    assert scored.sub_scores["spread_condition"] == 0.0
