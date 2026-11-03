"""
Smart Money Structure & Price Action Strategy Engine for AI GOLD WATCHER V4.
Implements institutional Market Structure Shift (MSS/CHoCH) and Candlestick Pattern Recognition.
Trades with structure breaks, rejection pinbars, and engulfing momentum, dynamically adapting
between SCALP and SWING targets.
"""

from typing import Optional
import pandas as pd

from src.data.models import SymbolSpec
from src.strategies.base_strategy import BaseStrategy, OrderSide, SignalCandidate


class SmartMoneyStructureStrategy(BaseStrategy):
    """
    SMC & Candlestick Price Action Strategy.
    Detects structural trend breaks (CHoCH), rejection pinbars, and engulfing expansions.
    Dynamically adjusts between Scalp and Swing targets depending on market momentum.
    """

    def __init__(
        self,
        max_sl_usd: float = 2.00,
        swing_rr_target: float = 2.5,
        scalp_rr_target: float = 1.30,
    ):
        super().__init__("SMC_STRUCTURE_PRICE_ACTION")
        self.max_sl_usd = max_sl_usd
        self.swing_rr_target = swing_rr_target
        self.scalp_rr_target = scalp_rr_target

    def evaluate(
        self, df: pd.DataFrame, spec: SymbolSpec
    ) -> Optional[SignalCandidate]:
        if df.empty or len(df) < 35:
            return None

        bar = df.iloc[-1]
        prev = df.iloc[-2]
        ts = df.index[-1]

        close = float(bar["close"])
        high = float(bar["high"])
        low = float(bar["low"])
        open_p = float(bar["open"])
        atr = float(bar.get("atr_14", 1.0))
        rsi = float(bar.get("rsi_14", 50.0))

        if atr <= 0.0:
            return None

        candle_range = max(0.05, high - low)

        # Market Structure Signals
        structure_bias = int(bar.get("structure_bias", 0))
        structure_shift = int(bar.get("structure_shift", 0))
        last_sh = float(bar.get("last_swing_high", 0.0))
        last_sl = float(bar.get("last_swing_low", 0.0))

        # Price Action Patterns
        is_pinbar_bull = bool(bar.get("is_pinbar_bull", False))
        is_pinbar_bear = bool(bar.get("is_pinbar_bear", False))
        is_engulfing_bull = bool(bar.get("is_engulfing_bull", False))
        is_engulfing_bear = bool(bar.get("is_engulfing_bear", False))

        # Decide whether current conditions warrant SWING or SCALP
        is_high_momentum = bool(bar.get("adx_14", 20.0) >= 25.0 and bar.get("efficiency_ratio_10", 0.3) >= 0.5)
        rr_target = self.swing_rr_target if is_high_momentum else self.scalp_rr_target

        # ---------------------------------------------------------------------
        # 1. BULLISH SMART MONEY SETUP
        # ---------------------------------------------------------------------
        # Condition A: Bullish CHoCH (Market Structure broke above previous Swing High)
        # Condition B: Bullish Rejection Pinbar or Bullish Engulfing in an established bull structure
        bull_choch = (structure_shift == 1) and (close > open_p) and (45.0 <= rsi <= 72.0)
        bull_pa_bounce = (structure_bias >= 0) and (is_pinbar_bull or is_engulfing_bull) and (40.0 <= rsi <= 68.0)

        if bull_choch or bull_pa_bounce:
            # Place structural Stop Loss below the recent structural pivot low or candle low
            ref_low = last_sl if (last_sl > 0.0 and close - last_sl <= self.max_sl_usd) else low
            sl_dist = max(0.50, min(self.max_sl_usd, (close - ref_low) + 0.20))
            entry_rounded = round(close, spec.digits)
            sl_price = round(entry_rounded - sl_dist, spec.digits)
            tp_dist = round(sl_dist * rr_target, spec.digits)
            tp_price = round(entry_rounded + tp_dist, spec.digits)

            reasons = []
            if bull_choch:
                reasons.append(f"Bullish Market Structure Shift / CHoCH broke above {last_sh:.2f}")
            if is_pinbar_bull:
                reasons.append("Bullish Pinbar rejection wick confirmed")
            if is_engulfing_bull:
                reasons.append("Bullish Engulfing expansion candle confirmed")
            reasons.append(f"Targeting {'SWING' if is_high_momentum else 'SCALP'} R:R 1:{rr_target:.1f} (TP: +${tp_dist:.2f})")

            confidence = 0.85 if bull_choch else 0.78
            if is_high_momentum:
                confidence = min(0.95, confidence + 0.07)

            return SignalCandidate(
                strategy_id=self.name,
                timestamp=ts,
                symbol=getattr(spec, "name", "XAUUSDm"),
                side=OrderSide.BUY,
                entry_price=entry_rounded,
                stop_loss=sl_price,
                take_profit=tp_price,
                raw_confidence=confidence,
                reasons=reasons,
            )

        # ---------------------------------------------------------------------
        # 2. BEARISH SMART MONEY SETUP
        # ---------------------------------------------------------------------
        # Condition A: Bearish CHoCH (Market Structure broke below previous Swing Low)
        # Condition B: Bearish Rejection Pinbar or Bearish Engulfing in an established bear structure
        bear_choch = (structure_shift == -1) and (close < open_p) and (28.0 <= rsi <= 55.0)
        bear_pa_drop = (structure_bias <= 0) and (is_pinbar_bear or is_engulfing_bear) and (32.0 <= rsi <= 60.0)

        if bear_choch or bear_pa_drop:
            ref_high = last_sh if (last_sh > 0.0 and last_sh - close <= self.max_sl_usd) else high
            sl_dist = max(0.50, min(self.max_sl_usd, (ref_high - close) + 0.20))
            entry_rounded = round(close, spec.digits)
            sl_price = round(entry_rounded + sl_dist, spec.digits)
            tp_dist = round(sl_dist * rr_target, spec.digits)
            tp_price = round(entry_rounded - tp_dist, spec.digits)

            reasons = []
            if bear_choch:
                reasons.append(f"Bearish Market Structure Shift / CHoCH broke below {last_sl:.2f}")
            if is_pinbar_bear:
                reasons.append("Bearish Pinbar rejection wick confirmed")
            if is_engulfing_bear:
                reasons.append("Bearish Engulfing expansion candle confirmed")
            reasons.append(f"Targeting {'SWING' if is_high_momentum else 'SCALP'} R:R 1:{rr_target:.1f} (TP: +${tp_dist:.2f})")

            confidence = 0.85 if bear_choch else 0.78
            if is_high_momentum:
                confidence = min(0.95, confidence + 0.07)

            return SignalCandidate(
                strategy_id=self.name,
                timestamp=ts,
                symbol=getattr(spec, "name", "XAUUSDm"),
                side=OrderSide.SELL,
                entry_price=entry_rounded,
                stop_loss=sl_price,
                take_profit=tp_price,
                raw_confidence=confidence,
                reasons=reasons,
            )

        return None
