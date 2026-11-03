"""
Comparative analysis across independent strategy engines for AI GOLD WATCHER V4.
"""

from dataclasses import dataclass
from typing import Dict, List
import pandas as pd
from src.execution.trade_lifecycle import ClosedTrade
from src.evaluation.performance_metrics import calculate_performance_metrics


@dataclass(frozen=True)
class StrategyComparisonRow:
    strategy_id: str
    total_trades: int
    win_rate: float
    net_pnl: float
    profit_factor: float
    max_drawdown_usd: float
    sharpe_ratio: float
    expectancy_usd: float


def compare_strategies(trades: List[ClosedTrade], initial_balance: float = 50.0) -> List[StrategyComparisonRow]:
    """
    Compare multiple strategies evaluated over the same market dataset.
    """
    if not trades:
        return []

    grouped: Dict[str, List[ClosedTrade]] = {}
    for t in trades:
        grouped.setdefault(t.strategy_id, []).append(t)

    rows: List[StrategyComparisonRow] = []
    for s_id, s_trades in grouped.items():
        # Build synthetic equity curve for this strategy
        s_sorted = sorted(s_trades, key=lambda x: x.exit_time)
        cum_equity = [initial_balance]
        for t in s_sorted:
            cum_equity.append(cum_equity[-1] + t.net_pnl)
        eq_series = pd.Series(cum_equity)

        metrics = calculate_performance_metrics(s_trades, eq_series, initial_balance=initial_balance)
        rows.append(
            StrategyComparisonRow(
                strategy_id=s_id,
                total_trades=metrics.total_trades,
                win_rate=metrics.win_rate,
                net_pnl=round(metrics.net_profit, 2),
                profit_factor=round(metrics.profit_factor, 2),
                max_drawdown_usd=round(metrics.max_drawdown_usd, 2),
                sharpe_ratio=round(metrics.sharpe_ratio, 2),
                expectancy_usd=round(metrics.expectancy_usd, 2),
            )
        )

    # Sort descending by Net PnL
    rows.sort(key=lambda r: r.net_pnl, reverse=True)
    return rows
