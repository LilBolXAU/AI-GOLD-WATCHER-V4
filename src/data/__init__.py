"""Data package for AI GOLD WATCHER V4."""
from src.data.models import BarData, TickData, Timeframe, SymbolSpec, DataError
from src.data.symbol_specs import DEFAULT_EXNESS_XAUUSD, validate_broker_symbol
from src.data.data_validator import DataValidator
from src.data.mt5_client import MT5ClientBase, MockMT5Client, LiveMT5Client
from src.data.data_engine import MT5DataEngine

__all__ = [
    "BarData",
    "TickData",
    "Timeframe",
    "SymbolSpec",
    "DataError",
    "DEFAULT_EXNESS_XAUUSD",
    "validate_broker_symbol",
    "DataValidator",
    "MT5ClientBase",
    "MockMT5Client",
    "LiveMT5Client",
    "MT5DataEngine",
]
