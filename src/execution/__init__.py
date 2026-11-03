"""Execution package for AI GOLD WATCHER V4."""
from src.execution.virtual_position import VirtualPosition
from src.execution.trade_lifecycle import ClosedTrade, ExitReason
from src.execution.paper_broker import PaperBroker
from src.execution.paper_trade_manager import PaperTradeManager

__all__ = [
    "VirtualPosition",
    "ClosedTrade",
    "ExitReason",
    "PaperBroker",
    "PaperTradeManager",
]
