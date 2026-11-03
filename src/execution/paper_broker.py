"""
Paper Broker execution simulator for AI GOLD WATCHER V4.
Simulates realistic fills with floating spreads and execution slippage.
"""

import uuid
from datetime import datetime
from src.data.models import SymbolSpec
from src.risk.risk_guard import ApprovedOrder
from src.strategies.base_strategy import OrderSide
from src.execution.virtual_position import VirtualPosition


class PaperBroker:
    """Simulates realistic execution fills without touching live broker order_send."""

    def __init__(self, spec: SymbolSpec, default_slippage_points: int = 1):
        self.spec = spec
        self.default_slippage_points = default_slippage_points

    def execute_fill(
        self,
        order: ApprovedOrder,
        current_spread_pts: int,
        fill_time: datetime,
        slippage_pts: int = 0,
    ) -> VirtualPosition:
        """
        Fill an ApprovedOrder into a VirtualPosition.
        Applies half-spread and slippage to entry price.
        """
        half_spread = (current_spread_pts * self.spec.point) / 2.0
        slip = slippage_pts * self.spec.point

        if order.side == OrderSide.BUY:
            # Buyers pay Ask + upward slippage
            fill_price = round(order.entry_price + half_spread + slip, self.spec.digits)
        else:
            # Sellers receive Bid - downward slippage
            fill_price = round(order.entry_price - half_spread - slip, self.spec.digits)

        pos_id = f"pos_{uuid.uuid4().hex[:8]}"

        return VirtualPosition(
            position_id=pos_id,
            magic_number=order.magic_number,
            strategy_id=order.strategy_id,
            symbol=order.symbol,
            side=order.side,
            volume=order.volume,
            entry_price=fill_price,
            entry_time=fill_time,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            spread_points=current_spread_pts,
            slippage_points=slippage_pts,
            current_price=fill_price,
            floating_pnl=0.0,
        )
