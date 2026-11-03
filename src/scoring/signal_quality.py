"""
Signal Quality and Scoring Models for AI GOLD WATCHER V4.
"""

from dataclasses import dataclass, field
from typing import Dict, List
from src.strategies.base_strategy import SignalCandidate


@dataclass(frozen=True)
class ScoredSignal:
    """
    Evaluated signal candidate with multi-factor confidence scoring.
    Note: Score represents structural concordance, NOT statistical win probability.
    """
    candidate: SignalCandidate
    total_score: float  # [0.0, 100.0]
    sub_scores: Dict[str, float] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    passes_threshold: bool = False

    @property
    def confidence_score(self) -> float:
        return self.total_score

    @property
    def strategy_id(self) -> str:
        return self.candidate.strategy_id

    @property
    def side(self):
        return self.candidate.side

    @property
    def entry_price(self) -> float:
        return self.candidate.entry_price

    @property
    def stop_loss(self) -> float:
        return self.candidate.stop_loss

    @property
    def take_profit(self) -> float:
        return self.candidate.take_profit
