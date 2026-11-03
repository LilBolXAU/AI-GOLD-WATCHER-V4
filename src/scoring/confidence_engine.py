"""
Confidence Scoring Engine for AI GOLD WATCHER V4.
Transparent multi-factor scoring of signal quality.
"""

from typing import Dict, Optional
import pandas as pd

from src.data.models import Timeframe
from src.regime.regime_detector import MarketRegimeState, RegimeType
from src.strategies.base_strategy import SignalCandidate, OrderSide
from src.scoring.signal_quality import ScoredSignal


class ConfidenceEngine:
    """
    Evaluates signal candidates across 5 weighted structural dimensions (0 to 100).
    Threshold default is 70.0 points (A+ Setup Quality).
    """

    def __init__(self, threshold: float = 70.0, max_spread_pts: int = 35):
        self.threshold = threshold
        self.max_spread_pts = max_spread_pts

    def score(
        self,
        candidate: SignalCandidate,
        regime_state: MarketRegimeState,
        current_spread: int,
        mtf_data: Optional[Dict[Timeframe, pd.DataFrame]] = None,
    ) -> ScoredSignal:
        sub_scores = {}
        reasons = []

        # 1. Regime Alignment Score (0 to 25 pts)
        regime_score = 0.0
        if candidate.side == OrderSide.BUY and regime_state.regime == RegimeType.BULL_TRENDING:
            regime_score = 25.0 * regime_state.confidence
            reasons.append(f"Regime Bull alignment (+{regime_score:.1f} pts)")
        elif candidate.side == OrderSide.SELL and regime_state.regime == RegimeType.BEAR_TRENDING:
            regime_score = 25.0 * regime_state.confidence
            reasons.append(f"Regime Bear alignment (+{regime_score:.1f} pts)")
        elif regime_state.regime == RegimeType.MEAN_REVERTING_RANGING and candidate.strategy_id == "RANGE_REVERSAL":
            regime_score = 25.0 * regime_state.confidence
            reasons.append(f"Regime Range alignment (+{regime_score:.1f} pts)")
        elif regime_state.regime == RegimeType.HIGH_VOLATILITY and candidate.strategy_id == "VOLATILITY_BREAKOUT":
            regime_score = 15.0
            reasons.append(f"High-vol breakout alignment (+15.0 pts)")
        else:
            regime_score = 5.0
            reasons.append("Weak or neutral regime alignment (+5.0 pts)")
        sub_scores["regime_alignment"] = round(regime_score, 1)

        # 2. Strategy Raw Confidence & Momentum (0 to 25 pts)
        momentum_score = round(candidate.raw_confidence * 25.0, 1)
        sub_scores["strategy_momentum"] = momentum_score
        reasons.append(f"Strategy base conviction ({candidate.raw_confidence:.2f}) -> +{momentum_score:.1f} pts")

        # 3. Risk/Reward Ratio Quality (0 to 20 pts)
        rr = candidate.risk_reward_ratio
        if rr >= 2.5:
            rr_score = 20.0
        elif rr >= 2.0:
            rr_score = 17.0
        elif rr >= 1.5:
            rr_score = 13.0
        else:
            rr_score = 5.0
        sub_scores["risk_reward"] = rr_score
        reasons.append(f"Risk:Reward {rr:.2f}:1 (+{rr_score:.1f} pts)")

        # 4. Spread Condition (0 to 15 pts)
        if current_spread <= 18:
            spread_score = 15.0
            reasons.append(f"Tight spread ({current_spread} pts) -> +15.0 pts")
        elif current_spread <= 25:
            spread_score = 10.0
            reasons.append(f"Normal spread ({current_spread} pts) -> +10.0 pts")
        elif current_spread <= self.max_spread_pts:
            spread_score = 5.0
            reasons.append(f"Wide spread ({current_spread} pts) -> +5.0 pts")
        else:
            spread_score = 0.0
            reasons.append(f"Spread {current_spread} exceeds limit {self.max_spread_pts} -> 0 pts")
        sub_scores["spread_condition"] = spread_score

        # 5. Multi-Timeframe Alignment (0 to 15 pts)
        mtf_score = 10.0  # Default neutral score
        if mtf_data and Timeframe.M15 in mtf_data:
            m15_df = mtf_data[Timeframe.M15]
            if not m15_df.empty and "ema_20" in m15_df.columns and "ema_50" in m15_df.columns:
                m15_last = m15_df.iloc[-1]
                m15_bull = m15_last["ema_20"] > m15_last["ema_50"]
                m15_bear = m15_last["ema_20"] < m15_last["ema_50"]

                if (candidate.side == OrderSide.BUY and m15_bull) or (candidate.side == OrderSide.SELL and m15_bear):
                    mtf_score = 15.0
                    reasons.append("M15 higher timeframe trend concurs (+15.0 pts)")
                else:
                    mtf_score = 5.0
                    reasons.append("M15 higher timeframe trend conflicts (+5.0 pts)")
        sub_scores["multi_timeframe"] = mtf_score

        total_score = round(sum(sub_scores.values()), 1)
        passes = total_score >= self.threshold and spread_score > 0

        return ScoredSignal(
            candidate=candidate,
            total_score=total_score,
            sub_scores=sub_scores,
            reasons=reasons,
            passes_threshold=passes,
        )
