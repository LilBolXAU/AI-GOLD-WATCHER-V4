"""
Strategy eligibility rules based on market regime in AI GOLD WATCHER V4.
"""

from typing import List
from src.regime.regime_detector import RegimeType


def get_eligible_strategies(regime: RegimeType) -> List[str]:
    """
    Returns the list of strategy IDs authorized to operate under the given regime.
    """
    if regime == RegimeType.BULL_TRENDING:
        return ["SMC_STRUCTURE_PRICE_ACTION", "TREND_FOLLOWING", "PULLBACK_CONTINUATION", "VOLATILITY_BREAKOUT", "LONDON_LIQUIDITY_SWEEP"]

    if regime == RegimeType.BEAR_TRENDING:
        return ["SMC_STRUCTURE_PRICE_ACTION", "TREND_FOLLOWING", "PULLBACK_CONTINUATION", "VOLATILITY_BREAKOUT", "LONDON_LIQUIDITY_SWEEP"]

    if regime == RegimeType.MEAN_REVERTING_RANGING:
        return ["SMC_STRUCTURE_PRICE_ACTION", "RANGE_REVERSAL", "ASIAN_RANGE_SCALPER"]

    if regime == RegimeType.HIGH_VOLATILITY:
        return ["SMC_STRUCTURE_PRICE_ACTION", "VOLATILITY_BREAKOUT", "LONDON_LIQUIDITY_SWEEP"]

    if regime == RegimeType.UNSTABLE:
        # Strict risk-off: zero strategy candidates permitted
        return []

    return []
