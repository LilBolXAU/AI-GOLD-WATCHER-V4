"""
Unit tests for Research, Sensitivity Analysis, and Optimization.
"""

from datetime import datetime, timezone
import pytest
import pandas as pd

from src.strategies.base_strategy import OrderSide
from src.regime.regime_detector import RegimeType
from src.execution.trade_lifecycle import ClosedTrade, ExitReason
from src.research.parameter_sensitivity import evaluate_parameter_curve
from src.research.regime_analysis import attribute_trades_by_regime
from src.research.strategy_comparison import compare_strategies
from src.research.optimization import run_grid_optimization


def test_parameter_sensitivity_cliff_detection():
    # Synthetic eval function with a sharp drop at param=25
    def mock_eval(params: dict) -> dict:
        v = params["threshold"]
        # Sharpe drops 70% from 2.0 to 0.5 when threshold moves from 20 to 25
        sharpe = 2.0 if v <= 20 else 0.5
        return {"sharpe_ratio": sharpe, "profit_factor": 1.5, "trades": 30, "max_drawdown": 2.0}

    summary = evaluate_parameter_curve(
        param_name="threshold",
        param_values=[15, 20, 25, 30],
        base_params={"threshold": 20},
        eval_fn=mock_eval,
        target_metric="sharpe_ratio",
        cliff_drop_threshold=0.50,
    )

    assert summary.is_cliff_detected is True
    assert "Drop from 20" in summary.cliff_notes
    assert len(summary.points) == 4


def test_regime_attribution():
    t0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc)

    trade1 = ClosedTrade(
        trade_id="t1", magic_number=1, strategy_id="TREND", symbol="XAUUSDm",
        side=OrderSide.BUY, volume=0.01, entry_price=2650.0, entry_time=t0,
        exit_price=2652.0, exit_time=t0, stop_loss=2649.0, take_profit=2652.0,
        exit_reason=ExitReason.TAKE_PROFIT, duration_seconds=300,
        gross_pnl=2.00, spread_cost=0.15, slippage_cost=0.02, net_pnl=1.83, points_pnl=200,
    )

    regime_map = {t0: RegimeType.BULL_TRENDING}
    attr = attribute_trades_by_regime([trade1], regime_history=regime_map)

    assert RegimeType.BULL_TRENDING.value in attr
    bull_stats = attr[RegimeType.BULL_TRENDING.value]
    assert bull_stats.trade_count == 1
    assert bull_stats.win_rate == 1.0
    assert bull_stats.total_net_pnl == 1.83


def test_strategy_comparison():
    t0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    trade_trend = ClosedTrade(
        trade_id="t1", magic_number=1, strategy_id="TREND_FOLLOWING", symbol="XAUUSDm",
        side=OrderSide.BUY, volume=0.01, entry_price=2650.0, entry_time=t0,
        exit_price=2652.0, exit_time=t0, stop_loss=2649.0, take_profit=2652.0,
        exit_reason=ExitReason.TAKE_PROFIT, duration_seconds=300,
        gross_pnl=2.00, spread_cost=0.15, slippage_cost=0.02, net_pnl=1.83, points_pnl=200,
    )
    trade_rev = ClosedTrade(
        trade_id="t2", magic_number=2, strategy_id="RANGE_REVERSAL", symbol="XAUUSDm",
        side=OrderSide.SELL, volume=0.01, entry_price=2650.0, entry_time=t0,
        exit_price=2651.0, exit_time=t0, stop_loss=2651.0, take_profit=2648.0,
        exit_reason=ExitReason.STOP_LOSS, duration_seconds=300,
        gross_pnl=-1.00, spread_cost=0.15, slippage_cost=0.02, net_pnl=-1.17, points_pnl=-100,
    )

    rows = compare_strategies([trade_trend, trade_rev], initial_balance=50.0)
    assert len(rows) == 2
    # Sorted by net_pnl descending
    assert rows[0].strategy_id == "TREND_FOLLOWING"
    assert rows[1].strategy_id == "RANGE_REVERSAL"


def test_grid_optimization():
    def mock_eval_fn(params: dict) -> dict:
        mult = params.get("atr_mult", 2.0)
        # Higher mult yields slightly better OOS sharpe
        oos_s = 1.0 + (mult * 0.2)
        return {
            "is_sharpe": 1.5,
            "oos_sharpe": oos_s,
            "is_pnl": 5.0,
            "oos_pnl": 3.0,
            "is_trades": 20,
            "oos_trades": 15,
            "oos_returns": [0.005, -0.002, 0.003] * 12,
        }

    study = run_grid_optimization(
        strategy_id="TREND_FOLLOWING",
        param_grid={"atr_mult": [1.5, 2.0, 2.5]},
        eval_fn=mock_eval_fn,
        max_trials=5,
    )

    assert study.total_trials == 3
    assert study.best_trial.params["atr_mult"] == 2.5
    assert len(study.all_trials) == 3
