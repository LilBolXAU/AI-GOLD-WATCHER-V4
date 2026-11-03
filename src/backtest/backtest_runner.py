"""
High-level backtest runner for AI GOLD WATCHER V4.
"""

from typing import Optional
import pandas as pd

from src.data.models import SymbolSpec
from src.data.symbol_specs import DEFAULT_EXNESS_XAUUSD
from src.data.mt5_client import MockMT5Client
from src.data.models import Timeframe
from src.backtest.event_engine import EventBacktestEngine, BacktestResult


def run_standard_backtest(
    df: Optional[pd.DataFrame] = None,
    spec: Optional[SymbolSpec] = None,
    initial_balance: float = 50.0,
    bar_count: int = 500,
) -> BacktestResult:
    """
    Execute a standard backtest.
    If no DataFrame is provided, generates synthetic Gold bars via MockMT5Client.
    """
    target_spec = spec or DEFAULT_EXNESS_XAUUSD

    if df is None or df.empty:
        client = MockMT5Client(spec=target_spec)
        client.generate_synthetic_bars(timeframe=Timeframe.M5, count=bar_count, volatility=1.8)
        bars = client.get_rates("XAUUSDm", Timeframe.M5, count=bar_count, closed_only=True)
        records = [
            {
                "time": b.timestamp,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.tick_volume,
                "spread": b.spread,
            }
            for b in bars
        ]
        df = pd.DataFrame.from_records(records).set_index("time")

    engine = EventBacktestEngine(spec=target_spec, initial_balance=initial_balance)
    result = engine.run(df)
    return result
