"""
Core data models and type definitions for market data in AI GOLD WATCHER V4.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Timeframe(str, Enum):
    """Supported timeframes with MT5 enum mapping."""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    H1 = "H1"
    D1 = "D1"

    @property
    def mt5_value(self) -> int:
        """Map to MetaTrader5 timeframe integer constants."""
        mapping = {
            "M1": 1,
            "M5": 5,
            "M15": 15,
            "H1": 16385,
            "D1": 16408,
        }
        return mapping[self.value]

    @property
    def minutes(self) -> int:
        mapping = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "D1": 1440}
        return mapping[self.value]


@dataclass(frozen=True)
class BarData:
    """Immutable representation of a single completed candle bar."""
    timestamp: datetime  # Guaranteed UTC
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int          # Spread in points at bar close

    def __post_init__(self):
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware UTC")
        if self.high < self.low:
            raise ValueError(f"High ({self.high}) cannot be lower than Low ({self.low})")
        if self.open < self.low or self.open > self.high:
            raise ValueError(f"Open ({self.open}) outside High-Low range ({self.low}-{self.high})")
        if self.close < self.low or self.close > self.high:
            raise ValueError(f"Close ({self.close}) outside High-Low range ({self.low}-{self.high})")


@dataclass(frozen=True)
class TickData:
    """Immutable representation of a market tick."""
    timestamp: datetime  # Guaranteed UTC
    bid: float
    ask: float
    spread_points: int
    volume: float = 0.0

    @property
    def mid(self) -> float:
        return round((self.bid + self.ask) / 2.0, 5)


@dataclass(frozen=True)
class SymbolSpec:
    """Broker symbol trading parameters."""
    name: str = "XAUUSDm"
    digits: int = 2
    point: float = 0.01
    contract_size: float = 100.0
    tick_size: float = 0.01
    tick_value: float = 1.00          # For 1 standard lot per tick
    volume_min: float = 0.01
    volume_max: float = 200.0
    volume_step: float = 0.01
    stops_level: int = 0
    filling_mode: int = 1             # SYMBOL_FILLING_FOK = 1, SYMBOL_FILLING_IOC = 2
    currency_base: str = "XAU"
    currency_profit: str = "USD"
    currency_margin: str = "USD"


class DataError(Exception):
    """Exception raised on market data integrity failures."""
    pass
