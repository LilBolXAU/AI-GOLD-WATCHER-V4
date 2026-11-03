"""
Unit tests for MT5OrderBridge safety invariants and retcode mapping.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from src.execution.mt5_order_bridge import MT5OrderBridge, ExecutionResult
from src.risk.risk_guard import ApprovedOrder
from src.strategies.base_strategy import OrderSide


def test_retcode_mapping():
    bridge = MT5OrderBridge.__new__(MT5OrderBridge)
    assert 10009 in bridge.RETCODE_MAP
    assert "DONE" in bridge.RETCODE_MAP[10009]
    assert "INVALID_STOPS" in bridge.RETCODE_MAP[10016]


@patch("MetaTrader5.initialize", return_value=True)
@patch("MetaTrader5.account_info")
def test_reject_real_account(mock_account, mock_init):
    # Setup mock real account (trade_mode = 2 means REAL)
    mock_acc = MagicMock()
    mock_acc.trade_mode = 2
    mock_acc.login = 999999
    mock_account.return_value = mock_acc

    with pytest.raises(PermissionError, match="CRITICAL SAFETY VIOLATION"):
        MT5OrderBridge(symbol="XAUUSDm")


@patch("MetaTrader5.initialize", return_value=True)
@patch("MetaTrader5.account_info")
def test_volume_cap_enforced(mock_account, mock_init):
    mock_acc = MagicMock()
    mock_acc.trade_mode = 0  # DEMO
    mock_acc.trade_expert = True
    mock_acc.login = 434467985
    mock_acc.name = "DEMOBOT"
    mock_acc.balance = 50.0
    mock_account.return_value = mock_acc

    bridge = MT5OrderBridge(symbol="XAUUSDm")
    bridge.get_open_positions = MagicMock(return_value=[])

    # Attempt to send 0.05 lot (violates 0.01 lot safety cap)
    bad_order = ApprovedOrder(
        magic_number=400001,
        strategy_id="TREND_FOLLOWING",
        symbol="XAUUSDm",
        side=OrderSide.BUY,
        volume=0.05,
        entry_price=2650.0,
        stop_loss=2649.0,
        take_profit=2652.0,
        risk_usd=5.0,
        timestamp=datetime.now(timezone.utc),
    )

    result = bridge.send_market_order(bad_order)
    assert not result.success
    assert result.retcode == 10014
    assert "Volume safety cap" in result.retcode_description
