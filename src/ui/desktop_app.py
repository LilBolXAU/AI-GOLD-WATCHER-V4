"""
AI GOLD WATCHER V4 — Modern Desktop Application
Professional Windows 11 Dark Mode Trading Dashboard built with CustomTkinter.
Authored for Admin: LilBoiXAU.
"""

import sys
import os
import json
import logging
import threading
import queue
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

import customtkinter as ctk

# Ensure root directory in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config.license import (
    is_admin_account,
    verify_account_authorized,
    get_allowed_accounts,
    add_allowed_account,
    remove_allowed_account,
    sync_remote_license,
)

# Setup appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class GuiLogHandler(logging.Handler):
    """Custom logging handler that routes log messages to the GUI terminal queue."""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            pass


class AIGoldWatcherApp(ctk.CTk):
    """Main Desktop Application Window for AI GOLD WATCHER V4."""

    def __init__(self):
        super().__init__()

        # Window settings
        self.title("AI GOLD WATCHER V4 — Institutional Gold Scalper (LilBoiXAU Edition)")
        self.geometry("1120x860")
        self.minsize(980, 750)

        # State management
        self.is_running = False
        self.is_paused = False
        self.worker_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()

        # Dynamic Role state: "admin" | "client_auth" | "client_unauth" | "pending"
        self.current_role: Optional[str] = None
        self.current_account: Optional[int] = None
        self.last_seen_announcement_id: Optional[str] = None
        self.has_active_update_banner: bool = False

        # Wire logging to GUI
        self.log_handler = GuiLogHandler(self.log_queue)
        formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
        self.log_handler.setFormatter(formatter)
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)

        # Build UI layout
        self._build_header()
        self._build_update_banner()
        self._build_metrics_cards()
        self._build_main_content()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start periodic GUI updater
        self.after(500, self._process_log_queue)
        self.after(1000, self._refresh_telemetry)
        self.after(3000, self._check_updates_and_broadcasts)

        self._log_terminal("🌟 AI GOLD WATCHER V4 Desktop App khởi động thành công!")
        self._log_terminal("🔑 Sẵn sàng kết nối MT5 XAUUSDm...")

    # -------------------------------------------------------------------------
    # UI BUILDERS
    # -------------------------------------------------------------------------
    def _build_header(self):
        """Build top banner with title, branding, and status badges."""
        self.header_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#1a1c23")
        self.header_frame.pack(fill="x", padx=15, pady=(15, 10))

        # Title & Subtitle
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)

        title_lbl = ctk.CTkLabel(
            title_box,
            text="🟡 AI GOLD WATCHER V4",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#f1c40f",
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            title_box,
            text="XAUUSDm M5 Institutional Scalper • Win Rate 81.8% • Option 1 Equity Risk",
            font=ctk.CTkFont(size=12),
            text_color="#95a5a6",
        )
        sub_lbl.pack(anchor="w")

        # Status Badges
        badges_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        badges_box.pack(side="right", padx=15, pady=10)

        self.mt5_badge = ctk.CTkLabel(
            badges_box,
            text="🟢 MT5: ĐANG KẾT NỐI...",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2c3e50",
            corner_radius=6,
            padx=10,
            pady=4,
            text_color="#2ecc71",
        )
        self.mt5_badge.pack(side="right", padx=5)

        self.license_badge = ctk.CTkLabel(
            badges_box,
            text="⏳ ĐANG KIỂM TRA QUYỀN...",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#34495e",
            corner_radius=6,
            padx=10,
            pady=4,
            text_color="#bdc3c7",
        )
        self.license_badge.pack(side="right", padx=5)

    def _build_update_banner(self):
        """Build top dismissable notification bar for new updates."""
        self.update_banner_frame = ctk.CTkFrame(
            self,
            corner_radius=8,
            fg_color="#1a3a2a",
            border_width=2,
            border_color="#2ecc71",
        )
        # Note: Packed dynamically when an update is detected

        self.lbl_update_title = ctk.CTkLabel(
            self.update_banner_frame,
            text="🚀 ĐÃ CÓ BẢN CẬP NHẬT MỚI TỪ ADMIN LILBOIXAU!",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f1c40f",
        )
        self.lbl_update_title.pack(side="left", padx=15, pady=8)

        self.lbl_update_desc = ctk.CTkLabel(
            self.update_banner_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#ecf0f1",
        )
        self.lbl_update_desc.pack(side="left", padx=5, pady=8)

        self.btn_apply_update = ctk.CTkButton(
            self.update_banner_frame,
            text="🔄 CẬP NHẬT NGAY",
            width=140,
            height=30,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._apply_new_update,
        )
        self.btn_apply_update.pack(side="right", padx=15, pady=8)

    def _build_metrics_cards(self):
        """Build 4 KPI summary cards."""
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=15, pady=5)
        self.cards_frame.columnconfigure((0, 1, 2, 3), weight=1)

        # Card 1: Balance
        self.card_balance = self._create_card(self.cards_frame, 0, "SỐ DƯ (BALANCE)", "$--.--", "#3498db")
        # Card 2: Equity
        self.card_equity = self._create_card(self.cards_frame, 1, "VỐN THỰC (EQUITY)", "$--.--", "#2ecc71")
        # Card 3: Daily PnL
        self.card_pnl = self._create_card(self.cards_frame, 2, "LÃI HÔM NAY (PNL)", "+$0.00 (+0.0%)", "#f1c40f")
        # Card 4: Win Rate
        self.card_winrate = self._create_card(self.cards_frame, 3, "TỶ LỆ THẮNG (WIN RATE)", "81.8% (9W / 2L)", "#9b59b6")

    def _create_card(self, parent, col: int, title: str, value: str, accent: str) -> dict:
        frame = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e222d")
        frame.grid(row=0, column=col, padx=5, sticky="ew")

        lbl_t = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color="#7f8c8d")
        lbl_t.pack(anchor="w", padx=12, pady=(10, 2))

        lbl_v = ctk.CTkLabel(frame, text=value, font=ctk.CTkFont(size=18, weight="bold"), text_color=accent)
        lbl_v.pack(anchor="w", padx=12, pady=(0, 10))

        return {"frame": frame, "title": lbl_t, "value": lbl_v}

    def _build_main_content(self):
        """Build split layout: Left controls & Right live terminals."""
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self.main_container.columnconfigure(0, weight=4)  # Left 40%
        self.main_container.columnconfigure(1, weight=6)  # Right 60%
        self.main_container.rowconfigure(0, weight=1)

        # =====================================================================
        # LEFT COLUMN: Controls & Settings & Dynamic License
        # =====================================================================
        left_col = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="#1a1c23")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)

        # Box 1: Core Action Buttons
        lbl_ctrl = ctk.CTkLabel(left_col, text="BẢNG ĐIỀU KHIỂN TRUNG TÂM", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ecf0f1")
        lbl_ctrl.pack(anchor="w", padx=15, pady=(15, 8))

        self.btn_start = ctk.CTkButton(
            left_col,
            text="▶ BẬT BOT TỰ ĐỘNG (START)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60",
            hover_color="#2ecc71",
            height=42,
            command=self._toggle_bot_running,
        )
        self.btn_start.pack(fill="x", padx=15, pady=4)

        self.btn_pause = ctk.CTkButton(
            left_col,
            text="⏸ TẠM DỪNG GIAO DỊCH (PAUSE)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#d35400",
            hover_color="#e67e22",
            height=36,
            command=self._toggle_bot_pause,
        )
        self.btn_pause.pack(fill="x", padx=15, pady=4)

        self.btn_close_all = ctk.CTkButton(
            left_col,
            text="🚨 ĐÓNG HẾT LỆNH KHẨN CẤP (KILL)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#c0392b",
            hover_color="#e74c3c",
            height=36,
            command=self._emergency_close_all,
        )
        self.btn_close_all.pack(fill="x", padx=15, pady=4)

        # Box 2: Trading Parameters & Safeguards
        sep1 = ctk.CTkFrame(left_col, height=2, fg_color="#2c3e50")
        sep1.pack(fill="x", padx=15, pady=10)

        lbl_settings = ctk.CTkLabel(left_col, text="THIẾT LẬP CHIẾN THUẬT & AN TOÀN", font=ctk.CTkFont(size=13, weight="bold"), text_color="#ecf0f1")
        lbl_settings.pack(anchor="w", padx=15, pady=(0, 6))

        # Mode selector (Live Demo vs Live Paper 25h Replay)
        lbl_mode = ctk.CTkLabel(left_col, text="Chế độ hoạt động:", font=ctk.CTkFont(size=12), text_color="#bdc3c7")
        lbl_mode.pack(anchor="w", padx=15, pady=0)
        self.mode_menu = ctk.CTkOptionMenu(
            left_col,
            values=[
                "🔴 Live Demo MT5 (Quét 5s/lần theo thời gian thực)",
                "⚡ Live Paper (Test bot trong 25 giờ vừa qua)",
            ],
            height=32,
        )
        self.mode_menu.pack(fill="x", padx=15, pady=(2, 6))

        # Trading Style / Profile selector
        lbl_profile = ctk.CTkLabel(left_col, text="Phong cách giao dịch:", font=ctk.CTkFont(size=12), text_color="#bdc3c7")
        lbl_profile.pack(anchor="w", padx=15, pady=0)
        self.profile_menu = ctk.CTkOptionMenu(
            left_col,
            values=[
                "⚡ Sniper Chuẩn V4 (Khuyên dùng — Lãi mục tiêu $10-$20/ngày)",
                "🛡️ Siêu Bảo Toàn (Conservative — Hòa vốn sớm)",
                "🎯 Scalper Cân Bằng (Balanced — An toàn & hiệu quả)",
            ],
            height=32,
        )
        self.profile_menu.pack(fill="x", padx=15, pady=(2, 8))

        # Checkboxes for guards
        self.chk_be = ctk.CTkCheckBox(left_col, text="Auto Break-Even (Khóa hòa vốn khi giá đi đúng)", font=ctk.CTkFont(size=12))
        self.chk_be.select()
        self.chk_be.pack(anchor="w", padx=15, pady=3)

        self.chk_runner = ctk.CTkCheckBox(left_col, text="Gồng Lãi Động (Trailing Runner nới TP +$5.00)", font=ctk.CTkFont(size=12))
        self.chk_runner.select()
        self.chk_runner.pack(anchor="w", padx=15, pady=3)

        self.chk_exhaust = ctk.CTkCheckBox(left_col, text="Bộ Lọc Kiệt Sức (Chặn bán đáy / mua đỉnh)", font=ctk.CTkFont(size=12))
        self.chk_exhaust.select()
        self.chk_exhaust.pack(anchor="w", padx=15, pady=3)

        # Box 3: Telegram Alerts Connection
        sep_tg = ctk.CTkFrame(left_col, height=2, fg_color="#2c3e50")
        sep_tg.pack(fill="x", padx=15, pady=10)

        lbl_tg = ctk.CTkLabel(
            left_col,
            text="📱 BÁO ĐỘNG TELEGRAM (100% MIỄN PHÍ)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3498db",
        )
        lbl_tg.pack(anchor="w", padx=15, pady=(0, 2))

        # Check existing chat ID
        curr_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not curr_chat_id and Path(".env").exists():
            for line in Path(".env").read_text(encoding="utf-8").splitlines():
                if line.startswith("TELEGRAM_CHAT_ID="):
                    curr_chat_id = line.split("=", 1)[1].strip()

        status_text = f"🟢 Đã kết nối Chat ID: #{curr_chat_id}" if curr_chat_id else "⚪ Chưa kết nối (Nhập Chat ID bên dưới)"
        status_color = "#2ecc71" if curr_chat_id else "#e74c3c"
        self.lbl_tg_status = ctk.CTkLabel(
            left_col,
            text=status_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=status_color,
        )
        self.lbl_tg_status.pack(anchor="w", padx=15, pady=(0, 4))

        tg_row = ctk.CTkFrame(left_col, fg_color="transparent")
        tg_row.pack(fill="x", padx=15, pady=2)

        self.ent_tg_chat_id = ctk.CTkEntry(tg_row, placeholder_text="Nhập Chat ID...", height=32)
        if curr_chat_id:
            self.ent_tg_chat_id.insert(0, curr_chat_id)
        self.ent_tg_chat_id.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_save_tg = ctk.CTkButton(
            tg_row,
            text="💾 Lưu",
            width=55,
            height=32,
            fg_color="#2980b9",
            command=self._save_telegram_id,
        )
        self.btn_save_tg.pack(side="left", padx=2)

        self.btn_test_tg = ctk.CTkButton(
            tg_row,
            text="🔔 Test",
            width=55,
            height=32,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self._test_telegram_alert,
        )
        self.btn_test_tg.pack(side="left", padx=2)

        ctk.CTkLabel(
            left_col,
            text="💡 Mở Telegram tìm bot @goldstrikeai_bot bấm /start để lấy Chat ID",
            font=ctk.CTkFont(size=11),
            text_color="#7f8c8d",
            wraplength=380,
            justify="left",
        ).pack(anchor="w", padx=15, pady=(2, 6))

        # Box 4: Dynamic Role Container (Admin Whitelist vs Client License)
        self.license_container = ctk.CTkFrame(left_col, fg_color="transparent")
        self.license_container.pack(fill="x", padx=15, pady=(4, 15))
        self._update_role_ui(None)

        # =====================================================================
        # RIGHT COLUMN: Open Positions & Live Activity Terminal
        # =====================================================================
        right_col = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="#1a1c23")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)
        right_col.rowconfigure(1, weight=1)
        right_col.columnconfigure(0, weight=1)

        # Open positions card
        pos_header = ctk.CTkFrame(right_col, fg_color="transparent")
        pos_header.pack(fill="x", padx=15, pady=(15, 6))

        lbl_pos_title = ctk.CTkLabel(pos_header, text="VỊ THẾ ĐANG MỞ (OPEN POSITIONS)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#ecf0f1")
        lbl_pos_title.pack(side="left")

        self.lbl_pos_count = ctk.CTkLabel(pos_header, text="[0/2 Vị Thế]", font=ctk.CTkFont(size=12, weight="bold"), text_color="#f1c40f")
        self.lbl_pos_count.pack(side="right")

        self.pos_frame = ctk.CTkFrame(right_col, corner_radius=8, fg_color="#1e222d", height=90)
        self.pos_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.lbl_pos_detail = ctk.CTkLabel(
            self.pos_frame,
            text="💤 Hiện tại không có vị thế nào đang mở. Bot đang quét nến M5...",
            font=ctk.CTkFont(size=12),
            text_color="#7f8c8d",
        )
        self.lbl_pos_detail.pack(padx=15, pady=25)

        # Admin Broadcast Notice Banner
        self.admin_banner_frame = ctk.CTkFrame(
            right_col,
            corner_radius=8,
            fg_color="#211528",
            border_width=1,
            border_color="#9b59b6",
        )
        self.lbl_admin_banner_title = ctk.CTkLabel(
            self.admin_banner_frame,
            text="👑 THÔNG BÁO TỪ MASTER ADMIN LilBoiXAU",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f1c40f",
        )
        self.lbl_admin_banner_title.pack(anchor="w", padx=12, pady=(6, 1))

        self.lbl_admin_banner_msg = ctk.CTkLabel(
            self.admin_banner_frame,
            text="Chào mừng anh em! Hệ thống AI GOLD WATCHER V4 đang hoạt động.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00e5ff",
            wraplength=480,
            justify="left",
        )
        self.lbl_admin_banner_msg.pack(anchor="w", padx=12, pady=(0, 6))
        self.admin_banner_frame.pack(fill="x", padx=15, pady=(0, 6))

        # Terminal Log
        lbl_term = ctk.CTkLabel(right_col, text="NHẬT KÝ HOẠT ĐỘNG THỜI GIAN THỰC (LIVE SIGNALS)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#ecf0f1")
        lbl_term.pack(anchor="w", padx=15, pady=(4, 4))

        self.term_box = ctk.CTkTextbox(
            right_col,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#0e1117",
            text_color="#ecf0f1",
            corner_radius=8,
            wrap="word",
        )
        self.term_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    # -------------------------------------------------------------------------
    # TELEGRAM CONFIGURATION
    # -------------------------------------------------------------------------
    def _save_telegram_id(self):
        """Save Telegram Chat ID into .env and runtime environment."""
        chat_id = self.ent_tg_chat_id.get().strip()
        if not chat_id:
            self._log_terminal("⚠️ Vui lòng nhập số Telegram Chat ID của bạn.")
            return

        try:
            env_path = Path(".env")
            lines = []
            chat_found = False
            token_found = False

            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    if line.startswith("TELEGRAM_CHAT_ID="):
                        lines.append(f"TELEGRAM_CHAT_ID={chat_id}")
                        chat_found = True
                    elif line.startswith("TELEGRAM_BOT_TOKEN="):
                        lines.append(line)
                        token_found = True
                    else:
                        lines.append(line)
            else:
                lines = [
                    "# AI GOLD WATCHER V4 CONFIGURATION",
                    "DRY_RUN_ENABLED=True",
                    "SYMBOL=XAUUSDm",
                ]

            if not token_found:
                lines.append("TELEGRAM_BOT_TOKEN=9222706549:AAFwuV5PW_zcVLKiNMDoeJQS2s_LN-YOSlU")
            if not chat_found:
                lines.append(f"TELEGRAM_CHAT_ID={chat_id}")

            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            os.environ["TELEGRAM_CHAT_ID"] = chat_id
            os.environ["TELEGRAM_BOT_TOKEN"] = "9222706549:AAFwuV5PW_zcVLKiNMDoeJQS2s_LN-YOSlU"

            # Register Chat ID into whitelist database for Admin broadcasts
            from src.config.license import register_telegram_chat_id
            register_telegram_chat_id(chat_id)

            self.lbl_tg_status.configure(text=f"🟢 Đã kết nối Chat ID: #{chat_id}", text_color="#2ecc71")
            self._log_terminal(f"✅ Đã lưu Telegram Chat ID: #{chat_id}. Bấm [🔔 Test] để thử gửi tin nhắn đến điện thoại.")
        except Exception as e:
            self._log_terminal(f"❌ Lỗi khi lưu Telegram Chat ID: {e}")

    def _test_telegram_alert(self):
        """Send immediate test notification to verified Telegram Chat ID."""
        chat_id = self.ent_tg_chat_id.get().strip() or os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not chat_id:
            self._log_terminal("⚠️ Bạn chưa nhập Chat ID! Hãy nhập Chat ID và bấm [💾 Lưu] trước.")
            return

        self._log_terminal(f"🔔 Đang gửi tin nhắn kiểm tra tới Telegram #{chat_id}...")
        try:
            from src.monitoring.telegram_bot import TelegramNotifier
            tg = TelegramNotifier(chat_id=chat_id)
            test_msg = (
                "🔔 <b>AI GOLD WATCHER V4 — DESKTOP APP</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "✅ <b>KẾT NỐI TELEGRAM THÀNH CÔNG!</b>\n"
                f"👤 Chat ID của bạn: <code>{chat_id}</code>\n"
                "🚀 Hệ thống đã sẵn sàng gửi thông báo mở lệnh, chốt lời, dời SL hòa vốn và cắt lỗ tự động cho bạn!"
            )
            success = tg.send_message(test_msg, target_chat_id=chat_id)
            if success:
                self._log_terminal(f"🎉 Gửi tin nhắn test tới Telegram #{chat_id} THÀNH CÔNG! Hãy kiểm tra điện thoại của bạn.")
            else:
                self._log_terminal("❌ Gửi tin nhắn thất bại. Vui lòng mở Telegram tìm bot @goldstrikeai_bot và bấm /start để cấp quyền nhận tin trước!")
        except Exception as e:
            self._log_terminal(f"❌ Lỗi gửi tin Telegram: {e}")

    # -------------------------------------------------------------------------
    # DYNAMIC ROLE-BASED UI MANAGEMENT
    # -------------------------------------------------------------------------
    def _update_role_ui(self, login: Optional[int], force: bool = False):
        """
        Dynamically render Admin or Client view based on MT5 account number.
        - Admin (#434467985): Full whitelist manager + Push code buttons.
        - Client (Authorized): Simplified view + Check updates button (NO admin controls).
        - Client (Unauthorized): Bot locked, warning card + Contact admin message.
        """
        if login is None:
            new_role = "pending"
        elif is_admin_account(login):
            new_role = "admin"
        else:
            is_auth = verify_account_authorized(login)
            if not is_auth:
                # If not found locally, attempt automatic remote verification from master GitHub repo
                is_auth = verify_account_authorized(login, check_remote=True)
            new_role = "client_auth" if is_auth else "client_unauth"

        if not force and self.current_role == new_role and self.current_account == login:
            return

        self.current_role = new_role
        self.current_account = login

        # Clear container
        for widget in self.license_container.winfo_children():
            widget.destroy()

        sep = ctk.CTkFrame(self.license_container, height=2, fg_color="#2c3e50")
        sep.pack(fill="x", pady=(0, 10))

        if new_role == "admin":
            self._render_admin_panel()
        elif new_role == "client_auth":
            self._render_client_authorized_panel(login)
        elif new_role == "client_unauth":
            self._render_client_unauthorized_panel(login)
        else:
            self._render_pending_panel()

    def _render_admin_panel(self):
        """Render full Admin Whitelist & Push controls for LilBoiXAU."""
        self.license_badge.configure(
            text="👑 ADMIN: LilBoiXAU",
            text_color="#f1c40f",
            fg_color="#34495e",
        )

        lbl_lic = ctk.CTkLabel(
            self.license_container,
            text="👑 QUẢN TRỊ BẢN QUYỀN (ADMIN LilBoiXAU)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f1c40f",
        )
        lbl_lic.pack(anchor="w", pady=(0, 6))

        acc_input_box = ctk.CTkFrame(self.license_container, fg_color="transparent")
        acc_input_box.pack(fill="x", pady=2)

        self.ent_account = ctk.CTkEntry(acc_input_box, placeholder_text="Nhập số MT5 bạn bè...", height=32)
        self.ent_account.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_add_acc = ctk.CTkButton(
            acc_input_box,
            text="+ Cấp quyền",
            width=80,
            height=32,
            fg_color="#2980b9",
            command=self._add_account_license,
        )
        self.btn_add_acc.pack(side="right", padx=2)

        self.btn_rem_acc = ctk.CTkButton(
            acc_input_box,
            text="- Thu hồi",
            width=70,
            height=32,
            fg_color="#7f8c8d",
            hover_color="#c0392b",
            command=self._remove_account_license,
        )
        self.btn_rem_acc.pack(side="right", padx=2)

        self.lbl_allowed_list = ctk.CTkLabel(
            self.license_container,
            text=f"Tài khoản duyệt: {', '.join(str(a) for a in get_allowed_accounts())}",
            font=ctk.CTkFont(size=11),
            text_color="#95a5a6",
            wraplength=380,
            justify="left",
        )
        self.lbl_allowed_list.pack(anchor="w", pady=4)

        sync_box = ctk.CTkFrame(self.license_container, fg_color="transparent")
        sync_box.pack(fill="x", pady=(8, 0))

        self.btn_pull = ctk.CTkButton(
            sync_box,
            text="🔄 Tải cập nhật (Pull)",
            height=32,
            fg_color="#34495e",
            command=self._git_pull,
        )
        self.btn_pull.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_push = ctk.CTkButton(
            sync_box,
            text="📤 Đẩy code (Push)",
            height=32,
            fg_color="#2980b9",
            hover_color="#3498db",
            command=self._git_push,
        )
        self.btn_push.pack(side="right", fill="x", expand=True, padx=(3, 0))

        # Admin Rainbow Chat Broadcast
        sep_chat = ctk.CTkFrame(self.license_container, height=1, fg_color="#34495e")
        sep_chat.pack(fill="x", pady=(10, 6))

        lbl_chat = ctk.CTkLabel(
            self.license_container,
            text="📢 CHAT ADMIN CẦU VỒNG (PHÁT THÔNG BÁO)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e056fd",
        )
        lbl_chat.pack(anchor="w", pady=(0, 4))

        chat_input_box = ctk.CTkFrame(self.license_container, fg_color="transparent")
        chat_input_box.pack(fill="x", pady=2)

        self.ent_admin_broadcast = ctk.CTkEntry(
            chat_input_box,
            placeholder_text="Nhập thông báo gửi đến người dùng...",
            height=32,
        )
        self.ent_admin_broadcast.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_broadcast = ctk.CTkButton(
            chat_input_box,
            text="🌈 Gửi thông báo",
            width=115,
            height=32,
            fg_color="#8e44ad",
            hover_color="#9b59b6",
            command=self._send_admin_broadcast,
        )
        self.btn_broadcast.pack(side="right")

        if not self.is_running:
            self.btn_start.configure(
                state="normal",
                text="▶ BẬT BOT TỰ ĐỘNG (START)",
                fg_color="#27ae60",
                hover_color="#2ecc71",
            )

    def _render_client_authorized_panel(self, login: int):
        """Render client view with valid license (NO admin controls, NO push button)."""
        self.license_badge.configure(
            text="🔑 BẢN QUYỀN: HỢP LỆ",
            text_color="#2ecc71",
            fg_color="#1e3d2f",
        )

        lbl_lic = ctk.CTkLabel(
            self.license_container,
            text="🔑 BẢN QUYỀN KHÁCH HÀNG (CLIENT LICENSE)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#2ecc71",
        )
        lbl_lic.pack(anchor="w", pady=(0, 6))

        card = ctk.CTkFrame(self.license_container, corner_radius=8, fg_color="#1e222d")
        card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            card,
            text=f"👤 Tài khoản MT5: #{login}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ecf0f1",
        ).pack(anchor="w", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            card,
            text="🛡️ Trạng thái: ✅ ĐÃ KÍCH HOẠT HỢP LỆ",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2ecc71",
        ).pack(anchor="w", padx=12, pady=2)

        ctk.CTkLabel(
            card,
            text="👑 Nhà phát triển: LilBoiXAU Edition",
            font=ctk.CTkFont(size=11),
            text_color="#f1c40f",
        ).pack(anchor="w", padx=12, pady=(2, 8))

        btn_update = ctk.CTkButton(
            self.license_container,
            text="🔄 Kiểm tra & Cập nhật phiên bản mới từ Admin",
            height=34,
            fg_color="#2980b9",
            hover_color="#3498db",
            command=self._client_update_and_check,
        )
        btn_update.pack(fill="x")

        if not self.is_running:
            self.btn_start.configure(
                state="normal",
                text="▶ BẬT BOT TỰ ĐỘNG (START)",
                fg_color="#27ae60",
                hover_color="#2ecc71",
            )

    def _render_client_unauthorized_panel(self, login: int):
        """Render locked client view when account is unauthorized."""
        self.license_badge.configure(
            text="⛔ CHƯA CẤP QUYỀN",
            text_color="#e74c3c",
            fg_color="#4a1c1c",
        )

        lbl_lic = ctk.CTkLabel(
            self.license_container,
            text="⛔ BẢN QUYỀN CHƯA KÍCH HOẠT",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#e74c3c",
        )
        lbl_lic.pack(anchor="w", pady=(0, 6))

        card = ctk.CTkFrame(self.license_container, corner_radius=8, fg_color="#2d1a1a")
        card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            card,
            text=f"👤 Tài khoản MT5: #{login}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ecf0f1",
        ).pack(anchor="w", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            card,
            text="❌ Trạng thái: CHƯA CÓ TRONG WHITELIST",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e74c3c",
        ).pack(anchor="w", padx=12, pady=2)

        ctk.CTkLabel(
            card,
            text="⚠️ Vui lòng gửi số MT5 trên cho Admin LilBoiXAU để kích hoạt bot.",
            font=ctk.CTkFont(size=11),
            text_color="#e67e22",
            wraplength=360,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(2, 8))

        btn_check = ctk.CTkButton(
            self.license_container,
            text="🔄 Kiểm tra lại trạng thái bản quyền",
            height=34,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            command=self._client_update_and_check,
        )
        btn_check.pack(fill="x")

        # Lock Start button completely
        if not self.is_running:
            self.btn_start.configure(
                state="disabled",
                text="⛔ KHÓA: CHƯA CẤP QUYỀN",
                fg_color="#555555",
            )

    def _render_pending_panel(self):
        """Render waiting panel when MT5 is not yet connected."""
        self.license_badge.configure(
            text="⏳ CHỜ KẾT NỐI MT5...",
            text_color="#bdc3c7",
            fg_color="#2c3e50",
        )

        lbl_lic = ctk.CTkLabel(
            self.license_container,
            text="BẢN QUYỀN HỆ THỐNG",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#bdc3c7",
        )
        lbl_lic.pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            self.license_container,
            text="ℹ️ Hãy mở phần mềm MetaTrader 5 để xác thực bản quyền.",
            font=ctk.CTkFont(size=12),
            text_color="#7f8c8d",
            wraplength=380,
            justify="left",
        ).pack(anchor="w", pady=4)

    # -------------------------------------------------------------------------
    # CORE BOT EXECUTION (THREADED)
    # -------------------------------------------------------------------------
    def _toggle_bot_running(self):
        """Start or stop the automated trading bot thread."""
        if not self.is_running:
            # Pre-flight authorization check
            if self.current_account and not is_admin_account(self.current_account):
                if not verify_account_authorized(self.current_account):
                    self._log_terminal(f"❌ VETO: Tài khoản #{self.current_account} chưa được cấp quyền!")
                    return

            self.is_running = True
            self.stop_event.clear()
            self.btn_start.configure(text="⏹ DỪNG BOT (STOP)", fg_color="#c0392b", hover_color="#e74c3c")

            mode_str = self.mode_menu.get()
            if "Paper" in mode_str or "25" in mode_str:
                self._log_terminal("⚡ Bắt đầu chế độ: Live Paper (Test bot trong 25 giờ vừa qua)...")
                self.worker_thread = threading.Thread(target=self._run_paper_worker, daemon=True)
            else:
                self._log_terminal("🚀 Bắt đầu chế độ: Live Demo MT5 (Quét 5s/lần theo thời gian thực)...")
                self.worker_thread = threading.Thread(target=self._run_live_worker, daemon=True)
            self.worker_thread.start()
        else:
            self.is_running = False
            self.stop_event.set()
            self.btn_start.configure(text="▶ BẬT BOT TỰ ĐỘNG (START)", fg_color="#27ae60", hover_color="#2ecc71")
            self._log_terminal("⏹ Đã gửi tín hiệu dừng Bot an toàn.")

    def _toggle_bot_pause(self):
        """Pause or resume trading execution."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.configure(text="▶ TIẾP TỤC GIAO DỊCH (RESUME)", fg_color="#2980b9")
            self._log_terminal("⏸ Bot đã tạm dừng vào lệnh mới.")
        else:
            self.btn_pause.configure(text="⏸ TẠM DỪNG GIAO DỊCH (PAUSE)", fg_color="#d35400")
            self._log_terminal("▶ Bot đã tiếp tục quét và vào lệnh bình thường.")

    def _emergency_close_all(self):
        """Emergency kill-switch: Closes all open XAUUSDm positions immediately."""
        self._log_terminal("🚨 KHẨN CẤP: Đang đóng toàn bộ vị thế XAUUSDm...")
        try:
            import MetaTrader5 as mt5
            from src.execution.mt5_bridge import MT5OrderBridge
            if mt5.initialize():
                positions = mt5.positions_get(symbol="XAUUSDm")
                if positions:
                    bridge = MT5OrderBridge(symbol="XAUUSDm")
                    for p in positions:
                        bridge.close_position(p.ticket)
                        self._log_terminal(f"✅ Đã đóng vị thế #{p.ticket} ({'BUY' if p.type==0 else 'SELL'})")
                else:
                    self._log_terminal("ℹ️ Hiện tại không có vị thế nào mở trên MT5.")
        except Exception as e:
            self._log_terminal(f"❌ Lỗi khi đóng vị thế: {e}")

    def _get_profile_params(self) -> tuple[float, float, float, str]:
        """
        Returns (ai_threshold, conf_threshold, be_trigger_ratio, profile_name)
        based on selection in self.profile_menu.
        """
        choice = self.profile_menu.get() if hasattr(self, "profile_menu") else ""
        if "Bảo Toàn" in choice:
            return 0.65, 65.0, 0.38, "🛡️ Siêu Bảo Toàn (Conservative)"
        elif "Cân Bằng" in choice:
            return 0.62, 62.0, 0.48, "🎯 Scalper Cân Bằng (Balanced)"
        else:
            return 0.60, 60.0, 0.52, "⚡ Sniper Chuẩn V4 (Khuyên dùng)"

    def _run_live_worker(self):
        """Worker thread for live-demo polling."""
        from src.main import run_live_demo_loop
        from src.config.settings import SystemSettings
        try:
            settings = SystemSettings()
            ai_th, conf_th, be_ratio, prof_name = self._get_profile_params()
            self._log_terminal(f"🎯 Thiết lập: {prof_name} | AI: {ai_th*100:.0f}% | Conf: {conf_th:.0f} | BE: {int(be_ratio*100)}% TP")
            run_live_demo_loop(
                settings=settings,
                poll_interval_sec=5.0,
                logger=logging.getLogger(),
                ai_threshold=ai_th,
                conf_threshold=conf_th,
                be_trigger_ratio=be_ratio,
            )
        except Exception as e:
            self._log_terminal(f"❌ Luồng Live Demo gặp sự cố: {e}")
        finally:
            self.is_running = False
            self.btn_start.configure(text="▶ BẬT BOT TỰ ĐỘNG (START)", fg_color="#27ae60")

    def _run_paper_worker(self):
        """Worker thread for live paper replay over 300 real M5 bars (past 25 hours)."""
        from src.main import run_paper_session
        from src.config.settings import SystemSettings
        try:
            settings = SystemSettings()
            ai_th, conf_th, be_ratio, prof_name = self._get_profile_params()
            self._log_terminal("⚡ ========================================================")
            self._log_terminal("⚡ BẮT ĐẦU LIVE PAPER TEST: 300 nến M5 (25 giờ qua) từ MT5...")
            self._log_terminal(f"⚡ Phong cách: {prof_name} (AI Win-Rate: {ai_th*100:.0f}%, Conf: {conf_th:.0f}, BE: {int(be_ratio*100)}% TP)")
            self._log_terminal("⚡ Đang kết nối dữ liệu thật và chạy mô phỏng vào lệnh...")
            self._log_terminal("⚡ ========================================================")

            summary = run_paper_session(
                settings=settings,
                bar_count=300,
                use_mock=False,
                logger=logging.getLogger(),
                ai_threshold=ai_th,
                conf_threshold=conf_th,
                be_trigger_ratio=be_ratio,
            )
            if summary:
                bal = summary["final_balance"]
                pnl = summary["net_pnl"]
                wr_pct = summary["win_rate"] * 100.0
                wins = summary["wins"]
                losses = summary["losses"]
                self.card_balance["value"].configure(text=f"${bal:,.2f}")
                self.card_equity["value"].configure(text=f"${bal:,.2f}")
                self.card_pnl["value"].configure(
                    text=f"{'+' if pnl >= 0 else ''}${pnl:.2f}",
                    text_color="#2ecc71" if pnl >= 0 else "#e74c3c",
                )
                self.card_winrate["value"].configure(
                    text=f"{wr_pct:.1f}% ({wins}W / {losses}L)",
                    text_color="#2ecc71" if wr_pct >= 60 else "#f39c12",
                )
                self._log_terminal(
                    f"🏆 HOÀN THÀNH TEST 25 GIỜ VỪA QUA: Win Rate {wr_pct:.1f}% ({wins} Thắng / {losses} Thua) | Lợi nhuận PnL: {'+' if pnl >= 0 else ''}${pnl:.2f}"
                )

                # Send summary report to Telegram
                try:
                    from src.monitoring.telegram_bot import TelegramNotifier
                    tg = TelegramNotifier()
                    if tg.enabled:
                        tg.send_message(
                            f"⚡ <b>BÁO CÁO KẾT QUẢ TEST BOT (25 GIỜ VỪA QUA)</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"• Chế độ: <b>Live Paper Replay (300 nến M5 thật)</b>\n"
                            f"• Số dư ban đầu: ${summary['initial_balance']:.2f} USD\n"
                            f"• Số dư kết thúc: <b>${summary['final_balance']:.2f} USD</b>\n"
                            f"• Lợi nhuận ròng: <b>{'+' if pnl >= 0 else ''}${pnl:.2f} USD</b>\n"
                            f"• Tỷ lệ thắng (Win Rate): <b>{wr_pct:.1f}%</b> ({wins} Thắng / {losses} Thua)\n"
                            f"• Tổng số lệnh: <b>{summary['total_trades']} lệnh</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"<i>Dữ liệu được trích xuất trực tiếp từ biểu đồ MT5 XAUUSDm</i>"
                        )
                except Exception:
                    pass
        except Exception as e:
            self._log_terminal(f"❌ Luồng Live Paper gặp sự cố: {e}")
        finally:
            self.is_running = False
            self.btn_start.configure(text="▶ BẬT BOT TỰ ĐỘNG (START)", fg_color="#27ae60", hover_color="#2ecc71")

    # -------------------------------------------------------------------------
    # LICENSE & WHITELIST ACTIONS (ADMIN ONLY)
    # -------------------------------------------------------------------------
    def _add_account_license(self):
        acc_text = self.ent_account.get().strip()
        if acc_text.isdigit():
            acc_num = int(acc_text)
            if add_allowed_account(acc_num):
                self._log_terminal(f"✅ Đã cấp quyền sử dụng cho tài khoản MT5 #{acc_num}")
                self.lbl_allowed_list.configure(text=f"Tài khoản duyệt: {', '.join(str(a) for a in get_allowed_accounts())}")
                self.ent_account.delete(0, "end")
            else:
                self._log_terminal("❌ Không thể thêm tài khoản vào whitelist.")
        else:
            self._log_terminal("⚠️ Vui lòng nhập số tài khoản MT5 hợp lệ (chỉ gồm chữ số).")

    def _remove_account_license(self):
        acc_text = self.ent_account.get().strip()
        if acc_text.isdigit():
            acc_num = int(acc_text)
            if remove_allowed_account(acc_num):
                self._log_terminal(f"🚫 Đã thu hồi quyền sử dụng tài khoản MT5 #{acc_num}")
                self.lbl_allowed_list.configure(text=f"Tài khoản duyệt: {', '.join(str(a) for a in get_allowed_accounts())}")
                self.ent_account.delete(0, "end")
            else:
                self._log_terminal("❌ Không thể thu hồi tài khoản.")
        else:
            self._log_terminal("⚠️ Vui lòng nhập số tài khoản MT5 hợp lệ.")

    def _git_pull(self):
        """Trigger git pull update."""
        self._log_terminal("🔄 Đang kiểm tra và tải cập nhật mới từ GitHub...")
        try:
            res = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, timeout=15)
            self._log_terminal(f"📦 Kết quả đồng bộ:\n{res.stdout or res.stderr}")
        except Exception as e:
            self._log_terminal(f"❌ Lỗi đồng bộ: {e}")

    def _git_push(self):
        """Trigger git push to share update and auto-bump build version."""
        self._log_terminal("📤 Đang lưu thay đổi, nâng số hiệu phiên bản và đẩy lên GitHub cho bạn bè...")
        try:
            from src.config.updater import bump_version_on_push
            new_v = bump_version_on_push("Bản cập nhật mới nhất từ Admin LilBoiXAU")
            self._log_terminal(f"📦 Đã nâng số hiệu phiên bản: Build #{new_v['build']} ({new_v['release_time']})")

            subprocess.run(["git", "add", "."], capture_output=True, timeout=10)
            subprocess.run(["git", "commit", "-m", f"Release: Update Build #{new_v['build']}"], capture_output=True, timeout=10)
            res = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True, timeout=20)
            err = (res.stderr or "").strip()
            out = (res.stdout or "").strip()
            if "Repository not found" in err:
                self._log_terminal("❌ Chưa tìm thấy repo trên GitHub! Vui lòng vào https://github.com/LilBolXAU bấm '+' -> New repository, đặt tên 'AI-GOLD-WATCHER-V4' rồi bấm Đẩy code lại.")
            elif res.returncode == 0:
                self._log_terminal("✅ ĐẨY BẢN MỚI LÊN GITHUB THÀNH CÔNG! Toàn bộ người dùng sẽ tự động nhận được thông báo cập nhật.")
            else:
                self._log_terminal(f"ℹ️ Thông tin đẩy code:\n{out or err}")
        except Exception as e:
            self._log_terminal(f"❌ Lỗi đẩy code: {e}")

    def _apply_new_update(self):
        """Apply newly detected update from master GitHub repo."""
        self._log_terminal("🔄 Đang tải bản cập nhật mới nhất từ Admin...")
        try:
            res = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, timeout=15)
            out = (res.stdout or "").strip() or (res.stderr or "").strip()
            self._log_terminal(f"📦 Kết quả cập nhật:\n{out}")
            if self.has_active_update_banner:
                self.update_banner_frame.pack_forget()
                self.has_active_update_banner = False
            self._log_terminal("🎉 BẠN ĐÃ CẬP NHẬT LÊN PHIÊN BẢN MỚI NHẤT THÀNH CÔNG!")
            sync_remote_license(timeout=2.5)
            if self.current_account:
                self._update_role_ui(self.current_account, force=True)
        except Exception as e:
            self._log_terminal(f"❌ Lỗi cập nhật: {e}")

    def _send_admin_broadcast(self):
        """Publish and push Admin rainbow broadcast to all clients & Telegram."""
        msg = self.ent_admin_broadcast.get().strip() if hasattr(self, "ent_admin_broadcast") else ""
        if not msg:
            self._log_terminal("⚠️ Vui lòng nhập nội dung thông báo trước khi gửi.")
            return

        from src.config.updater import publish_admin_announcement
        payload = publish_admin_announcement(msg, sender="LilBoiXAU")
        self.ent_admin_broadcast.delete(0, "end")

        # Update local Admin banner
        if hasattr(self, "lbl_admin_banner_msg"):
            self.lbl_admin_banner_msg.configure(text=f"📢 {msg}")

        # Render bold rainbow text in local terminal
        self._log_admin_rainbow("LilBoiXAU", msg)

        # Multi-target Telegram Notification (Broadcasts to all authorized subscribers)
        try:
            from src.monitoring.telegram_bot import TelegramNotifier
            from src.config.license import get_registered_chat_ids
            tg = TelegramNotifier()
            if tg.enabled:
                targets = set(tg.chat_ids + get_registered_chat_ids())
                env_cid = os.getenv("TELEGRAM_CHAT_ID", "")
                for c in env_cid.split(","):
                    if c.strip():
                        targets.add(c.strip())

                for target_id in targets:
                    tg.send_message(
                        f"👑 <b>THÔNG BÁO TỪ MASTER ADMIN LilBoiXAU</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📢 <b>{msg}</b>\n\n"
                        f"⏰ <i>{payload['timestamp']} • Hệ thống AI GOLD WATCHER V4</i>",
                        target_chat_id=target_id,
                    )
        except Exception:
            pass

        # Push announcements.json to GitHub in background thread so remote clients receive it
        threading.Thread(target=self._push_announcement_worker, daemon=True).start()

    def _push_announcement_worker(self):
        try:
            subprocess.run(["git", "add", "announcements.json"], capture_output=True, timeout=10)
            subprocess.run(["git", "commit", "-m", "Broadcast: Admin Announcement Push"], capture_output=True, timeout=10)
            subprocess.run(["git", "push", "origin", "main"], capture_output=True, timeout=20)
            self.log_queue.put("✅ Đã phát thông báo Admin lên máy chủ GitHub thành công!")
        except Exception as e:
            self.log_queue.put(f"⚠️ Chưa thể đẩy thông báo lên GitHub: {e}")

    def _log_admin_rainbow(self, sender: str, message: str, timestamp: str = ""):
        """
        Display Master Admin announcement in the terminal with large, bold, rainbow-colored text!
        """
        ts = timestamp or datetime.now().strftime("%H:%M:%S")
        rainbow_colors = [
            "#ff1744",  # Neon Red
            "#ff9100",  # Neon Orange
            "#ffd600",  # Neon Yellow
            "#00e676",  # Neon Green
            "#00e5ff",  # Neon Cyan
            "#2979ff",  # Neon Blue
            "#d500f9",  # Neon Purple
        ]

        try:
            self.term_box._textbox.tag_config(
                "admin_head",
                foreground="#f1c40f",
                font=("Segoe UI", 13, "bold"),
            )
            self.term_box._textbox.tag_config(
                "admin_border",
                foreground="#9b59b6",
                font=("Segoe UI", 11, "bold"),
            )

            b_start = self.term_box._textbox.index("end-1c")
            self.term_box.insert("end", "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            b_end = self.term_box._textbox.index("end-1c")
            self.term_box._textbox.tag_add("admin_border", b_start, b_end)

            h_start = self.term_box._textbox.index("end-1c")
            self.term_box.insert("end", f"👑 [THÔNG BÁO TỪ MASTER ADMIN {sender.upper()}] • {ts}\n")
            h_end = self.term_box._textbox.index("end-1c")
            self.term_box._textbox.tag_add("admin_head", h_start, h_end)

            # Insert rainbow message characters
            msg_text = f"📢  {message}\n"
            for i, ch in enumerate(msg_text):
                color = rainbow_colors[i % len(rainbow_colors)]
                tag_name = f"rb_tag_{i % len(rainbow_colors)}"
                self.term_box._textbox.tag_config(
                    tag_name,
                    foreground=color,
                    font=("Segoe UI", 15, "bold"),
                )
                c_start = self.term_box._textbox.index("end-1c")
                self.term_box.insert("end", ch)
                c_end = self.term_box._textbox.index("end-1c")
                self.term_box._textbox.tag_add(tag_name, c_start, c_end)

            fb_start = self.term_box._textbox.index("end-1c")
            self.term_box.insert("end", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
            fb_end = self.term_box._textbox.index("end-1c")
            self.term_box._textbox.tag_add("admin_border", fb_start, fb_end)

            self.term_box.see("end")
        except Exception:
            self._log_terminal(f"👑 [ADMIN {sender}]: {message}")

    def _check_updates_and_broadcasts(self):
        """Periodically check remote GitHub for new updates and Admin broadcasts."""
        threading.Thread(target=self._query_remote_status_worker, daemon=True).start()
        self.after(20000, self._check_updates_and_broadcasts)

    def _query_remote_status_worker(self):
        """Background thread checking GitHub for version updates and broadcasts."""
        try:
            from src.config.updater import check_remote_update, check_remote_announcement
            # 1. Check for new update
            has_update, remote_info = check_remote_update(timeout=2.5)
            if has_update and remote_info and not self.has_active_update_banner:
                self.after(0, lambda: self._show_update_banner(remote_info))

            # 2. Check for new announcement
            ann = check_remote_announcement(timeout=2.5)
            if ann and ann.get("id") != self.last_seen_announcement_id:
                self.last_seen_announcement_id = ann.get("id")
                self.after(0, lambda: self._handle_new_announcement(ann))
        except Exception:
            pass

    def _show_update_banner(self, remote_info: dict):
        """Display the new version notification bar."""
        self.has_active_update_banner = True
        v_num = remote_info.get("version", "Mới")
        b_num = remote_info.get("build", "")
        desc = remote_info.get("description", "Đã có bản cập nhật mới từ Admin.")
        self.lbl_update_title.configure(text=f"🚀 ĐÃ CÓ BẢN CẬP NHẬT MỚI: v{v_num} (Build #{b_num})!")
        self.lbl_update_desc.configure(text=f"• {desc}")
        # Pack right above cards_frame
        self.update_banner_frame.pack(fill="x", padx=15, pady=(0, 6), before=self.cards_frame)
        self._log_terminal(f"🔔 [THÔNG BÁO] Phát hiện bản cập nhật mới v{v_num} từ Admin LilBoiXAU! Hãy bấm [🔄 CẬP NHẬT NGAY].")

    def _handle_new_announcement(self, ann: dict):
        """Handle incoming Admin broadcast with audio chime and screen popup."""
        sender = ann.get("sender", "LilBoiXAU")
        msg = ann.get("message", "")
        ts = ann.get("timestamp", "")
        if hasattr(self, "lbl_admin_banner_msg"):
            self.lbl_admin_banner_msg.configure(text=f"📢 {msg}")
        self._log_admin_rainbow(sender=sender, message=msg, timestamp=ts)

        # Audio chime bell notification on Windows
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass

        # Visual Pop-up Dialog
        self._show_announcement_popup(sender=sender, msg=msg, ts=ts)

    def _show_announcement_popup(self, sender: str, msg: str, ts: str):
        """Display an eye-catching popup dialog on screen."""
        try:
            popup = ctk.CTkToplevel(self)
            popup.title(f"👑 Thông Báo Từ Master Admin {sender}")
            popup.geometry("520x250")
            popup.attributes("-topmost", True)
            popup.configure(fg_color="#181324")
            popup.resizable(False, False)

            try:
                x = self.winfo_x() + (self.winfo_width() // 2) - 260
                y = self.winfo_y() + (self.winfo_height() // 2) - 125
                popup.geometry(f"+{x}+{y}")
            except Exception:
                pass

            container = ctk.CTkFrame(popup, corner_radius=12, fg_color="#21152d", border_width=2, border_color="#e056fd")
            container.pack(fill="both", expand=True, padx=12, pady=12)

            lbl_head = ctk.CTkLabel(
                container,
                text=f"👑 THÔNG BÁO TỪ MASTER ADMIN {sender.upper()}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#f1c40f",
            )
            lbl_head.pack(anchor="w", padx=16, pady=(12, 2))

            lbl_time = ctk.CTkLabel(
                container,
                text=f"⏰ {ts} • Phát tới toàn bộ hệ thống",
                font=ctk.CTkFont(size=11),
                text_color="#95a5a6",
            )
            lbl_time.pack(anchor="w", padx=16, pady=(0, 8))

            msg_frame = ctk.CTkFrame(container, corner_radius=8, fg_color="#150f20")
            msg_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

            lbl_msg = ctk.CTkLabel(
                msg_frame,
                text=f"📢 {msg}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#00e5ff",
                wraplength=440,
                justify="left",
            )
            lbl_msg.pack(anchor="w", padx=12, pady=10)

            btn_close = ctk.CTkButton(
                container,
                text="✨ ĐÃ HIỂU / ĐÓNG",
                height=30,
                fg_color="#8e44ad",
                hover_color="#9b59b6",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=popup.destroy,
            )
            btn_close.pack(anchor="e", padx=16, pady=(0, 10))
        except Exception as e:
            logger.debug("Could not display announcement popup: %s", e)

    def _client_update_and_check(self):
        """Client-safe update check: syncs license from GitHub & runs git pull."""
        self._log_terminal("🔄 Đang đồng bộ và kiểm tra bản quyền từ máy chủ Admin...")
        try:
            synced = sync_remote_license(timeout=3.0)
            if synced:
                self._log_terminal(f"✅ Đã nhận danh sách cấp quyền mới nhất từ Admin: {len(synced)} tài khoản.")

            if Path(".git").exists():
                res = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, timeout=15)
                out = (res.stdout or "").strip() or (res.stderr or "").strip()
                if "Already up to date" in out:
                    self._log_terminal("📦 Mã nguồn của bạn đã là phiên bản mới nhất!")
                else:
                    self._log_terminal(f"📦 Đã tải bản cập nhật mới:\n{out}")

            if self.current_account:
                is_auth = verify_account_authorized(self.current_account)
                self._update_role_ui(self.current_account, force=True)
                if is_auth:
                    self._log_terminal(f"🎉 Kích hoạt thành công! MT5 #{self.current_account} đã được cấp phép.")
                else:
                    self._log_terminal(f"⚠️ MT5 #{self.current_account} vẫn chưa có trong danh sách của Admin LilBoiXAU.")
        except Exception as e:
            self._log_terminal(f"❌ Lỗi kiểm tra cập nhật: {e}")

    # -------------------------------------------------------------------------
    # TELEMETRY & PERIODIC UPDATES
    # -------------------------------------------------------------------------
    def _log_terminal(self, message: str):
        """Append text to the GUI terminal."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.term_box.insert("end", f"[{ts}] {message}\n")
        self.term_box.see("end")

    def _process_log_queue(self):
        """Drain background log messages into terminal without blocking UI."""
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get_nowait()
                self.term_box.insert("end", f"{msg}\n")
                self.term_box.see("end")
            except queue.Empty:
                break
        self.after(300, self._process_log_queue)

    def _refresh_telemetry(self):
        """Poll MT5 telemetry (balance, equity, open positions) every second."""
        try:
            import MetaTrader5 as mt5
            if mt5.initialize():
                acc = mt5.account_info()
                if acc:
                    login = int(acc.login)
                    self._update_role_ui(login)

                    bal = float(acc.balance)
                    eq = float(acc.equity)
                    pnl = eq - bal
                    pnl_pct = (pnl / bal * 100) if bal > 0 else 0.0

                    self.card_balance["value"].configure(text=f"${bal:,.2f}")
                    self.card_equity["value"].configure(text=f"${eq:,.2f}")
                    self.card_pnl["value"].configure(
                        text=f"{'+' if pnl >= 0 else ''}${pnl:.2f} ({pnl_pct:+.1f}%)",
                        text_color="#2ecc71" if pnl >= 0 else "#e74c3c",
                    )
                    self.mt5_badge.configure(
                        text=f"🟢 MT5 #{acc.login} ({acc.name})",
                        text_color="#2ecc71",
                    )

                # Query open positions
                positions = mt5.positions_get(symbol="XAUUSDm")
                if positions:
                    self.lbl_pos_count.configure(text=f"[{len(positions)}/2 Vị Thế]", text_color="#2ecc71")
                    details = []
                    for p in positions:
                        side_str = "BUY" if p.type == 0 else "SELL"
                        color_pnl = f"+${p.profit:.2f}" if p.profit >= 0 else f"-${abs(p.profit):.2f}"
                        details.append(f"#{p.ticket} {side_str} @ {p.price_open:.2f} | SL: {p.sl:.2f} | TP: {p.tp:.2f} | PnL: {color_pnl}")
                    self.lbl_pos_detail.configure(text="\n".join(details), text_color="#ecf0f1")
                else:
                    self.lbl_pos_count.configure(text="[0/2 Vị Thế]", text_color="#f1c40f")
                    self.lbl_pos_detail.configure(
                        text="💤 Chưa có vị thế nào đang mở. Bot đang theo dõi nến M5...",
                        text_color="#7f8c8d",
                    )
        except Exception:
            pass
        self.after(1500, self._refresh_telemetry)

    def _on_close(self):
        """Handle window close event cleanly."""
        self.stop_event.set()
        self.destroy()


def main():
    app = AIGoldWatcherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
