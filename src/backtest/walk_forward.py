"""
Walk-Forward Optimization and Cross-Validation for AI GOLD WATCHER V4.
Prevents train-test leakage by generating chronological in-sample / out-of-sample splits.
"""

from dataclasses import dataclass
from typing import List, Tuple
import pandas as pd

from src.data.models import SymbolSpec
from src.backtest.event_engine import EventBacktestEngine, BacktestResult


@dataclass
class WalkForwardFoldResult:
    fold_index: int
    train_bars: int
    test_bars: int
    train_result: BacktestResult
    test_result: BacktestResult


class WalkForwardOptimizer:
    """
    Executes chronological walk-forward cross-validation.
    Ensures that strategies are only evaluated on out-of-sample data they haven't seen.
    """

    def __init__(
        self,
        spec: SymbolSpec,
        train_window_bars: int = 400,
        test_window_bars: int = 150,
        embargo_bars: int = 5,
    ):
        self.spec = spec
        self.train_window_bars = train_window_bars
        self.test_window_bars = test_window_bars
        self.embargo_bars = embargo_bars

    def generate_splits(self, df: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """Generate chronological (train_df, test_df) slices."""
        total_len = len(df)
        step = self.test_window_bars
        splits = []

        start = 0
        while start + self.train_window_bars + self.embargo_bars + self.test_window_bars <= total_len:
            train_end = start + self.train_window_bars
            test_start = train_end + self.embargo_bars
            test_end = test_start + self.test_window_bars

            train_df = df.iloc[start:train_end]
            test_df = df.iloc[test_start:test_end]
            splits.append((train_df, test_df))

            start += step

        return splits

    def run(self, df: pd.DataFrame, initial_balance: float = 50.0) -> List[WalkForwardFoldResult]:
        """Run backtests across all chronological splits."""
        splits = self.generate_splits(df)
        results = []

        for idx, (train_df, test_df) in enumerate(splits):
            engine_train = EventBacktestEngine(spec=self.spec, initial_balance=initial_balance)
            engine_test = EventBacktestEngine(spec=self.spec, initial_balance=initial_balance)

            res_train = engine_train.run(train_df)
            res_test = engine_test.run(test_df)

            results.append(
                WalkForwardFoldResult(
                    fold_index=idx,
                    train_bars=len(train_df),
                    test_bars=len(test_df),
                    train_result=res_train,
                    test_result=res_test,
                )
            )

        return results
