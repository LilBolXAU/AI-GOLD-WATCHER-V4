"""
Feature extraction for market regime classification in AI GOLD WATCHER V4.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RegimeFeatures:
    """Snapshot of regime-sensitive features for the latest closed bar."""
    adx: float
    plus_di: float
    minus_di: float
    atr: float
    atr_zscore: float
    ema_slope: float
    efficiency_ratio: float
    bb_width: float
    ema_bull_aligned: bool
    ema_bear_aligned: bool


def extract_regime_features(
    df: pd.DataFrame, atr_z_lookback: int = 50
) -> Optional[RegimeFeatures]:
    """
    Extract latest closed-bar regime features from an enriched indicator DataFrame.
    Returns None if history is insufficient.
    """
    if df.empty or len(df) < atr_z_lookback:
        return None

    last_row = df.iloc[-1]

    # Calculate ATR z-score against historical baseline (excluding current observation)
    atr_hist = df["atr_14"].iloc[-atr_z_lookback:-1]
    hist_mean = atr_hist.mean()
    hist_std = atr_hist.std()

    if hist_std is None or hist_std == 0 or np.isnan(hist_std):
        atr_zscore = 0.0
    else:
        atr_zscore = (last_row["atr_14"] - hist_mean) / hist_std

    return RegimeFeatures(
        adx=float(last_row.get("adx_14", 0.0)),
        plus_di=float(last_row.get("plus_di", 0.0)),
        minus_di=float(last_row.get("minus_di", 0.0)),
        atr=float(last_row.get("atr_14", 0.0)),
        atr_zscore=float(atr_zscore),
        ema_slope=float(last_row.get("ema_20_slope", 0.0)),
        efficiency_ratio=float(last_row.get("efficiency_ratio_10", 0.0)),
        bb_width=float(last_row.get("bb_width", 0.0)),
        ema_bull_aligned=bool(last_row.get("ema_aligned_bull", False)),
        ema_bear_aligned=bool(last_row.get("ema_aligned_bear", False)),
    )
