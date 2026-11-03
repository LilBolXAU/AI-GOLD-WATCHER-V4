"""
Profit and Loss calculator for AI GOLD WATCHER V4.
Strict adherence to contract size and point value math for XAUUSDm.
"""

from src.data.models import SymbolSpec
from src.strategies.base_strategy import OrderSide


def calculate_gross_pnl(
    entry_price: float,
    exit_price: float,
    side: OrderSide,
    volume: float,
    spec: SymbolSpec,
) -> float:
    """
    Calculate gross profit/loss in account currency (USD).
    Formula: (exit - entry) * direction * volume * contract_size
    For XAUUSDm: contract_size = 100.0.
    Example: 0.01 lot * 100 = 1 oz. If gold moves from 2650.0 to 2651.0 (+1.0),
    PnL = 1.0 * 1.0 = +$1.00.
    """
    direction = 1.0 if side == OrderSide.BUY else -1.0
    price_delta = (exit_price - entry_price) * direction
    gross_pnl = price_delta * volume * spec.contract_size
    return round(gross_pnl, spec.digits)


def calculate_points_pnl(
    entry_price: float,
    exit_price: float,
    side: OrderSide,
    spec: SymbolSpec,
) -> int:
    """Calculate price movement in broker points."""
    direction = 1.0 if side == OrderSide.BUY else -1.0
    price_delta = (exit_price - entry_price) * direction
    points = int(round(price_delta / spec.point))
    return points
