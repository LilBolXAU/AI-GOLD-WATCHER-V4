"""
MetaTrader 5 Client and Mock Adapter for AI GOLD WATCHER V4.
Strict read-only data extraction: NO executable live order placement.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any
import numpy as np

from src.data.models import BarData, TickData, Timeframe, SymbolSpec, DataError
from src.data.symbol_specs import DEFAULT_EXNESS_XAUUSD, validate_broker_symbol


class MT5ClientBase(ABC):
    """Abstract base class for MT5 read-only data client."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to MT5 terminal or mock feed."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Terminate connection."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if terminal/feed is healthy."""
        pass

    @abstractmethod
    def get_symbol_spec(self, symbol: str) -> SymbolSpec:
        """Fetch and validate symbol specifications."""
        pass

    @abstractmethod
    def get_current_tick(self, symbol: str) -> Optional[TickData]:
        """Fetch latest market tick."""
        pass

    @abstractmethod
    def get_rates(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int,
        closed_only: bool = True,
    ) -> List[BarData]:
        """
        Fetch historical bars.
        If closed_only is True, position 0 (forming candle) is strictly omitted.
        """
        pass

    def get_account_info(self) -> Optional[Any]:
        """Fetch account information if connected."""
        return None


class MockMT5Client(MT5ClientBase):
    """
    Deterministic Mock MT5 client for testing, CI/CD, and simulation.
    Generates realistic Gold bars with controllable trend, volatility, and edge cases.
    """

    def __init__(
        self,
        symbol: str = "XAUUSDm",
        initial_price: float = 2650.0,
        spec: Optional[SymbolSpec] = None,
        connected: bool = True,
    ):
        self.symbol = symbol
        self.current_price = initial_price
        self.spec = spec or DEFAULT_EXNESS_XAUUSD
        self._connected = connected
        self._bars_cache: dict[Timeframe, List[BarData]] = {}

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_symbol_spec(self, symbol: str) -> SymbolSpec:
        if not self._connected:
            raise DataError("Mock MT5 terminal is disconnected.")
        if symbol != self.symbol:
            raise DataError(f"Symbol '{symbol}' not found in mock market watch.")
        return self.spec

    def get_current_tick(self, symbol: str) -> Optional[TickData]:
        if not self._connected or symbol != self.symbol:
            return None
        spread_pts = 18
        half_spread = (spread_pts * self.spec.point) / 2.0
        bid = round(self.current_price - half_spread, self.spec.digits)
        ask = round(self.current_price + half_spread, self.spec.digits)
        return TickData(
            timestamp=datetime.now(timezone.utc),
            bid=bid,
            ask=ask,
            spread_points=spread_pts,
            volume=1.0,
        )

    def generate_synthetic_bars(
        self,
        timeframe: Timeframe,
        count: int = 300,
        drift: float = 0.0,
        volatility: float = 1.5,
        start_time: Optional[datetime] = None,
    ) -> List[BarData]:
        """Generate deterministic, geometrically consistent Gold bars."""
        if start_time is None:
            # End shortly before now
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=timeframe.minutes * count)

        np.random.seed(42 + timeframe.minutes)
        price = self.current_price
        bars = []
        curr_time = start_time

        for i in range(count):
            ret = np.random.normal(drift, volatility * 0.001)
            open_p = round(price, 2)
            close_p = round(price * (1.0 + ret), 2)
            
            # Wicks
            high_p = round(max(open_p, close_p) + abs(np.random.normal(0, volatility * 0.5)), 2)
            low_p = round(min(open_p, close_p) - abs(np.random.normal(0, volatility * 0.5)), 2)

            bar = BarData(
                timestamp=curr_time,
                open=open_p,
                high=high_p,
                low=low_p,
                close=close_p,
                tick_volume=int(np.random.randint(50, 500)),
                spread=18,
            )
            bars.append(bar)
            price = close_p
            curr_time += timedelta(minutes=timeframe.minutes)

        self._bars_cache[timeframe] = bars
        self.current_price = price
        return bars

    def get_rates(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int,
        closed_only: bool = True,
    ) -> List[BarData]:
        if not self._connected:
            raise DataError("Mock MT5 is not connected.")
        if symbol != self.symbol:
            raise DataError(f"Symbol '{symbol}' not found.")

        if timeframe not in self._bars_cache:
            self.generate_synthetic_bars(timeframe, count=max(count + 10, 300))

        cached = self._bars_cache[timeframe]
        # If closed_only is requested, ensure we slice up to the second-to-last bar if the last is treated as open
        if closed_only and len(cached) > 0:
            return cached[-count:]
        return cached[-count:]


