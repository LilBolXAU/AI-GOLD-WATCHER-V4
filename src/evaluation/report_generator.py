"""
Tearsheet and performance report generator for AI GOLD WATCHER V4.
"""

from src.backtest.event_engine import BacktestResult
from src.evaluation.performance_metrics import PerformanceMetrics
from src.evaluation.trade_analysis import analyze_by_side, analyze_by_strategy, analyze_exit_reasons


def generate_markdown_tearsheet(
    result: BacktestResult,
    metrics: PerformanceMetrics,
    title: str = "AI GOLD WATCHER V4 Backtest Report",
) -> str:
    """Generate comprehensive markdown tearsheet summarizing backtest results."""
    side_stats = analyze_by_side(result.trades)
    strat_stats = analyze_by_strategy(result.trades)
    exit_stats = analyze_exit_reasons(result.trades)

    data_warning = ""
    if not metrics.is_sufficient_data:
        data_warning = "> [!WARNING]\n> **INSUFFICIENT DATA**: Backtest contains fewer than 10 closed trades. Statistical metrics carry low confidence.\n\n"

    report = f"""# {title}

{data_warning}## 1. Capital & Return Overview
| Metric | Value |
| :--- | :--- |
| **Initial Balance** | ${result.initial_balance:.2f} USD |
| **Final Balance** | ${result.final_balance:.2f} USD |
| **Total Net Profit** | ${result.total_net_profit:.2f} USD ({result.return_pct:+.2f}%) |
| **Gross Profit** | ${metrics.gross_profit:.2f} USD |
| **Gross Loss** | ${metrics.gross_loss:.2f} USD |
| **Profit Factor** | {metrics.profit_factor:.2f} |
| **Expectancy per Trade** | ${metrics.expectancy_usd:.2f} USD |

## 2. Risk & Drawdown Telemetry
| Metric | Value |
| :--- | :--- |
| **Max Drawdown ($)** | ${metrics.max_drawdown_usd:.2f} USD |
| **Max Drawdown (%)** | {metrics.max_drawdown_pct:.2f}% |
| **Sharpe Ratio** | {metrics.sharpe_ratio:.2f} |
| **Sortino Ratio** | {metrics.sortino_ratio:.2f} |
| **Recovery Factor** | {metrics.recovery_factor:.2f} |

## 3. Trade Execution Distribution
| Metric | Value |
| :--- | :--- |
| **Total Trades** | {metrics.total_trades} |
| **Win Rate** | {metrics.win_rate * 100:.1f}% ({metrics.winning_trades} wins / {metrics.losing_trades} losses) |
| **Average Win** | ${metrics.avg_win:.2f} USD |
| **Average Loss** | ${metrics.avg_loss:.2f} USD |
| **Win / Loss Ratio** | {abs(metrics.avg_win / metrics.avg_loss) if metrics.avg_loss != 0 else 0.0:.2f} |
| **Avg Trade Duration** | {metrics.avg_trade_duration_sec:.0f} seconds |

## 4. Directional Breakdown
| Direction | Trades | Win Rate | Net P&L |
| :--- | :---: | :---: | :---: |
"""
    for side, stats in side_stats.items():
        report += f"| **{side}** | {stats['trades']} | {stats['win_rate']*100:.1f}% | ${stats['net_pnl']:+.2f} USD |\n"

    report += "\n## 5. Strategy Engine Breakdown\n| Strategy ID | Trades | Win Rate | Profit Factor | Net P&L |\n| :--- | :---: | :---: | :---: | :---: |\n"
    for strat, stats in strat_stats.items():
        report += f"| **{strat}** | {stats['trades']} | {stats['win_rate']*100:.1f}% | {stats.get('profit_factor', 0.0):.2f} | ${stats['net_pnl']:+.2f} USD |\n"

    report += "\n## 6. Exit Reason Breakdown\n| Exit Reason | Count |\n| :--- | :---: |\n"
    for reason, count in exit_stats.items():
        report += f"| **{reason}** | {count} |\n"

    report += "\n---\n*Report generated deterministically by AI GOLD WATCHER V4 Performance Engine.*\n"
    return report
