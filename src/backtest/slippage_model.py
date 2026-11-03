"""
Slippage models for event-driven backtesting in AI GOLD WATCHER V4.
"""

from typing import Protocol
import numpy as np


class SlippageModel(Protocol):
    def get_slippage_points(self, bar_index: int, current_atr: float) -> int:
        ...


class FixedSlippageModel:
    def __init__(self, slippage_points: int = 1):
        self.slippage_points = slippage_points

    def get_slippage_points(self, bar_index: int, current_atr: float) -> int:
        return self.slippage_points


class RandomSlippageModel:
    """Simulates realistic execution slippage with bounded half-normal distribution."""
    def __init__(self, mean_points: float = 1.0, max_points: int = 5, seed: int = 42):
        self.mean_points = mean_points
        self.max_points = max_points
        self.rng = np.random.RandomState(seed)

    def get_slippage_points(self, bar_index: int, current_atr: float) -> int:
        slip = int(abs(self.rng.normal(self.mean_points, 0.5)))
        return min(slip, self.max_points)
