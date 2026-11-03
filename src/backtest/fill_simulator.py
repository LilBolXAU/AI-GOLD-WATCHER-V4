"""
Fill simulator for event-driven backtesting in AI GOLD WATCHER V4.
Enforces next-bar fill (signal at bar t, fill at bar t+1 open).
"""

from typing import Tuple, Optional
from src.data.models import BarData, SymbolSpec
from src.strategies.base_strategy import OrderSide
from src.risk.risk_guard import ApprovedOrder
from src.execution.virtual_position import VirtualPosition
from src.execution.trade_lifecycle import ExitReason


class FillSimulator:
    """Simulates realistic order fills during event-driven historical playback."""

    def __init__(self, spec: SymbolSpec):
        self.spec = spec

    def simulate_entry_fill(
        self,
        order: ApprovedOrder,
        next_bar: BarData,
        spread_pts: int,
        slippage_pts: int,
    ) -> VirtualPosition:
        """
        Fill an approved order at next_bar.open + spread/slippage.
        Guarantees zero lookahead.
        """
        half_spread = (spread_pts * self.spec.point) / 2.0
        slip = slippage_pts * self.spec.point

        if order.side == OrderSide.BUY:
            fill_price = round(next_bar.open + half_spread + slip, self.spec.digits)
        else:
            fill_price = round(next_bar.open - half_spread - slip, self.spec.digits)

        return VirtualPosition(
            position_id=f"bt_{order.magic_number}",
            magic_number=order.magic_number,
            strategy_id=order.strategy_id,
            symbol=order.symbol,
            side=order.side,
            volume=order.volume,
            entry_price=fill_price,
            entry_time=next_bar.timestamp,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            spread_points=spread_pts,
            slippage_points=slippage_pts,
            current_price=fill_price,
            floating_pnl=0.0,
        )

    def check_intrabar_exit(
        self, pos: VirtualPosition, bar: BarData
    ) -> Tuple[bool, Optional[float], Optional[ExitReason]]:
        """
        Check if bar touched Stop Loss or Take Profit.
        Conservative assumption: if both levels are touched, Stop Loss is assumed first.
        """
        if pos.side == OrderSide.BUY:
            sl_hit = bar.low <= pos.stop_loss
            tp_hit = bar.high >= pos.take_profit

            if sl_hit:
                # If gap below SL, fill at bar open or SL price
                exit_price = min(pos.stop_loss, bar.open) if bar.open < pos.stop_loss else pos.stop_loss
                return True, round(exit_price, self.spec.digits), ExitReason.STOP_LOSS
            if tp_hit:
                exit_price = max(pos.take_profit, bar.open) if bar.open > pos.take_profit else pos.take_profit
                return True, round(exit_price, self.spec.digits), ExitReason.TAKE_PROFIT

        elif pos.side == OrderSide.SELL:
            sl_hit = bar.high >= pos.stop_loss
            tp_hit = bar.low <= pos.take_profit

            if sl_hit:
                exit_price = max(pos.stop_loss, bar.open) if bar.open > pos.stop_loss else pos.stop_loss
                return True, round(exit_price, self.spec.digits), ExitReason.STOP_LOSS
            if tp_hit:
                exit_price = min(pos.take_profit, bar.open) if bar.open < pos.take_profit else pos.take_profit
                return True, round(exit_price, self.spec.digits), ExitReason.TAKE_PROFIT

        return False, None, None
