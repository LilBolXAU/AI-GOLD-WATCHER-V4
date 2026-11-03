"""
Evaluation and performance analytics module for AI GOLD WATCHER V4.
"""

from src.evaluation.performance_metrics import (
    PerformanceMetrics,
    calculate_performance_metrics,
)
from src.evaluation.trade_analysis import (
    analyze_by_side,
    analyze_by_strategy,
    analyze_exit_reasons,
)
from src.evaluation.robustness import (
    compute_deflated_sharpe,
)
from src.evaluation.report_generator import (
    generate_markdown_tearsheet,
)

__all__ = [
    "PerformanceMetrics",
    "calculate_performance_metrics",
    "analyze_by_side",
    "analyze_by_strategy",
    "analyze_exit_reasons",
    "compute_deflated_sharpe",
    "generate_markdown_tearsheet",
]
