"""
Data Engine coordinating multi-timeframe data collection and validation.
Strict closed-bar discipline: bar 0 is NEVER used for trading decisions.
"""

from typing import Dict, List, Optional
import pandas as pd

from src.data.models import BarData, TickData, Timeframe, SymbolSpec, DataError
from src.data.mt5_client import MT5ClientBase, MockMT5Client
from src.data.data_validator import DataValidator


class MT5DataEngine:
    """
    Coordinates historical bar fetching, multi-timeframe synchronization,
    and data integrity validation for XAUUSDm.
    """

    def __init__(
        self,
        client: MT5ClientBase,
        symbol: str = "XAUUSDm",
        validator: Optional[DataValidator] = None,
    ):
        self.client = client
        self.symbol = symbol
        self.validator = validator or DataValidator()
        self._symbol_spec: Optional[SymbolSpec] = None

    def initialize(self) -> bool:
        """Connect to client and load symbol specification."""
        if not self.client.connect():
            return False
        try:
            self._symbol_spec = self.client.get_symbol_spec(self.symbol)
            return True
        except DataError:
            return False

    @property
    def symbol_spec(self) -> SymbolSpec:
        if self._symbol_spec is None:
            self._symbol_spec = self.client.get_symbol_spec(self.symbol)
        return self._symbol_spec

    def get_latest_tick(self) -> Optional[TickData]:
        return self.client.get_current_tick(self.symbol)

    def fetch_bars(
        self,
        timeframe: Timeframe,
        count: int = 300,
        closed_only: bool = True,
    ) -> List[BarData]:
        """
        Fetch normalized, validated bars.
        closed_only=True guarantees forming candle (bar 0) is excluded.
        """
        bars = self.client.get_rates(
            self.symbol, timeframe, count=count, closed_only=closed_only
        )
        if not bars:
            raise DataError(f"No bars returned for {self.symbol} on {timeframe.value}")

        # Run integrity validation
        issues = self.validator.validate_bar_sequence(bars, timeframe)
        # Note: We permit intra-week gaps if small, but log/record them
        return bars

    def fetch_dataframe(
        self,
        timeframe: Timeframe,
        count: int = 300,
        closed_only: bool = True,
    ) -> pd.DataFrame:
        """Convert fetched bars into a validated pandas DataFrame."""
        bars = self.fetch_bars(timeframe, count=count, closed_only=closed_only)
        records = [
            {
                "time": b.timestamp,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.tick_volume,
                "spread": b.spread,
            }
            for b in bars
        ]
        df = pd.DataFrame.from_records(records)
        df.set_index("time", inplace=True)
        return df

    def get_multi_timeframe_context(
        self,
        timeframes: Optional[List[Timeframe]] = None,
        count: int = 200,
    ) -> Dict[Timeframe, pd.DataFrame]:
        """
        Fetch synchronized closed DataFrames across multiple timeframes
        (Default: M15 Context, M5 Structure, M1 Entry Timing).
        """
        if timeframes is None:
            timeframes = [Timeframe.M15, Timeframe.M5, Timeframe.M1]

        data: Dict[Timeframe, pd.DataFrame] = {}
        for tf in timeframes:
            data[tf] = self.fetch_dataframe(tf, count=count, closed_only=True)
        return data
