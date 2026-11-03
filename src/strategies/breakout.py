"""
Volatility Breakout Strategy Engine for AI GOLD WATCHER V4.
Captures explosive expansions from tight consolidation zones with false-breakout filters.
"""

from typing import Optional
import pandas as pd

from src.data.models import SymbolSpec
from src.strategies.base_strategy import BaseStrategy, OrderSide, SignalCandidate


class BreakoutStrategy(BaseStrategy):
    """
    Independent Breakout Engine.
    Emits signals when price closes outside Donchian channels on expanding volume.
    """

    def __init__(self, risk_reward_target: float = 2.0):
        super().__init__("VOLATILITY_BREAKOUT")
        self.risk_reward_target = risk_reward_target

    def evaluate(
        self, df: pd.DataFrame, spec: SymbolSpec
    ) -> Optional[SignalCandidate]:
        if df.empty or len(df) < 30:
            return None

        bar = df.iloc[-1]
        ts = df.index[-1]

        close = float(bar["close"])
        open_p = float(bar["open"])
        high = float(bar["high"])
        low = float(bar["low"])
        vol = float(bar["volume"])

        donchian_high = float(bar.get("donchian_high_20", high + 1.0))
        donchian_low = float(bar.get("donchian_low_20", low - 1.0))
        bb_width = float(bar.get("bb_width", 0.05))
        bb_mid = float(bar.get("bb_middle", close))
        atr = float(bar.get("atr_14", 0.0))
        rsi = float(bar.get("rsi_14", 50.0))
        adx = float(bar.get("adx_14", 20.0))
        er = float(bar.get("efficiency_ratio_10", 0.35))

        if atr <= 0.0:
            return None

        candle_range = high - low
        if candle_range <= 0.0:
            return None

        # 1. Bullish Breakout
        # Candle closes above the 20-bar high, closing in the top 30% of its candle range
        # Gated by RSI <= 70.0 and ADX >= 24.0 to eliminate false-breakout whipsaws in chop
        closed_above_donchian = close > donchian_high
        strong_close_bull = (close - low) / candle_range >= 0.70
        has_momentum_thrust = (adx >= 24.0) and (er >= 0.35)

        if closed_above_donchian and strong_close_bull and (50.0 <= rsi <= 70.0) and has_momentum_thrust:
            sl_dist = max(close - bb_mid, atr * 1.2)
            sl_dist = max(0.50, min(sl_dist, 2.00))  # Dynamic ATR breakout distance
            entry_rounded = round(close, spec.digits)
            sl_price = round(entry_rounded - sl_dist, spec.digits)
            tp_price = round(entry_rounded + (sl_dist * self.risk_reward_target), spec.digits)

            return SignalCandidate(
                strategy_id=self.name,
                timestamp=ts,
                symbol=spec.name,
                side=OrderSide.BUY,
                entry_price=entry_rounded,
                stop_loss=sl_price,
                take_profit=tp_price,
                raw_confidence=0.75,
                reasons=[
                    f"Close ({close:.2f}) broke above 20-bar Donchian High ({donchian_high:.2f})",
                    f"Strong candle close in top 30% of bar range",
                    f"ADX={adx:.1f} >= 24 & ER={er:.2f} confirm genuine breakout thrust",
                    f"Consolidation expansion (BB Width={bb_width:.4f})",
                ],
            )

        # 2. Bearish Breakout
        # Candle closes below the 20-bar low, closing in the bottom 30% of its candle range
        # Gated by RSI >= 30.0 and ADX >= 24.0 to eliminate false-breakout whipsaws in chop
        closed_below_donchian = close < donchian_low
        strong_close_bear = (high - close) / candle_range >= 0.70

        if closed_below_donchian and strong_close_bear and (30.0 <= rsi <= 50.0) and has_momentum_thrust:
            sl_dist = max(bb_mid - close, atr * 1.2)
            sl_dist = max(0.50, min(sl_dist, 2.00))  # Dynamic ATR breakout distance
            entry_rounded = round(close, spec.digits)
            sl_price = round(entry_rounded + sl_dist, spec.digits)
            tp_price = round(entry_rounded - (sl_dist * self.risk_reward_target), spec.digits)

            return SignalCandidate(
                strategy_id=self.name,
                timestamp=ts,
                symbol=spec.name,
                side=OrderSide.SELL,
                entry_price=entry_rounded,
                stop_loss=sl_price,
                take_profit=tp_price,
                raw_confidence=0.75,
                reasons=[
                    f"Close ({close:.2f}) broke below 20-bar Donchian Low ({donchian_low:.2f})",
                    f"Strong candle close in bottom 30% of bar range",
                    f"ADX={adx:.1f} >= 24 & ER={er:.2f} confirm genuine breakout thrust",
                    f"Consolidation expansion (BB Width={bb_width:.4f})",
                ],
            )

        return None
