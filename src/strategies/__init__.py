"""Strategies package for AI GOLD WATCHER V4."""
from src.strategies.base_strategy import BaseStrategy, OrderSide, SignalCandidate
from src.strategies.trend_following import TrendFollowingStrategy
from src.strategies.pullback import PullbackStrategy
from src.strategies.breakout import BreakoutStrategy
from src.strategies.range_reversal import RangeReversalStrategy

__all__ = [
    "BaseStrategy",
    "OrderSide",
    "SignalCandidate",
    "TrendFollowingStrategy",
    "PullbackStrategy",
    "BreakoutStrategy",
    "RangeReversalStrategy",
]
