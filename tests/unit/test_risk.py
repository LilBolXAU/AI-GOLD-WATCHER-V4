"""
Unit tests for Financial & Risk Management Core (Stage 3).
"""

from datetime import datetime, timezone
import pytest

from src.data.models import SymbolSpec
from src.data.symbol_specs import DEFAULT_EXNESS_XAUUSD
from src.strategies.base_strategy import SignalCandidate, OrderSide
from src.scoring.signal_quality import ScoredSignal
from src.risk.pnl_calculator import calculate_gross_pnl, calculate_points_pnl
from src.risk.cost_calculator import calculate_spread_cost, calculate_slippage_cost, calculate_net_pnl
from src.risk.position_sizing import calculate_position_size
from src.risk.drawdown_guard import DrawdownGuard
from src.risk.kill_switch import KillSwitch
from src.risk.risk_guard import RiskGuard, ApprovedOrder


def test_pnl_and_points_math(symbol_spec: SymbolSpec):
    # Buy 0.01 lot from 2650.00 to 2652.00 -> $2.00 profit, 200 points
    gross = calculate_gross_pnl(2650.00, 2652.00, OrderSide.BUY, 0.01, symbol_spec)
    assert round(gross, 2) == 2.00

    pts = calculate_points_pnl(2650.00, 2652.00, OrderSide.BUY, symbol_spec)
    assert pts == 200

    # Spread cost for 20 points spread at 0.01 lot = $0.20
    spr_cost = calculate_spread_cost(20, 0.01, symbol_spec)
    assert round(spr_cost, 2) == 0.20


def test_position_sizing_within_budget(symbol_spec: SymbolSpec):
    # SL distance of 1.00 (100 points) on $50 balance with $1 risk budget
    vol, dollar_risk, is_allowed, reason = calculate_position_size(
        sl_distance=1.00,
        balance=50.0,
        spec=symbol_spec,
        target_risk_usd=1.00,
    )
    assert is_allowed is True
    assert vol == 0.01
    assert dollar_risk <= 1.00


def test_position_sizing_sl_too_wide_rejected(symbol_spec: SymbolSpec):
    # SL distance of 2.50 (250 points) -> at 0.01 lot minimum, dollar risk = $2.50 > $1.00 budget -> REJECT
    vol, dollar_risk, is_allowed, reason = calculate_position_size(
        sl_distance=2.50,
        balance=50.0,
        spec=symbol_spec,
        target_risk_usd=1.00,
    )
    assert is_allowed is False
    assert "exceeds" in reason


def test_drawdown_daily_limit_circuit_breaker():
    guard = DrawdownGuard(reference_balance=50.0, daily_loss_limit_usd=2.00)
    now = datetime.now(timezone.utc)

    # Initial state
    can, _ = guard.can_trade(now)
    assert can is True

    # Record cumulative loss of $2.50 (breaches $2.00 limit)
    guard.record_trade_result(net_pnl=-2.50, current_dt=now)
    can, reason = guard.can_trade(now)
    assert can is False
    assert "Daily loss circuit breaker" in reason


def test_drawdown_consecutive_loss_breaker():
    guard = DrawdownGuard(reference_balance=50.0, max_consecutive_losses=3)
    now = datetime.now(timezone.utc)

    guard.record_trade_result(net_pnl=-0.50, current_dt=now)
    guard.record_trade_result(net_pnl=-0.50, current_dt=now)
    assert guard.can_trade(now)[0] is True

    # 3rd consecutive loss
    guard.record_trade_result(net_pnl=-0.50, current_dt=now)
    can, reason = guard.can_trade(now)
    assert can is False
    assert "Consecutive loss" in reason


def test_risk_guard_mutual_exclusivity(symbol_spec: SymbolSpec):
    risk_guard = RiskGuard(spec=symbol_spec, reference_balance=50.0)
    now = datetime.now(timezone.utc)

    cand = SignalCandidate(
        strategy_id="TREND_FOLLOWING",
        timestamp=now,
        symbol="XAUUSDm",
        side=OrderSide.BUY,
        entry_price=2650.0,
        stop_loss=2649.0,
        take_profit=2652.5,
        raw_confidence=0.9,
    )
    scored = ScoredSignal(candidate=cand, total_score=80.0, passes_threshold=True)

    # First check: passes
    res1 = risk_guard.evaluate_signal(scored, current_spread=15, current_time=now)
    assert res1.is_approved is True
    assert isinstance(res1.order, ApprovedOrder)

    # Simulate position active
    risk_guard.active_position_count = 1

    # Second check: must be vetoed due to mutual exclusivity (max 1 position)
    res2 = risk_guard.evaluate_signal(scored, current_spread=15, current_time=now)
    assert res2.is_approved is False
    assert "Position limit reached" in res2.rejection_reason


def test_risk_guard_scale_in_break_even(symbol_spec: SymbolSpec):
    """Verify Pyramiding (Scale-in) allows 2nd entry ONLY when position 1 is risk-free at Break-Even."""
    from unittest.mock import MagicMock

    risk_guard = RiskGuard(spec=symbol_spec, reference_balance=50.0, allow_pyramiding=True, max_concurrent_positions=2)
    now = datetime.now(timezone.utc)

    # Signal 2: Another BUY setup
    cand = SignalCandidate(
        strategy_id="PULLBACK_CONTINUATION",
        timestamp=now,
        symbol="XAUUSDm",
        side=OrderSide.BUY,
        entry_price=2652.0,
        stop_loss=2651.0,
        take_profit=2654.0,
        raw_confidence=0.85,
    )
    scored = ScoredSignal(candidate=cand, total_score=78.0, passes_threshold=True)

    # Case A: Position 1 is NOT at Break-Even (entry: 2650.0, sl: 2648.5)
    pos_red = MagicMock()
    pos_red.side = OrderSide.BUY
    pos_red.entry_price = 2650.0
    pos_red.stop_loss = 2648.5
    pos_red.ticket = 101

    risk_guard.active_position_count = 1
    res_red = risk_guard.evaluate_signal(scored, current_spread=15, current_time=now, open_positions=[pos_red])
    assert res_red.is_approved is False
    assert "has not locked Break-Even yet" in res_red.rejection_reason

    # Case B: Position 1 HAS locked Break-Even (entry: 2650.0, sl: 2650.10)
    pos_green = MagicMock()
    pos_green.side = OrderSide.BUY
    pos_green.entry_price = 2650.0
    pos_green.stop_loss = 2650.10
    pos_green.ticket = 101

    res_green = risk_guard.evaluate_signal(scored, current_spread=15, current_time=now, open_positions=[pos_green])
    assert res_green.is_approved is True
    assert res_green.order is not None

    # Case C: Scale-in direction conflict (Position 1 is SELL, Signal is BUY)
    pos_conflict = MagicMock()
    pos_conflict.side = OrderSide.SELL
    pos_conflict.entry_price = 2655.0
    pos_conflict.stop_loss = 2654.0

    res_conf = risk_guard.evaluate_signal(scored, current_spread=15, current_time=now, open_positions=[pos_conflict])
    assert res_conf.is_approved is False
    assert "Scale-in direction conflict" in res_conf.rejection_reason

