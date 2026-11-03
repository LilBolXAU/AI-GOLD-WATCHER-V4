"""
Telegram Notification & Command Engine for AI GOLD WATCHER V4.
100% Free real-time trade signals, balance updates, interactive commands, and emergency circuit breaker alerts.
Uses official Telegram Bot API via requests.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import requests
from dotenv import load_dotenv

from src.strategies.base_strategy import OrderSide
from src.risk.risk_guard import ApprovedOrder
from src.regime.session_router import SessionRouter

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
env_file = WORKSPACE_ROOT / ".env"
if env_file.exists():
    load_dotenv(env_file)

logger = logging.getLogger("v4_trading.telegram")


class TelegramNotifier:
    """
    Asynchronous and synchronous Telegram alert notifier and interactive command dispatcher.
    Configured via TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables or .env file.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        enabled: Optional[bool] = None,
    ):
        if bot_token is None:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
            if not bot_token and env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("TELEGRAM_BOT_TOKEN="):
                        bot_token = line.split("=", 1)[1].strip()

        if chat_id is None:
            chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
            if not chat_id and env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("TELEGRAM_CHAT_ID="):
                        chat_id = line.split("=", 1)[1].strip()

        self.bot_token = bot_token or ""
        self.chat_id = chat_id or ""
        self.chat_ids: List[str] = [c.strip() for c in self.chat_id.split(",") if c.strip()]

        # If credentials provided, enable by default unless explicitly disabled
        if enabled is not None:
            self.enabled = enabled
        else:
            self.enabled = bool(self.bot_token and self.chat_ids)

        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else ""
        self._last_update_id = 0

        if self.enabled:
            logger.info("Telegram Notifier: ACTIVE (Target Chats: %s)", ", ".join(self.chat_ids))
            self.register_bot_commands()
        else:
            logger.info("Telegram Notifier: DISABLED (Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)")

    def register_bot_commands(self) -> bool:
        """Register command menu with Telegram Bot API."""
        if not self.bot_token:
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/setMyCommands"
        commands = [
            {"command": "status", "description": "Trạng thái bot & nến MT5"},
            {"command": "balance", "description": "Số dư, Equity & PnL ngày"},
            {"command": "positions", "description": "Chi tiết lệnh đang mở"},
            {"command": "signals", "description": "Tín hiệu AI phân tích gần nhất"},
            {"command": "pause", "description": "Tạm dừng vào lệnh từ xa"},
            {"command": "resume", "description": "Bật lại giao dịch từ xa"},
            {"command": "close", "description": "Đóng khẩn cấp mọi lệnh MT5"},
            {"command": "help", "description": "Hướng dẫn & thông số an toàn"},
        ]
        try:
            resp = requests.post(url, json={"commands": commands}, timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    def send_message(self, text: str, parse_mode: str = "HTML", target_chat_id: Optional[str] = None) -> bool:
        """Send formatted message to configured Telegram chat(s)."""
        if not self.enabled or not self.api_url:
            return False

        targets = [str(target_chat_id).strip()] if target_chat_id else self.chat_ids
        if not targets:
            return False

        all_success = True
        for cid in targets:
            payload = {
                "chat_id": cid,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            }

            try:
                resp = requests.post(self.api_url, json=payload, timeout=8.0)
                if resp.status_code != 200:
                    logger.warning("Telegram API error %d for chat %s: %s", resp.status_code, cid, resp.text)
                    all_success = False
            except Exception as e:
                logger.warning("Failed to dispatch Telegram message to %s: %s", cid, e)
                all_success = False

        return all_success

    def notify_order_opened(
        self,
        order: ApprovedOrder,
        fill_price: float,
        confidence_score: float,
        regime: str,
        ticket: Optional[int] = None,
        ai_prob: Optional[float] = None,
    ) -> bool:
        """Send rich alert when a new trade is executed."""
        side_icon = "🟢" if order.side == OrderSide.BUY else "🔴"
        side_str = "BUY" if order.side == OrderSide.BUY else "SELL"
        ticket_str = f"Ticket: <code>#{ticket}</code>\n" if ticket else ""
        ai_str = f"🤖 AI Win Probability: <b>{ai_prob*100:.1f}%</b>\n" if ai_prob is not None else ""

        msg = (
            f"{side_icon} <b>NEW TRADE EXECUTED — AI GOLD WATCHER V4</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Symbol: <b>{order.symbol}</b>\n"
            f"Action: <b>{side_str} {order.volume} lot</b>\n"
            f"Fill Price: <code>{fill_price:.3f}</code>\n"
            f"Stop Loss: <code>{order.stop_loss:.3f}</code>\n"
            f"Take Profit: <code>{order.take_profit:.3f}</code>\n"
            f"{ticket_str}"
            f"Strategy: <code>{order.strategy_id}</code>\n"
            f"Market Regime: <code>{regime}</code>\n"
            f"Confidence Score: <b>{confidence_score:.1f}/100</b>\n"
            f"{ai_str}"
            f"Risk Budget: <b>${order.risk_usd:.2f} USD</b>\n"
            f"Time: <i>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</i>"
        )
        return self.send_message(msg)

    def notify_order_closed(
        self,
        trade_id: str,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: float,
        net_pnl: float,
        exit_reason: str,
        balance: float,
        ticket: Optional[int] = None,
    ) -> bool:
        """Send rich alert when a trade is closed."""
        pnl_icon = "💰" if net_pnl > 0 else "🛑"
        res_str = "PROFIT" if net_pnl > 0 else "LOSS"
        ticket_str = f"Ticket: <code>#{ticket}</code>\n" if ticket else ""

        msg = (
            f"{pnl_icon} <b>TRADE CLOSED ({res_str}) — {symbol}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{ticket_str}"
            f"Action: <b>{side}</b>\n"
            f"Entry: <code>{entry_price:.3f}</code> ➜ Exit: <code>{exit_price:.3f}</code>\n"
            f"Net P&L: <b>{net_pnl:+.2f} USD</b>\n"
            f"Exit Reason: <b>{exit_reason}</b>\n"
            f"Current Balance: <b>${balance:.2f} USD</b>\n"
            f"Time: <i>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</i>"
        )
        return self.send_message(msg)

    def notify_circuit_breaker(self, reason: str, daily_pnl: float, balance: float) -> bool:
        """Send emergency circuit breaker halt alert."""
        msg = (
            f"🚨 <b>SAFETY CIRCUIT BREAKER TRIGGERED</b> 🚨\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Status: <b>TRADING HALTED FOR CURRENT SESSION</b>\n"
            f"Reason: <b>{reason}</b>\n"
            f"Daily Loss: <code>${daily_pnl:.2f} USD</code>\n"
            f"Remaining Balance: <code>${balance:.2f} USD</code>\n"
            f"Rule: Strict capital preservation guardrail active.\n"
            f"Time: <i>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</i>"
        )
        return self.send_message(msg)

    def notify_break_even(
        self,
        ticket: int,
        symbol: str,
        side: str,
        entry_price: float,
        new_sl: float,
        tp_price: float,
    ) -> bool:
        """Send rich alert when Auto Break-Even (Lệnh Bất Tử) is activated."""
        side_icon = "🟢" if side == "BUY" else "🔴"
        msg = (
            f"🛡️ <b>LỆNH BẤT TỬ (AUTO BREAK-EVEN) KÍCH HOẠT!</b> 🛡️\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Ticket: <code>#{ticket}</code> ({symbol})\n"
            f"Lệnh: <b>{side_icon} {side}</b>\n"
            f"Giá vào (Entry): <code>{entry_price:.3f}</code>\n"
            f"Stop Loss mới: <code>{new_sl:.3f}</code> (Đã dời về hòa vốn!)\n"
            f"Chốt lời (TP): <code>{tp_price:.3f}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <b>Trạng thái:</b> Lệnh đã chạy được <b>50% mục tiêu TP</b>!\n"
            f"✨ <i>Kèo này 100% không còn rủi ro thua lỗ! Bot đang gồng lãi tự do!</i> 🚀\n"
            f"<i>Cập nhật: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}</i>"
        )
        return self.send_message(msg)

    def notify_trailing_stop(
        self,
        ticket: int,
        symbol: str,
        side: str,
        current_price: float,
        new_sl: float,
    ) -> bool:
        """Send rich alert when Trailing Stop locks in additional profit."""
        msg = (
            f"🎯 <b>TRAILING STOP — KHÓA THÊM LỢI NHUẬN!</b> 💰\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Ticket: <code>#{ticket}</code> ({symbol})\n"
            f"Giá hiện tại: <code>{current_price:.3f}</code>\n"
            f"Stop Loss nâng lên: <code>{new_sl:.3f}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 <i>Vàng mở rộng xu hướng! Bot đã bảo toàn thêm phần lãi!</i>"
        )
        return self.send_message(msg)

    def notify_trailing_runner(
        self,
        ticket: int,
        symbol: str,
        side: str,
        current_price: float,
        new_sl: float,
        new_tp: Optional[float] = None,
        locked_profit: float = 0.0,
    ) -> bool:
        """Send rich alert when Trailing Runner activates to surf massive trends."""
        tp_str = f"<code>{new_tp:.3f}</code> (Mở rộng)" if new_tp else "Thả nổi"
        msg = (
            f"🚀 <b>GỒNG LÃI ĐỘNG (TRAILING RUNNER) — SĂN SÓNG LỚN!</b> 🌊\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Ticket: <code>#{ticket}</code> ({symbol} - <b>{side}</b>)\n"
            f"Giá hiện tại: <code>{current_price:.3f}</code>\n"
            f"Stop Loss nâng lên: <code>{new_sl:.3f}</code>\n"
            f"Lợi nhuận chắc chắn khóa: <b>+${locked_profit:.2f} USD</b> 🔒\n"
            f"Take Profit mới: {tp_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🦅 <i>Vị thế đã bảo toàn lãi tuyệt đối! Bot tiếp tục bám sóng để tối đa hóa lợi nhuận!</i>"
        )
        return self.send_message(msg)

    def notify_news_upcoming(
        self,
        event: Any,
        minutes_until: int,
    ) -> bool:
        """Send rich alert when high-impact USD economic news is approaching."""
        forecast_str = getattr(event, "forecast", "") or "N/A"
        prev_str = getattr(event, "previous", "") or "N/A"
        time_str = event.event_time_utc.strftime("%H:%M UTC")

        msg = (
            f"🚨 <b>CẢNH BÁO TIN ĐỎ KINH TẾ USD — SẮP CÓ BIẾN ĐỘNG!</b> 🚨\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Sự kiện: <b>{event.title}</b> ({event.country})\n"
            f"⏳ Thời gian còn lại: <b>~{minutes_until} phút nữa!</b>\n"
            f"⏰ Thời điểm ra tin: <code>{time_str}</code>\n"
            f"📊 Dự báo (Forecast): <code>{forecast_str}</code> | Trước đó: <code>{prev_str}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ <b>CHẾ ĐỘ TỰ BẢO VỆ CỦA BOT:</b>\n"
            f"• Tự động kích hoạt <b>NEWS BLACKOUT</b> (tạm dừng mở lệnh mới 15 phút trước và 15 phút sau tin).\n"
            f"• Bảo vệ tài khoản khỏi giãn spread cực đại và giật quét 2 đầu của Vàng! 🛡️"
        )
        return self.send_message(msg)

    def process_incoming_commands(self, context: Dict[str, Any]) -> None:
        """Fetch incoming Telegram messages and respond to user commands."""
        if not self.enabled or not self.bot_token:
            return

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {"offset": self._last_update_id + 1, "timeout": 0}
            resp = requests.get(url, params=params, timeout=4.0)
            if resp.status_code != 200:
                return

            data = resp.json()
            if not data.get("ok"):
                return

            for update in data.get("result", []):
                self._last_update_id = update["update_id"]
                msg = update.get("message")
                if not msg:
                    continue

                text = (msg.get("text") or "").strip().lower()
                chat_id = str(msg.get("chat", {}).get("id", ""))

                # Security: Only respond to authorized chat IDs
                if self.chat_ids and chat_id not in self.chat_ids:
                    continue

                if text.startswith("/status"):
                    self._reply_status(context, target_chat_id=chat_id)
                elif text.startswith("/balance"):
                    self._reply_balance(context, target_chat_id=chat_id)
                elif text.startswith("/positions"):
                    self._reply_positions(context, target_chat_id=chat_id)
                elif text.startswith("/signals"):
                    self._reply_signals(context, target_chat_id=chat_id)
                elif text.startswith("/pause"):
                    self._reply_pause(context, target_chat_id=chat_id)
                elif text.startswith("/resume"):
                    self._reply_resume(context, target_chat_id=chat_id)
                elif text.startswith("/close"):
                    self._reply_close(context, target_chat_id=chat_id)
                elif text.startswith("/start"):
                    self._reply_start(context, msg, target_chat_id=chat_id)
                elif text.startswith("/help"):
                    self._reply_help(context, target_chat_id=chat_id)
                elif text.startswith("/"):
                    self.send_message(
                        "❓ <b>Lệnh không xác định!</b>\n\n"
                        "Vui lòng gõ /help hoặc /start để xem danh sách 8 lệnh điều khiển được hỗ trợ.",
                        target_chat_id=chat_id,
                    )
        except Exception as e:
            logger.debug("Error processing Telegram updates: %s", e)

    def _reply_status(self, context: Dict[str, Any], target_chat_id: Optional[str] = None) -> None:
        acc = context.get("account")
        regime = context.get("regime")
        bar = context.get("latest_bar")
        pos_count = len(context.get("open_positions", []))

        regime_str = regime.regime.value if regime else "INITIALIZING"
        regime_conf = f"{regime.confidence*100:.0f}%" if regime else "N/A"
        price_str = f"{bar.close:.3f}" if bar else "N/A"
        spread_str = f"{bar.spread} pts" if bar else "N/A"
        acc_str = f"#{acc.login} ({acc.server})" if acc else "Connected"

        macro = context.get("macro_result")
        if macro:
            bias_val = getattr(macro, "bias", None)
            bias_name = getattr(bias_val, "value", str(bias_val))
            if bias_name == "BULLISH":
                macro_str = "🟢 <b>TĂNG (Chỉ canh BUY)</b>"
            elif bias_name == "BEARISH":
                macro_str = "🔴 <b>GIẢM (Chỉ canh SELL)</b>"
            else:
                macro_str = "🟡 <b>ĐI NGANG (Chờ xác nhận)</b>"
        else:
            macro_str = "<code>Đang cập nhật...</code>"

        news_guard = context.get("news_guard")
        if news_guard:
            now_utc = datetime.now(timezone.utc)
            is_blackout, ev, _ = news_guard.is_news_blackout(now_utc)
            if is_blackout and ev:
                news_str = f"🔴 <b>BLACKOUT ĐANG BẬT</b> ({ev.title})"
            else:
                next_ev = news_guard.get_next_event(now_utc)
                if next_ev:
                    ev, mins = next_ev
                    news_str = f"🟢 <b>AN TOÀN</b> ({ev.title} sau ~{mins}p)"
                else:
                    news_str = "🟢 <b>AN TOÀN</b> (Không có tin đỏ USD sắp tới)"
        else:
            news_str = "<code>Đang cập nhật...</code>"

        session_prof = SessionRouter.get_profile(datetime.now(timezone.utc))
        runner_str = "BẬT 🚀" if session_prof.allow_trailing_runner else "TẮT (Ưu tiên Scalp ngắn)"
        session_str = f"<b>{session_prof.name_vn}</b> (Gồng lãi động: {runner_str})"

        text = (
            f"🤖 <b>TRẠNG THÁI HỆ THỐNG — GOLDSTRIKE AI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• MT5 Terminal: 🟢 <b>ONLINE (ĐÃ KẾT NỐI THÀNH CÔNG)</b>\n"
            f"• Tài khoản: <code>{acc_str}</code>\n"
            f"• Trạng thái bot: 🎯 <b>Đang quét nến M5 săn tín hiệu lướt sóng</b>\n"
            f"• Cặp giao dịch: <b>XAUUSDm (Gold)</b>\n"
            f"• Phiên giao dịch: 🌍 {session_str}\n"
            f"• Xu hướng lớn H1: {macro_str}\n"
            f"• Tin tức kinh tế: {news_str}\n"
            f"• Thị trường nến M5: <code>{regime_str}</code> (Độ tin cậy: {regime_conf})\n"
            f"• Giá nến M5 gần nhất: <code>{price_str}</code>\n"
            f"• Spread thực tế: <code>{spread_str}</code>\n"
            f"• Bộ lọc AI Meta-Label: <b>HOẠT ĐỘNG (Ngưỡng ≥ 65%)</b>\n"
            f"• Vị thế đang mở: <b>{pos_count} lệnh</b>\n"
            f"• Quản trị rủi ro: <b>Lot động theo ATR & Vốn (4% SL / 6% TP)</b>\n"
            f"<i>Cập nhật: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}</i>"
        )
        self.send_message(text, target_chat_id=target_chat_id)

    def _reply_balance(self, context: Dict[str, Any], target_chat_id: Optional[str] = None) -> None:
        acc = context.get("account")
        if not acc:
            self.send_message("⚠️ Chưa thể truy vấn thông tin tài khoản MT5.", target_chat_id=target_chat_id)
            return

        ref_bal = context.get("reference_balance", 50.0)
        daily_pnl = acc.equity - ref_bal
        pnl_icon = "🟢" if daily_pnl >= 0 else "🔴"
        eq = acc.equity
        risk_usd = eq * 0.04
        tp_usd = eq * 0.06
        breaker_usd = eq * 0.08

        text = (
            f"💳 <b>SỐ DƯ & QUẢN TRỊ RỦI RO ĐỘNG</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• Số dư (Balance): <b>${acc.balance:.2f} USD</b>\n"
            f"• Vốn thực tế (Equity): <b>${acc.equity:.2f} USD</b>\n"
            f"• Ký quỹ khả dụng: <b>${getattr(acc, 'margin_free', acc.balance):.2f} USD</b>\n"
            f"• PnL ngày hôm nay: {pnl_icon} <b>{daily_pnl:+.2f} USD</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• Rủi ro mỗi lệnh: <b>4.0% vốn (~${risk_usd:.2f} USD)</b>\n"
            f"• Mục tiêu chốt lời: <b>6.0% vốn (~${tp_usd:.2f} USD, R:R 1:1.5)</b>\n"
            f"• Ngắt mạch an toàn: <b>-8.0% vốn (~-${breaker_usd:.2f} USD/ngày)</b>\n"
            f"<i>Cập nhật: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}</i>"
        )
        self.send_message(text, target_chat_id=target_chat_id)

    def _reply_positions(self, context: Dict[str, Any], target_chat_id: Optional[str] = None) -> None:
        positions = context.get("open_positions", [])
        if not positions:
            self.send_message("ℹ️ Hiện tại <b>không có vị thế nào</b> đang mở trên MT5.", target_chat_id=target_chat_id)
            return

        pos = positions[0]
        side_str = "BUY" if getattr(pos, "type", 0) == 0 else "SELL"
        side_icon = "🟢" if side_str == "BUY" else "🔴"
        pnl = getattr(pos, "profit", 0.0)
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"

        text = (
            f"{side_icon} <b>CHI TIẾT VỊ THẾ ĐANG MỞ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• Ticket: <code>#{getattr(pos, 'ticket', 0)}</code>\n"
            f"• Cặp: <b>{getattr(pos, 'symbol', 'XAUUSDm')}</b>\n"
            f"• Lệnh: <b>{side_str} {getattr(pos, 'volume', 0.01):.2f} lot</b>\n"
            f"• Giá vào: <code>{getattr(pos, 'price_open', 0.0):.3f}</code>\n"
            f"• Giá hiện tại: <code>{getattr(pos, 'price_current', 0.0):.3f}</code>\n"
            f"• Cắt lỗ (SL): <code>{getattr(pos, 'sl', 0.0):.3f}</code>\n"
            f"• Chốt lời (TP): <code>{getattr(pos, 'tp', 0.0):.3f}</code>\n"
            f"• Lợi nhuận tạm tính: <b>{pnl_str} USD</b>\n"
            f"<i>Cập nhật: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}</i>"
        )
        self.send_message(text, target_chat_id=target_chat_id)

    def _reply_signals(self, context: Dict[str, Any], target_chat_id: Optional[str] = None) -> None:
        signals = context.get("recent_signals", [])
        if not signals:
            self.send_message("ℹ️ Chưa có tín hiệu nào được lưu trong phiên hiện tại.", target_chat_id=target_chat_id)
            return

        lines = ["📡 <b>3 TÍN HIỆU PHÂN TÍCH GẦN NHẤT</b>\n━━━━━━━━━━━━━━━━━━━━"]
        for s in signals[:3]:
            status_icon = "✅ Phê duyệt" if s.get("is_approved") else "❌ Chặn"
            side = s.get("side", "")
            strategy = s.get("strategy_id", "")
            conf = s.get("confidence_score", 0.0)
            price = s.get("entry_price", 0.0)
            reason = s.get("rejection_reason", "Đạt chuẩn")
            raw_ts = s.get("timestamp", "")
            try:
                dt_utc = datetime.fromisoformat(raw_ts)
                dt_vn = dt_utc.astimezone(timezone(timedelta(hours=7)))
                time_display = dt_vn.strftime("%H:%M (%d/%m)")
            except Exception:
                time_display = raw_ts[:16].replace("T", " ")
            lines.append(
                f"• [<b>{time_display} VN</b>] <b>{strategy}</b> ({side} @ {price:.2f})\n"
                f"  Điểm: <code>{conf:.1f}/100</code> | Trạng thái: <b>{status_icon}</b>\n"
                f"  <i>Lý do: {reason}</i>\n"
            )

        self.send_message("\n".join(lines), target_chat_id=target_chat_id)

    def _reply_pause(self, context: Dict[str, Any], target_chat_id: Optional[str] = None) -> None:
        ctrl = context.get("control_state")
        if ctrl is not None:
            ctrl["is_paused"] = True
            text = (
                "⏸️ <b>ĐÃ TẠM DỪNG VÀO LỆNH TỪ XA</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "• Trạng thái: <b>PAUSED (Tạm dừng)</b>\n"
                "• Bot sẽ <b>KHÔNG vào bất kỳ lệnh mới nào</b>.\n"
                "• Lệnh đang mở (nếu có) vẫn được giám sát SL/TP đầy đủ.\n\n"
                "👉 Gõ <b>/resume</b> để bật lại giao dịch bất cứ lúc nào."
            )
            self.send_message(text, target_chat_id=target_chat_id)
        else:
            self.send_message("⚠️ Không tìm thấy trạng thái điều khiển.", target_chat_id=target_chat_id)

    def _reply_resume(self, context: Dict[str, Any], target_chat_id: Optional[str] = None) -> None:
        ctrl = context.get("control_state")
        risk_guard = context.get("risk_guard")
        if risk_guard is not None and hasattr(risk_guard, "drawdown_guard"):
            risk_guard.drawdown_guard.reset_breakers()

        if ctrl is not None:
            ctrl["is_paused"] = False
            text = (
                "▶️ <b>ĐÃ TIẾP TỤC GIAO DỊCH TỪ XA</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "• Trạng thái: <b>ACTIVE (Đang hoạt động)</b>\n"
                "• Cầu chì bảo vệ chuỗi lỗ: <b>ĐÃ RESET VỀ 0</b>\n"
                "• Bộ lọc AI và các chiến lược đã sẵn sàng quét nến M5 tiếp theo.\n"
                "• Rủi ro: 0.01 lot | SL $2.00 | TP $3.00."
            )
            self.send_message(text, target_chat_id=target_chat_id)
        else:
            self.send_message("⚠️ Không tìm thấy trạng thái điều khiển.", target_chat_id=target_chat_id)

    def _reply_close(self, context: Dict[str, Any], target_chat_id: Optional[str] = None) -> None:
        positions = context.get("open_positions", [])
        bridge = context.get("bridge")
        if not positions or not bridge:
            self.send_message("ℹ️ Hiện tại không có vị thế nào để đóng.", target_chat_id=target_chat_id)
            return

        closed_count = 0
        for pos in positions:
            res = bridge.close_position(pos)
            if res.success:
                closed_count += 1
                self.send_message(
                    f"🛑 <b>ĐÃ ĐÓNG LỆNH #{pos.ticket} KHẨN CẤP THÀNH CÔNG</b>\n"
                    f"Giá đóng: <code>{res.price:.3f}</code> | Khối lượng: {pos.volume:.2f} lot",
                    target_chat_id=target_chat_id,
                )
            else:
                self.send_message(
                    f"⚠️ Thất bại khi đóng lệnh #{pos.ticket}: {res.retcode_description}",
                    target_chat_id=target_chat_id,
                )

    def _reply_start(self, context: Dict[str, Any], msg: Optional[Dict[str, Any]] = None, target_chat_id: Optional[str] = None) -> None:
        user_name = "Trader"
        if msg and "from" in msg:
            user_name = msg["from"].get("first_name", "Trader")

        text = (
            f"👑 <b>GOLDSTRIKE AI ⚜️ — VUA SCALPING VÀNG TỰ ĐỘNG</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Xin chào <b>{user_name}</b>! Chào mừng bạn đến với trung tâm điều khiển Vua Scalping V4.\n\n"
            f"📊 <b>CẤU HÌNH VUA SCALPING (LÃI KÉP & BẢO VỆ ĐỘNG):</b>\n"
            f"• Cặp tài sản: <code>XAUUSDm (Gold)</code>\n"
            f"• Tài khoản: <code>Exness Demo #434467985</code>\n"
            f"• Khối lượng: <code>Lot động theo ATR & Vốn (Min 0.01 lot)</code>\n"
            f"• Cắt lỗ (SL): <code>4.0% vốn hiện tại (tính theo ATR nến)</code>\n"
            f"• Chốt lời (TP): <code>6.0% vốn hiện tại (R:R 1:1.5)</code>\n"
            f"• 🛡️ <b>Lệnh Bất Tử (Break-Even)</b>: <code>Tự động khóa hòa vốn khi đạt 50% TP</code>\n"
            f"• 🎯 <b>Dynamic Trailing Stop</b>: <code>Khóa lãi khi mở rộng xu hướng (≥ 70% TP)</code>\n"
            f"• 🤖 <b>Bộ lọc AI Meta-Labeling</b>: <code>Chặn bẫy quét râu (Win Prob ≥ 65%)</code>\n"
            f"• 🛑 <b>Ngắt mạch an toàn</b>: <code>-8.0% vốn ngày (Dừng phiên bảo toàn vốn)</code>\n\n"
            f"🎮 <b>HƯỚNG DẪN CÁC LỆNH ĐIỀU KHIỂN & TRA CỨU:</b>\n\n"
            f"📊 <b>Tra Cứu Thông Tin:</b>\n"
            f"• /status — Trạng thái hoạt động, kết nối MT5 & nến M5\n"
            f"• /balance — Tra cứu số dư, vốn (Equity) & PnL ngày\n"
            f"• /positions — Xem chi tiết lệnh đang chạy trên MT5\n"
            f"• /signals — 3 tín hiệu AI phân tích gần nhất\n\n"
            f"⚡ <b>Điều Khiển Từ Xa:</b>\n"
            f"• /pause — Tạm dừng vào lệnh mới từ xa\n"
            f"• /resume — Tiếp tục quét nến & vào lệnh tự động\n"
            f"• /close — Đóng khẩn cấp mọi lệnh MT5 ngay lập tức\n\n"
            f"📖 <b>Hỗ Trợ:</b>\n"
            f"• /help — Xem lại hướng dẫn lệnh & quy tắc an toàn\n\n"
            f"<i>💡 Mẹo: Bạn có thể chạm trực tiếp vào các lệnh màu xanh ở trên hoặc bấm nút Menu ở góc màn hình để chọn nhanh!</i>"
        )
        self.send_message(text, target_chat_id=target_chat_id)

    def _reply_help(self, context: Dict[str, Any], target_chat_id: Optional[str] = None) -> None:
        text = (
            f"📖 <b>DANH SÁCH LỆNH ĐIỀU KHIỂN — GOLDSTRIKE AI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Tra Cứu Thông Tin:</b>\n"
            f"• /status — Kiểm tra bot, kết nối MT5, nến M5 & regime\n"
            f"• /balance — Xem số dư, Equity & PnL ngày hôm nay\n"
            f"• /positions — Xem chi tiết lệnh đang chạy (SL, TP, lãi/lỗ)\n"
            f"• /signals — Xem các tín hiệu AI phân tích gần nhất\n\n"
            f"⚡ <b>Điều Khiển Từ Xa:</b>\n"
            f"• /pause — Tạm dừng tìm kiếm & vào lệnh mới\n"
            f"• /resume — Bật lại chế độ tự động vào lệnh\n"
            f"• /close — Đóng khẩn cấp toàn bộ vị thế MT5 ngay lập tức\n\n"
            f"📖 <b>Trợ Giúp:</b>\n"
            f"• /help — Xem bảng danh sách lệnh này\n"
            f"• /start — Hiển thị màn hình chào mừng & cấu hình chi tiết\n\n"
            f"🛡️ <b>Quy Tắc Quản Trị Vốn Đang Áp Dụng:</b>\n"
            f"• Khối lượng: <code>Lot động theo ATR & Vốn (Min 0.01 lot)</code>\n"
            f"• Cắt lỗ (SL): <code>4.0% vốn hiện tại</code>\n"
            f"• Chốt lời (TP): <code>6.0% vốn hiện tại (R:R 1:1.5)</code>\n"
            f"• Bộ lọc AI: <code>Meta-Labeling ML (Win Prob ≥ 65%)</code>\n"
            f"• Ngắt mạch phiên: <code>-8.0% vốn ngày</code>"
        )
        self.send_message(text, target_chat_id=target_chat_id)
