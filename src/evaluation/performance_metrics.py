"""
Performance metrics evaluation for AI GOLD WATCHER V4.
Handles zero division and insufficient data safely.
"""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import pandas as pd
from src.execution.trade_lifecycle import ClosedTrade


@dataclass(frozen=True)
class PerformanceMetrics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    gross_profit: float
    gross_loss: float
    net_profit: float
    profit_factor: float
    expectancy_usd: float
    avg_win: float
    avg_loss: float
    max_drawdown_usd: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    recovery_factor: float
    avg_trade_duration_sec: float
    is_sufficient_data: bool


def calculate_performance_metrics(
    trades: List[ClosedTrade],
    equity_curve: pd.Series,
    initial_balance: float = 50.0,
    annualization_factor: float = 252.0,
) -> PerformanceMetrics:
    """
    Calculate comprehensive performance metrics from closed trades and equity series.
    Safely handles zero trades and division by zero.
    """
    total = len(trades)
    if total == 0:
        return PerformanceMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            gross_profit=0.0,
            gross_loss=0.0,
            net_profit=0.0,
            profit_factor=0.0,
            expectancy_usd=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            max_drawdown_usd=0.0,
            max_drawdown_pct=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            recovery_factor=0.0,
            avg_trade_duration_sec=0.0,
            is_sufficient_data=False,
        )

    wins = [t.net_pnl for t in trades if t.net_pnl > 0]
    losses = [t.net_pnl for t in trades if t.net_pnl < 0]

    n_wins = len(wins)
    n_losses = len(losses)
    win_rate = round(n_wins / total, 4)

    gross_profit = round(sum(wins), 2)
    gross_loss = round(abs(sum(losses)), 2)
    net_profit = round(gross_profit - gross_loss, 2)

    if gross_loss > 0:
        profit_factor = round(gross_profit / gross_loss, 2)
    else:
        profit_factor = 99.0 if gross_profit > 0 else 0.0

    avg_win = round(float(np.mean(wins)), 2) if n_wins > 0 else 0.0
    avg_loss = round(float(np.mean(losses)), 2) if n_losses > 0 else 0.0
    expectancy = round((win_rate * avg_win) + ((1.0 - win_rate) * avg_loss), 2)

    # Max drawdown from equity curve
    if not equity_curve.empty:
        peak = equity_curve.cummax()
        dd_usd = peak - equity_curve
        max_dd_usd = round(float(dd_usd.max()), 2)
        dd_pct = dd_usd / peak.replace(0, np.nan)
        max_dd_pct = round(float(dd_pct.max()) * 100.0, 2)

        # Returns for Sharpe and Sortino
        returns = equity_curve.pct_change().dropna()
        if len(returns) > 1 and returns.std() > 0:
            sharpe = round(float(returns.mean() / returns.std() * np.sqrt(annualization_factor)), 2)
            neg_returns = returns[returns < 0]
            downside_std = neg_returns.std()
            if downside_std > 0:
                sortino = round(float(returns.mean() / downside_std * np.sqrt(annualization_factor)), 2)
            else:
                sortino = 99.0 if returns.mean() > 0 else 0.0
        else:
            sharpe = 0.0
            sortino = 0.0
    else:
        max_dd_usd = 0.0
        max_dd_pct = 0.0
        sharpe = 0.0
        sortino = 0.0

    recovery_factor = round(net_profit / max_dd_usd, 2) if max_dd_usd > 0 else 0.0
    avg_dur = round(float(np.mean([t.duration_seconds for t in trades])), 1)

    return PerformanceMetrics(
        total_trades=total,
        winning_trades=n_wins,
        losing_trades=n_losses,
        win_rate=win_rate,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        net_profit=net_profit,
        profit_factor=profit_factor,
        expectancy_usd=expectancy,
        avg_win=avg_win,
        avg_loss=avg_loss,
        max_drawdown_usd=max_dd_usd,
        max_drawdown_pct=max_dd_pct,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        recovery_factor=recovery_factor,
        avg_trade_duration_sec=avg_dur,
        is_sufficient_data=total >= 10,
    )
