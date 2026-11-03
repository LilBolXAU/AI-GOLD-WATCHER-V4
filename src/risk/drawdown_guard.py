"""
Drawdown and loss circuit breakers for AI GOLD WATCHER V4.
Enforces dynamic daily loss limits (8% of equity), max peak-to-trough drawdown (15%),
and consecutive loss pauses (3 consecutive losses).
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Tuple, Optional


@dataclass
class DrawdownState:
    daily_realized_pnl: float = 0.0
    daily_unrealized_pnl: float = 0.0
    consecutive_losses: int = 0
    peak_equity: float = 50.0
    current_equity: float = 50.0
    is_daily_breaker_tripped: bool = False
    is_consecutive_breaker_tripped: bool = False
    consecutive_trip_time: Optional[datetime] = None
    last_reset_date: date = date.today()


class DrawdownGuard:
    """
    Enforces dynamic daily loss limits (8% of equity), max drawdown, and consecutive loss pauses.
    """

    def __init__(
        self,
        reference_balance: float = 50.0,
        daily_loss_limit_usd: Optional[float] = None,
        daily_loss_limit_pct: float = 0.08,
        max_consecutive_losses: int = 3,
        max_drawdown_pct: float = 0.15,
        consecutive_pause_minutes: float = 60.0,
    ):
        self.reference_balance = reference_balance
        self.daily_loss_limit_pct = daily_loss_limit_pct
        # If daily_loss_limit_usd explicitly given, use it, else calculate from pct
        self.daily_loss_limit_usd = (
            daily_loss_limit_usd
            if daily_loss_limit_usd is not None
            else round(reference_balance * daily_loss_limit_pct, 2)
        )
        self.max_consecutive_losses = max_consecutive_losses
        self.max_drawdown_pct = max_drawdown_pct
        self.consecutive_pause_minutes = consecutive_pause_minutes

        self.state = DrawdownState(
            peak_equity=reference_balance, current_equity=reference_balance
        )

    @property
    def effective_daily_limit(self) -> float:
        """Dynamic daily loss dollar limit based on current reference balance."""
        if self.daily_loss_limit_usd is not None:
            return self.daily_loss_limit_usd
        return max(2.00, round(self.reference_balance * self.daily_loss_limit_pct, 2))

    def update_live_equity(self, live_equity: float, current_dt: datetime) -> None:
        """Update live equity from MT5 terminal telemetry."""
        self.check_daily_reset(current_dt)
        self.state.current_equity = live_equity
        if live_equity > self.state.peak_equity:
            self.state.peak_equity = live_equity

    def check_daily_reset(self, current_dt: datetime) -> None:
        """Reset daily PnL accumulator at UTC midnight and update reference balance."""
        current_date = current_dt.date()
        if current_date > self.state.last_reset_date:
            self.state.daily_realized_pnl = 0.0
            self.state.is_daily_breaker_tripped = False
            self.state.consecutive_losses = 0
            self.state.is_consecutive_breaker_tripped = False
            self.state.consecutive_trip_time = None
            self.state.last_reset_date = current_date
            self.reference_balance = self.state.current_equity
            self.daily_loss_limit_usd = round(self.reference_balance * self.daily_loss_limit_pct, 2)

    def record_trade_result(self, net_pnl: float, current_dt: datetime) -> None:
        """Update state when a trade closes."""
        self.check_daily_reset(current_dt)
        self.state.daily_realized_pnl += net_pnl
        self.state.current_equity += net_pnl

        if self.state.current_equity > self.state.peak_equity:
            self.state.peak_equity = self.state.current_equity

        # Track consecutive losses
        if net_pnl < 0:
            self.state.consecutive_losses += 1
            if self.state.consecutive_losses >= self.max_consecutive_losses:
                self.state.is_consecutive_breaker_tripped = True
                self.state.consecutive_trip_time = current_dt
        else:
            self.state.consecutive_losses = 0
            self.state.is_consecutive_breaker_tripped = False
            self.state.consecutive_trip_time = None

        # Check daily loss limit dynamically against effective_daily_limit
        if self.state.daily_realized_pnl <= -self.effective_daily_limit:
            self.state.is_daily_breaker_tripped = True

    def reset_breakers(self) -> None:
        """Manually reset all circuit breakers (e.g. via Telegram /resume)."""
        self.state.consecutive_losses = 0
        self.state.is_consecutive_breaker_tripped = False
        self.state.consecutive_trip_time = None
        self.state.is_daily_breaker_tripped = False

    def can_trade(self, current_dt: datetime) -> Tuple[bool, str]:
        """Verify whether new trades are permitted under drawdown limits."""
        self.check_daily_reset(current_dt)

        if self.state.is_daily_breaker_tripped:
            return (
                False,
                f"Daily loss circuit breaker tripped: ${self.state.daily_realized_pnl:.2f} <= -${self.effective_daily_limit:.2f} (8% of ${self.reference_balance:.2f})",
            )

        if self.state.is_consecutive_breaker_tripped:
            # Check if cool-off period has passed (e.g. 60 minutes)
            if self.state.consecutive_trip_time is not None:
                elapsed_min = (current_dt - self.state.consecutive_trip_time).total_seconds() / 60.0
                if elapsed_min >= self.consecutive_pause_minutes:
                    self.state.is_consecutive_breaker_tripped = False
                    self.state.consecutive_losses = 0
                    self.state.consecutive_trip_time = None
                else:
                    rem_mins = max(1, int(self.consecutive_pause_minutes - elapsed_min))
                    return (
                        False,
                        f"Consecutive loss breaker active ({self.state.consecutive_losses} losses in a row). Cooling down for {rem_mins}m (or type /resume).",
                    )
            else:
                return (
                    False,
                    f"Consecutive loss breaker tripped: {self.state.consecutive_losses} losses in a row",
                )

        # Check max drawdown from peak
        if self.state.peak_equity > 0:
            dd_pct = (self.state.peak_equity - self.state.current_equity) / self.state.peak_equity
            if dd_pct >= self.max_drawdown_pct:
                return (
                    False,
                    f"Max drawdown breach: {dd_pct*100:.1f}% >= {self.max_drawdown_pct*100:.1f}%",
                )

        return True, "Drawdown and loss limits OK."
