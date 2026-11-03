"""
Adaptive Strategy Selector for AI GOLD WATCHER V4.
Routes signals based on regime eligibility, filters conflicting candidates, and enforces mutual exclusivity.
"""

from typing import Dict, List, Optional
import pandas as pd

from src.data.models import SymbolSpec
from src.regime.regime_detector import MarketRegimeState, RegimeType
from src.strategies.base_strategy import BaseStrategy, OrderSide, SignalCandidate
from src.strategies.trend_following import TrendFollowingStrategy
from src.strategies.pullback import PullbackStrategy
from src.strategies.breakout import BreakoutStrategy
from src.strategies.range_reversal import RangeReversalStrategy
from src.strategies.asian_scalp import AsianRangeScalper
from src.strategies.london_sweep import LondonSweepStrategy
from src.strategies.smc_structure import SmartMoneyStructureStrategy
from src.selector.strategy_eligibility import get_eligible_strategies
from src.regime.macro_trend import MacroTrendBias
from src.regime.session_router import SessionRouter
from src.regime.exhaustion_filter import ExhaustionFilter
from datetime import datetime
import logging

logger = logging.getLogger("v4_trading.selector")


class AdaptiveStrategySelector:
    """
    Selects and prioritizes the best signal candidate among eligible strategies.
    Ensures zero conflicting trades, regime alignment, H1 multi-timeframe concordance,
    and market session liquidity optimization.
    """

    def __init__(self, strategies: Optional[Dict[str, BaseStrategy]] = None):
        if strategies is None:
            self.strategies: Dict[str, BaseStrategy] = {
                "SMC_STRUCTURE_PRICE_ACTION": SmartMoneyStructureStrategy(),
                "TREND_FOLLOWING": TrendFollowingStrategy(),
                "PULLBACK_CONTINUATION": PullbackStrategy(),
                "VOLATILITY_BREAKOUT": BreakoutStrategy(),
                "RANGE_REVERSAL": RangeReversalStrategy(),
                "ASIAN_RANGE_SCALPER": AsianRangeScalper(),
                "LONDON_LIQUIDITY_SWEEP": LondonSweepStrategy(),
            }
        else:
            self.strategies = strategies

    def evaluate(
        self,
        df: pd.DataFrame,
        regime_state: MarketRegimeState,
        spec: SymbolSpec,
        macro_bias: Optional[MacroTrendBias] = None,
        current_time: Optional[datetime] = None,
    ) -> Optional[SignalCandidate]:
        """
        Evaluate eligible strategies under current market regime, H1 macro bias, and active trading session.
        Returns highest-confidence SignalCandidate or None (NO_TRADE).
        """
        if regime_state.regime == RegimeType.UNSTABLE:
            # Abstain from trading in unstable conditions
            return None

        # Resolve current time from DataFrame index if not supplied
        if current_time is None and not df.empty:
            last_ts = df.index[-1]
            if isinstance(last_ts, (datetime, pd.Timestamp)):
                current_time = last_ts.to_pydatetime() if hasattr(last_ts, "to_pydatetime") else last_ts

        session_profile = SessionRouter.get_profile(current_time)

        eligible_ids = get_eligible_strategies(regime_state.regime)
        if not eligible_ids:
            return None

        candidates: List[SignalCandidate] = []

        for strat_id in eligible_ids:
            strat = self.strategies.get(strat_id)
            if strat is None:
                continue

            signal = strat.evaluate(df, spec)
            if signal is None:
                continue

            # 1. Directional verification against regime
            if regime_state.regime == RegimeType.BULL_TRENDING and signal.side != OrderSide.BUY:
                continue  # Discard short signal during bull trend
            if regime_state.regime == RegimeType.BEAR_TRENDING and signal.side != OrderSide.SELL:
                continue  # Discard long signal during bear trend

            # 2. Multi-Timeframe Directional Verification against H1 Macro Trend
            # Trend-continuation strategies MUST align strictly with the higher-timeframe H1 tide.
            # Structural reversals (CHoCH, Asian Scalper, Range Reversal) are permitted to trade early turnarounds.
            is_trend_following = signal.strategy_id in [
                "TREND_FOLLOWING",
                "PULLBACK_CONTINUATION",
                "VOLATILITY_BREAKOUT",
            ]
            if is_trend_following:
                if macro_bias == MacroTrendBias.BULLISH and signal.side == OrderSide.SELL:
                    continue  # Never sell into an H1 Bullish Tide
                if macro_bias == MacroTrendBias.BEARISH and signal.side == OrderSide.BUY:
                    continue  # Never buy into an H1 Bearish Tide

            # 3. Market Exhaustion Filter (Chống Bán Đuổi Đáy / Mua Đuổi Đỉnh)
            is_exhausted, exhaust_reason = ExhaustionFilter.is_exhausted(
                df, signal.side, signal.strategy_id
            )
            if is_exhausted:
                logger.info(
                    f"Exhaustion Filter VETO [{signal.strategy_id} {signal.side.value} @ {signal.entry_price}]: {exhaust_reason}"
                )
                continue

            candidates.append(signal)

        if not candidates:
            return None

        # Conflict Resolution: If both BUY and SELL candidates coexist, reject all (ambiguous edge)
        sides = {c.side for c in candidates}
        if len(sides) > 1:
            return None

        # Select candidate with highest session-adjusted confidence
        def score_candidate(cand: SignalCandidate) -> float:
            session_bonus = SessionRouter.get_strategy_session_bonus(cand.strategy_id, current_time)
            return cand.raw_confidence + (session_bonus * 0.05)

        best_candidate = max(candidates, key=score_candidate)
        return best_candidate
