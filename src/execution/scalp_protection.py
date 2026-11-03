"""
Scalp Protection Engine for AI GOLD WATCHER V4 ("Vua Scalping").
Implements high-frequency institutional trade management:
1. Auto Break-Even ("Lệnh Bất Tử"): Automatically moves Stop Loss to Entry + Buffer
   when trade advances 50% toward Take Profit, eliminating loss risk completely.
2. Dynamic Trailing Stop: Continuously locks in profits as price advances beyond 70% TP.
3. Gồng Lãi Động (Trailing Runner): When trade reaches 85%+ TP in high-liquidity sessions,
   dynamically expands Take Profit to capture mega waves (5 - 15+ points) while locking guaranteed profits.
"""

from dataclasses import dataclass
from typing import Optional, Set, Any
import logging

logger = logging.getLogger("v4_trading.scalp_protection")


@dataclass(frozen=True)
class ScalpAction:
    """Action recommendation from the Scalp Protection Engine."""
    ticket: Any
    action_type: str  # "BREAK_EVEN", "TRAILING_STOP", "TRAILING_RUNNER"
    new_sl: float
    old_sl: float
    current_price: float
    reason: str
    new_tp: Optional[float] = None


class ScalpProtectionEngine:
    """
    Automated trade guardian for scalping operations.
    Monitors active positions in real time and enforces break-even, trailing, and runner expansion.
    """

    def __init__(
        self,
        be_trigger_ratio: float = 0.38,         # Trigger BE at 38% progress to TP (was 0.50)
        be_buffer_usd: float = 0.25,            # +$0.25 buffer above entry (covers full ~20pt gold spread + net profit)
        trailing_trigger_ratio: float = 0.65,   # Trigger Trailing Stop at 65% progress to TP (was 0.70)
        trailing_step_usd: float = 0.20,        # Minimum move before updating trailing SL
        enable_trailing_runner: bool = True,    # Gồng Lãi Động mode
        runner_trigger_ratio: float = 0.82,     # Expand runner at 82% TP progress
        runner_tp_expansion_usd: float = 5.00,  # Expand TP by +$5.00 USD on gold
        runner_trailing_dist_usd: float = 0.80, # Distance behind peak for runner trailing
    ):
        self.be_trigger_ratio = be_trigger_ratio
        self.be_buffer_usd = be_buffer_usd
        self.trailing_trigger_ratio = trailing_trigger_ratio
        self.trailing_step_usd = trailing_step_usd
        self.enable_trailing_runner = enable_trailing_runner
        self.runner_trigger_ratio = runner_trigger_ratio
        self.runner_tp_expansion_usd = runner_tp_expansion_usd
        self.runner_trailing_dist_usd = runner_trailing_dist_usd

        self._break_even_tickets: Set[Any] = set()
        self._runner_expanded_tickets: Set[Any] = set()

    def reset_ticket(self, ticket: Any) -> None:
        """Clear state when a position is closed."""
        self._break_even_tickets.discard(ticket)
        self._runner_expanded_tickets.discard(ticket)

    def evaluate_position(self, position: Any) -> Optional[ScalpAction]:
        """
        Evaluate an open position (MT5 position or VirtualPosition) for scalp protections.
        Returns ScalpAction if a Stop Loss adjustment or TP expansion is warranted, or None.
        """
        raw_id = getattr(position, "ticket", None)
        if raw_id is None:
            raw_id = getattr(position, "position_id", 0)
        try:
            ticket = int(raw_id)
        except (ValueError, TypeError):
            ticket = str(raw_id)

        # Determine position type (0 = BUY, 1 = SELL in MT5)
        pos_type = getattr(position, "type", None)
        if pos_type is None:
            side = getattr(position, "side", None)
            is_buy = str(side).upper().endswith("BUY")
        else:
            is_buy = (pos_type == 0)

        entry_price = float(getattr(position, "price_open", getattr(position, "entry_price", 0.0)))
        current_price = float(getattr(position, "price_current", getattr(position, "current_price", entry_price)))
        current_sl = float(getattr(position, "sl", getattr(position, "stop_loss", 0.0)))
        tp = float(getattr(position, "tp", getattr(position, "take_profit", 0.0)))

        if entry_price <= 0.0 or tp <= 0.0:
            return None

        # ---------------------------------------------------------------------
        # 1. Evaluate BUY Position
        # ---------------------------------------------------------------------
        if is_buy:
            tp_distance = tp - entry_price
            if tp_distance <= 0:
                return None

            progress = current_price - entry_price

            # --- 1A. Check Trailing Runner (85%+ progress) ---
            if self.enable_trailing_runner:
                runner_threshold = entry_price + (tp_distance * self.runner_trigger_ratio)
                if current_price >= runner_threshold:
                    candidate_sl = round(current_price - self.runner_trailing_dist_usd, 3)
                    # Guaranteed profit buffer: ensure new_sl is at least entry + $0.80
                    min_guaranteed_sl = round(entry_price + 0.80, 3)
                    candidate_sl = max(candidate_sl, min_guaranteed_sl)

                    # Expand TP once if not yet expanded
                    new_tp = None
                    if ticket not in self._runner_expanded_tickets:
                        new_tp = round(tp + self.runner_tp_expansion_usd, 3)
                        self._runner_expanded_tickets.add(ticket)

                    if candidate_sl > current_sl + self.trailing_step_usd or new_tp is not None:
                        effective_sl = max(candidate_sl, current_sl)
                        logger.info(
                            "TRAILING RUNNER ACTIVE for BUY #%s: Price %.3f -> Elevating SL: %.3f (Guaranteed Win), Expanded TP: %s",
                            ticket, current_price, effective_sl, new_tp
                        )
                        return ScalpAction(
                            ticket=ticket,
                            action_type="TRAILING_RUNNER",
                            new_sl=effective_sl,
                            old_sl=current_sl,
                            current_price=current_price,
                            reason=f"Trailing Runner surfing BUY momentum @ {current_price:.3f} (Locked in ${effective_sl - entry_price:.2f} profit).",
                            new_tp=new_tp,
                        )

            # --- 1B. Check Dynamic Trailing Stop (70%+ progress) ---
            trailing_threshold = entry_price + (tp_distance * self.trailing_trigger_ratio)
            if current_price >= trailing_threshold:
                trailing_distance = max(0.50, tp_distance * 0.30)
                candidate_sl = round(current_price - trailing_distance, 3)
                if candidate_sl > current_sl + self.trailing_step_usd:
                    logger.info(
                        "TRAILING STOP TRIGGERED for BUY #%s: Price %.3f -> Elevating SL from %.3f to %.3f",
                        ticket, current_price, current_sl, candidate_sl
                    )
                    return ScalpAction(
                        ticket=ticket,
                        action_type="TRAILING_STOP",
                        new_sl=candidate_sl,
                        old_sl=current_sl,
                        current_price=current_price,
                        reason=f"Trailing Stop trailing behind peak price at {candidate_sl:.3f}.",
                    )

            # --- 1C. Check Auto Break-Even (50% progress) ---
            if ticket not in self._break_even_tickets:
                be_threshold = entry_price + (tp_distance * self.be_trigger_ratio)
                if current_price >= be_threshold:
                    target_be_sl = round(entry_price + self.be_buffer_usd, 3)
                    if current_sl < target_be_sl:
                        self._break_even_tickets.add(ticket)
                        logger.info(
                            "AUTO BREAK-EVEN TRIGGERED for BUY #%s: Price %.3f reached %d%% TP -> New SL %.3f",
                            ticket, current_price, int(self.be_trigger_ratio * 100), target_be_sl
                        )
                        return ScalpAction(
                            ticket=ticket,
                            action_type="BREAK_EVEN",
                            new_sl=target_be_sl,
                            old_sl=current_sl,
                            current_price=current_price,
                            reason=f"BUY achieved {int(self.be_trigger_ratio * 100)}% TP progress ({progress:.2f}/{tp_distance:.2f} USD). Locked in BE.",
                        )

        # ---------------------------------------------------------------------
        # 2. Evaluate SELL Position
        # ---------------------------------------------------------------------
        else:
            tp_distance = entry_price - tp
            if tp_distance <= 0:
                return None

            progress = entry_price - current_price

            # --- 2A. Check Trailing Runner (85%+ progress) ---
            if self.enable_trailing_runner:
                runner_threshold = entry_price - (tp_distance * self.runner_trigger_ratio)
                if current_price <= runner_threshold:
                    candidate_sl = round(current_price + self.runner_trailing_dist_usd, 3)
                    # Guaranteed profit buffer: ensure new_sl is at least entry - $0.80
                    min_guaranteed_sl = round(entry_price - 0.80, 3)
                    candidate_sl = min(candidate_sl, min_guaranteed_sl)

                    new_tp = None
                    if ticket not in self._runner_expanded_tickets:
                        new_tp = round(tp - self.runner_tp_expansion_usd, 3)
                        self._runner_expanded_tickets.add(ticket)

                    if current_sl == 0.0 or candidate_sl < current_sl - self.trailing_step_usd or new_tp is not None:
                        effective_sl = min(candidate_sl, current_sl) if current_sl > 0.0 else candidate_sl
                        logger.info(
                            "TRAILING RUNNER ACTIVE for SELL #%s: Price %.3f -> Tightening SL: %.3f (Guaranteed Win), Expanded TP: %s",
                            ticket, current_price, effective_sl, new_tp
                        )
                        return ScalpAction(
                            ticket=ticket,
                            action_type="TRAILING_RUNNER",
                            new_sl=effective_sl,
                            old_sl=current_sl,
                            current_price=current_price,
                            reason=f"Trailing Runner surfing SELL momentum @ {current_price:.3f} (Locked in ${entry_price - effective_sl:.2f} profit).",
                            new_tp=new_tp,
                        )

            # --- 2B. Check Dynamic Trailing Stop (70%+ progress) ---
            trailing_threshold = entry_price - (tp_distance * self.trailing_trigger_ratio)
            if current_price <= trailing_threshold:
                trailing_distance = max(0.50, tp_distance * 0.30)
                candidate_sl = round(current_price + trailing_distance, 3)
                if current_sl == 0.0 or candidate_sl < current_sl - self.trailing_step_usd:
                    logger.info(
                        "TRAILING STOP TRIGGERED for SELL #%s: Price %.3f -> Tightening SL from %.3f to %.3f",
                        ticket, current_price, current_sl, candidate_sl
                    )
                    return ScalpAction(
                        ticket=ticket,
                        action_type="TRAILING_STOP",
                        new_sl=candidate_sl,
                        old_sl=current_sl,
                        current_price=current_price,
                        reason=f"Trailing Stop trailing behind dip price at {candidate_sl:.3f}.",
                    )

            # --- 2C. Check Auto Break-Even (50% progress) ---
            if ticket not in self._break_even_tickets:
                be_threshold = entry_price - (tp_distance * self.be_trigger_ratio)
                if current_price <= be_threshold:
                    target_be_sl = round(entry_price - self.be_buffer_usd, 3)
                    if current_sl == 0.0 or current_sl > target_be_sl:
                        self._break_even_tickets.add(ticket)
                        logger.info(
                            "AUTO BREAK-EVEN TRIGGERED for SELL #%s: Price %.3f reached %d%% TP -> New SL %.3f",
                            ticket, current_price, int(self.be_trigger_ratio * 100), target_be_sl
                        )
                        return ScalpAction(
                            ticket=ticket,
                            action_type="BREAK_EVEN",
                            new_sl=target_be_sl,
                            old_sl=current_sl,
                            current_price=current_price,
                            reason=f"SELL achieved {int(self.be_trigger_ratio * 100)}% TP progress ({progress:.2f}/{tp_distance:.2f} USD). Locked in BE.",
                        )

        return None
