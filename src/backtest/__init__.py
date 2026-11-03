"""Backtest package for AI GOLD WATCHER V4."""
from src.backtest.spread_model import SpreadModel, ConstantSpreadModel, DynamicSpreadModel
from src.backtest.slippage_model import SlippageModel, FixedSlippageModel, RandomSlippageModel
from src.backtest.commission_model import ZeroCommissionModel, PerLotCommissionModel
from src.backtest.fill_simulator import FillSimulator
from src.backtest.event_engine import EventBacktestEngine, BacktestResult
from src.backtest.walk_forward import WalkForwardOptimizer, WalkForwardFoldResult
from src.backtest.backtest_runner import run_standard_backtest

__all__ = [
    "SpreadModel",
    "ConstantSpreadModel",
    "DynamicSpreadModel",
    "SlippageModel",
    "FixedSlippageModel",
    "RandomSlippageModel",
    "ZeroCommissionModel",
    "PerLotCommissionModel",
    "FillSimulator",
    "EventBacktestEngine",
    "BacktestResult",
    "WalkForwardOptimizer",
    "WalkForwardFoldResult",
    "run_standard_backtest",
]
