"""
Trade lifecycle and closed trade records for AI GOLD WATCHER V4.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from src.strategies.base_strategy import OrderSide


class ExitReason(str, Enum):
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_LOSS = "STOP_LOSS"
    SIGNAL_REVERSAL = "SIGNAL_REVERSAL"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    MANUAL_CLOSE = "MANUAL_CLOSE"
    TIMEOUT = "TIMEOUT"


@dataclass(frozen=True)
class ClosedTrade:
    """Immutable audit record of a completed trade."""
    trade_id: str
    magic_number: int
    strategy_id: str
    symbol: str
    side: OrderSide
    volume: float
    entry_price: float
    entry_time: datetime
    exit_price: float
    exit_time: datetime
    stop_loss: float
    take_profit: float
    exit_reason: ExitReason
    duration_seconds: int
    gross_pnl: float
    spread_cost: float
    slippage_cost: float
    net_pnl: float
    points_pnl: int
