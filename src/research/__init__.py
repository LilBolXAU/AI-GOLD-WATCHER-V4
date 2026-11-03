"""
Research and quantitative optimization module for AI GOLD WATCHER V4.
"""

from src.research.parameter_sensitivity import (
    ParameterSensitivityPoint,
    ParameterSensitivitySummary,
    evaluate_parameter_curve,
)
from src.research.regime_analysis import (
    RegimeAttribution,
    attribute_trades_by_regime,
)
from src.research.strategy_comparison import (
    StrategyComparisonRow,
    compare_strategies,
)
from src.research.optimization import (
    OptimizationTrialResult,
    OptimizationStudyResult,
    run_grid_optimization,
)

__all__ = [
    "ParameterSensitivityPoint",
    "ParameterSensitivitySummary",
    "evaluate_parameter_curve",
    "RegimeAttribution",
    "attribute_trades_by_regime",
    "StrategyComparisonRow",
    "compare_strategies",
    "OptimizationTrialResult",
    "OptimizationStudyResult",
    "run_grid_optimization",
]
