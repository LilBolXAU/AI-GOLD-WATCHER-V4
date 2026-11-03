"""
Detailed trade breakdown and attribution analysis for AI GOLD WATCHER V4.
"""

from typing import Dict, List
import pandas as pd
from src.strategies.base_strategy import OrderSide
from src.execution.trade_lifecycle import ClosedTrade


def analyze_by_side(trades: List[ClosedTrade]) -> Dict[str, Dict[str, float]]:
    """Breakdown performance by Long vs Short side."""
    if not trades:
        return {}

    longs = [t for t in trades if t.side == OrderSide.BUY]
    shorts = [t for t in trades if t.side == OrderSide.SELL]

    def _side_stats(subset: List[ClosedTrade]):
        if not subset:
            return {"trades": 0, "net_pnl": 0.0, "win_rate": 0.0}
        n_wins = len([t for t in subset if t.net_pnl > 0])
        return {
            "trades": len(subset),
            "net_pnl": round(sum(t.net_pnl for t in subset), 2),
            "win_rate": round(n_wins / len(subset), 4),
        }

    return {"LONG": _side_stats(longs), "SHORT": _side_stats(shorts)}


def analyze_by_strategy(trades: List[ClosedTrade]) -> Dict[str, Dict[str, float]]:
    """Breakdown performance by individual strategy engine."""
    if not trades:
        return {}

    grouped: Dict[str, List[ClosedTrade]] = {}
    for t in trades:
        grouped.setdefault(t.strategy_id, []).append(t)

    result = {}
    for strat_id, subset in grouped.items():
        n_wins = len([t for t in subset if t.net_pnl > 0])
        result[strat_id] = {
            "trades": len(subset),
            "net_pnl": round(sum(t.net_pnl for t in subset), 2),
            "win_rate": round(n_wins / len(subset), 4),
            "profit_factor": round(
                sum(t.net_pnl for t in subset if t.net_pnl > 0)
                / max(abs(sum(t.net_pnl for t in subset if t.net_pnl < 0)), 0.01),
                2,
            ),
        }
    return result


def analyze_exit_reasons(trades: List[ClosedTrade]) -> Dict[str, int]:
    """Breakdown frequency of exit reasons (TP, SL, etc.)."""
    counts: Dict[str, int] = {}
    for t in trades:
        counts[t.exit_reason.value] = counts.get(t.exit_reason.value, 0) + 1
    return counts
