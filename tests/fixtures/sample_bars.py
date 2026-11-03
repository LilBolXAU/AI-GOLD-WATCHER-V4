"""
Deterministic test bar generator fixtures for AI GOLD WATCHER V4 tests.
"""

from datetime import datetime, timedelta, timezone
from typing import List
import numpy as np
import pandas as pd
from src.data.models import BarData


def create_trending_bars(
    direction: str = "up",
    count: int = 100,
    base_price: float = 2650.0,
    step: float = 0.50,
) -> pd.DataFrame:
    """Generates continuous bullish or bearish trending bars."""
    start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    records = []
    price = base_price
    drift = step if direction == "up" else -step

    for i in range(count):
        t = start_time + timedelta(minutes=5 * i)
        open_p = price
        close_p = open_p + drift
        high_p = max(open_p, close_p) + 0.30
        low_p = min(open_p, close_p) - 0.30
        records.append({
            "time": t,
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": 100 + i,
            "spread": 15,
        })
        price = close_p

    df = pd.DataFrame(records).set_index("time")
    return df


def create_ranging_bars(
    count: int = 100,
    base_price: float = 2650.0,
    amplitude: float = 0.3,
) -> pd.DataFrame:
    """Generates mean-reverting chopping/ranging bars with low ADX and tight BB width."""
    start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    records = []

    for i in range(count):
        t = start_time + timedelta(minutes=5 * i)
        osc = amplitude * np.sin(i * 1.5)
        p = base_price + osc
        open_p = p
        close_p = p + (0.1 if i % 2 == 0 else -0.1)
        high_p = max(open_p, close_p) + 0.20
        low_p = min(open_p, close_p) - 0.20
        records.append({
            "time": t,
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": 80,
            "spread": 15,
        })

    df = pd.DataFrame(records).set_index("time")
    return df


def create_shock_bars(
    count: int = 100,
    shock_index: int = -1,
    shock_size: float = 25.0,
) -> pd.DataFrame:
    """Generates normal bars with a massive single-bar volatility shock."""
    df = create_ranging_bars(count=count, base_price=2650.0, amplitude=0.3)
    # Inject shock candle at shock_index
    target_idx = shock_index if shock_index >= 0 else count + shock_index
    shock_time = df.index[target_idx]
    df.loc[shock_time, "high"] = df.loc[shock_time, "open"] + shock_size
    df.loc[shock_time, "low"] = df.loc[shock_time, "open"] - shock_size
    df.loc[shock_time, "close"] = df.loc[shock_time, "open"] + (shock_size * 0.8)
    return df


def dataframe_to_bar_data_list(df: pd.DataFrame) -> List[BarData]:
    """Convert pandas DataFrame to List[BarData]."""
    bars = []
    for idx, row in df.iterrows():
        bars.append(
            BarData(
                timestamp=idx.to_pydatetime() if isinstance(idx, pd.Timestamp) else idx,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                tick_volume=int(row.get("volume", 100)),
                spread=int(row.get("spread", 15)),
            )
        )
    return bars
