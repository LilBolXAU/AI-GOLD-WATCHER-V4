"""
Multi-Timeframe Macro Trend Filter for AI GOLD WATCHER V4.
Analyzes H1 closed bars to establish higher-timeframe directional bias (Triple Screen System).
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import pandas as pd

from src.data.models import BarData


class MacroTrendBias(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True)
class MacroTrendResult:
    bias: MacroTrendBias
    h1_close: float
    h1_ema20: float
    h1_ema50: float
    description: str


class MacroTrendDetector:
    """
    Multi-Timeframe Macro Trend Filter.
    Analyzes H1 closed bars to establish higher-timeframe directional bias.
    Guarantees zero trades against the major H1 market tide.
    """

    @classmethod
    def analyze(cls, h1_bars: List[BarData]) -> MacroTrendResult:
        if not h1_bars or len(h1_bars) < 20:
            return MacroTrendResult(
                bias=MacroTrendBias.NEUTRAL,
                h1_close=0.0,
                h1_ema20=0.0,
                h1_ema50=0.0,
                description="Insufficient H1 bars for macro trend classification",
            )

        closes = pd.Series([b.close for b in h1_bars])
        ema20 = closes.ewm(span=20, adjust=False).mean()
        ema50 = closes.ewm(span=50, adjust=False).mean()

        last_c = float(closes.iloc[-1])
        last_e20 = float(ema20.iloc[-1])
        last_e50 = float(ema50.iloc[-1])

        if last_c >= last_e50 and last_e20 >= last_e50:
            bias = MacroTrendBias.BULLISH
            desc = f"H1 Bullish Trend: Close ({last_c:.2f}) >= EMA50 ({last_e50:.2f}) & EMA20 ({last_e20:.2f}) >= EMA50"
        elif last_c <= last_e50 and last_e20 <= last_e50:
            bias = MacroTrendBias.BEARISH
            desc = f"H1 Bearish Trend: Close ({last_c:.2f}) <= EMA50 ({last_e50:.2f}) & EMA20 ({last_e20:.2f}) <= EMA50"
        else:
            bias = MacroTrendBias.NEUTRAL
            desc = f"H1 Neutral/Consolidation: Close ({last_c:.2f}) between EMA20 ({last_e20:.2f}) and EMA50 ({last_e50:.2f})"

        return MacroTrendResult(
            bias=bias,
            h1_close=last_c,
            h1_ema20=last_e20,
            h1_ema50=last_e50,
            description=desc,
        )
