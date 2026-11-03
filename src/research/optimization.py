"""
Parameter optimization and hypothesis validation for AI GOLD WATCHER V4.
Implements multi-trial parameter search with Deflated Sharpe Ratio (DSR) multiple-testing correction.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List
import itertools
import random
from src.evaluation.robustness import compute_deflated_sharpe


@dataclass(frozen=True)
class OptimizationTrialResult:
    trial_id: int
    params: Dict[str, Any]
    is_sharpe: float
    oos_sharpe: float
    is_net_pnl: float
    oos_net_pnl: float
    is_trades: int
    oos_trades: int
    deflated_sharpe_p_value: float
    is_statistically_significant: bool


@dataclass(frozen=True)
class OptimizationStudyResult:
    strategy_id: str
    total_trials: int
    best_trial: OptimizationTrialResult
    all_trials: List[OptimizationTrialResult]
    overfitting_alert: bool
    summary_notes: str


def run_grid_optimization(
    strategy_id: str,
    param_grid: Dict[str, List[Any]],
    eval_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    max_trials: int = 50,
) -> OptimizationStudyResult:
    """
    Execute systematic parameter search across combinations.
    eval_fn(params) -> {
        'is_sharpe': float, 'oos_sharpe': float,
        'is_pnl': float, 'oos_pnl': float,
        'is_trades': int, 'oos_trades': int,
        'oos_returns': List[float]
    }
    """
    keys = list(param_grid.keys())
    value_combinations = list(itertools.product(*[param_grid[k] for k in keys]))

    if len(value_combinations) > max_trials:
        # Sample deterministically with fixed seed
        rnd = random.Random(42)
        selected_combos = rnd.sample(value_combinations, max_trials)
    else:
        selected_combos = value_combinations

    total_trials = len(selected_combos)
    trial_results: List[OptimizationTrialResult] = []

    for idx, combo in enumerate(selected_combos):
        params = dict(zip(keys, combo))
        res = eval_fn(params)

        oos_sharpe = float(res.get("oos_sharpe", 0.0))
        oos_returns = res.get("oos_returns", [])

        # Multiple testing penalty via Deflated Sharpe
        dsr_p = compute_deflated_sharpe(
            observed_sharpe=oos_sharpe,
            num_trials=total_trials,
            returns=oos_returns if oos_returns else [0.0] * 35,
        )

        trial_results.append(
            OptimizationTrialResult(
                trial_id=idx + 1,
                params=params,
                is_sharpe=float(res.get("is_sharpe", 0.0)),
                oos_sharpe=oos_sharpe,
                is_net_pnl=float(res.get("is_pnl", 0.0)),
                oos_net_pnl=float(res.get("oos_pnl", 0.0)),
                is_trades=int(res.get("is_trades", 0)),
                oos_trades=int(res.get("oos_trades", 0)),
                deflated_sharpe_p_value=round(dsr_p, 4),
                is_statistically_significant=(dsr_p >= 0.95),
            )
        )

    # Rank primarily by out-of-sample Sharpe and DSR
    trial_results.sort(key=lambda t: (t.oos_sharpe, t.deflated_sharpe_p_value), reverse=True)
    best = trial_results[0]

    # Overfitting alert: high in-sample Sharpe but negative or severely degraded OOS Sharpe
    overfitting = best.is_sharpe > 1.5 and best.oos_sharpe < 0.5

    notes = (
        f"Completed {total_trials} parameter trials for {strategy_id}. "
        f"Best params: {best.params} (IS Sharpe: {best.is_sharpe:.2f}, OOS Sharpe: {best.oos_sharpe:.2f}, DSR p: {best.deflated_sharpe_p_value:.3f})."
    )

    return OptimizationStudyResult(
        strategy_id=strategy_id,
        total_trials=total_trials,
        best_trial=best,
        all_trials=trial_results,
        overfitting_alert=overfitting,
        summary_notes=notes,
    )
