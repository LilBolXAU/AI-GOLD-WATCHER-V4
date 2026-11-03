"""
Central Pre-Trade Risk Engine for AI GOLD WATCHER V4.
Holds absolute veto authority over all trading signals.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.data.models import SymbolSpec
from src.scoring.signal_quality import ScoredSignal
from src.strategies.base_strategy import OrderSide
from src.risk.position_sizing import calculate_position_size
from src.risk.drawdown_guard import DrawdownGuard
from src.risk.kill_switch import KillSwitch
from src.risk.news_guard import NewsGuard


@dataclass(frozen=True)
class ApprovedOrder:
    """Pre-trade approved order ready for simulated paper execution."""
    magic_number: int
    strategy_id: str
    symbol: str
    side: OrderSide
    volume: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_usd: float
    timestamp: datetime


@dataclass(frozen=True)
class RiskCheckResult:
    is_approved: bool
    order: Optional[ApprovedOrder] = None
    rejection_reason: str = ""


class RiskGuard:
    """
    Financial & Risk Pre-Trade Gate.
    Vetoes any trade that breaches safety, sizing, spread, or drawdown limits.
    """

    def __init__(
        self,
        spec: SymbolSpec,
        drawdown_guard: Optional[DrawdownGuard] = None,
        kill_switch: Optional[KillSwitch] = None,
        news_guard: Optional[NewsGuard] = None,
        reference_balance: float = 50.0,
        max_spread_pts: int = 35,
        max_sl_pts: int = 350,
        target_risk_usd: Optional[float] = None,
        max_risk_pct: float = 0.04,
        magic_base: int = 400000,
        allow_pyramiding: bool = True,
        max_concurrent_positions: int = 2,
    ):
        self.spec = spec
        self.drawdown_guard = drawdown_guard or DrawdownGuard(
            reference_balance=reference_balance, daily_loss_limit_pct=0.08
        )
        self.kill_switch = kill_switch or KillSwitch()
        self.news_guard = news_guard
        self.reference_balance = reference_balance
        self.max_spread_pts = max_spread_pts
        self.max_sl_pts = max_sl_pts
        self.target_risk_usd = target_risk_usd
        self.max_risk_pct = max_risk_pct
        self.magic_base = magic_base
        self.allow_pyramiding = allow_pyramiding
        self.max_concurrent_positions = max_concurrent_positions
        self.active_position_count: int = 0
        self._magic_counter: int = 1

    def evaluate_signal(
        self,
        scored: ScoredSignal,
        current_spread: int,
        current_time: datetime,
        open_positions: Optional[list] = None,
    ) -> RiskCheckResult:
        """
        Evaluate signal against strict pre-trade risk controls.
        Returns RiskCheckResult with ApprovedOrder if passing, or rejection reason.
        """
        # 1. Kill switch check
        if self.kill_switch.is_triggered:
            return RiskCheckResult(
                is_approved=False,
                rejection_reason=f"VETO: Kill switch active ({self.kill_switch.reason})",
            )

        # 2. Drawdown circuit breaker check
        can_trade, dd_reason = self.drawdown_guard.can_trade(current_time)
        if not can_trade:
            return RiskCheckResult(is_approved=False, rejection_reason=f"VETO: {dd_reason}")

        # 3. High-Impact Economic News Blackout check
        if self.news_guard is not None:
            is_blackout, event, news_reason = self.news_guard.is_news_blackout(current_time)
            if is_blackout:
                return RiskCheckResult(is_approved=False, rejection_reason=f"VETO: {news_reason}")

        # 4. Position Concurrency & Institutional Pyramiding Gate
        cand = scored.candidate

        if self.active_position_count >= self.max_concurrent_positions:
            return RiskCheckResult(
                is_approved=False,
                rejection_reason=f"VETO: Position limit reached (max {self.max_concurrent_positions} concurrent positions).",
            )

        if self.active_position_count >= 1:
            if not self.allow_pyramiding:
                return RiskCheckResult(
                    is_approved=False,
                    rejection_reason="VETO: Position limit reached (max 1 concurrent position).",
                )

            # Pyramiding is enabled: verify that existing open position is 100% Risk-Free (Break-Even locked)
            if not open_positions:
                return RiskCheckResult(
                    is_approved=False,
                    rejection_reason="VETO: Position limit reached (scale-in requires existing position to lock Break-Even first).",
                )

            for p in open_positions:
                p_side = getattr(p, "side", None)
                if p_side is None:
                    p_type = getattr(p, "type", 0)
                    p_side = OrderSide.BUY if p_type == 0 else OrderSide.SELL

                # Directional check: Never hedge or open opposing trades
                if p_side != cand.side:
                    return RiskCheckResult(
                        is_approved=False,
                        rejection_reason=f"VETO: Scale-in direction conflict (open position is {p_side.value}, signal is {cand.side.value}).",
                    )

                p_entry = float(getattr(p, "entry_price", getattr(p, "price_open", 0.0)))
                p_sl = float(getattr(p, "stop_loss", getattr(p, "sl", 0.0)))

                is_be = False
                if p_side == OrderSide.BUY and p_sl >= p_entry - 0.02:
                    is_be = True
                elif p_side == OrderSide.SELL and (0.0 < p_sl <= p_entry + 0.02):
                    is_be = True

                if not is_be:
                    pos_id_str = str(getattr(p, "ticket", getattr(p, "position_id", "1")))
                    return RiskCheckResult(
                        is_approved=False,
                        rejection_reason=(
                            f"VETO: Scale-in prohibited. Position #{pos_id_str} has not locked Break-Even yet "
                            f"(Entry: {p_entry:.2f}, SL: {p_sl:.2f})."
                        ),
                    )

        # 5. Confidence Score Gate
        if not scored.passes_threshold:
            return RiskCheckResult(
                is_approved=False,
                rejection_reason=f"VETO: Confidence score {scored.total_score:.1f} below threshold.",
            )

        # 6. Spread Gate
        if current_spread > self.max_spread_pts:
            return RiskCheckResult(
                is_approved=False,
                rejection_reason=f"VETO: Spread {current_spread} pts exceeds limit ({self.max_spread_pts} pts).",
            )

        cand = scored.candidate

        # 7. Stop Loss & Take Profit Directional Validation
        if cand.side == OrderSide.BUY:
            if cand.stop_loss >= cand.entry_price:
                return RiskCheckResult(
                    is_approved=False,
                    rejection_reason=f"VETO: Buy SL ({cand.stop_loss}) >= Entry ({cand.entry_price}).",
                )
            if cand.take_profit <= cand.entry_price:
                return RiskCheckResult(
                    is_approved=False,
                    rejection_reason=f"VETO: Buy TP ({cand.take_profit}) <= Entry ({cand.entry_price}).",
                )
        else:
            if cand.stop_loss <= cand.entry_price:
                return RiskCheckResult(
                    is_approved=False,
                    rejection_reason=f"VETO: Sell SL ({cand.stop_loss}) <= Entry ({cand.entry_price}).",
                )
            if cand.take_profit >= cand.entry_price:
                return RiskCheckResult(
                    is_approved=False,
                    rejection_reason=f"VETO: Sell TP ({cand.take_profit}) >= Entry ({cand.entry_price}).",
                )

        # 7. Risk/Reward Validation (Min 1.5 R:R)
        if cand.risk_reward_ratio < 1.45:
            return RiskCheckResult(
                is_approved=False,
                rejection_reason=f"VETO: Risk:Reward {cand.risk_reward_ratio:.2f} < 1.50 minimum.",
            )

        # 8. Position Sizing & Dollar Risk Budget ($2.00 / 4% on $50)
        sl_dist = cand.risk_distance
        point_scale = 0.01 if getattr(self.spec, "digits", 2) >= 3 else getattr(self.spec, "point", 0.01)
        max_sl_dist_usd = max(3.50, self.max_sl_pts * point_scale)
        vol, risk_usd, is_sized, size_reason = calculate_position_size(
            sl_distance=sl_dist,
            balance=self.drawdown_guard.state.current_equity,
            spec=self.spec,
            target_risk_usd=self.target_risk_usd,
            max_risk_pct=self.max_risk_pct,
            max_sl_distance=max_sl_dist_usd,
        )

        if not is_sized:
            return RiskCheckResult(is_approved=False, rejection_reason=f"VETO: {size_reason}")

        # Construct unique magic number
        magic = self.magic_base + self._magic_counter
        self._magic_counter += 1

        approved = ApprovedOrder(
            magic_number=magic,
            strategy_id=cand.strategy_id,
            symbol=cand.symbol,
            side=cand.side,
            volume=vol,
            entry_price=cand.entry_price,
            stop_loss=cand.stop_loss,
            take_profit=cand.take_profit,
            risk_usd=risk_usd,
            timestamp=current_time,
        )

        return RiskCheckResult(is_approved=True, order=approved, rejection_reason="Approved.")
