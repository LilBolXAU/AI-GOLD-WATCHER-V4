"""
Telegram Bot Registration Helper for AI GOLD WATCHER V4.
Automatically captures Chat ID when the user sends /start to their bot,
updates .env, and sends a test welcome message.
"""

import os
import sys
import time
from pathlib import Path
import requests

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = WORKSPACE_ROOT / ".env"


def register_telegram():
    # Read bot token from .env or argument
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token and ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip()

    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN not found in .env!")
        return False

    print("==================================================")
    print("   AI GOLD WATCHER V4 — TELEGRAM BOT PAIRING      ")
    print("==================================================")
    print(f"Bot Token: {token[:12]}...{token[-6:]}")
    
    # 1. Check Bot Identity
    me_resp = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()
    if not me_resp.get("ok"):
        print(f"[ERROR] Invalid token: {me_resp}")
        return False

    bot_info = me_resp["result"]
    username = bot_info.get("username", "your_bot")
    print(f"Bot Name : {bot_info.get('first_name')}")
    print(f"Username : @{username}")
    print("--------------------------------------------------")
    print(f"👉 HÃY MỞ TELEGRAM, VÀO BOT: https://t.me/{username}")
    print("👉 VÀ BẤM NÚT 'START' (HOẶC GỬI TIN NHẮN BẤT KỲ VÀO BOT)...")
    print("--------------------------------------------------")
    print("Đang chờ bạn gửi tin nhắn vào bot...")

    chat_id = None
    user_name = ""

    # 2. Poll for updates (up to 60 seconds)
    for attempt in range(30):
        try:
            upd_resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=5.0).json()
            if upd_resp.get("ok") and upd_resp.get("result"):
                for update in reversed(upd_resp["result"]):
                    msg = update.get("message") or update.get("edited_message")
                    if msg and "chat" in msg:
                        chat_id = msg["chat"]["id"]
                        user_name = msg["from"].get("first_name", "Trader")
                        break
            if chat_id:
                break
        except Exception:
            pass
        time.sleep(2)

    if not chat_id:
        print("\n[HẾT THỜI GIAN CHỜ] Chưa nhận được tin nhắn từ bạn.")
        print(f"Vui lòng vào https://t.me/{username} bấm START rồi chạy lại script này nhé!")
        return False

    print(f"\n✅ ĐÃ TÌM THẤY CHAT ID: {chat_id} (Người dùng: {user_name})")

    # 3. Update .env file
    if ENV_PATH.exists():
        content = ENV_PATH.read_text(encoding="utf-8")
        lines = []
        replaced = False
        for line in content.splitlines():
            if line.startswith("TELEGRAM_CHAT_ID="):
                lines.append(f"TELEGRAM_CHAT_ID={chat_id}")
                replaced = True
            else:
                lines.append(line)
        if not replaced:
            lines.append(f"TELEGRAM_CHAT_ID={chat_id}")
        ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"✅ Đã tự động cập nhật TELEGRAM_CHAT_ID={chat_id} vào file .env!")

    # 4. Send Confirmation Welcome Message
    welcome_text = (
        f"⚜️ <b>GOLDSTRIKE AI — HỆ THỐNG GIAO DỊCH VÀNG TỰ ĐỘNG</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Xin chào <b>{user_name}</b>! Bot AI GOLD WATCHER V4 đã liên kết thành công với tài khoản Telegram của bạn.\n\n"
        f"📊 <b>Cấu hình giao dịch hiện tại:</b>\n"
        f"• Tài sản: <code>XAUUSDm (Gold)</code>\n"
        f"• Tài khoản: <code>Exness Demo #434467985</code>\n"
        f"• Khối lượng: <code>0.01 lot</code>\n"
        f"• Cắt lỗ (SL): <code>$2.00 (4.0% vốn $50)</code>\n"
        f"• Chốt lời (TP): <code>$3.00 (6.0% vốn $50, R:R 1:1.5)</code>\n"
        f"• Bộ lọc AI: <code>Meta-Labeling ML (Win Prob ≥ 65%)</code>\n"
        f"• Ngắt mạch an toàn: <code>-$4.00 USD/ngày</code>\n\n"
        f"🎮 <b>HƯỚNG DẪN CÁC LỆNH ĐIỀU KHIỂN & TRA CỨU:</b>\n\n"
        f"📊 <b>Tra Cứu Thông Tin:</b>\n"
        f"• /status — Trạng thái bot, kết nối MT5 & nến M5\n"
        f"• /balance — Tra cứu số dư, Equity & PnL ngày\n"
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
    send_resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": welcome_text, "parse_mode": "HTML"},
        timeout=8.0,
    )
    if send_resp.status_code == 200:
        print("🎉 Tin nhắn chào mừng thử nghiệm đã được gửi đến Telegram của bạn thành công!")
    else:
        print(f"[CẢNH BÁO] Không gửi được tin nhắn: {send_resp.text}")

    return True


if __name__ == "__main__":
    register_telegram()
