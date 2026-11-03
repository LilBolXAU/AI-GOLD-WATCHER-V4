"""
Unit tests for Machine Learning Meta-Labeling Engine.
"""

from datetime import datetime, timezone
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from src.scoring.meta_labeler import MetaLabelEngine, MetaLabelResult
from src.strategies.base_strategy import SignalCandidate, OrderSide
from src.regime.regime_detector import MarketRegimeState, RegimeType


@pytest.fixture
def sample_candidate():
    return SignalCandidate(
        strategy_id="TREND_FOLLOWING",
        timestamp=datetime.now(timezone.utc),
        symbol="XAUUSDm",
        side=OrderSide.BUY,
        entry_price=2650.0,
        stop_loss=2649.0,
        take_profit=2652.0,
        raw_confidence=0.80,
    )


@pytest.fixture
def sample_indicators():
    records = []
    base = 2650.0
    for i in range(50):
        records.append({
            "close": base + i * 0.1,
            "rsi": 55.0,
            "atr": 1.5,
            "adx": 30.0,
            "ema_20": base + i * 0.1,
            "ema_50": base + i * 0.08,
            "ema_200": base,
            "bb_upper": base + i * 0.1 + 3.0,
            "bb_lower": base + i * 0.1 - 3.0,
            "bb_middle": base + i * 0.1,
            "efficiency_ratio": 0.65,
        })
    return pd.DataFrame.from_records(records)


@pytest.fixture
def sample_regime():
    return MarketRegimeState(
        timestamp=datetime.now(timezone.utc),
        regime=RegimeType.BULL_TRENDING,
        confidence=0.85,
        raw_candidate=RegimeType.BULL_TRENDING,
    )


def test_meta_label_feature_extraction(sample_candidate, sample_indicators, sample_regime):
    engine = MetaLabelEngine(threshold=0.65, model_path=None)
    feats = engine.extract_features(sample_candidate, sample_indicators, sample_regime, current_spread=20)
    assert len(feats) == 13
    assert isinstance(feats, np.ndarray)


def test_meta_label_heuristic_prediction(sample_candidate, sample_indicators, sample_regime):
    engine = MetaLabelEngine(threshold=0.65, model_path=None)
    res = engine.predict_win_probability(sample_candidate, sample_indicators, sample_regime, current_spread=20)
    assert isinstance(res, MetaLabelResult)
    assert 0.0 <= res.win_probability <= 1.0
    assert isinstance(res.passes_filter, bool)
    assert "ML" in res.reason


def test_meta_label_train_and_predict(tmp_path, sample_candidate, sample_indicators, sample_regime):
    model_file = tmp_path / "test_meta_model.joblib"
    engine = MetaLabelEngine(threshold=0.60, model_path=str(model_file))

    # Generate synthetic historical features and binary outcomes
    np.random.seed(42)
    X = np.random.randn(60, 13)
    # y=1 when first feature > 0
    y = (X[:, 0] > 0).astype(int)

    acc = engine.train_on_history(X, y, save=True)
    assert acc > 0.0
    assert model_file.exists()

    # Inference using trained model
    res = engine.predict_win_probability(sample_candidate, sample_indicators, sample_regime, current_spread=20)
    assert isinstance(res, MetaLabelResult)
    assert 0.0 <= res.win_probability <= 1.0
    assert "ML Model Win Probability" in res.reason
