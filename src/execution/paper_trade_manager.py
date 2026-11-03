"""
Paper Trading Manager for AI GOLD WATCHER V4.
Manages position lifecycle, checks intrabar SL/TP hits, and records trade history.
"""

from typing import List, Optional
from datetime import datetime

from src.data.models import BarData, SymbolSpec
from src.risk.risk_guard import ApprovedOrder, RiskGuard
from src.risk.pnl_calculator import calculate_gross_pnl, calculate_points_pnl
from src.risk.cost_calculator import calculate_spread_cost, calculate_slippage_cost, calculate_net_pnl
from src.strategies.base_strategy import OrderSide
from src.execution.virtual_position import VirtualPosition
from src.execution.trade_lifecycle import ClosedTrade, ExitReason
from src.execution.paper_broker import PaperBroker
from src.execution.scalp_protection import ScalpProtectionEngine


class PaperTradeManager:
    """
    Manages active virtual positions and monitors exit conditions.
    Never sends orders to MetaTrader 5.
    """

    def __init__(
        self,
        spec: SymbolSpec,
        risk_guard: RiskGuard,
        broker: Optional[PaperBroker] = None,
        scalp_engine: Optional[ScalpProtectionEngine] = None,
    ):
        self.spec = spec
        self.risk_guard = risk_guard
        self.broker = broker or PaperBroker(spec=spec)
        self.scalp_engine = scalp_engine or ScalpProtectionEngine()
        self.active_positions: List[VirtualPosition] = []
        self.trade_history: List[ClosedTrade] = []

    @property
    def active_position(self) -> Optional[VirtualPosition]:
        """Provides backwards compatibility for callers expecting a single position."""
        return self.active_positions[0] if self.active_positions else None

    @active_position.setter
    def active_position(self, val: Optional[VirtualPosition]) -> None:
        if val is None:
            self.active_positions = []
        else:
            self.active_positions = [val]

    def open_position(
        self,
        order: ApprovedOrder,
        current_spread_pts: int,
        fill_time: datetime,
        slippage_pts: int = 0,
    ) -> bool:
        """Open a new virtual position (supports institutional scale-in up to 2 positions)."""
        if len(self.active_positions) >= 2:
            return False

        pos = self.broker.execute_fill(
            order=order,
            current_spread_pts=current_spread_pts,
            fill_time=fill_time,
            slippage_pts=slippage_pts,
        )
        self.active_positions.append(pos)
        self.risk_guard.active_position_count = len(self.active_positions)
        return True

    def on_bar_update(self, bar: BarData) -> Optional[ClosedTrade]:
        """
        Check active positions against the latest closed bar's High, Low, and Close.
        Evaluates Stop Loss and Take Profit triggers for all open positions.
        """
        if not self.active_positions:
            return None

        last_closed: Optional[ClosedTrade] = None
        remaining: List[VirtualPosition] = []

        for pos in self.active_positions:
            pos.update_price(bar.close, self.spec)
            exit_reason: Optional[ExitReason] = None
            exit_price: float = 0.0
            is_bullish = bar.close >= bar.open
            is_buy = (pos.side == OrderSide.BUY)

            # Realistic intra-bar 4-point OHLC traversal:
            # Bullish candle: Open -> Low -> High -> Close
            # Bearish candle: Open -> High -> Low -> Close
            first_extreme = bar.low if is_bullish else bar.high
            second_extreme = bar.high if is_bullish else bar.low

            # Phase 1: Traverse first extreme
            pos.current_price = first_extreme
            if is_buy:
                if first_extreme <= pos.stop_loss:
                    exit_price = pos.stop_loss
                    exit_reason = ExitReason.STOP_LOSS
                elif self.scalp_engine is not None:
                    scalp_act = self.scalp_engine.evaluate_position(pos)
                    if scalp_act is not None:
                        pos.stop_loss = scalp_act.new_sl
                        if scalp_act.new_tp is not None:
                            pos.take_profit = scalp_act.new_tp
            else:  # SELL
                if first_extreme >= pos.stop_loss:
                    exit_price = pos.stop_loss
                    exit_reason = ExitReason.STOP_LOSS
                elif self.scalp_engine is not None:
                    scalp_act = self.scalp_engine.evaluate_position(pos)
                    if scalp_act is not None:
                        pos.stop_loss = scalp_act.new_sl
                        if scalp_act.new_tp is not None:
                            pos.take_profit = scalp_act.new_tp

            # Phase 2: If not exited at first extreme, traverse second extreme
            if exit_reason is None:
                pos.current_price = second_extreme
                if is_buy:
                    if second_extreme >= pos.take_profit:
                        exit_price = pos.take_profit
                        exit_reason = ExitReason.TAKE_PROFIT
                    elif second_extreme <= pos.stop_loss:
                        exit_price = pos.stop_loss
                        exit_reason = ExitReason.STOP_LOSS
                    elif self.scalp_engine is not None:
                        scalp_act = self.scalp_engine.evaluate_position(pos)
                        if scalp_act is not None:
                            pos.stop_loss = scalp_act.new_sl
                            if scalp_act.new_tp is not None:
                                pos.take_profit = scalp_act.new_tp
                else:  # SELL
                    if second_extreme <= pos.take_profit:
                        exit_price = pos.take_profit
                        exit_reason = ExitReason.TAKE_PROFIT
                    elif second_extreme >= pos.stop_loss:
                        exit_price = pos.stop_loss
                        exit_reason = ExitReason.STOP_LOSS
                    elif self.scalp_engine is not None:
                        scalp_act = self.scalp_engine.evaluate_position(pos)
                        if scalp_act is not None:
                            pos.stop_loss = scalp_act.new_sl
                            if scalp_act.new_tp is not None:
                                pos.take_profit = scalp_act.new_tp

            # Phase 3: Final bar close settlement
            pos.current_price = bar.close
            if exit_reason is not None:
                last_closed = self._close_single_position(
                    pos=pos,
                    exit_price=exit_price,
                    exit_time=bar.timestamp,
                    reason=exit_reason,
                )
            else:
                if self.scalp_engine is not None:
                    scalp_act = self.scalp_engine.evaluate_position(pos)
                    if scalp_act is not None:
                        pos.stop_loss = scalp_act.new_sl
                        if scalp_act.new_tp is not None:
                            pos.take_profit = scalp_act.new_tp
                remaining.append(pos)

        self.active_positions = remaining
        self.risk_guard.active_position_count = len(self.active_positions)
        return last_closed

    def close_position(
        self,
        exit_price: float,
        exit_time: datetime,
        reason: ExitReason,
    ) -> ClosedTrade:
        """Close first active virtual position and record performance."""
        if not self.active_positions:
            raise RuntimeError("No active position to close.")

        pos = self.active_positions.pop(0)
        self.risk_guard.active_position_count = len(self.active_positions)
        return self._close_single_position(pos, exit_price, exit_time, reason)

    def _close_single_position(
        self,
        pos: VirtualPosition,
        exit_price: float,
        exit_time: datetime,
        reason: ExitReason,
    ) -> ClosedTrade:
        """Helper to compute PnL, record trade, and update risk guards."""
        gross_pnl = calculate_gross_pnl(
            entry_price=pos.entry_price,
            exit_price=exit_price,
            side=pos.side,
            volume=pos.volume,
            spec=self.spec,
        )
        pts_pnl = calculate_points_pnl(
            entry_price=pos.entry_price,
            exit_price=exit_price,
            side=pos.side,
            spec=self.spec,
        )
        spread_cost = calculate_spread_cost(
            spread_points=pos.spread_points,
            volume=pos.volume,
            spec=self.spec,
        )
        slip_cost = calculate_slippage_cost(
            slippage_points=pos.slippage_points,
            volume=pos.volume,
            spec=self.spec,
        )
        net_pnl = calculate_net_pnl(
            gross_pnl=gross_pnl, spread_cost=spread_cost
        )
        duration = int((exit_time - pos.entry_time).total_seconds())

        trade = ClosedTrade(
            trade_id=f"trd_{len(self.trade_history) + 1:04d}",
            magic_number=pos.magic_number,
            strategy_id=pos.strategy_id,
            symbol=pos.symbol,
            side=pos.side,
            volume=pos.volume,
            entry_price=pos.entry_price,
            entry_time=pos.entry_time,
            exit_price=exit_price,
            exit_time=exit_time,
            stop_loss=pos.stop_loss,
            take_profit=pos.take_profit,
            exit_reason=reason,
            duration_seconds=duration,
            gross_pnl=gross_pnl,
            spread_cost=spread_cost,
            slippage_cost=slip_cost,
            net_pnl=net_pnl,
            points_pnl=pts_pnl,
        )

        self.trade_history.append(trade)
        # Update risk drawdown guard
        self.risk_guard.drawdown_guard.record_trade_result(net_pnl, exit_time)
        if self.scalp_engine is not None:
            self.scalp_engine.reset_ticket(pos.position_id)

        return trade
