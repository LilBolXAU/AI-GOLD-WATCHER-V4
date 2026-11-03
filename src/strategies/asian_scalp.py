"""
Asian Range Scalper Strategy Engine for AI GOLD WATCHER V4.
Optimized for the Asian Session (07:00 - 13:30 VN / 00:00 - 06:30 UTC).
Captures mean-reverting swing trades between Bollinger Bands when Gold consolidates in a tight range.
"""

from typing import Optional
import pandas as pd

from src.data.models import SymbolSpec
from src.strategies.base_strategy import BaseStrategy, OrderSide, SignalCandidate


class AsianRangeScalper(BaseStrategy):
    """
    Asian Range Scalper Engine.
    Executes precision bounce scalps at upper/lower Bollinger Bands with strict R:R and tight stops.
    """

    def __init__(
        self,
        rsi_overbought: float = 62.0,
        rsi_oversold: float = 38.0,
        max_sl_usd: float = 1.30,      # Tight Asian stop ($1.00 - $1.30)
        target_rr: float = 1.5,        # 1:1.5 standard R:R
    ):
        super().__init__("ASIAN_RANGE_SCALPER")
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.max_sl_usd = max_sl_usd
        self.target_rr = target_rr

    def evaluate(
        self, df: pd.DataFrame, spec: SymbolSpec
    ) -> Optional[SignalCandidate]:
        if df.empty or len(df) < 30:
            return None

        bar = df.iloc[-1]
        prev = df.iloc[-2]
        ts = df.index[-1]

        close = float(bar["close"])
        high = float(bar["high"])
        low = float(bar["low"])
        open_price = float(bar["open"])

        bb_upper = float(bar.get("bb_upper", 0.0))
        bb_lower = float(bar.get("bb_lower", 0.0))
        bb_mid = float(bar.get("bb_middle", 0.0))
        rsi = float(bar.get("rsi_14", 50.0))
        prev_rsi = float(prev.get("rsi_14", 50.0))
        atr = float(bar.get("atr_14", 1.0))

        if bb_upper <= 0.0 or bb_lower <= 0.0 or atr <= 0.0:
            return None

        candle_range = max(0.01, high - low)

        # ---------------------------------------------------------------------
        # 1. Bullish Mean-Reversion Bounce (Bottom of Asian Range)
        # ---------------------------------------------------------------------
        # Condition: Low punctures below or touches lower Bollinger Band,
        # close recovers upward with a bullish rejection wick, RSI turns up from oversold.
        lower_wick = min(open_price, close) - low
        is_bull_rejection = (low <= bb_lower or prev.get("low", 0.0) <= bb_lower) and (lower_wick / candle_range >= 0.25)

        if is_bull_rejection and rsi <= self.rsi_oversold and rsi > prev_rsi:
            entry_rounded = round(close, spec.digits)
            sl_dist = round(max(0.50, min(self.max_sl_usd, (close - low) + 0.25)), spec.digits)
            sl_price = round(entry_rounded - sl_dist, spec.digits)
            tp_dist = round(sl_dist * self.target_rr, spec.digits)
            tp_price = round(entry_rounded + tp_dist, spec.digits)

            # Confidence higher when closer to extreme band
            confidence = min(0.92, 0.70 + (self.rsi_oversold - rsi) * 0.01 + (lower_wick / candle_range) * 0.1)

            return SignalCandidate(
                strategy_id=self.name,
                timestamp=ts,
                symbol=getattr(spec, "name", "XAUUSDm"),
                side=OrderSide.BUY,
                entry_price=entry_rounded,
                stop_loss=sl_price,
                take_profit=tp_price,
                raw_confidence=confidence,
                reasons=[
                    f"Asian lower Bollinger Band rejection (Low: {low:.2f} <= BB: {bb_lower:.2f})",
                    f"RSI oversold reversal ({rsi:.1f} > prev {prev_rsi:.1f})",
                    f"Tight scalp SL distance ${sl_dist:.2f} (Target TP: ${tp_dist:.2f})",
                ],
            )

        # ---------------------------------------------------------------------
        # 2. Bearish Mean-Reversion Bounce (Top of Asian Range)
        # ---------------------------------------------------------------------
        # Condition: High touches or pokes above upper Bollinger Band,
        # close drops back down with an upper rejection wick, RSI turns down from overbought.
        upper_wick = high - max(open_price, close)
        is_bear_rejection = (high >= bb_upper or prev.get("high", 0.0) >= bb_upper) and (upper_wick / candle_range >= 0.25)

        if is_bear_rejection and rsi >= self.rsi_overbought and rsi < prev_rsi:
            entry_rounded = round(close, spec.digits)
            sl_dist = round(max(0.50, min(self.max_sl_usd, (high - close) + 0.25)), spec.digits)
            sl_price = round(entry_rounded + sl_dist, spec.digits)
            tp_dist = round(sl_dist * self.target_rr, spec.digits)
            tp_price = round(entry_rounded - tp_dist, spec.digits)

            confidence = min(0.92, 0.70 + (rsi - self.rsi_overbought) * 0.01 + (upper_wick / candle_range) * 0.1)

            return SignalCandidate(
                strategy_id=self.name,
                timestamp=ts,
                symbol=getattr(spec, "name", "XAUUSDm"),
                side=OrderSide.SELL,
                entry_price=entry_rounded,
                stop_loss=sl_price,
                take_profit=tp_price,
                raw_confidence=confidence,
                reasons=[
                    f"Asian upper Bollinger Band rejection (High: {high:.2f} >= BB: {bb_upper:.2f})",
                    f"RSI overbought reversal ({rsi:.1f} < prev {prev_rsi:.1f})",
                    f"Tight scalp SL distance ${sl_dist:.2f} (Target TP: ${tp_dist:.2f})",
                ],
            )

        return None
