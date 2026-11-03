"""
Range Reversal Strategy Engine for AI GOLD WATCHER V4.
Fades Bollinger Band extremes confirmed by RSI exhaustion in non-trending regimes.
"""

from typing import Optional
import pandas as pd

from src.data.models import SymbolSpec
from src.strategies.base_strategy import BaseStrategy, OrderSide, SignalCandidate


class RangeReversalStrategy(BaseStrategy):
    """
    Independent Range Reversal Engine.
    Fades outer Bollinger Bands in low-ADX, mean-reverting market conditions.
    """

    def __init__(self, rsi_oversold: float = 32.0, rsi_overbought: float = 68.0):
        super().__init__("RANGE_REVERSAL")
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def evaluate(
        self, df: pd.DataFrame, spec: SymbolSpec
    ) -> Optional[SignalCandidate]:
        if df.empty or len(df) < 30:
            return None

        bar = df.iloc[-1]
        ts = df.index[-1]

        close = float(bar["close"])
        open_p = float(bar["open"])
        low = float(bar["low"])
        high = float(bar["high"])

        bb_upper = float(bar.get("bb_upper", close + 5.0))
        bb_lower = float(bar.get("bb_lower", close - 5.0))
        bb_mid = float(bar.get("bb_middle", close))
        rsi = float(bar.get("rsi_14", 50.0))
        adx = float(bar.get("adx_14", 30.0))
        atr = float(bar.get("atr_14", 0.0))

        if atr <= 0.0 or adx >= 22.0:
            # Range reversal is disqualified if a strong trend is emerging
            return None

        # 1. Bullish Mean Reversion at Lower Band
        # Low pierced or tagged lower band, RSI is oversold, candle closed positive
        tested_lower_bb = low <= bb_lower * 1.0005
        bull_reversal_candle = close > open_p

        if tested_lower_bb and (rsi <= self.rsi_oversold) and bull_reversal_candle:
            sl_dist = max(close - (low - 0.20), atr * 1.0)
            sl_dist = max(0.50, min(sl_dist, 2.00))  # Dynamic ATR range distance
            entry_rounded = round(close, spec.digits)
            sl_price = round(entry_rounded - sl_dist, spec.digits)
            tp_price = round(entry_rounded + (sl_dist * 1.5), spec.digits)

            return SignalCandidate(
                strategy_id=self.name,
                timestamp=ts,
                symbol=spec.name,
                side=OrderSide.BUY,
                entry_price=entry_rounded,
                stop_loss=sl_price,
                take_profit=tp_price,
                raw_confidence=0.70,
                reasons=[
                    f"Low ({low:.2f}) touched lower Bollinger Band ({bb_lower:.2f})",
                    f"RSI={rsi:.1f} <= oversold threshold ({self.rsi_oversold})",
                    f"Bullish reversal candle closed green ({close:.2f} > {open_p:.2f})",
                    f"Low ADX={adx:.1f} confirms non-trending ranging conditions",
                ],
            )

        # 2. Bearish Mean Reversion at Upper Band
        # High pierced or tagged upper band, RSI is overbought, candle closed negative
        tested_upper_bb = high >= bb_upper * 0.9995
        bear_reversal_candle = close < open_p

        if tested_upper_bb and (rsi >= self.rsi_overbought) and bear_reversal_candle:
            sl_dist = max((high + 0.20) - close, atr * 1.0)
            sl_dist = max(0.50, min(sl_dist, 2.00))  # Dynamic ATR range distance
            entry_rounded = round(close, spec.digits)
            sl_price = round(entry_rounded + sl_dist, spec.digits)
            tp_price = round(entry_rounded - (sl_dist * 1.5), spec.digits)

            return SignalCandidate(
                strategy_id=self.name,
                timestamp=ts,
                symbol=spec.name,
                side=OrderSide.SELL,
                entry_price=entry_rounded,
                stop_loss=sl_price,
                take_profit=tp_price,
                raw_confidence=0.70,
                reasons=[
                    f"High ({high:.2f}) touched upper Bollinger Band ({bb_upper:.2f})",
                    f"RSI={rsi:.1f} >= overbought threshold ({self.rsi_overbought})",
                    f"Bearish reversal candle closed red ({close:.2f} < {open_p:.2f})",
                    f"Low ADX={adx:.1f} confirms non-trending ranging conditions",
                ],
            )

        return None
