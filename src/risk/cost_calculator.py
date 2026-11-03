"""
Transaction cost calculator for AI GOLD WATCHER V4.
Models floating spreads, slippage, and swap costs for XAUUSDm on Exness.
"""

from src.data.models import SymbolSpec


def calculate_spread_cost(
    spread_points: int, volume: float, spec: SymbolSpec
) -> float:
    """
    Cost incurred crossing the bid-ask spread.
    Cost = spread_points * point * contract_size * volume.
    Example: 20 points ($0.20) on 0.01 lot = 0.20 * 100 * 0.01 = $0.20.
    """
    price_spread = spread_points * spec.point
    cost = price_spread * spec.contract_size * volume
    return round(cost, 4)


def calculate_slippage_cost(
    slippage_points: int, volume: float, spec: SymbolSpec
) -> float:
    """Cost incurred from execution price slippage."""
    price_slip = slippage_points * spec.point
    cost = price_slip * spec.contract_size * volume
    return round(cost, 4)


def calculate_net_pnl(
    gross_pnl: float,
    spread_cost: float,
    commission: float = 0.0,
    swap: float = 0.0,
) -> float:
    """Calculate net P&L after deducting spread, commission, and swap fees."""
    return round(gross_pnl - spread_cost - commission + swap, 2)
