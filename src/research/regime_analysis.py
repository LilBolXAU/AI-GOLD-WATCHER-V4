"""
Regime conditioning and performance attribution for AI GOLD WATCHER V4.
Analyzes how strategies and signals perform across specific market regimes.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd
from src.regime.regime_detector import RegimeType
from src.execution.trade_lifecycle import ClosedTrade


@dataclass(frozen=True)
class RegimeAttribution:
    regime: RegimeType
    trade_count: int
    winning_trades: int
    win_rate: float
    total_net_pnl: float
    avg_pnl_per_trade: float
    profit_factor: float


def attribute_trades_by_regime(
    trades: List[ClosedTrade],
    regime_history: Optional[Dict[pd.Timestamp, RegimeType]] = None,
) -> Dict[str, RegimeAttribution]:
    """
    Attribution of closed trades across market regimes.
    If regime_history is provided, trade entry time is matched to the regime.
    Otherwise, if trades contain regime tagging in metadata, tags are used.
    """
    if not trades:
        return {}

    buckets: Dict[RegimeType, List[ClosedTrade]] = {r: [] for r in RegimeType}

    for t in trades:
        regime = RegimeType.UNSTABLE
        if regime_history and t.entry_time in regime_history:
            regime = regime_history[t.entry_time]
        elif regime_history:
            # Match nearest prior timestamp
            prior_times = [ts for ts in regime_history.keys() if ts <= t.entry_time]
            if prior_times:
                latest_ts = max(prior_times)
                regime = regime_history[latest_ts]
        buckets[regime].append(t)

    result: Dict[str, RegimeAttribution] = {}
    for r_type, trade_list in buckets.items():
        if not trade_list:
            continue
        n_trades = len(trade_list)
        wins = [t for t in trade_list if t.net_pnl > 0]
        losses = [t for t in trade_list if t.net_pnl < 0]
        gross_win = sum(t.net_pnl for t in wins)
        gross_loss = abs(sum(t.net_pnl for t in losses))
        pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_win > 0 else 0.0)
        net_pnl = sum(t.net_pnl for t in trade_list)

        result[r_type.value] = RegimeAttribution(
            regime=r_type,
            trade_count=n_trades,
            winning_trades=len(wins),
            win_rate=round(len(wins) / n_trades, 4) if n_trades > 0 else 0.0,
            total_net_pnl=round(net_pnl, 2),
            avg_pnl_per_trade=round(net_pnl / n_trades, 2) if n_trades > 0 else 0.0,
            profit_factor=pf,
        )

    return result
