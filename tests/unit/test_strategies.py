"""
Unit tests for the 4 Independent Trading Strategy Engines.
"""

import pandas as pd
import pytest

from src.data.models import SymbolSpec
from src.indicators.indicator_engine import SharedIndicatorEngine
from src.strategies.base_strategy import OrderSide, SignalCandidate
from src.strategies.trend_following import TrendFollowingStrategy
from src.strategies.pullback import PullbackStrategy
from src.strategies.breakout import BreakoutStrategy
from src.strategies.range_reversal import RangeReversalStrategy
from src.strategies.asian_scalp import AsianRangeScalper
from src.strategies.london_sweep import LondonSweepStrategy


def test_trend_following_strategy_buy(trending_up_df: pd.DataFrame, symbol_spec: SymbolSpec):
    enriched = SharedIndicatorEngine.compute_all(trending_up_df)
    strat = TrendFollowingStrategy()
    sig = strat.evaluate(enriched, symbol_spec)

    if sig is not None:
        assert isinstance(sig, SignalCandidate)
        assert sig.side == OrderSide.BUY
        assert sig.entry_price > sig.stop_loss
        assert sig.take_profit > sig.entry_price
        assert sig.risk_reward_ratio >= 1.5
        assert sig.symbol == symbol_spec.symbol


def test_trend_following_strategy_sell(trending_down_df: pd.DataFrame, symbol_spec: SymbolSpec):
    enriched = SharedIndicatorEngine.compute_all(trending_down_df)
    strat = TrendFollowingStrategy()
    sig = strat.evaluate(enriched, symbol_spec)

    if sig is not None:
        assert isinstance(sig, SignalCandidate)
        assert sig.side == OrderSide.SELL
        assert sig.entry_price < sig.stop_loss
        assert sig.take_profit < sig.entry_price
        assert sig.risk_reward_ratio >= 1.5


def test_breakout_strategy(trending_up_df: pd.DataFrame, symbol_spec: SymbolSpec):
    enriched = SharedIndicatorEngine.compute_all(trending_up_df)
    strat = BreakoutStrategy()
    sig = strat.evaluate(enriched, symbol_spec)

    if sig is not None:
        assert isinstance(sig, SignalCandidate)
        assert sig.strategy_id == "VOLATILITY_BREAKOUT"
        assert sig.risk_distance > 0


def test_range_reversal_strategy(ranging_df: pd.DataFrame, symbol_spec: SymbolSpec):
    enriched = SharedIndicatorEngine.compute_all(ranging_df)
    strat = RangeReversalStrategy()
    sig = strat.evaluate(enriched, symbol_spec)

    if sig is not None:
        assert isinstance(sig, SignalCandidate)
        assert sig.strategy_id == "RANGE_REVERSAL"
        assert sig.risk_reward_ratio >= 1.5


def test_asian_range_scalper(ranging_df: pd.DataFrame, symbol_spec: SymbolSpec):
    enriched = SharedIndicatorEngine.compute_all(ranging_df)
    strat = AsianRangeScalper()
    sig = strat.evaluate(enriched, symbol_spec)

    # Test interface adherence
    assert strat.name == "ASIAN_RANGE_SCALPER"
    if sig is not None:
        assert isinstance(sig, SignalCandidate)
        assert sig.strategy_id == "ASIAN_RANGE_SCALPER"
        assert sig.risk_distance <= 1.35
        assert sig.risk_reward_ratio >= 1.4


def test_london_sweep_strategy(trending_up_df: pd.DataFrame, symbol_spec: SymbolSpec):
    enriched = SharedIndicatorEngine.compute_all(trending_up_df)
    strat = LondonSweepStrategy()
    sig = strat.evaluate(enriched, symbol_spec)

    assert strat.name == "LONDON_LIQUIDITY_SWEEP"
    if sig is not None:
        assert isinstance(sig, SignalCandidate)
        assert sig.strategy_id == "LONDON_LIQUIDITY_SWEEP"
        assert sig.risk_distance <= 2.05
        assert sig.risk_reward_ratio >= 2.0
