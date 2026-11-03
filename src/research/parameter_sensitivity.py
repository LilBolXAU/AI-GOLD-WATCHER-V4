"""
Parameter sensitivity analysis for AI GOLD WATCHER V4.
Evaluates strategy stability across parameter surfaces to detect overfitting cliffs.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Any
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ParameterSensitivityPoint:
    params: Dict[str, Any]
    metric_name: str
    metric_value: float
    total_trades: int
    profit_factor: float
    max_drawdown_usd: float


@dataclass(frozen=True)
class ParameterSensitivitySummary:
    parameter_name: str
    points: List[ParameterSensitivityPoint]
    mean_metric: float
    std_metric: float
    cv_metric: float  # Coefficient of variation (std / mean)
    is_cliff_detected: bool
    cliff_notes: str


def evaluate_parameter_curve(
    param_name: str,
    param_values: List[Any],
    base_params: Dict[str, Any],
    eval_fn: Callable[[Dict[str, Any]], Dict[str, float]],
    target_metric: str = "sharpe_ratio",
    cliff_drop_threshold: float = 0.50,  # 50% drop between adjacent parameter steps flags cliff
) -> ParameterSensitivitySummary:
    """
    Vary a single parameter along a list of values, keeping base parameters constant.
    eval_fn takes a dict of params and returns a dict with metrics:
    {'sharpe_ratio': ..., 'profit_factor': ..., 'net_profit': ..., 'max_drawdown': ..., 'trades': ...}
    """
    points: List[ParameterSensitivityPoint] = []
    metric_vals: List[float] = []

    for val in param_values:
        trial_params = dict(base_params)
        trial_params[param_name] = val
        res = eval_fn(trial_params)

        target_val = float(res.get(target_metric, 0.0))
        metric_vals.append(target_val)

        points.append(
            ParameterSensitivityPoint(
                params=trial_params,
                metric_name=target_metric,
                metric_value=target_val,
                total_trades=int(res.get("trades", 0)),
                profit_factor=float(res.get("profit_factor", 0.0)),
                max_drawdown_usd=float(res.get("max_drawdown", 0.0)),
            )
        )

    arr = np.array(metric_vals)
    mean_val = float(np.mean(arr)) if len(arr) > 0 else 0.0
    std_val = float(np.std(arr)) if len(arr) > 0 else 0.0
    cv_val = float(std_val / abs(mean_val)) if mean_val != 0.0 else 0.0

    # Cliff detection: check relative drop between consecutive steps
    cliff_detected = False
    cliff_reasons: List[str] = []

    for i in range(len(metric_vals) - 1):
        v1 = metric_vals[i]
        v2 = metric_vals[i + 1]
        if v1 > 0 and (v1 - v2) / v1 > cliff_drop_threshold:
            cliff_detected = True
            cliff_reasons.append(
                f"Drop from {param_values[i]} ({v1:.2f}) to {param_values[i+1]} ({v2:.2f}) exceeds {cliff_drop_threshold:.0%}"
            )
        elif v2 > 0 and (v2 - v1) / v2 > cliff_drop_threshold:
            cliff_detected = True
            cliff_reasons.append(
                f"Drop from {param_values[i+1]} ({v2:.2f}) to {param_values[i]} ({v1:.2f}) exceeds {cliff_drop_threshold:.0%}"
            )

    notes = "; ".join(cliff_reasons) if cliff_reasons else "Surface is smooth across tested domain."

    return ParameterSensitivitySummary(
        parameter_name=param_name,
        points=points,
        mean_metric=round(mean_val, 4),
        std_metric=round(std_val, 4),
        cv_metric=round(cv_val, 4),
        is_cliff_detected=cliff_detected,
        cliff_notes=notes,
    )
