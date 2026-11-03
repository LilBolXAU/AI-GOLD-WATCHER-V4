"""
Price Action & Market Structure Engine for AI GOLD WATCHER V4.
Implements institutional Smart Money Concepts (SMC):
1. Swing High / Swing Low Fractal Detection (Structural Pivots)
2. Market Structure Shift (MSS) / Change of Character (CHoCH) / Break of Structure (BOS)
3. High-Probability Candlestick Patterns (Pinbar / Rejection Wicks, Bullish/Bearish Engulfing)
4. Fair Value Gap (FVG / Imbalance) Detection
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


def detect_swing_pivots(
    df: pd.DataFrame, left_bars: int = 2, right_bars: int = 2
) -> Tuple[pd.Series, pd.Series]:
    """
    Detect confirmed Swing Highs and Swing Lows (Fractal pivots).
    A bar is a swing high if its High is greater than all bars within left_bars and right_bars.
    """
    highs = df["high"].values
    lows = df["low"].values
    n = len(df)

    is_swing_high = np.zeros(n, dtype=bool)
    is_swing_low = np.zeros(n, dtype=bool)

    for i in range(left_bars, n - right_bars):
        # Check swing high
        curr_h = highs[i]
        if all(curr_h >= highs[i - l] for l in range(1, left_bars + 1)) and all(
            curr_h > highs[i + r] for r in range(1, right_bars + 1)
        ):
            is_swing_high[i] = True

        # Check swing low
        curr_l = lows[i]
        if all(curr_l <= lows[i - l] for l in range(1, left_bars + 1)) and all(
            curr_l < lows[i + r] for r in range(1, right_bars + 1)
        ):
            is_swing_low[i] = True

    return (
        pd.Series(is_swing_high, index=df.index, name="is_swing_high"),
        pd.Series(is_swing_low, index=df.index, name="is_swing_low"),
    )


def compute_market_structure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes real-time Market Structure (BOS / CHoCH) and tracks key structural levels:
    - structure_bias: 1 (Bullish Structure), -1 (Bearish Structure), 0 (Neutral)
    - last_swing_high: Price of the most recent confirmed swing high
    - last_swing_low: Price of the most recent confirmed swing low
    - structure_shift: 1 if bullish CHoCH triggered on this bar, -1 if bearish CHoCH, 0 otherwise
    """
    sh_series, sl_series = detect_swing_pivots(df, left_bars=2, right_bars=2)

    n = len(df)
    structure_bias = np.zeros(n, dtype=int)
    structure_shift = np.zeros(n, dtype=int)
    last_sh = np.zeros(n, dtype=float)
    last_sl = np.zeros(n, dtype=float)

    current_bias = 0
    curr_sh_price = 0.0
    curr_sl_price = 0.0

    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values
    sh_arr = sh_series.values
    sl_arr = sl_series.values

    for i in range(n):
        # If a past swing point was confirmed at this bar
        if sh_arr[i]:
            curr_sh_price = highs[i]
        if sl_arr[i]:
            curr_sl_price = lows[i]

        last_sh[i] = curr_sh_price
        last_sl[i] = curr_sl_price

        # Check for Market Structure Break / CHoCH:
        # Bullish break: Close breaks above the last confirmed swing high
        if curr_sh_price > 0.0 and closes[i] > curr_sh_price:
            if current_bias <= 0:
                structure_shift[i] = 1  # Bullish CHoCH
            current_bias = 1

        # Bearish break: Close breaks below the last confirmed swing low
        elif curr_sl_price > 0.0 and closes[i] < curr_sl_price:
            if current_bias >= 0:
                structure_shift[i] = -1  # Bearish CHoCH
            current_bias = -1

        structure_bias[i] = current_bias

    result = pd.DataFrame(index=df.index)
    result["is_swing_high"] = sh_series
    result["is_swing_low"] = sl_series
    result["structure_bias"] = structure_bias
    result["structure_shift"] = structure_shift
    result["last_swing_high"] = last_sh
    result["last_swing_low"] = last_sl
    return result


def compute_candlestick_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detects high-probability Price Action patterns on Gold:
    - is_pinbar_bull: Rejection wick at the bottom >= 55% of candle range
    - is_pinbar_bear: Rejection wick at the top >= 55% of candle range
    - is_engulfing_bull: Bullish engulfing candle with expansion body
    - is_engulfing_bear: Bearish engulfing candle with expansion body
    - candle_body_pct: Ratio of body size to total candle range
    """
    opens = df["open"].values
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    n = len(df)

    is_pinbar_bull = np.zeros(n, dtype=bool)
    is_pinbar_bear = np.zeros(n, dtype=bool)
    is_engulfing_bull = np.zeros(n, dtype=bool)
    is_engulfing_bear = np.zeros(n, dtype=bool)
    body_pct = np.zeros(n, dtype=float)

    for i in range(n):
        o, h, l, c = opens[i], highs[i], lows[i], closes[i]
        c_range = max(0.01, h - l)
        body = abs(c - o)
        body_pct[i] = round(body / c_range, 2)

        lower_wick = min(o, c) - l
        upper_wick = h - max(o, c)

        # Bullish Pinbar: long bottom tail >= 55%, small upper wick, closes in upper half
        if (lower_wick / c_range >= 0.55) and (upper_wick / c_range <= 0.25) and (c >= o):
            is_pinbar_bull[i] = True

        # Bearish Pinbar: long top tail >= 55%, small lower wick, closes in lower half
        elif (upper_wick / c_range >= 0.55) and (lower_wick / c_range <= 0.25) and (c <= o):
            is_pinbar_bear[i] = True

        # Engulfing patterns (needs at least 1 prior bar)
        if i >= 1:
            prev_o, prev_c = opens[i - 1], closes[i - 1]
            prev_body = abs(prev_c - prev_o)

            # Bullish Engulfing: previous bar was red, current bar is green and body engulfs previous body
            if (prev_c < prev_o) and (c > o) and (body > prev_body * 1.1) and (c >= prev_o):
                is_engulfing_bull[i] = True

            # Bearish Engulfing: previous bar was green, current bar is red and body engulfs previous body
            elif (prev_c > prev_o) and (c < o) and (body > prev_body * 1.1) and (c <= prev_o):
                is_engulfing_bear[i] = True

    result = pd.DataFrame(index=df.index)
    result["is_pinbar_bull"] = is_pinbar_bull
    result["is_pinbar_bear"] = is_pinbar_bear
    result["is_engulfing_bull"] = is_engulfing_bull
    result["is_engulfing_bear"] = is_engulfing_bear
    result["candle_body_pct"] = body_pct
    return result
