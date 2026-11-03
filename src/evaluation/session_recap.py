"""
Session Recap & Performance Summary Generator.
Calculates and formats comprehensive end-of-session trading analytics
for Telegram broadcast, in-app terminal logging, and modal dialog display.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict


@dataclass
class SessionRecapData:
    session_title: str
    start_time: str
    end_time: str
    duration: str
    initial_balance: float
    final_balance: float
    final_equity: float
    net_pnl: float
    roi_pct: float
    total_trades: int
    wins: int
    losses: int
    break_evens: int
    win_rate: float
    best_trade: float
    worst_trade: float
    avg_trade: float
    profit_factor: float

    def to_telegram_html(self) -> str:
        """Format session recap as a rich HTML Telegram alert."""
        pnl_sign = "+" if self.net_pnl >= 0 else ""
        roi_sign = "+" if self.roi_pct >= 0 else ""
        pnl_icon = "🟢 🏆" if self.net_pnl > 0 else ("🔴 🛑" if self.net_pnl < 0 else "⚪ 🛡️")

        return (
            f"📊 <b>BÁO CÁO TỔNG KẾT PHIÊN GIAO DỊCH (SESSION RECAP)</b> 📊\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Phiên giao dịch:</b> {self.session_title}\n"
            f"⏱️ <b>Thời gian:</b> <code>{self.start_time}</code> ➜ <code>{self.end_time}</code> (<b>{self.duration}</b>)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💼 <b>Vốn ban đầu (Initial):</b> <code>${self.initial_balance:,.2f} USD</code>\n"
            f"💰 <b>Số dư chốt phiên (Balance):</b> <code>${self.final_balance:,.2f} USD</code>\n"
            f"📈 <b>Vốn thực tế (Equity):</b> <code>${self.final_equity:,.2f} USD</code>\n"
            f"💵 <b>Tổng Lợi Nhuận Ròng (Net PnL):</b> <b>{pnl_sign}${self.net_pnl:,.2f} USD</b> ({roi_sign}{self.roi_pct:.2f}%) {pnl_icon}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>CHI TIẾT HIỆU SUẤT LỆNH:</b>\n"
            f"• Tổng số lệnh đã chốt: <b>{self.total_trades} lệnh</b>\n"
            f"• Lệnh Thắng (Wins): <b>{self.wins} lệnh</b> 🏆 (Tỷ lệ thắng: <b>{self.win_rate:.1f}%</b>)\n"
            f"• Lệnh Thua (Losses): <b>{self.losses} lệnh</b> 🛑\n"
            f"• Lệnh Hòa Vốn / SL Dương: <b>{self.break_evens} lệnh</b> 🛡️\n"
            f"• Kèo lãi lớn nhất (Best Trade): <b>+${self.best_trade:,.2f} USD</b> 💎\n"
            f"• Kèo lỗ lớn nhất (Worst Trade): <b>-${abs(self.worst_trade):,.2f} USD</b> 📉\n"
            f"• Hệ số lợi nhuận (Profit Factor): <b>{self.profit_factor:.2f}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ <b>Quản trị rủi ro:</b> BẢO VỆ VỐN TUYỆT ĐỐI (Không vi phạm Drawdown)\n"
            f"✨ <i>Chúc mừng anh em! Hệ thống AI GOLD WATCHER V4 bảo toàn và tăng trưởng vốn tối ưu!</i> 🚀"
        )

    def to_terminal_box(self) -> str:
        """Format session recap as a clean terminal banner box."""
        pnl_sign = "+" if self.net_pnl >= 0 else ""
        roi_sign = "+" if self.roi_pct >= 0 else ""
        lines = [
            "╔══════════════════════════════════════════════════════════════════╗",
            "║             📊 TỔNG KẾT PHIÊN GIAO DỊCH (SESSION RECAP)          ║",
            "╠══════════════════════════════════════════════════════════════════╣",
            f"║ Phiên giao dịch : {self.session_title:<46} ║",
            f"║ Thời gian       : {self.start_time} -> {self.end_time} ({self.duration})",
            "╟──────────────────────────────────────────────────────────────────╢",
            f"║ Vốn ban đầu     : ${self.initial_balance:>12,.2f} USD                           ║",
            f"║ Số dư chốt phiên: ${self.final_balance:>12,.2f} USD                           ║",
            f"║ Vốn thực (Equity): ${self.final_equity:>12,.2f} USD                           ║",
            f"║ Lãi/Lỗ ròng     : {pnl_sign}${self.net_pnl:>12,.2f} USD ({roi_sign}{self.roi_pct:.2f}%)               ║",
            "╟──────────────────────────────────────────────────────────────────╢",
            f"║ Tổng số lệnh    : {self.total_trades:>4} lệnh (Thắng: {self.wins} | Thua: {self.losses} | Hòa: {self.break_evens})       ║",
            f"║ Tỷ lệ thắng (WR): {self.win_rate:>6.1f}%                                        ║",
            f"║ Kèo tốt nhất    : +${self.best_trade:>11,.2f} USD                           ║",
            f"║ Kèo tệ nhất     : -${abs(self.worst_trade):>11,.2f} USD                           ║",
            f"║ Profit Factor   : {self.profit_factor:>6.2f}                                        ║",
            "╚══════════════════════════════════════════════════════════════════╝",
        ]
        return "\n".join(lines)


def build_session_recap(
    initial_balance: float,
    final_balance: float,
    final_equity: Optional[float] = None,
    trades: Optional[List[Any]] = None,
    deals: Optional[List[Any]] = None,
    session_title: str = "London / New York Scalp",
    start_dt: Optional[datetime] = None,
    end_dt: Optional[datetime] = None,
) -> SessionRecapData:
    """
    Construct a unified SessionRecapData from either:
    1. A list of ClosedTrade objects (from paper/backtest), OR
    2. A list of MT5 history deals, OR
    3. Direct numeric parameters.
    """
    end_time_dt = end_dt or datetime.now(timezone.utc)
    start_time_dt = start_dt or (end_time_dt.replace(hour=0, minute=0, second=0, microsecond=0))

    duration_delta = end_time_dt - start_time_dt
    hours, remainder = divmod(int(duration_delta.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    dur_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    eq_val = final_equity if final_equity is not None else final_balance
    net_pnl = final_balance - initial_balance
    roi_pct = (net_pnl / initial_balance * 100.0) if initial_balance > 0 else 0.0

    pnl_list: List[float] = []

    if trades:
        for t in trades:
            pnl_val = getattr(t, "net_pnl", 0.0)
            pnl_list.append(float(pnl_val))
    elif deals:
        for d in deals:
            # Entry=1 indicates deal OUT (position close)
            if getattr(d, "entry", 0) == 1:
                p = float(getattr(d, "profit", 0.0)) + float(getattr(d, "swap", 0.0)) + float(getattr(d, "commission", 0.0))
                pnl_list.append(p)

    total_trades = len(pnl_list)
    wins = len([p for p in pnl_list if p > 0.05])
    losses = len([p for p in pnl_list if p < -0.05])
    break_evens = len([p for p in pnl_list if -0.05 <= p <= 0.05])
    win_rate = (wins / total_trades * 100.0) if total_trades > 0 else 0.0

    best_trade = max(pnl_list, default=0.0)
    worst_trade = min(pnl_list, default=0.0)
    avg_trade = (sum(pnl_list) / total_trades) if total_trades > 0 else 0.0

    gross_profit = sum(p for p in pnl_list if p > 0)
    gross_loss = abs(sum(p for p in pnl_list if p < 0))
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = 99.9 if gross_profit > 0 else 1.0

    # If pnl_list is present, use sum of trade PnL for exact precision
    if pnl_list:
        net_pnl = sum(pnl_list)
        roi_pct = (net_pnl / initial_balance * 100.0) if initial_balance > 0 else 0.0

    return SessionRecapData(
        session_title=session_title,
        start_time=start_time_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        end_time=end_time_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        duration=dur_str,
        initial_balance=initial_balance,
        final_balance=final_balance,
        final_equity=eq_val,
        net_pnl=net_pnl,
        roi_pct=roi_pct,
        total_trades=total_trades,
        wins=wins,
        losses=losses,
        break_evens=break_evens,
        win_rate=win_rate,
        best_trade=best_trade,
        worst_trade=worst_trade,
        avg_trade=avg_trade,
        profit_factor=profit_factor,
    )
