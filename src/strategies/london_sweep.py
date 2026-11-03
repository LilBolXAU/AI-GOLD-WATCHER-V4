"""
London Liquidity Sweep Strategy Engine for AI GOLD WATCHER V4.
Optimized for London & New York session opens (14:00 - 18:30 VN & 19:30 - 23:30 VN).
Captures institutional false breakout traps (Judas Swings) where price punctures the Asian range
high/low to harvest liquidity before violently reversing.
"""

from datetime import time, timezone
from typing import Optional
import pandas as pd

from src.data.models import SymbolSpec
from src.strategies.base_strategy import BaseStrategy, OrderSide, SignalCandidate


class LondonSweepStrategy(BaseStrategy):
    """
    London & NY Liquidity Sweep (SMC Judas Swing) Engine.
    Executes high R:R counter-reversal orders when key session highs/lows are swept and rejected.
    """

    def __init__(
        self,
        min_wick_ratio: float = 0.35,      # Rejection wick must be at least 35% of total bar
        risk_reward_target: float = 2.2,   # High R:R target (1:2.2)
        max_sl_usd: float = 2.00,          # Strict $2.00 cap for micro-risk budget
    ):
        super().__init__("LONDON_LIQUIDITY_SWEEP")
        self.min_wick_ratio = min_wick_ratio
        self.risk_reward_target = risk_reward_target
        self.max_sl_usd = max_sl_usd

    def evaluate(
        self, df: pd.DataFrame, spec: SymbolSpec
    ) -> Optional[SignalCandidate]:
        if df.empty or len(df) < 40:
            return None

        bar = df.iloc[-1]
        ts = df.index[-1]

        close = float(bar["close"])
        high = float(bar["high"])
        low = float(bar["low"])
        open_price = float(bar["open"])
        rsi = float(bar.get("rsi_14", 50.0))
        atr = float(bar.get("atr_14", 1.0))

        if atr <= 0.0:
            return None

        candle_range = max(0.05, high - low)

        # ---------------------------------------------------------------------
        # Determine Reference Liquidity Pool (Asian High / Low)
        # ---------------------------------------------------------------------
        # Slice prior bars excluding the active bar
        prior_df = df.iloc[:-1]

        # Attempt to filter bars in today's Asian window (00:00 - 06:30 UTC)
        try:
            if hasattr(prior_df.index, "tz") and prior_df.index.tz is not None:
                utc_idx = prior_df.index.tz_convert(timezone.utc)
            else:
                utc_idx = prior_df.index

            asian_mask = [
                time(0, 0) <= t.time() < time(6, 30) if hasattr(t, "time") else False
                for t in utc_idx
            ]
            asian_bars = prior_df[asian_mask]
            if len(asian_bars) >= 12:
                asian_high = float(asian_bars["high"].max())
                asian_low = float(asian_bars["low"].min())
            else:
                # Fallback to rolling 30-bar swing high/low
                asian_high = float(prior_df["high"].tail(30).max())
                asian_low = float(prior_df["low"].tail(30).min())
        except Exception:
            asian_high = float(prior_df["high"].tail(30).max())
            asian_low = float(prior_df["low"].tail(30).min())

        # ---------------------------------------------------------------------
        # 1. Bearish Liquidity Sweep (Quét Đỉnh Bẫy Mua — Fakeout High)
        # ---------------------------------------------------------------------
        # Price spikes above Asian High, but closes back BELOW it with an upper wick
        upper_wick = high - max(open_price, close)
        is_bear_sweep = (high > asian_high) and (close < asian_high) and (upper_wick / candle_range >= self.min_wick_ratio)

        if is_bear_sweep and rsi >= 50.0:
            entry_rounded = round(close, spec.digits)
            raw_sl_dist = (high - close) + 0.20
            sl_dist = round(max(0.60, min(self.max_sl_usd, raw_sl_dist)), spec.digits)
            sl_price = round(entry_rounded + sl_dist, spec.digits)
            tp_dist = round(sl_dist * self.risk_reward_target, spec.digits)
            tp_price = round(entry_rounded - tp_dist, spec.digits)

            confidence = min(0.95, 0.72 + (upper_wick / candle_range) * 0.15 + (rsi / 100.0) * 0.05)

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
                    f"Bearish liquidity sweep above Asian High ({high:.2f} > {asian_high:.2f})",
                    f"Upper rejection wick {upper_wick / candle_range * 100:.0f}% of bar",
                    f"Institutional trap reversal target R:R 1:{self.risk_reward_target:.1f}",
                ],
            )

        # ---------------------------------------------------------------------
        # 2. Bullish Liquidity Sweep (Quét Đáy Bẫy Bán — Fakeout Low)
        # ---------------------------------------------------------------------
        # Price plunges below Asian Low, but closes back ABOVE it with a lower wick
        lower_wick = min(open_price, close) - low
        is_bull_sweep = (low < asian_low) and (close > asian_low) and (lower_wick / candle_range >= self.min_wick_ratio)

        if is_bull_sweep and rsi <= 50.0:
            entry_rounded = round(close, spec.digits)
            raw_sl_dist = (close - low) + 0.20
            sl_dist = round(max(0.60, min(self.max_sl_usd, raw_sl_dist)), spec.digits)
            sl_price = round(entry_rounded - sl_dist, spec.digits)
            tp_dist = round(sl_dist * self.risk_reward_target, spec.digits)
            tp_price = round(entry_rounded + tp_dist, spec.digits)

            confidence = min(0.95, 0.72 + (lower_wick / candle_range) * 0.15 + ((100.0 - rsi) / 100.0) * 0.05)

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
                    f"Bullish liquidity sweep below Asian Low ({low:.2f} < {asian_low:.2f})",
                    f"Lower rejection wick {lower_wick / candle_range * 100:.0f}% of bar",
                    f"Institutional trap reversal target R:R 1:{self.risk_reward_target:.1f}",
                ],
            )

        return None
