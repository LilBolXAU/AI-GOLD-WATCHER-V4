"""
Trend Following Strategy Engine for AI GOLD WATCHER V4.
Captures persistent directional moves using EMA multi-period alignment and ADX confirmation.
"""

from typing import Optional
import pandas as pd

from src.data.models import SymbolSpec
from src.strategies.base_strategy import BaseStrategy, OrderSide, SignalCandidate


class TrendFollowingStrategy(BaseStrategy):
    """
    Independent Trend Following Engine.
    Emits signals strictly when EMA 20/50/200 align, ADX > 25, and momentum is positive.
    """

    def __init__(
        self,
        adx_threshold: float = 25.0,
        atr_multiplier: float = 1.5,
        risk_reward_target: float = 2.0,
    ):
        super().__init__("TREND_FOLLOWING")
        self.adx_threshold = adx_threshold
        self.atr_multiplier = atr_multiplier
        self.risk_reward_target = risk_reward_target

    def evaluate(
        self, df: pd.DataFrame, spec: SymbolSpec
    ) -> Optional[SignalCandidate]:
        if df.empty or len(df) < 200:
            return None

        bar = df.iloc[-1]
        ts = df.index[-1]
        close = float(bar["close"])
        atr = float(bar.get("atr_14", 0.0))
        adx = float(bar.get("adx_14", 0.0))
        rsi = float(bar.get("rsi_14", 50.0))
        slope = float(bar.get("ema_20_slope", 0.0))

        if atr <= 0.0 or adx < self.adx_threshold:
            return None

        # Dynamic Stop distance based on market ATR volatility (Max $2.00 to guarantee <= 4% risk on 0.01 lot)
        sl_dist = round(atr * self.atr_multiplier, spec.digits)
        sl_dist = max(0.50, min(sl_dist, 2.00))

        # 1. Bullish Trend Setup
        bull_aligned = bool(bar.get("ema_aligned_bull", False))
        if bull_aligned and slope > 0.05 and 48.0 <= rsi <= 65.0:
            entry_rounded = round(close, spec.digits)
            sl_price = round(entry_rounded - sl_dist, spec.digits)
            tp_price = round(entry_rounded + (sl_dist * self.risk_reward_target), spec.digits)
            confidence = min(0.95, 0.65 + (adx / 100.0) * 0.2 + (slope * 0.1))

            return SignalCandidate(
                strategy_id=self.name,
                timestamp=ts,
                symbol=spec.name,
                side=OrderSide.BUY,
                entry_price=entry_rounded,
                stop_loss=sl_price,
                take_profit=tp_price,
                raw_confidence=confidence,
                reasons=[
                    f"Bullish EMA alignment (20>50>200)",
                    f"ADX={adx:.1f} >= {self.adx_threshold}",
                    f"Positive EMA20 slope={slope:.2f}",
                    f"RSI={rsi:.1f} in safe momentum zone [48, 65]",
                ],
            )

        # 2. Bearish Trend Setup
        bear_aligned = bool(bar.get("ema_aligned_bear", False))
        if bear_aligned and slope < -0.05 and 35.0 <= rsi <= 52.0:
            entry_rounded = round(close, spec.digits)
            sl_price = round(entry_rounded + sl_dist, spec.digits)
            tp_price = round(entry_rounded - (sl_dist * self.risk_reward_target), spec.digits)
            confidence = min(0.95, 0.65 + (adx / 100.0) * 0.2 + (abs(slope) * 0.1))

            return SignalCandidate(
                strategy_id=self.name,
                timestamp=ts,
                symbol=spec.name,
                side=OrderSide.SELL,
                entry_price=entry_rounded,
                stop_loss=sl_price,
                take_profit=tp_price,
                raw_confidence=confidence,
                reasons=[
                    f"Bearish EMA alignment (20<50<200)",
                    f"ADX={adx:.1f} >= {self.adx_threshold}",
                    f"Negative EMA20 slope={slope:.2f}",
                    f"RSI={rsi:.1f} in safe momentum zone [35, 52]",
                ],
            )

        return None
