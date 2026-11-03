"""
Unit tests for Virtual Position, Paper Broker, and Trade Lifecycle.
"""

from datetime import datetime, timedelta, timezone
import pytest

from src.data.models import BarData, SymbolSpec
from src.strategies.base_strategy import OrderSide
from src.risk.risk_guard import ApprovedOrder, RiskGuard
from src.execution.paper_broker import PaperBroker
from src.execution.paper_trade_manager import PaperTradeManager
from src.execution.trade_lifecycle import ExitReason


def test_paper_broker_fill_slippage(symbol_spec: SymbolSpec):
    broker = PaperBroker(spec=symbol_spec)
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    order = ApprovedOrder(
        magic_number=400001,
        strategy_id="TREND_FOLLOWING",
        symbol="XAUUSDm",
        side=OrderSide.BUY,
        volume=0.01,
        entry_price=2650.00,
        stop_loss=2649.00,
        take_profit=2652.50,
        risk_usd=1.00,
        timestamp=now,
    )

    # Buy order fills at Ask = entry_price + half_spread + slippage
    pos = broker.execute_fill(order, current_spread_pts=20, fill_time=now, slippage_pts=2)
    assert pos.volume == 0.01
    assert pos.side == OrderSide.BUY
    # 20 pts spread = 0.20 price; half is 0.10; slippage 2 pts = 0.02
    assert round(pos.entry_price, 2) == 2650.12


def test_paper_trade_manager_tp_hit(symbol_spec: SymbolSpec):
    risk_guard = RiskGuard(spec=symbol_spec, reference_balance=50.0)
    mgr = PaperTradeManager(spec=symbol_spec, risk_guard=risk_guard)
    t0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    order = ApprovedOrder(
        magic_number=400001,
        strategy_id="TREND_FOLLOWING",
        symbol="XAUUSDm",
        side=OrderSide.BUY,
        volume=0.01,
        entry_price=2650.00,
        stop_loss=2649.00,
        take_profit=2652.00,
        risk_usd=1.00,
        timestamp=t0,
    )

    mgr.open_position(order, current_spread_pts=15, fill_time=t0)
    assert mgr.active_position is not None
    assert risk_guard.active_position_count == 1

    # Next bar spikes High to 2653.00, hitting TP (2652.00)
    t1 = t0 + timedelta(minutes=5)
    bar = BarData(
        timestamp=t1,
        open=2650.50,
        high=2653.00,
        low=2650.20,
        close=2652.80,
        tick_volume=120,
        spread=15,
    )

    closed = mgr.on_bar_update(bar)
    assert closed is not None
    assert closed.exit_reason == ExitReason.TAKE_PROFIT
    assert closed.net_pnl > 0.0
    assert mgr.active_position is None
    assert risk_guard.active_position_count == 0


def test_paper_trade_manager_sl_hit(symbol_spec: SymbolSpec):
    risk_guard = RiskGuard(spec=symbol_spec, reference_balance=50.0)
    mgr = PaperTradeManager(spec=symbol_spec, risk_guard=risk_guard)
    t0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    order = ApprovedOrder(
        magic_number=400002,
        strategy_id="TREND_FOLLOWING",
        symbol="XAUUSDm",
        side=OrderSide.BUY,
        volume=0.01,
        entry_price=2650.00,
        stop_loss=2649.00,
        take_profit=2652.50,
        risk_usd=1.00,
        timestamp=t0,
    )

    mgr.open_position(order, current_spread_pts=15, fill_time=t0)

    # Next bar drops Low to 2648.50, hitting SL (2649.00)
    t1 = t0 + timedelta(minutes=5)
    bar = BarData(
        timestamp=t1,
        open=2649.50,
        high=2649.80,
        low=2648.50,
        close=2648.70,
        tick_volume=120,
        spread=15,
    )

    closed = mgr.on_bar_update(bar)
    assert closed is not None
    assert closed.exit_reason == ExitReason.STOP_LOSS
    assert closed.net_pnl < 0.0
    assert mgr.active_position is None
