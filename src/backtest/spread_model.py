"""
Spread models for event-driven backtesting in AI GOLD WATCHER V4.
"""

from typing import Protocol


class SpreadModel(Protocol):
    def get_spread_points(self, bar_index: int, current_atr: float) -> int:
        ...


class ConstantSpreadModel:
    """Fixed spread simulation."""
    def __init__(self, spread_points: int = 18):
        self.spread_points = spread_points

    def get_spread_points(self, bar_index: int, current_atr: float) -> int:
        return self.spread_points


class DynamicSpreadModel:
    """Volatility-scaled floating spread model (models Exness Gold dynamics)."""
    def __init__(self, base_spread: int = 18, max_spread: int = 60):
        self.base_spread = base_spread
        self.max_spread = max_spread

    def get_spread_points(self, bar_index: int, current_atr: float) -> int:
        if current_atr <= 0:
            return self.base_spread
        # Higher ATR expands the floating spread
        vol_factor = max(1.0, current_atr / 1.5)
        spread = int(round(self.base_spread * vol_factor))
        return min(spread, self.max_spread)
