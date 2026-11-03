"""
Base Strategy Interface and Signal Candidate Definitions for AI GOLD WATCHER V4.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import pandas as pd

from src.data.models import SymbolSpec


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class SignalCandidate:
    """
    Standardized trading signal emitted independently by each strategy engine.
    Pure signal candidate: DOES NOT place orders or execute trades.
    """
    strategy_id: str
    timestamp: datetime
    symbol: str
    side: OrderSide
    entry_price: float
    stop_loss: float
    take_profit: float
    raw_confidence: float  # [0.0, 1.0]
    reasons: List[str] = field(default_factory=list)

    @property
    def risk_distance(self) -> float:
        return abs(self.entry_price - self.stop_loss)

    @property
    def reward_distance(self) -> float:
        return abs(self.take_profit - self.entry_price)

    @property
    def risk_reward_ratio(self) -> float:
        if self.risk_distance == 0:
            return 0.0
        return round(self.reward_distance / self.risk_distance, 2)


class BaseStrategy(ABC):
    """Abstract interface for all 4 decoupled strategy engines."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def evaluate(
        self, df: pd.DataFrame, spec: SymbolSpec
    ) -> Optional[SignalCandidate]:
        """
        Evaluate closed-bar DataFrame and return a SignalCandidate if entry criteria match,
        or None if conditions are unsuitable.
        """
        pass
