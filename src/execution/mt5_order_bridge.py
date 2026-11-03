"""
Live MetaTrader 5 Order Bridge for AI GOLD WATCHER V4.
Strictly restricted to DEMO accounts and capped at 0.01 lot ($1.00 risk budget).
Implements the institutional order submission protocol from mt5-python-bridge-for-forex-bots.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, List
import logging

from src.data.models import SymbolSpec
from src.strategies.base_strategy import OrderSide
from src.risk.risk_guard import ApprovedOrder


logger = logging.getLogger("v4_trading.mt5_bridge")


@dataclass(frozen=True)
class ExecutionResult:
    """Standardized result of an MT5 order execution attempt."""
    success: bool
    retcode: int
    retcode_description: str
    order_ticket: int = 0
    deal_ticket: int = 0
    volume: float = 0.0
    price: float = 0.0
    comment: str = ""


class MT5OrderBridge:
    """
    Direct MT5 execution bridge with hard financial guardrails:
    - DEMO ACCOUNT ONLY (Zero live real funds access)
    - Max volume 0.01 lot
    - Max 1 concurrent position
    - Real-time retcode classification
    """

    # Retcode descriptions mapping
    RETCODE_MAP = {
        10004: "TRADE_RETCODE_REQUOTE (Requote)",
        10006: "TRADE_RETCODE_REJECT (Request rejected)",
        10007: "TRADE_RETCODE_CANCEL (Request canceled by trader)",
        10008: "TRADE_RETCODE_PLACED (Order placed)",
        10009: "TRADE_RETCODE_DONE (Request completed)",
        10010: "TRADE_RETCODE_DONE_PARTIAL (Only part of request was completed)",
        10011: "TRADE_RETCODE_ERROR (Request processing error)",
        10012: "TRADE_RETCODE_TIMEOUT (Request canceled by timeout)",
        10013: "TRADE_RETCODE_INVALID (Invalid request)",
        10014: "TRADE_RETCODE_INVALID_VOLUME (Invalid volume in request)",
        10015: "TRADE_RETCODE_INVALID_PRICE (Invalid price in request)",
        10016: "TRADE_RETCODE_INVALID_STOPS (Invalid stops in request)",
        10017: "TRADE_RETCODE_TRADE_DISABLED (Trade is disabled)",
        10018: "TRADE_RETCODE_MARKET_CLOSED (Market is closed)",
        10019: "TRADE_RETCODE_NO_MONEY (Not enough money to complete request)",
        10020: "TRADE_RETCODE_PRICE_CHANGED (Prices changed)",
        10021: "TRADE_RETCODE_PRICE_OFF (There are no quotes to process request)",
        10022: "TRADE_RETCODE_INVALID_EXPIRATION (Invalid order expiration date)",
        10023: "TRADE_RETCODE_ORDER_CHANGED (Order state changed)",
        10024: "TRADE_RETCODE_TOO_MANY_REQUESTS (Too frequent requests)",
        10025: "TRADE_RETCODE_NO_CHANGES (No changes in request)",
        10026: "TRADE_RETCODE_SERVER_DISABLES_AT (Autotrading disabled by server)",
        10027: "TRADE_RETCODE_CLIENT_DISABLES_AT (Autotrading disabled by client terminal)",
        10028: "TRADE_RETCODE_LOCKED (Request locked for processing)",
        10029: "TRADE_RETCODE_FROZEN (Order or position being modified is frozen)",
        10030: "TRADE_RETCODE_INVALID_FILL (Unsupported filling mode)",
        10031: "TRADE_RETCODE_CONNECTION (No connection with trade server)",
    }

    def __init__(self, symbol: str = "XAUUSDm", magic_base: int = 400000):
        self.symbol = symbol
        self.magic_base = magic_base
        self._mt5: Any = None
        self._verify_environment()

    def _verify_environment(self) -> None:
        """Verify MT5 terminal and enforce DEMO-only safety latch."""
        import MetaTrader5 as mt5
        self._mt5 = mt5

        if not self._mt5.initialize():
            raise RuntimeError(f"Failed to initialize MetaTrader 5: {self._mt5.last_error()}")

        account = self._mt5.account_info()
        if account is None:
            raise RuntimeError("Unable to retrieve MT5 account info. Please ensure MT5 is logged in.")

        # STRICT SAFETY GUARD: Check trade_mode == ACCOUNT_TRADE_MODE_DEMO (0)
        # 0 = DEMO, 1 = CONTEST, 2 = REAL
        if account.trade_mode != 0:
            self._mt5.shutdown()
            raise PermissionError(
                f"CRITICAL SAFETY VIOLATION: Connected account '{account.login}' is NOT a Demo account "
                f"(trade_mode={account.trade_mode}). Live real trading is strictly prohibited!"
            )

        # Check Algorithmic Trading permission
        if not account.trade_expert:
            logger.warning(
                "Algorithmic Trading is disabled in MT5 terminal. Please enable 'Allow algorithmic trading' in Tools -> Options."
            )

        logger.info(
            "MT5 Order Bridge initialized on DEMO Account #%s (%s, Balance: $%.2f)",
            account.login,
            account.name,
            account.balance,
        )

    def get_open_positions(self) -> List[Any]:
        """Fetch all open positions for this symbol."""
        positions = self._mt5.positions_get(symbol=self.symbol)
        if positions is None:
            return []
        return list(positions)

    def send_market_order(self, order: ApprovedOrder) -> ExecutionResult:
        """
        Execute market deal on MT5 Demo terminal.
        Enforces volume limit (0.01 lot) and mutual exclusivity (max 1 position).
        """
        # 1. Double check account is DEMO
        account = self._mt5.account_info()
        if account is None or account.trade_mode != 0:
            return ExecutionResult(
                success=False,
                retcode=10017,
                retcode_description="CRITICAL SAFETY: Non-demo account rejected.",
            )

        # 2. Enforce mutual exclusivity (max 1 position)
        open_pos = self.get_open_positions()
        if len(open_pos) >= 1:
            return ExecutionResult(
                success=False,
                retcode=10025,
                retcode_description=f"Mutual exclusivity: Position #{open_pos[0].ticket} already open.",
            )

        # 3. Enforce volume cap
        if order.volume > 0.01:
            return ExecutionResult(
                success=False,
                retcode=10014,
                retcode_description=f"Volume safety cap violated: {order.volume} > 0.01 lot.",
            )

        # 4. Get latest broker tick
        tick = self._mt5.symbol_info_tick(self.symbol)
        if tick is None:
            return ExecutionResult(
                success=False,
                retcode=10021,
                retcode_description="Unable to fetch current market tick from MT5.",
            )

        info = self._mt5.symbol_info(self.symbol)
        if info is None:
            return ExecutionResult(
                success=False,
                retcode=10013,
                retcode_description=f"Symbol {self.symbol} not found in Market Watch.",
            )

        digits = info.digits

        # 5. Determine order type and price
        if order.side == OrderSide.BUY:
            order_type = self._mt5.ORDER_TYPE_BUY
            price = tick.ask
        elif order.side == OrderSide.SELL:
            order_type = self._mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            return ExecutionResult(
                success=False,
                retcode=10013,
                retcode_description=f"Invalid order side: {order.side}",
            )

        # 6. Format stops with broker precision
        sl_price = round(order.stop_loss, digits)
        tp_price = round(order.take_profit, digits)

        # 7. Determine filling mode (Exness supports IOC for Market Execution)
        filling_mode = self._mt5.ORDER_FILLING_IOC

        request = {
            "action": self._mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": order.volume,
            "type": order_type,
            "price": price,
            "sl": sl_price,
            "tp": tp_price,
            "deviation": 20,
            "magic": order.magic_number,
            "comment": f"AGW_V4_{order.strategy_id[:6]}",
            "type_time": self._mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        logger.info(
            "Submitting Live MT5 DEMO Order: %s %.2f lot %s @ %.3f (SL: %.3f, TP: %.3f, Magic: %d)",
            order.side.value,
            order.volume,
            self.symbol,
            price,
            sl_price,
            tp_price,
            order.magic_number,
        )

        result = self._mt5.order_send(request)

        if result is None:
            err = self._mt5.last_error()
            return ExecutionResult(
                success=False,
                retcode=err[0] if isinstance(err, tuple) else 0,
                retcode_description=f"order_send returned None: {err}",
            )

        ret_desc = self.RETCODE_MAP.get(result.retcode, f"RETCODE_{result.retcode}")

        if result.retcode == 10009:  # TRADE_RETCODE_DONE
            logger.info(
                "MT5 Order Executed Successfully! Order Ticket: #%d, Deal Ticket: #%d, Fill Price: %.3f, Volume: %.2f",
                result.order,
                result.deal,
                result.price,
                result.volume,
            )
            return ExecutionResult(
                success=True,
                retcode=result.retcode,
                retcode_description=ret_desc,
                order_ticket=result.order,
                deal_ticket=result.deal,
                volume=result.volume,
                price=result.price,
                comment=result.comment,
            )
        else:
            logger.error(
                "MT5 Order Rejected! Retcode: %d (%s), Comment: %s",
                result.retcode,
                ret_desc,
                result.comment,
            )
            return ExecutionResult(
                success=False,
                retcode=result.retcode,
                retcode_description=f"{ret_desc} - {result.comment}",
            )

    def close_position(self, position: Any) -> ExecutionResult:
        """
        Close an existing open position on MT5 Demo (Remote Kill Switch / Manual exit).
        """
        tick = self._mt5.symbol_info_tick(self.symbol)
        if tick is None:
            return ExecutionResult(
                success=False,
                retcode=10021,
                retcode_description="Unable to fetch current tick to close position.",
            )

        # Opposite order type for market close
        order_type = (
            self._mt5.ORDER_TYPE_SELL
            if position.type == self._mt5.ORDER_TYPE_BUY
            else self._mt5.ORDER_TYPE_BUY
        )
        price = tick.bid if order_type == self._mt5.ORDER_TYPE_SELL else tick.ask

        request = {
            "action": self._mt5.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": self.symbol,
            "volume": position.volume,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": position.magic,
            "comment": "AGW_V4_REMOTE_CLOSE",
            "type_time": self._mt5.ORDER_TIME_GTC,
            "type_filling": self._mt5.ORDER_FILLING_IOC,
        }

        logger.info(
            "Sending Remote MT5 Position Close: Ticket #%d (%s %.2f lot @ %.3f)",
            position.ticket,
            "BUY" if position.type == 0 else "SELL",
            position.volume,
            price,
        )

        result = self._mt5.order_send(request)
        if result is None:
            err = self._mt5.last_error()
            return ExecutionResult(
                success=False,
                retcode=err[0] if isinstance(err, tuple) else 0,
                retcode_description=f"order_send close returned None: {err}",
            )

        if result.retcode == 10009:
            logger.info("Position #%d Closed Successfully @ %.3f", position.ticket, result.price)
            return ExecutionResult(
                success=True,
                retcode=result.retcode,
                retcode_description="Position closed successfully.",
                price=result.price,
                deal_ticket=result.deal,
                comment=result.comment,
            )
        else:
            logger.error("Failed to close position #%d: %d (%s)", position.ticket, result.retcode, result.comment)
            return ExecutionResult(
                success=False,
                retcode=result.retcode,
                retcode_description=f"Close rejected: {result.comment}",
            )

    def modify_position_sl(
        self, position: Any, new_sl: float, new_tp: Optional[float] = None
    ) -> ExecutionResult:
        """
        Modify Stop Loss (and optionally Take Profit) on an existing MT5 position
        (Auto Break-Even, Trailing Stop, or Gồng Lãi Động / Trailing Runner).
        Uses TRADE_ACTION_SLTP to update stops without affecting position volume or entry.
        """
        sym_info = self._mt5.symbol_info(self.symbol)
        digits = sym_info.digits if sym_info else 3
        sl_rounded = round(float(new_sl), digits)
        target_tp = round(float(new_tp), digits) if new_tp is not None else float(getattr(position, "tp", 0.0))

        request = {
            "action": self._mt5.TRADE_ACTION_SLTP,
            "position": position.ticket,
            "symbol": self.symbol,
            "sl": sl_rounded,
            "tp": target_tp,
        }

        logger.info(
            "Sending MT5 Stop Modification: Ticket #%d (%s) -> New SL: %.3f, New TP: %.3f",
            position.ticket,
            "BUY" if position.type == 0 else "SELL",
            sl_rounded,
            target_tp,
        )

        result = self._mt5.order_send(request)
        if result is None:
            err = self._mt5.last_error()
            return ExecutionResult(
                success=False,
                retcode=err[0] if isinstance(err, tuple) else 0,
                retcode_description=f"order_send modify returned None: {err}",
            )

        if result.retcode == 10009:
            logger.info("Position #%d SL Modified Successfully to %.3f", position.ticket, sl_rounded)
            return ExecutionResult(
                success=True,
                retcode=result.retcode,
                retcode_description="Position SL modified successfully.",
                price=sl_rounded,
                comment=result.comment,
            )
        else:
            logger.warning(
                "Failed to modify position #%d SL: %d (%s)",
                position.ticket,
                result.retcode,
                result.comment,
            )
            return ExecutionResult(
                success=False,
                retcode=result.retcode,
                retcode_description=f"Modify SL rejected: {result.comment}",
            )