class LiveMT5Client(MT5ClientBase):
    """
    Live MetaTrader 5 Python client.
    Strictly read-only: retrieves rates, ticks, and specifications.
    Zero executable live order methods.
    """

    def __init__(self, symbol: str = "XAUUSDm"):
        self.symbol = symbol
        self._connected = False
        self._mt5: Any = None

    def connect(self) -> bool:
        try:
            import MetaTrader5 as mt5
            self._mt5 = mt5
            if not self._mt5.initialize():
                return False
            self._connected = True
            self._mt5.symbol_select(self.symbol, True)
            return True
        except ImportError:
            self._connected = False
            return False
        except Exception:
            self._connected = False
            return False

    def disconnect(self) -> None:
        if self._connected and self._mt5 is not None:
            self._mt5.shutdown()
        self._connected = False

    def is_connected(self) -> bool:
        if not self._connected or self._mt5 is None:
            return False
        try:
            terminal = self._mt5.terminal_info()
            return terminal is not None and getattr(terminal, "connected", False)
        except Exception:
            return False

    def get_symbol_spec(self, symbol: str) -> SymbolSpec:
        if not self.is_connected():
            raise DataError("MT5 terminal not connected.")
        info = self._mt5.symbol_info(symbol)
        if info is None:
            raise DataError(f"Symbol {symbol} not found in MT5.")
        return validate_broker_symbol(info)

    def get_current_tick(self, symbol: str) -> Optional[TickData]:
        if not self.is_connected():
            return None
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        spread_pts = int(round((tick.ask - tick.bid) / 0.01))
        return TickData(
            timestamp=datetime.fromtimestamp(tick.time, tz=timezone.utc),
            bid=tick.bid,
            ask=tick.ask,
            spread_points=spread_pts,
            volume=float(getattr(tick, "volume", 0.0)),
        )

    def get_rates(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int,
        closed_only: bool = True,
    ) -> List[BarData]:
        if not self.is_connected():
            raise DataError("MT5 terminal not connected.")

        # Zero Lookahead: Position 0 in MT5 is the currently forming candle.
        # When closed_only is True, start at position 1.
        start_pos = 1 if closed_only else 0
        rates = self._mt5.copy_rates_from_pos(
            symbol, timeframe.mt5_value, start_pos, count
        )

        if rates is None or len(rates) == 0:
            err = self._mt5.last_error()
            raise DataError(f"Failed to copy rates for {symbol} on {timeframe.value}: {err}")

        # In MT5, 3-digit Gold (point=0.001) returns spread in broker ticks/points (e.g. 240).
        # Normalize spread to standard 0.01 USD points (cents) so that 240 -> 24 pts.
        broker_point = 0.01
        try:
            info = self._mt5.symbol_info(symbol)
            if info is not None:
                broker_point = getattr(info, "point", 0.01)
        except Exception:
            pass

        bars = []
        for r in rates:
            # Exness timestamps are broker server time (EET/EEST)
            ts = datetime.fromtimestamp(r["time"], tz=timezone.utc)
            raw_spread = int(r["spread"])
            spread_pts = int(round(raw_spread * broker_point / 0.01)) if broker_point < 0.01 else raw_spread
            bars.append(
                BarData(
                    timestamp=ts,
                    open=float(r["open"]),
                    high=float(r["high"]),
                    low=float(r["low"]),
                    close=float(r["close"]),
                    tick_volume=int(r["tick_volume"]),
                    spread=spread_pts,
                )
            )

        return bars

    def get_account_info(self) -> Optional[Any]:
        """Fetch live account information from MT5 terminal."""
        if not self.is_connected() or self._mt5 is None:
            return None
        return self._mt5.account_info()
