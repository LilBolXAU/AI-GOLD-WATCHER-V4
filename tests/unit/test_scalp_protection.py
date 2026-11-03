"""
Unit tests for ScalpProtectionEngine (Auto Break-Even and Trailing Stop).
"""

from unittest.mock import MagicMock
import pytest

from src.execution.scalp_protection import ScalpProtectionEngine, ScalpAction


def test_buy_break_even_trigger():
    engine = ScalpProtectionEngine(be_trigger_ratio=0.50, be_buffer_usd=0.10)

    # Position: BUY @ 2650.0, SL: 2648.0, TP: 2653.0 (distance = 3.0, 50% = 1.5 -> trigger at 2651.50)
    pos = MagicMock()
    pos.ticket = 1001
    pos.type = 0  # BUY
    pos.price_open = 2650.0
    pos.sl = 2648.0
    pos.tp = 2653.0

    # 1. Price at 2651.0 (only 33% progress) -> No action
    pos.price_current = 2651.0
    act = engine.evaluate_position(pos)
    assert act is None

    # 2. Price reaches 2651.55 (>= 50% progress) -> Triggers BREAK_EVEN
    pos.price_current = 2651.55
    act = engine.evaluate_position(pos)
    assert act is not None
    assert act.action_type == "BREAK_EVEN"
    assert act.new_sl == 2650.10
    assert act.ticket == 1001

    # 3. Simulate position modified with new SL:
    pos.sl = 2650.10
    # Next tick at 2651.60 -> should not duplicate BREAK_EVEN
    pos.price_current = 2651.60
    act2 = engine.evaluate_position(pos)
    assert act2 is None


def test_sell_break_even_trigger():
    engine = ScalpProtectionEngine(be_trigger_ratio=0.50, be_buffer_usd=0.10)

    # Position: SELL @ 2650.0, SL: 2652.0, TP: 2647.0 (distance = 3.0, 50% = 1.5 -> trigger at 2648.50)
    pos = MagicMock()
    pos.ticket = 1002
    pos.type = 1  # SELL
    pos.price_open = 2650.0
    pos.sl = 2652.0
    pos.tp = 2647.0

    # 1. Price at 2649.0 (only 33% progress) -> No action
    pos.price_current = 2649.0
    act = engine.evaluate_position(pos)
    assert act is None

    # 2. Price reaches 2648.40 (>= 50% progress) -> Triggers BREAK_EVEN
    pos.price_current = 2648.40
    act = engine.evaluate_position(pos)
    assert act is not None
    assert act.action_type == "BREAK_EVEN"
    assert act.new_sl == 2649.90
    assert act.ticket == 1002


def test_trailing_stop_after_break_even():
    engine = ScalpProtectionEngine(
        be_trigger_ratio=0.50,
        be_buffer_usd=0.10,
        trailing_trigger_ratio=0.70,
        trailing_step_usd=0.20,
    )

    pos = MagicMock()
    pos.ticket = 1003
    pos.type = 0  # BUY
    pos.price_open = 2650.0
    pos.sl = 2648.0
    pos.tp = 2654.0  # distance = 4.0, 50% = 2.0 (2652.0), 70% = 2.8 (2652.80)

    # 1. Reach BE
    pos.price_current = 2652.10
    act_be = engine.evaluate_position(pos)
    assert act_be.action_type == "BREAK_EVEN"
    pos.sl = act_be.new_sl  # 2650.10

    # 2. Advance to 75% (2653.00) -> Triggers Trailing Stop
    pos.price_current = 2653.00
    act_trail = engine.evaluate_position(pos)
    assert act_trail is not None
    assert act_trail.action_type == "TRAILING_STOP"
    assert act_trail.new_sl > pos.sl


def test_trailing_runner_trigger_and_tp_expansion():
    engine = ScalpProtectionEngine(
        enable_trailing_runner=True,
        runner_trigger_ratio=0.85,
        runner_tp_expansion_usd=5.0,
        runner_trailing_dist_usd=0.80,
    )

    pos = MagicMock()
    pos.ticket = 2001
    pos.type = 0  # BUY
    pos.price_open = 2650.0
    pos.sl = 2648.0
    pos.tp = 2654.0  # distance = 4.0, 85% = 3.4 (2653.40)

    # 1. Price hits 2653.50 (87.5% progress >= 85%) -> Triggers TRAILING_RUNNER
    pos.price_current = 2653.50
    act_runner = engine.evaluate_position(pos)
    assert act_runner is not None
    assert act_runner.action_type == "TRAILING_RUNNER"
    assert act_runner.new_tp == 2659.0  # 2654.0 + 5.0 expansion
    assert act_runner.new_sl >= 2650.80  # Guaranteed profit above entry
    assert act_runner.new_sl == round(2653.50 - 0.80, 3)  # 2652.70


def test_sell_trailing_runner_trigger():
    engine = ScalpProtectionEngine(
        enable_trailing_runner=True,
        runner_trigger_ratio=0.85,
        runner_tp_expansion_usd=5.0,
        runner_trailing_dist_usd=0.80,
    )

    pos = MagicMock()
    pos.ticket = 2002
    pos.type = 1  # SELL
    pos.price_open = 2650.0
    pos.sl = 2652.0
    pos.tp = 2646.0  # distance = 4.0, 85% = 3.4 (2646.60)

    # 1. Price drops to 2646.50 (87.5% progress >= 85%) -> Triggers TRAILING_RUNNER
    pos.price_current = 2646.50
    act_runner = engine.evaluate_position(pos)
    assert act_runner is not None
    assert act_runner.action_type == "TRAILING_RUNNER"
    assert act_runner.new_tp == 2641.0  # 2646.0 - 5.0 expansion
    assert act_runner.new_sl <= 2649.20  # Guaranteed profit locked below entry
    assert act_runner.new_sl == round(2646.50 + 0.80, 3)  # 2647.30


def test_reset_ticket():
    engine = ScalpProtectionEngine()
    pos = MagicMock()
    pos.ticket = 999
    pos.type = 0
    pos.price_open = 100.0
    pos.sl = 98.0
    pos.tp = 104.0
    pos.price_current = 102.50

    # Trigger BE
    act = engine.evaluate_position(pos)
    assert act is not None
    assert 999 in engine._break_even_tickets

    # Reset
    engine.reset_ticket(999)
    assert 999 not in engine._break_even_tickets
