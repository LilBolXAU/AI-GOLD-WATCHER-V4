"""
Virtual position representation for AI GOLD WATCHER V4 paper trading.
"""

from dataclasses import dataclass
from datetime import datetime
from src.data.models import SymbolSpec
from src.strategies.base_strategy import OrderSide
from src.risk.pnl_calculator import calculate_gross_pnl


@dataclass
class VirtualPosition:
    """Represents an open paper position in memory."""
    position_id: str
    magic_number: int
    strategy_id: str
    symbol: str
    side: OrderSide
    volume: float
    entry_price: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    spread_points: int
    slippage_points: int = 0
    current_price: float = 0.0
    floating_pnl: float = 0.0

    @property
    def unrealized_pnl(self) -> float:
        """Alias for floating_pnl for consistency across engines."""
        return self.floating_pnl

    def update_price(self, current_price: float, spec: SymbolSpec) -> float:
        """Update current price and recalculate floating P&L."""
        self.current_price = current_price
        self.floating_pnl = calculate_gross_pnl(
            self.entry_price, self.current_price, self.side, self.volume, spec
        )
        return self.floating_pnl
