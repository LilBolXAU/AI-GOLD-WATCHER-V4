"""
Market Exhaustion & Climax Filter for AI GOLD WATCHER V4.
Implements institutional safeguards against selling exhausted bottoms and buying overbought tops:
1. RSI Extreme Exhaustion (Current RSI < 33.0 or RSI > 67.0)
2. Mean-Reversion Band Climax (Price > 2.0 ATR outside Bollinger envelope)
3. Candlestick Rejection Wick Absorption (Wick >= 45% opposing momentum)
4. Key Psychological Round-Number Rejection (Support/Resistance at $X900, $X950, $X000)
5. Climax Reversal / Post-Climax Bounce Protection (Bouncing > 0.8 ATR after <30 or >70 RSI climax)
"""

from typing import Tuple
import pandas as pd
from src.strategies.base_strategy import OrderSide


class ExhaustionFilter:
    """
    Evaluates whether current price action indicates a market climax or momentum exhaustion,
    prohibiting trend-following and breakout strategies from chasing the move at turning points.
    """

    EXEMPT_STRATEGIES = {"RANGE_REVERSAL", "ASIAN_RANGE_SCALPER"}

    @classmethod
    def is_exhausted(
        cls,
        df: pd.DataFrame,
        side: OrderSide,
        strategy_id: str,
    ) -> Tuple[bool, str]:
        """
        Returns (is_exhausted: bool, reason: str).
        If is_exhausted is True, the trade candidate should be rejected.
        """
        if strategy_id in cls.EXEMPT_STRATEGIES:
            return False, ""

        if df.empty or len(df) < 5:
            return False, ""

        bar = df.iloc[-1]
        close_p = float(bar["close"])
        open_p = float(bar["open"])
        high_p = float(bar["high"])
        low_p = float(bar["low"])
        c_range = max(0.01, high_p - low_p)

        rsi = float(bar.get("rsi_14", 50.0))
        atr = float(bar.get("atr_14", 1.0))
        ema_20 = float(bar.get("ema_20", close_p))
        bb_lower = float(bar.get("bb_lower", close_p - 2.0))
        bb_upper = float(bar.get("bb_upper", close_p + 2.0))

        # Check Round Number Proximity ($50 increments like 3900, 3950, 4000)
        round_50 = round(close_p / 50.0) * 50.0
        near_round_number = abs(close_p - round_50) <= 0.60

        # Recent multi-bar context (last 6 bars ~ 30 minutes)
        lookback = min(6, len(df))
        recent_bars = df.iloc[-lookback:]
        recent_rsi = recent_bars["rsi_14"] if "rsi_14" in recent_bars.columns else pd.Series([50.0])
        min_recent_rsi = float(recent_rsi.min())
        max_recent_rsi = float(recent_rsi.max())
        lowest_low = float(recent_bars["low"].min())
        highest_high = float(recent_bars["high"].max())

        # ---------------------------------------------------------------------
        # 1. OVERSOLD CLIMAX (Chống Bán Đuổi Đáy)
        # ---------------------------------------------------------------------
        if side == OrderSide.SELL:
            lower_wick = min(open_p, close_p) - low_p
            lower_wick_ratio = lower_wick / c_range

            # a) Severe oversold momentum depletion
            if rsi < 33.0:
                return True, f"RSI={rsi:.1f} < 33.0 indicates severe oversold exhaustion. Prohibits selling into the bottom."

            # b) Hyper-extension below Bollinger Lower Band & EMA20
            if (close_p < bb_lower) and ((ema_20 - close_p) > 2.0 * atr):
                return True, f"Price ({close_p:.2f}) stretched > 2.0 ATR below EMA20 and outside lower band. High mean-reversion risk."

            # c) Strong rejection wick absorbing selling pressure at lows
            if lower_wick_ratio >= 0.45 and close_p < ema_20:
                return True, f"Bullish rejection wick ({lower_wick_ratio*100:.0f}%) detected at lows. Buying pressure absorbing sell flow."

            # d) Rejection right at a key round number support
            if near_round_number and lower_wick_ratio >= 0.35:
                return True, f"Institutional support rejection near psychological level {round_50:.0f} (Wick: {lower_wick_ratio*100:.0f}%)."

            # e) Climax Bottom Rebound: Recent RSI visited deep oversold (< 30.0)
            # and price is already rebounding > 0.8 ATR off the lowest low
            if min_recent_rsi < 30.0 and (close_p - lowest_low > 0.8 * atr):
                return True, (
                    f"Climax bottom rebound active: Recent RSI touched {min_recent_rsi:.1f} (< 30.0) "
                    f"and price rebounded +${close_p - lowest_low:.2f} off bottom {lowest_low:.2f}. Prohibits selling into rebound."
                )

        # ---------------------------------------------------------------------
        # 2. OVERBOUGHT CLIMAX (Chống Mua Đuổi Đỉnh)
        # ---------------------------------------------------------------------
        elif side == OrderSide.BUY:
            upper_wick = high_p - max(open_p, close_p)
            upper_wick_ratio = upper_wick / c_range

            # a) Severe overbought momentum depletion
            if rsi > 67.0:
                return True, f"RSI={rsi:.1f} > 67.0 indicates severe overbought exhaustion. Prohibits buying at the top."

            # b) Hyper-extension above Bollinger Upper Band & EMA20
            if (close_p > bb_upper) and ((close_p - ema_20) > 2.0 * atr):
                return True, f"Price ({close_p:.2f}) stretched > 2.0 ATR above EMA20 and outside upper band. High pullback risk."

            # c) Strong rejection wick absorbing buying pressure at highs
            if upper_wick_ratio >= 0.45 and close_p > ema_20:
                return True, f"Bearish rejection wick ({upper_wick_ratio*100:.0f}%) detected at highs. Selling pressure pushing price down."

            # d) Rejection right at a key round number resistance
            if near_round_number and upper_wick_ratio >= 0.35:
                return True, f"Institutional resistance rejection near psychological level {round_50:.0f} (Wick: {upper_wick_ratio*100:.0f}%)."

            # e) Climax Top Rollover: Recent RSI visited deep overbought (> 70.0)
            # and price is already rolling over > 0.8 ATR off the highest high
            if max_recent_rsi > 70.0 and (highest_high - close_p > 0.8 * atr):
                return True, (
                    f"Climax top rollover active: Recent RSI touched {max_recent_rsi:.1f} (> 70.0) "
                    f"and price dropped -${highest_high - close_p:.2f} off high {highest_high:.2f}. Prohibits buying into rollover."
                )

        return False, ""
