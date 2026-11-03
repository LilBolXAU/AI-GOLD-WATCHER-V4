"""
Storage and database persistence module for AI GOLD WATCHER V4.
"""

from src.storage.database import Database, init_db
from src.storage.migrations import apply_migrations
from src.storage.repositories import (
    TradeRepository,
    SignalRepository,
    EquityRepository,
)

__all__ = [
    "Database",
    "init_db",
    "apply_migrations",
    "TradeRepository",
    "SignalRepository",
    "EquityRepository",
]
