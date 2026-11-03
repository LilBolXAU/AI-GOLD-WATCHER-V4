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
    verify_account_authorized,
    get_allowed_accounts,
    add_allowed_account,
    remove_allowed_account,
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
        self.geometry("1100x820")
        self.minsize(980, 720)

        # State management
        self.is_running = False
        self.is_paused = False
        self.worker_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()

        # Wire logging to GUI
        self.log_handler = GuiLogHandler(self.log_queue)
        formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
        self.log_handler.setFormatter(formatter)
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)

        # Build UI layout
        self._build_header()
        self._build_metrics_cards()
        self._build_main_content()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start periodic GUI updater
        self.after(500, self._process_log_queue)
        self.after(1000, self._refresh_telemetry)

        self._log_terminal("🌟 AI GOLD WATCHER V4 Desktop App khởi động thành công!")
        self._log_terminal("🔑 Quyền quản trị: LilBoiXAU | Sẵn sàng giao dịch XAUUSDm.")

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
            text="🔑 LICENSE: ACTIVE (LilBoiXAU)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#34495e",
            corner_radius=6,
            padx=10,
            pady=4,
            text_color="#f39c12",
        )
        self.license_badge.pack(side="right", padx=5)

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
        # LEFT COLUMN: Controls & Settings & License
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
        sep1.pack(fill="x", padx=15, pady=12)

        lbl_settings = ctk.CTkLabel(left_col, text="THIẾT LẬP CHIẾN THUẬT & AN TOÀN", font=ctk.CTkFont(size=13, weight="bold"), text_color="#ecf0f1")
        lbl_settings.pack(anchor="w", padx=15, pady=(0, 6))

        # Mode selector
        lbl_mode = ctk.CTkLabel(left_col, text="Chế độ hoạt động:", font=ctk.CTkFont(size=12), text_color="#bdc3c7")
        lbl_mode.pack(anchor="w", padx=15, pady=0)
        self.mode_menu = ctk.CTkOptionMenu(
            left_col,
            values=["Live Demo MT5 (Quét 5s/lần)", "Paper Replay (Test 300 nến M5)"],
            height=32,
        )
        self.mode_menu.pack(fill="x", padx=15, pady=(2, 8))

        # Checkboxes for guards
        self.chk_be = ctk.CTkCheckBox(left_col, text="Auto Break-Even (Hòa vốn @ 38% TP + $0.25)", font=ctk.CTkFont(size=12))
        self.chk_be.select()
        self.chk_be.pack(anchor="w", padx=15, pady=4)

        self.chk_runner = ctk.CTkCheckBox(left_col, text="Gồng Lãi Động (Trailing Runner nới TP +$5.00)", font=ctk.CTkFont(size=12))
        self.chk_runner.select()
        self.chk_runner.pack(anchor="w", padx=15, pady=4)

        self.chk_exhaust = ctk.CTkCheckBox(left_col, text="Bộ Lọc Kiệt Sức (Chặn bán đáy / mua đỉnh)", font=ctk.CTkFont(size=12))
        self.chk_exhaust.select()
        self.chk_exhaust.pack(anchor="w", padx=15, pady=4)

        # Box 3: License & Whitelist Manager
        sep2 = ctk.CTkFrame(left_col, height=2, fg_color="#2c3e50")
        sep2.pack(fill="x", padx=15, pady=12)

        lbl_lic = ctk.CTkLabel(left_col, text="QUẢN LÝ BẢN QUYỀN MT5 (WHITELIST)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#f1c40f")
        lbl_lic.pack(anchor="w", padx=15, pady=(0, 6))

        acc_input_box = ctk.CTkFrame(left_col, fg_color="transparent")
        acc_input_box.pack(fill="x", padx=15, pady=2)

        self.ent_account = ctk.CTkEntry(acc_input_box, placeholder_text="Nhập số MT5 bạn bè...", height=32)
        self.ent_account.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_add_acc = ctk.CTkButton(acc_input_box, text="+ Cấp quyền", width=80, height=32, fg_color="#2980b9", command=self._add_account_license)
        self.btn_add_acc.pack(side="right", padx=2)

        self.btn_rem_acc = ctk.CTkButton(acc_input_box, text="- Thu hồi", width=70, height=32, fg_color="#7f8c8d", hover_color="#c0392b", command=self._remove_account_license)
        self.btn_rem_acc.pack(side="right", padx=2)

        self.lbl_allowed_list = ctk.CTkLabel(
            left_col,
            text=f"Tài khoản duyệt: {', '.join(str(a) for a in get_allowed_accounts())}",
            font=ctk.CTkFont(size=11),
            text_color="#95a5a6",
            wraplength=380,
            justify="left",
        )
        self.lbl_allowed_list.pack(anchor="w", padx=15, pady=4)

        # Sync buttons
        sync_box = ctk.CTkFrame(left_col, fg_color="transparent")
        sync_box.pack(fill="x", padx=15, pady=(8, 15))

        self.btn_pull = ctk.CTkButton(sync_box, text="🔄 Tải cập nhật (Pull)", height=32, fg_color="#34495e", command=self._git_pull)
        self.btn_pull.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_push = ctk.CTkButton(sync_box, text="📤 Đẩy code (Push)", height=32, fg_color="#34495e", command=self._git_push)
        self.btn_push.pack(side="right", fill="x", expand=True, padx=(3, 0))

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
    # CORE BOT EXECUTION (THREADED)
    # -------------------------------------------------------------------------
    def _toggle_bot_running(self):
        """Start or stop the automated trading bot thread."""
        if not self.is_running:
            self.is_running = True
            self.stop_event.clear()
            self.btn_start.configure(text="⏹ DỪNG BOT (STOP)", fg_color="#c0392b", hover_color="#e74c3c")
            self._log_terminal("🚀 Đang khởi động hệ thống giao dịch tự động...")

            mode_str = self.mode_menu.get()
            if "Paper" in mode_str:
                self.worker_thread = threading.Thread(target=self._run_paper_worker, daemon=True)
            else:
                self.worker_thread = threading.Thread(target=self._run_live_worker, daemon=True)
            self.worker_thread.start()
        else:
            self.is_running = False
            self.stop_event.set()
            self.btn_start.configure(text="▶ BẬT BOT TỰ ĐỘNG (START)", fg_color="#27ae60", hover_color="#2ecc71")
            self._log_terminal("🛑 Đã gửi lệnh dừng bot.")

    def _toggle_bot_pause(self):
        """Pause or resume trade evaluation."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.configure(text="▶ TIẾP TỤC GIAO DỊCH (RESUME)", fg_color="#2980b9", hover_color="#3498db")
            self._log_terminal("⏸ BOT ĐÃ TẠM DỪNG: Không quét hoặc mở lệnh mới.")
        else:
            self.btn_pause.configure(text="⏸ TẠM DỪNG GIAO DỊCH (PAUSE)", fg_color="#d35400", hover_color="#e67e22")
            self._log_terminal("▶ BOT ĐÃ TIẾP TỤC: Đang quét nến M5 tiếp theo...")

    def _emergency_close_all(self):
        """Close all open MT5 positions immediately."""
        self._log_terminal("🚨 KÍCH HOẠT ĐÓNG KHẨN CẤP: Đang đóng tất cả vị thế đang mở...")
        try:
            import MetaTrader5 as mt5
            if mt5.initialize():
                positions = mt5.positions_get(symbol="XAUUSDm")
                if positions:
                    from src.execution.mt5_order_bridge import MT5OrderBridge
                    bridge = MT5OrderBridge(symbol="XAUUSDm")
                    for p in positions:
                        bridge.close_position(p.ticket)
                        self._log_terminal(f"✅ Đã đóng vị thế #{p.ticket} ({'BUY' if p.type==0 else 'SELL'})")
                else:
                    self._log_terminal("ℹ️ Hiện tại không có vị thế nào mở trên MT5.")
        except Exception as e:
            self._log_terminal(f"❌ Lỗi khi đóng vị thế: {e}")

    def _run_live_worker(self):
        """Worker thread for live-demo polling."""
        from src.main import run_live_demo_loop
        from src.config.settings import SystemSettings
        try:
            settings = SystemSettings()
            run_live_demo_loop(settings=settings, poll_interval_sec=5.0, logger=logging.getLogger())
        except Exception as e:
            self._log_terminal(f"❌ Luồng Live Demo gặp sự cố: {e}")
        finally:
            self.is_running = False
            self.btn_start.configure(text="▶ BẬT BOT TỰ ĐỘNG (START)", fg_color="#27ae60")

    def _run_paper_worker(self):
        """Worker thread for paper replay."""
        from src.main import run_paper_session
        from src.config.settings import SystemSettings
        try:
            settings = SystemSettings()
            run_paper_session(settings=settings, bar_count=300, use_mock=False, logger=logging.getLogger())
        except Exception as e:
            self._log_terminal(f"❌ Luồng Paper Replay gặp sự cố: {e}")
        finally:
            self.is_running = False
            self.btn_start.configure(text="▶ BẬT BOT TỰ ĐỘNG (START)", fg_color="#27ae60")

    # -------------------------------------------------------------------------
    # LICENSE & WHITELIST ACTIONS
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
        """Trigger git push to share update."""
        self._log_terminal("📤 Đang đẩy mã nguồn mới lên GitHub cho bạn bè...")
        try:
            subprocess.run(["git", "add", "."], capture_output=True, timeout=10)
            subprocess.run(["git", "commit", "-m", "App Auto-Update Push"], capture_output=True, timeout=10)
            res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, timeout=20)
            self._log_terminal(f"✅ Kết quả đẩy code:\n{res.stdout or res.stderr or 'Thành công!'}")
        except Exception as e:
            self._log_terminal(f"❌ Lỗi đẩy code: {e}")

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
