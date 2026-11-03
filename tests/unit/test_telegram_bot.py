"""
Unit tests for TelegramNotifier formatting and dispatching.
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import pytest

from src.monitoring.telegram_bot import TelegramNotifier
from src.risk.risk_guard import ApprovedOrder
from src.strategies.base_strategy import OrderSide


def test_telegram_disabled_when_empty_creds():
    notifier = TelegramNotifier(bot_token="", chat_id="")
    assert not notifier.enabled
    assert not notifier.send_message("Hello")


@patch("requests.post")
def test_send_message_success(mock_post):
    mock_post.return_value.status_code = 200
    notifier = TelegramNotifier(bot_token="123456:ABC-DEF", chat_id="987654321", enabled=True)
    assert notifier.enabled

    result = notifier.send_message("Test message")
    assert result
    assert mock_post.called
    args, kwargs = mock_post.call_args
    assert "https://api.telegram.org/bot123456:ABC-DEF/sendMessage" in args[0]
    assert kwargs["json"]["chat_id"] == "987654321"


@patch("requests.post")
def test_notify_order_opened(mock_post):
    mock_post.return_value.status_code = 200
    notifier = TelegramNotifier(bot_token="123456:ABC-DEF", chat_id="987654321", enabled=True)

    order = ApprovedOrder(
        magic_number=400001,
        strategy_id="TREND_FOLLOWING",
        symbol="XAUUSDm",
        side=OrderSide.BUY,
        volume=0.01,
        entry_price=2650.0,
        stop_loss=2649.0,
        take_profit=2652.0,
        risk_usd=1.0,
        timestamp=datetime.now(timezone.utc),
    )

    result = notifier.notify_order_opened(
        order=order,
        fill_price=2650.05,
        confidence_score=75.0,
        regime="BULL_TRENDING",
        ticket=1234567,
        ai_prob=0.72,
    )
    assert result
    assert "NEW TRADE EXECUTED" in mock_post.call_args[1]["json"]["text"]
    assert "AI Win Probability: <b>72.0%</b>" in mock_post.call_args[1]["json"]["text"]


@patch("requests.post")
def test_notify_order_closed(mock_post):
    mock_post.return_value.status_code = 200
    notifier = TelegramNotifier(bot_token="123456:ABC-DEF", chat_id="987654321", enabled=True)

    # 1. TP Win test
    result = notifier.notify_order_closed(
        trade_id="trd_001",
        symbol="XAUUSDm",
        side="BUY",
        entry_price=2650.0,
        exit_price=2656.0,
        net_pnl=600.00,
        exit_reason="TAKE_PROFIT (Chốt lời TP)",
        balance=10600.00,
        ticket=1234567,
        equity=10600.00,
    )
    assert result
    text = mock_post.call_args[1]["json"]["text"]
    assert "CHỐT LỜI THÀNH CÔNG (TP WIN)" in text
    assert "+600.00 USD" in text
    assert "SỐ DƯ HIỆN TẠI (BALANCE)" in text
    assert "10,600.00" in text

    # 2. SL Hit test
    result_sl = notifier.notify_order_closed(
        trade_id="trd_002",
        symbol="XAUUSDm",
        side="SELL",
        entry_price=2650.0,
        exit_price=2654.0,
        net_pnl=-400.00,
        exit_reason="STOP_LOSS (Cắt lỗ bảo vệ vốn)",
        balance=9600.00,
        ticket=1234568,
        equity=9600.00,
    )
    assert result_sl
    text_sl = mock_post.call_args[1]["json"]["text"]
    assert "ĐÓNG LỆNH CẮT LỖ (SL HIT)" in text_sl
    assert "-400.00 USD" in text_sl
    assert "SỐ DƯ HIỆN TẠI (BALANCE)" in text_sl
    assert "9,600.00" in text_sl

    # 3. SL Win / Break-even runner test
    result_be = notifier.notify_order_closed(
        trade_id="trd_003",
        symbol="XAUUSDm",
        side="BUY",
        entry_price=2650.0,
        exit_price=2651.5,
        net_pnl=150.00,
        exit_reason="TRAILING_STOP_SL_WIN (SL Dương)",
        balance=10750.00,
        ticket=1234569,
        equity=10750.00,
    )
    assert result_be
    text_be = mock_post.call_args[1]["json"]["text"]
    assert "HÒA VỐN / SL DƯƠNG THÀNH CÔNG" in text_be
    assert "+150.00 USD" in text_be
    assert "10,750.00" in text_be


@patch("requests.get")
@patch("requests.post")
def test_process_incoming_status_command(mock_post, mock_get):
    mock_post.return_value.status_code = 200
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "ok": True,
        "result": [
            {
                "update_id": 101,
                "message": {
                    "text": "/status",
                    "chat": {"id": 987654321},
                },
            }
        ],
    }

    notifier = TelegramNotifier(bot_token="123456:ABC-DEF", chat_id="987654321", enabled=True)
    notifier.process_incoming_commands(context={})

    assert mock_post.called
    assert "TRẠNG THÁI HỆ THỐNG" in mock_post.call_args[1]["json"]["text"]


@patch("requests.get")
@patch("requests.post")
def test_process_incoming_start_command(mock_post, mock_get):
    mock_post.return_value.status_code = 200
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "ok": True,
        "result": [
            {
                "update_id": 102,
                "message": {
                    "text": "/start",
                    "chat": {"id": 987654321},
                    "from": {"first_name": "Luna"},
                },
            }
        ],
    }

    notifier = TelegramNotifier(bot_token="123456:ABC-DEF", chat_id="987654321", enabled=True)
    notifier.process_incoming_commands(context={})

    assert mock_post.called
    text = mock_post.call_args[1]["json"]["text"]
    assert "Xin chào <b>Luna</b>" in text
    assert "/status" in text
    assert "/balance" in text
    assert "/positions" in text
    assert "/pause" in text
    assert "/resume" in text
    assert "/close" in text
    assert "/help" in text
    assert "4.0%" in text
    assert "6.0%" in text


@patch("requests.get")
@patch("requests.post")
def test_process_incoming_help_command(mock_post, mock_get):
    mock_post.return_value.status_code = 200
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "ok": True,
        "result": [
            {
                "update_id": 103,
                "message": {
                    "text": "/help",
                    "chat": {"id": 987654321},
                },
            }
        ],
    }

    notifier = TelegramNotifier(bot_token="123456:ABC-DEF", chat_id="987654321", enabled=True)
    notifier.process_incoming_commands(context={})

    assert mock_post.called
    text = mock_post.call_args[1]["json"]["text"]
    assert "DANH SÁCH LỆNH ĐIỀU KHIỂN" in text
    assert "/close" in text
    assert "4.0%" in text
    assert "6.0%" in text


@patch("requests.post")
def test_notify_news_upcoming(mock_post):
    mock_post.return_value.status_code = 200
    notifier = TelegramNotifier(bot_token="123456:ABC-DEF", chat_id="987654321", enabled=True)

    from src.risk.news_guard import EconomicNewsEvent
    event = EconomicNewsEvent(
        title="CPI m/m",
        country="USD",
        impact="High",
        event_time_utc=datetime(2026, 11, 3, 13, 30, tzinfo=timezone.utc),
        forecast="0.3%",
        previous="0.2%",
    )

    res = notifier.notify_news_upcoming(event=event, minutes_until=28)
    assert res is True
    assert mock_post.called
    text = mock_post.call_args[1]["json"]["text"]
    assert "CẢNH BÁO TIN ĐỎ KINH TẾ USD" in text
    assert "CPI m/m" in text
    assert "28 phút" in text
    assert "NEWS BLACKOUT" in text


@patch("requests.post")
def test_multiple_chat_ids_broadcast(mock_post):
    mock_post.return_value.status_code = 200
    notifier = TelegramNotifier(bot_token="123456:ABC-DEF", chat_id="7263316819, 987654321", enabled=True)
    assert len(notifier.chat_ids) == 2
    assert "7263316819" in notifier.chat_ids
    assert "987654321" in notifier.chat_ids

    mock_post.reset_mock()
    res = notifier.send_message("Broadcast message")
    assert res is True
    assert mock_post.call_count == 2




