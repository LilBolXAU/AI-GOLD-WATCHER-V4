"""
Tests for Backtesting Engine, Fill Simulator, and Walk-Forward Optimization.
"""

from datetime import datetime, timezone
import pandas as pd
import pytest

from src.data.models import SymbolSpec, BarData
from src.data.symbol_specs import DEFAULT_EXNESS_XAUUSD
from src.strategies.base_strategy import OrderSide
from src.execution.virtual_position import VirtualPosition
from src.execution.trade_lifecycle import ExitReason
from src.backtest.fill_simulator import FillSimulator
from src.backtest.event_engine import EventBacktestEngine, BacktestResult
from src.backtest.walk_forward import WalkForwardOptimizer
from tests.fixtures.sample_bars import create_trending_bars


def test_event_backtest_engine_run(symbol_spec: SymbolSpec):
    # 200 bars of trending data
    df = create_trending_bars(direction="up", count=200, step=0.30)
    engine = EventBacktestEngine(spec=symbol_spec, initial_balance=50.0)
    result = engine.run(df)

    assert isinstance(result, BacktestResult)
    assert result.initial_balance == 50.0
    assert result.final_balance > 0.0
    assert len(result.equity_curve) > 0


def test_fill_simulator_conservative_tie_breaker(symbol_spec: SymbolSpec):
    sim = FillSimulator(spec=symbol_spec)
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    pos = VirtualPosition(
        position_id="test_pos",
        magic_number=400001,
        strategy_id="TREND",
        symbol="XAUUSDm",
        side=OrderSide.BUY,
        volume=0.01,
        entry_price=2650.0,
        entry_time=now,
        stop_loss=2645.0,
        take_profit=2655.0,
        spread_points=15,
        slippage_points=0,
        current_price=2650.0,
        floating_pnl=0.0,
    )
    bar = BarData(
        timestamp=now,
        open=2650.0,
        high=2660.0,  # Touches TP
        low=2640.0,   # Touches SL
        close=2650.0,
        tick_volume=100,
        spread=15,
    )

    # Conservative tie-breaker: Stop Loss takes precedence if both touched in the same bar
    is_exit, exit_price, reason = sim.check_intrabar_exit(pos, bar)
    assert is_exit is True
    assert reason == ExitReason.STOP_LOSS


def test_walk_forward_splits(symbol_spec: SymbolSpec):
    optimizer = WalkForwardOptimizer(spec=symbol_spec, train_window_bars=100, test_window_bars=40, embargo_bars=5)
    df = create_trending_bars(count=200)
    splits = optimizer.generate_splits(df)

    assert len(splits) >= 1
    for train_df, test_df in splits:
        # Train and test must be disjoint and chronological
        assert train_df.index[-1] < test_df.index[0]
        assert len(train_df) == 100
        assert len(test_df) == 40
