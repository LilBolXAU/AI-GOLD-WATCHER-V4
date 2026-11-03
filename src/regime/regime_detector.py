"""
Market Regime Detector for AI GOLD WATCHER V4.
Classifies market states with Wilder ADX, ATR z-score, and a 3-bar hysteresis filter.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import pandas as pd

from src.regime.regime_features import extract_regime_features, RegimeFeatures


class RegimeType(str, Enum):
    BULL_TRENDING = "BULL_TRENDING"
    BEAR_TRENDING = "BEAR_TRENDING"
    MEAN_REVERTING_RANGING = "MEAN_REVERTING_RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    UNSTABLE = "UNSTABLE"


@dataclass(frozen=True)
class MarketRegimeState:
    """Confirmed regime state emitted after hysteresis filter evaluation."""
    timestamp: datetime
    regime: RegimeType
    confidence: float
    raw_candidate: RegimeType
    reasons: List[str] = field(default_factory=list)
    bars_confirmed: int = 1


class MarketRegimeDetector:
    """
    Robust market regime classifier.
    Uses hysteresis to prevent whipsaws, with an immediate override on volatility shocks.
    """

    def __init__(
        self,
        adx_trend_threshold: float = 25.0,
        adx_range_threshold: float = 20.0,
        volatility_z_threshold: float = 2.0,
        hysteresis_bars: int = 3,
    ):
        self.adx_trend_threshold = adx_trend_threshold
        self.adx_range_threshold = adx_range_threshold
        self.volatility_z_threshold = volatility_z_threshold
        self.hysteresis_bars = hysteresis_bars

        # State tracking
        self.current_regime: RegimeType = RegimeType.UNSTABLE
        self.candidate_regime: RegimeType = RegimeType.UNSTABLE
        self.consecutive_candidate_bars: int = 0

    def reset(self) -> None:
        self.current_regime = RegimeType.UNSTABLE
        self.candidate_regime = RegimeType.UNSTABLE
        self.consecutive_candidate_bars = 0

    def classify_raw_candidate(self, feats: RegimeFeatures) -> tuple[RegimeType, float, List[str]]:
        """Determine instantaneous regime candidate without hysteresis."""
        reasons = []

        # 1. Volatility Shock Check (Outranks trend/range models)
        if feats.atr_zscore >= self.volatility_z_threshold:
            reasons.append(f"ATR z-score ({feats.atr_zscore:.2f}) >= threshold ({self.volatility_z_threshold})")
            return RegimeType.HIGH_VOLATILITY, 0.90, reasons

        # 2. Bull Trend Check
        is_bull_dmi = (feats.adx >= self.adx_trend_threshold) and (feats.plus_di > feats.minus_di)
        if is_bull_dmi and feats.ema_bull_aligned:
            reasons.append(f"ADX ({feats.adx:.1f}) >= {self.adx_trend_threshold} with +DI > -DI and Bull EMA alignment")
            conf = min(0.95, 0.65 + (feats.efficiency_ratio * 0.3))
            return RegimeType.BULL_TRENDING, conf, reasons

        # 3. Bear Trend Check
        is_bear_dmi = (feats.adx >= self.adx_trend_threshold) and (feats.minus_di > feats.plus_di)
        if is_bear_dmi and feats.ema_bear_aligned:
            reasons.append(f"ADX ({feats.adx:.1f}) >= {self.adx_trend_threshold} with -DI > +DI and Bear EMA alignment")
            conf = min(0.95, 0.65 + (feats.efficiency_ratio * 0.3))
            return RegimeType.BEAR_TRENDING, conf, reasons

        # 4. Mean-Reverting Ranging Check
        if feats.adx < self.adx_range_threshold and feats.bb_width < 0.03:
            reasons.append(f"ADX ({feats.adx:.1f}) < {self.adx_range_threshold} and tight BB width ({feats.bb_width:.4f})")
            conf = min(0.90, 0.60 + ((self.adx_range_threshold - feats.adx) / self.adx_range_threshold) * 0.3)
            return RegimeType.MEAN_REVERTING_RANGING, conf, reasons

        # 5. Abstain / Unstable
        reasons.append("Conflicting directional and volatility indicators; abstaining.")
        return RegimeType.UNSTABLE, 0.50, reasons

    def update(self, df: pd.DataFrame) -> MarketRegimeState:
        """
        Evaluate enriched DataFrame up to the latest closed bar and apply hysteresis.
        """
        feats = extract_regime_features(df)
        last_time = df.index[-1] if not df.empty else datetime.utcnow()

        if feats is None:
            return MarketRegimeState(
                timestamp=last_time,
                regime=RegimeType.UNSTABLE,
                confidence=0.0,
                raw_candidate=RegimeType.UNSTABLE,
                reasons=["Insufficient historical bars for regime classification"],
                bars_confirmed=0,
            )

        raw_cand, raw_conf, reasons = self.classify_raw_candidate(feats)

        # Immediate override for high-volatility shock (zero hysteresis delay for capital protection)
        if raw_cand == RegimeType.HIGH_VOLATILITY:
            self.current_regime = RegimeType.HIGH_VOLATILITY
            self.candidate_regime = RegimeType.HIGH_VOLATILITY
            self.consecutive_candidate_bars = self.hysteresis_bars
            return MarketRegimeState(
                timestamp=last_time,
                regime=RegimeType.HIGH_VOLATILITY,
                confidence=raw_conf,
                raw_candidate=raw_cand,
                reasons=reasons + ["IMMEDIATE OVERRIDE: Volatility shock bypasses hysteresis"],
                bars_confirmed=self.consecutive_candidate_bars,
            )

        # Hysteresis Filter Logic
        if raw_cand == self.current_regime:
            # Candidate matches confirmed regime; reset switch counter
            self.consecutive_candidate_bars = 0
            self.candidate_regime = raw_cand
        else:
            if raw_cand == self.candidate_regime:
                self.consecutive_candidate_bars += 1
            else:
                self.candidate_regime = raw_cand
                self.consecutive_candidate_bars = 1

            # Switch confirmed regime if hysteresis threshold met
            if self.consecutive_candidate_bars >= self.hysteresis_bars:
                self.current_regime = raw_cand
                reasons.append(f"Regime transition confirmed after {self.hysteresis_bars} consecutive bars.")

        return MarketRegimeState(
            timestamp=last_time,
            regime=self.current_regime,
            confidence=raw_conf,
            raw_candidate=raw_cand,
            reasons=reasons,
            bars_confirmed=self.consecutive_candidate_bars,
        )
