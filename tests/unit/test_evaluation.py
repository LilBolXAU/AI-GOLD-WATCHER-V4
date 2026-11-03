"""
Unit tests for Performance Evaluation, Trade Analysis, and Robustness Metrics.
"""

from datetime import datetime, timezone
import pandas as pd
import pytest

from src.strategies.base_strategy import OrderSide
from src.execution.trade_lifecycle import ClosedTrade, ExitReason
from src.evaluation.performance_metrics import calculate_performance_metrics, PerformanceMetrics
from src.evaluation.trade_analysis import analyze_by_side, analyze_by_strategy
from src.evaluation.robustness import compute_deflated_sharpe


def test_performance_metrics_zero_trades():
    trades = []
    eq = pd.Series([50.0])
    metrics = calculate_performance_metrics(trades, eq, initial_balance=50.0)

    assert isinstance(metrics, PerformanceMetrics)
    assert metrics.total_trades == 0
    assert metrics.win_rate == 0.0
    assert metrics.profit_factor == 0.0
    assert metrics.is_sufficient_data is False


def test_performance_metrics_sample_trades():
    t0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    trade1 = ClosedTrade(
        trade_id="t1", magic_number=1, strategy_id="TREND", symbol="XAUUSDm",
        side=OrderSide.BUY, volume=0.01, entry_price=2650.0, entry_time=t0,
        exit_price=2652.0, exit_time=t0, stop_loss=2649.0, take_profit=2652.0,
        exit_reason=ExitReason.TAKE_PROFIT, duration_seconds=300,
        gross_pnl=2.00, spread_cost=0.15, slippage_cost=0.02, net_pnl=1.83, points_pnl=200,
    )
    trade2 = ClosedTrade(
        trade_id="t2", magic_number=2, strategy_id="TREND", symbol="XAUUSDm",
        side=OrderSide.BUY, volume=0.01, entry_price=2652.0, entry_time=t0,
        exit_price=2651.0, exit_time=t0, stop_loss=2651.0, take_profit=2654.0,
        exit_reason=ExitReason.STOP_LOSS, duration_seconds=300,
        gross_pnl=-1.00, spread_cost=0.15, slippage_cost=0.02, net_pnl=-1.17, points_pnl=-100,
    )

    trades = [trade1, trade2]
    eq = pd.Series([50.0, 51.83, 50.66])
    metrics = calculate_performance_metrics(trades, eq, initial_balance=50.0)

    assert metrics.total_trades == 2
    assert metrics.winning_trades == 1
    assert metrics.losing_trades == 1
    assert metrics.win_rate == 0.5
    assert metrics.net_profit == round(1.83 - 1.17, 2)
    assert metrics.profit_factor > 1.0


def test_trade_analysis_breakdown():
    t0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    t_buy = ClosedTrade(
        trade_id="t1", magic_number=1, strategy_id="TREND_FOLLOWING", symbol="XAUUSDm",
        side=OrderSide.BUY, volume=0.01, entry_price=2650.0, entry_time=t0,
        exit_price=2652.0, exit_time=t0, stop_loss=2649.0, take_profit=2652.0,
        exit_reason=ExitReason.TAKE_PROFIT, duration_seconds=300,
        gross_pnl=2.00, spread_cost=0.15, slippage_cost=0.02, net_pnl=1.83, points_pnl=200,
    )
    t_sell = ClosedTrade(
        trade_id="t2", magic_number=2, strategy_id="RANGE_REVERSAL", symbol="XAUUSDm",
        side=OrderSide.SELL, volume=0.01, entry_price=2650.0, entry_time=t0,
        exit_price=2651.0, exit_time=t0, stop_loss=2651.0, take_profit=2648.0,
        exit_reason=ExitReason.STOP_LOSS, duration_seconds=300,
        gross_pnl=-1.00, spread_cost=0.15, slippage_cost=0.02, net_pnl=-1.17, points_pnl=-100,
    )

    side_stats = analyze_by_side([t_buy, t_sell])
    assert side_stats["LONG"]["trades"] == 1
    assert side_stats["LONG"]["win_rate"] == 1.0
    assert side_stats["SHORT"]["trades"] == 1
    assert side_stats["SHORT"]["win_rate"] == 0.0

    strat_stats = analyze_by_strategy([t_buy, t_sell])
    assert "TREND_FOLLOWING" in strat_stats
    assert "RANGE_REVERSAL" in strat_stats


def test_deflated_sharpe_ratio():
    # Sample returns
    returns = [0.01, -0.005, 0.008, 0.012, -0.003, 0.004, 0.006] * 6  # 42 observations
    dsr = compute_deflated_sharpe(observed_sharpe=1.8, num_trials=10, returns=returns)
    assert 0.0 <= dsr <= 1.0
