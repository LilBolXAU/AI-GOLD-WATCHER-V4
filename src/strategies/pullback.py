"""
Pullback Continuation Strategy Engine for AI GOLD WATCHER V4.
Enters high-probability continuation moves when price retraces to key dynamic support/resistance.
"""

from typing import Optional
import pandas as pd

from src.data.models import SymbolSpec
from src.strategies.base_strategy import BaseStrategy, OrderSide, SignalCandidate


class PullbackStrategy(BaseStrategy):
    """
    Independent Pullback Engine.
    Identifies healthy retracements to EMA 20/50 support/resistance within established trends.
    """

    def __init__(self, risk_reward_target: float = 1.50):
        super().__init__("PULLBACK_CONTINUATION")
        self.risk_reward_target = risk_reward_target

    def evaluate(
        self, df: pd.DataFrame, spec: SymbolSpec
    ) -> Optional[SignalCandidate]:
        if df.empty or len(df) < 60:
            return None

        bar = df.iloc[-1]
        prev_bar = df.iloc[-2]
        ts = df.index[-1]

        close = float(bar["close"])
        open_p = float(bar["open"])
        low = float(bar["low"])
        high = float(bar["high"])

        ema_20 = float(bar.get("ema_20", 0.0))
        ema_50 = float(bar.get("ema_50", 0.0))
        atr = float(bar.get("atr_14", 0.0))
        rsi = float(bar.get("rsi_14", 50.0))
        prev_rsi = float(prev_bar.get("rsi_14", 50.0))
        swing_low = float(bar.get("swing_low_5", low - 0.5))
        swing_high = float(bar.get("swing_high_5", high + 0.5))

        if atr <= 0.0:
            return None

        # 1. Bullish Pullback: Trend is Bullish (EMA 20 > EMA 50)
        # Price dipped to or near EMA 20/50 zone and rejected with a bullish closed candle
        if ema_20 > ema_50:
            tested_ema_zone = (low <= ema_20 * 1.002) and (close >= ema_20)
            bull_rejection = close > open_p
            rsi_hook_up = (rsi > prev_rsi) and (40.0 <= rsi <= 62.0)

            if tested_ema_zone and bull_rejection and rsi_hook_up:
                # Stop loss placed beyond recent structural swing low (Max $2.00 to guarantee <= 4% risk on 0.01 lot)
                sl_dist = max(close - swing_low, atr * 1.0)
                sl_dist = max(0.50, min(sl_dist, 2.00))  # Dynamic ATR swing distance
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
                        f"Bull trend (EMA20 > EMA50)",
                        f"Pullback into EMA20 ({ema_20:.2f}) rejected",
                        f"Bullish candle close ({close:.2f} > {open_p:.2f})",
                        f"RSI hooked upward from {prev_rsi:.1f} to {rsi:.1f}",
                    ],
                )

        # 2. Bearish Pullback: Trend is Bearish (EMA 20 < EMA 50)
        # Price retraced up to or near EMA 20/50 zone and rejected with a bearish closed candle
        if ema_20 < ema_50:
            tested_ema_zone = (high >= ema_20 * 0.998) and (close <= ema_20)
            bear_rejection = close < open_p
            rsi_hook_down = (rsi < prev_rsi) and (38.0 <= rsi <= 60.0)

            if tested_ema_zone and bear_rejection and rsi_hook_down:
                sl_dist = max(swing_high - close, atr * 1.0)
                sl_dist = max(0.50, min(sl_dist, 2.00))  # Dynamic ATR swing distance
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
                        f"Bear trend (EMA20 < EMA50)",
                        f"Retracement into EMA20 ({ema_20:.2f}) rejected",
                        f"Bearish candle close ({close:.2f} < {open_p:.2f})",
                        f"RSI hooked downward from {prev_rsi:.1f} to {rsi:.1f}",
                    ],
                )

        return None
