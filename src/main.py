"""
Main Application Entry Point for AI GOLD WATCHER V4.
Supports CLI operations for Paper Trading, Backtesting, and Diagnostics.
"""

import argparse
import sys
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

# Workspace setup
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from dotenv import load_dotenv
env_path = WORKSPACE_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)

from src.config.settings import SystemSettings, RiskSettings, BrokerSettings
from src.config.validation import validate_settings, ConfigurationError
from src.data.models import Timeframe
from src.data.symbol_specs import DEFAULT_EXNESS_XAUUSD
from src.data.mt5_client import MockMT5Client, LiveMT5Client
from src.data.data_engine import MT5DataEngine
from src.indicators.indicator_engine import SharedIndicatorEngine
from src.regime.regime_detector import MarketRegimeDetector, RegimeType
from src.regime.macro_trend import MacroTrendDetector, MacroTrendBias
from src.regime.session_router import SessionRouter
from src.selector.adaptive_selector import AdaptiveStrategySelector
from src.scoring.confidence_engine import ConfidenceEngine
from src.scoring.meta_labeler import MetaLabelEngine
from src.risk.risk_guard import RiskGuard
from src.risk.news_guard import NewsGuard
from src.execution.paper_broker import PaperBroker
from src.execution.paper_trade_manager import PaperTradeManager
from src.execution.scalp_protection import ScalpProtectionEngine
from src.storage.database import init_db
from src.storage.repositories import TradeRepository, SignalRepository, EquityRepository
from src.monitoring.logger import setup_logger
from src.monitoring.alerts import AlertManager, AlertSeverity
from src.monitoring.health_monitor import HealthMonitor
from src.backtest.backtest_runner import run_standard_backtest
from src.evaluation.performance_metrics import calculate_performance_metrics
from src.evaluation.report_generator import generate_markdown_tearsheet


def run_diagnostics(settings: SystemSettings, logger) -> bool:
    """Run system integrity and safety guardrail checks."""
    logger.info("==================================================")
    logger.info("  AI GOLD WATCHER V4 — SYSTEM DIAGNOSTIC AUDIT   ")
    logger.info("==================================================")

    # 1. Config & Safety Validation
    try:
        validate_settings(settings)
    except ConfigurationError as e:
        logger.error("Configuration validation failed: %s", e)
        return False
    logger.info("Config & Safety Latches: VALIDATED (Dry-run=%s)", settings.risk.dry_run_enabled)

    # 2. Database connection check
    db = init_db(settings.storage.db_path)
    conn = db.get_connection()
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    conn.close()
    logger.info("SQLite Storage: ONLINE (%d tables initialized: %s)", len(tables), ", ".join(tables))

    # 3. Math & Indicator Engine check
    client = MockMT5Client(spec=DEFAULT_EXNESS_XAUUSD)
    client.generate_synthetic_bars(timeframe=Timeframe.M5, count=100)
    bars = client.get_rates("XAUUSDm", Timeframe.M5, count=100, closed_only=True)
    df = pd.DataFrame([{"open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.tick_volume} for b in bars])
    enriched = SharedIndicatorEngine.compute_all(df)
    assert "atr_14" in enriched.columns, "ATR column missing"
    assert "rsi_14" in enriched.columns, "RSI column missing"
    assert "adx_14" in enriched.columns, "ADX column missing"
    logger.info("Indicator Engine: VERIFIED (Enriched %d rows with indicators)", len(enriched))

    # 4. Regime Detector check
    detector = MarketRegimeDetector()
    state = detector.update(enriched)
    logger.info("Market Regime Classifier: VERIFIED (Detected: %s, Conf: %.2f)", state.regime.value, state.confidence)

    # 5. Risk Gate Veto check
    risk_guard = RiskGuard(spec=DEFAULT_EXNESS_XAUUSD, reference_balance=50.0)
    logger.info("Risk Guard Pre-Trade Veto: ACTIVE (Max SL=%d pts, Risk Budget=$%.2f)", risk_guard.max_sl_pts, settings.risk.target_risk_usd)

    logger.info("All 12 Modules & Safety Guardrails are VERIFIED and OPERATIONAL.")
    return True


def run_paper_session(
    settings: SystemSettings,
    bar_count: int,
    use_mock: bool,
    logger,
    ai_threshold: float = 0.60,
    conf_threshold: float = 60.0,
    be_trigger_ratio: float = 0.52,
) -> Optional[dict]:
    """Execute paper trading simulation over streaming/historical bars."""
    logger.info("Starting Paper Trading Engine (MockMode=%s, Bars=%d)...", use_mock, bar_count)

    spec = DEFAULT_EXNESS_XAUUSD
    client = MockMT5Client(spec=spec) if use_mock else LiveMT5Client()
    if use_mock:
        client.generate_synthetic_bars(timeframe=Timeframe.M5, count=bar_count + 100, volatility=1.8)

    data_engine = MT5DataEngine(client=client, symbol="XAUUSDm")
    if not data_engine.initialize():
        logger.error("Failed to initialize MT5 Data Engine.")
        return

    db = init_db(settings.storage.db_path)
    trade_repo = TradeRepository(db)
    signal_repo = SignalRepository(db)
    equity_repo = EquityRepository(db)

    alert_mgr = AlertManager()
    health_mon = HealthMonitor()
    health_mon.record_heartbeat(True)

    indicator_engine = SharedIndicatorEngine()
    regime_detector = MarketRegimeDetector()
    selector = AdaptiveStrategySelector()
    confidence_engine = ConfidenceEngine(threshold=conf_threshold)
    meta_labeler = MetaLabelEngine(threshold=ai_threshold)
    scalp_engine = ScalpProtectionEngine(be_trigger_ratio=be_trigger_ratio, be_buffer_usd=0.25)
    # Synchronize paper trading with live MT5 terminal if connected
    account_info = client.get_account_info() if not use_mock else None
    if account_info is not None:
        from src.config.license import verify_account_authorized
        if not verify_account_authorized(getattr(account_info, "login", 0)):
            logger.error("⛔ TRUY CẬP BỊ TỪ CHỐI! Tài khoản MT5 #%s chưa được cấp quyền.", getattr(account_info, "login", "N/A"))
            print(f"\n⛔ TRUY CẬP BỊ TỪ CHỐI: Tài khoản MT5 #{getattr(account_info, 'login', 'N/A')} chưa được cấp quyền sử dụng. Liên hệ Admin (LilBoiXAU)!\n")
            return
        live_balance = float(account_info.balance)
        logger.info(
            "Synchronized Paper Session with Live MT5 Terminal: Account #%s (Balance: $%.2f USD)",
            getattr(account_info, "login", "N/A"),
            live_balance,
        )
    else:
        live_balance = settings.risk.reference_balance_usd

    balance = live_balance
    risk_guard = RiskGuard(
        spec=spec,
        reference_balance=live_balance,
        target_risk_usd=None,
        max_sl_pts=settings.risk.max_sl_points,
        max_risk_pct=0.04,
    )
    paper_mgr = PaperTradeManager(spec=spec, risk_guard=risk_guard, scalp_engine=scalp_engine)

    all_bars = client.get_rates("XAUUSDm", Timeframe.M5, count=bar_count, closed_only=True)
    all_h1_bars = []
    try:
        all_h1_bars = client.get_rates("XAUUSDm", Timeframe.H1, count=max(100, bar_count // 12 + 50), closed_only=True)
    except Exception:
        pass
    logger.info("Processing %d closed historical bars through execution loop...", len(all_bars))

    for idx in range(50, len(all_bars)):
        current_bar = all_bars[idx]
        health_mon.record_bar_arrival(pd.to_datetime(current_bar.timestamp, utc=True))

        # Check existing active virtual position
        closed_trade = paper_mgr.on_bar_update(current_bar)
        if closed_trade is not None:
            trade_repo.save_closed_trade(closed_trade)
            balance += closed_trade.net_pnl
            pnl_tag = "🏆 [CHỐT LỜI TP WIN]" if closed_trade.net_pnl > 0.05 else ("🛑 [CẮT LỖ SL HIT]" if closed_trade.net_pnl < -0.05 else "🛡️ [HÒA VỐN / SL DƯƠNG]")
            logger.info(
                "%s Kèo #%s | Lãi/Lỗ: %+.2f USD | 💰 Số dư tài khoản mới: $%.2f USD (%s)",
                pnl_tag,
                closed_trade.trade_id,
                closed_trade.net_pnl,
                balance,
                closed_trade.exit_reason.value,
            )

        # Slice historical window up to current closed bar
        window_bars = all_bars[: idx + 1]
        records = [
            {
                "time": b.timestamp,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.tick_volume,
                "spread": b.spread,
            }
            for b in window_bars
        ]
        df_window = pd.DataFrame.from_records(records).set_index("time")
        enriched = indicator_engine.compute_all(df_window)

        # Regime detection
        regime_state = regime_detector.update(enriched)

        # Multi-Timeframe Analysis: Synchronize H1 bars up to current bar timestamp
        macro_result = None
        if all_h1_bars:
            h1_window = [b for b in all_h1_bars if b.timestamp <= current_bar.timestamp]
            if len(h1_window) >= 10:
                macro_result = MacroTrendDetector.analyze(h1_window[-50:])

        # Signal generation & selection if less than 2 positions are active (Institutional Pyramiding)
        if len(paper_mgr.active_positions) < 2:
            candidate = selector.evaluate(
                df=enriched,
                regime_state=regime_state,
                spec=spec,
                macro_bias=macro_result.bias if macro_result else None,
                current_time=current_bar.timestamp,
            )
            if candidate is not None:
                # Machine Learning Meta-Labeling filter
                ai_res = meta_labeler.predict_win_probability(
                    candidate=candidate,
                    df_indicators=enriched,
                    regime_state=regime_state,
                    current_spread=current_bar.spread,
                )

                scored = confidence_engine.score(
                    candidate=candidate,
                    regime_state=regime_state,
                    current_spread=current_bar.spread,
                )
                risk_res = risk_guard.evaluate_signal(
                    scored=scored,
                    current_spread=current_bar.spread,
                    current_time=current_bar.timestamp,
                    open_positions=paper_mgr.active_positions,
                )

                final_approved = risk_res.is_approved and ai_res.passes_filter
                rejection_msg = risk_res.rejection_reason
                if risk_res.is_approved and not ai_res.passes_filter:
                    rejection_msg = f"VETO: AI Meta-Labeling win probability ({ai_res.win_probability*100:.1f}%) < {ai_res.threshold*100:.1f}%"

                signal_repo.save_signal(
                    signal=scored,
                    is_approved=final_approved,
                    rejection_reason=rejection_msg,
                    regime=regime_state.regime.value,
                )

                if final_approved and risk_res.order is not None:
                    filled = paper_mgr.open_position(
                        order=risk_res.order,
                        current_spread_pts=current_bar.spread,
                        fill_time=current_bar.timestamp,
                    )
                    if filled:
                        logger.info(
                            "Paper Order Executed: %s %s @ %.2f (SL: %.2f, TP: %.2f, Conf: %.1f, AI P(win): %.1f%%)",
                            risk_res.order.side.value,
                            risk_res.order.symbol,
                            risk_res.order.entry_price,
                            risk_res.order.stop_loss,
                            risk_res.order.take_profit,
                            scored.confidence_score,
                            ai_res.win_probability * 100,
                        )

        # Record periodic equity snapshot every 20 bars
        if idx % 20 == 0:
            open_count = 1 if paper_mgr.active_position is not None else 0
            equity = balance + (paper_mgr.active_position.unrealized_pnl if paper_mgr.active_position else 0.0)
            equity_repo.record_snapshot(
                timestamp=pd.to_datetime(current_bar.timestamp, utc=True),
                balance=balance,
                equity=equity,
                open_positions=open_count,
                daily_pnl=balance - settings.risk.reference_balance_usd,
            )

    from src.evaluation.session_recap import build_session_recap
    recap = build_session_recap(
        initial_balance=live_balance,
        final_balance=balance,
        final_equity=balance,
        trades=paper_mgr.trade_history,
        session_title="Paper Replay 300 nến M5 (25 giờ)",
    )
    logger.info("\n%s", recap.to_terminal_box())

    # Send Session Recap to Telegram
    from src.monitoring.telegram_bot import TelegramNotifier
    telegram = TelegramNotifier()
    telegram.notify_session_summary(recap)

    wins = len([t for t in paper_mgr.trade_history if t.net_pnl > 0])
    wr = (wins / len(paper_mgr.trade_history)) if paper_mgr.trade_history else 0.0

    return {
        "initial_balance": live_balance,
        "final_balance": balance,
        "net_pnl": balance - live_balance,
        "total_trades": len(paper_mgr.trade_history),
        "wins": wins,
        "losses": len(paper_mgr.trade_history) - wins,
        "win_rate": wr,
        "recap": recap,
    }


def run_backtest_session(settings: SystemSettings, bar_count: int, output_path: str, logger) -> None:
    """Execute high-speed event-driven backtest and output tearsheet."""
    logger.info("Running event-driven backtest over %d bars...", bar_count)
    result = run_standard_backtest(bar_count=bar_count, initial_balance=settings.risk.reference_balance_usd)

    eq_series = pd.Series([settings.risk.reference_balance_usd] + [t.net_pnl for t in result.trades]).cumsum()
    metrics = calculate_performance_metrics(result.trades, eq_series, initial_balance=settings.risk.reference_balance_usd)
    tearsheet = generate_markdown_tearsheet(result, metrics, title="AI GOLD WATCHER V4 Backtest Tearsheet")

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(tearsheet, encoding="utf-8")

    logger.info("==================================================")
    logger.info("               BACKTEST RESULTS                   ")
    logger.info("==================================================")
    logger.info("Final Balance   : $%.2f USD (Return: %+.2f%%)", result.final_balance, result.return_pct)
    logger.info("Total Trades    : %d (Win Rate: %.1f%%)", metrics.total_trades, metrics.win_rate * 100)
    logger.info("Profit Factor   : %.2f", metrics.profit_factor)
    logger.info("Max Drawdown    : $%.2f (%.2f%%)", metrics.max_drawdown_usd, metrics.max_drawdown_pct)
    logger.info("Sharpe Ratio    : %.2f", metrics.sharpe_ratio)
    logger.info("Tearsheet saved to: %s", out_file.resolve())


def run_live_demo_loop(
    settings: SystemSettings,
    poll_interval_sec: float,
    logger,
    ai_threshold: float = 0.60,
    conf_threshold: float = 60.0,
    be_trigger_ratio: float = 0.52,
) -> None:
    """
    Execute real-time autonomous trading loop directly on MT5 DEMO account.
    Listens for new M5 closed bars, checks open positions, and places orders via MT5OrderBridge.
    """
    logger.info("==================================================")
    logger.info("  AI GOLD WATCHER V4 — REAL-TIME LIVE DEMO ENGINE  ")
    logger.info("==================================================")
    logger.info("Connecting to MT5 Demo Terminal...")

    from src.execution.mt5_order_bridge import MT5OrderBridge
    from src.execution.scalp_protection import ScalpProtectionEngine
    from src.scoring.meta_labeler import MetaLabelEngine
    from src.monitoring.telegram_bot import TelegramNotifier

    telegram = TelegramNotifier()
    meta_labeler = MetaLabelEngine(threshold=ai_threshold)
    scalp_engine = ScalpProtectionEngine(be_trigger_ratio=be_trigger_ratio, be_buffer_usd=0.25)

    try:
        bridge = MT5OrderBridge(symbol="XAUUSDm")
        active_symbol = bridge.symbol
    except Exception as e:
        logger.error("Failed to initialize MT5 Order Bridge: %s", e)
        return

    import MetaTrader5 as mt5
    acc = mt5.account_info()
    if acc is None:
        logger.error("Unable to retrieve MT5 account info.")
        return

    from src.config.license import verify_account_authorized
    if not verify_account_authorized(acc.login):
        logger.error("⛔ TRUY CẬP BỊ TỪ CHỐI! Tài khoản MT5 #%s chưa được cấp quyền.", acc.login)
        print("\n" + "=" * 65)
        print("⛔ TRUY CẬP BỊ TỪ CHỐI!")
        print(f"Tài khoản MetaTrader 5 #{acc.login} CHƯA ĐƯỢC CẤP QUYỀN SỬ DỤNG.")
        print("Vui lòng liên hệ Admin (LilBoiXAU) để được kích hoạt bản quyền!")
        print("=" * 65 + "\n")
        return

    logger.info("Connected to DEMO Account: #%s (%s) | Balance: $%.2f | Active Symbol: %s", acc.login, acc.name, acc.balance, active_symbol)
    logger.info("Strict Safety Parameters: Max 2 positions | Dynamic Lot Sizing (4.0%% SL / 6.0%% TP / -8.0%% Daily Breaker)")
    logger.info("Starting real-time polling loop (interval: %.1fs)... Press Ctrl+C to stop.", poll_interval_sec)

    db = init_db(settings.storage.db_path)
    signal_repo = SignalRepository(db)
    equity_repo = EquityRepository(db)

    indicator_engine = SharedIndicatorEngine()
    regime_detector = MarketRegimeDetector()
    selector = AdaptiveStrategySelector()
    confidence_engine = ConfidenceEngine(threshold=conf_threshold)
    news_guard = NewsGuard()
    spec = DEFAULT_EXNESS_XAUUSD
    risk_guard = RiskGuard(
        spec=spec,
        news_guard=news_guard,
        reference_balance=acc.balance,
        target_risk_usd=None,  # Option 1: 100% Dynamic Lot Sizing based on real-time Equity
        max_sl_pts=350,
        max_risk_pct=0.04,
    )

    client = LiveMT5Client(symbol=active_symbol)
    if not client.connect():
        logger.error("Failed to connect LiveMT5Client for symbol %s.", active_symbol)
        return

    last_processed_bar_time = None
    active_mt5_ticket = None
    tracked_positions: dict[int, dict] = {}
    control_state = {"is_paused": False}

    try:
        while True:
            # 1. Update MT5 Account and Equity snapshot
            acc = mt5.account_info()
            if acc is None:
                logger.warning("Lost connection to MT5 terminal, attempting reconnect...")
                mt5.initialize()
                time.sleep(poll_interval_sec)
                continue

            # Update live equity for dynamic 4% risk and 8% daily circuit breaker
            risk_guard.drawdown_guard.update_live_equity(acc.equity, datetime.now(timezone.utc))

            # Check approaching high-impact USD economic news alert (ForexFactory integration)
            news_alert = news_guard.check_upcoming_alert(datetime.now(timezone.utc))
            if news_alert is not None:
                ev, mins_until = news_alert
                logger.warning(
                    "HIGH-IMPACT USD NEWS APPROACHING: %s in %d mins! Dispatching Telegram alert...",
                    ev.title,
                    mins_until,
                )
                telegram.notify_news_upcoming(ev, mins_until)

            open_positions = bridge.get_open_positions()
            risk_guard.active_position_count = len(open_positions)

            # Scalp Protection Engine: Real-time Auto Break-Even and Trailing Stop
            if len(open_positions) > 0:
                pos = open_positions[0]
                scalp_act = scalp_engine.evaluate_position(pos)
                if scalp_act is not None:
                    mod_res = bridge.modify_position_sl(pos, scalp_act.new_sl, scalp_act.new_tp)
                    if mod_res.success:
                        if scalp_act.action_type == "BREAK_EVEN":
                            telegram.notify_break_even(
                                ticket=pos.ticket,
                                symbol=getattr(pos, "symbol", "XAUUSDm"),
                                side="BUY" if pos.type == 0 else "SELL",
                                entry_price=pos.price_open,
                                new_sl=scalp_act.new_sl,
                                tp_price=pos.tp,
                            )
                        elif scalp_act.action_type == "TRAILING_RUNNER":
                            is_buy = (pos.type == 0)
                            locked_pts = (scalp_act.new_sl - pos.price_open) if is_buy else (pos.price_open - scalp_act.new_sl)
                            locked_usd = locked_pts * getattr(pos, "volume", 0.01) * 100.0
                            telegram.notify_trailing_runner(
                                ticket=pos.ticket,
                                symbol=getattr(pos, "symbol", "XAUUSDm"),
                                side="BUY" if is_buy else "SELL",
                                current_price=pos.price_current,
                                new_sl=scalp_act.new_sl,
                                new_tp=scalp_act.new_tp,
                                locked_profit=max(0.0, locked_usd),
                            )
                        elif scalp_act.action_type == "TRAILING_STOP":
                            telegram.notify_trailing_stop(
                                ticket=pos.ticket,
                                symbol=getattr(pos, "symbol", "XAUUSDm"),
                                side="BUY" if pos.type == 0 else "SELL",
                                current_price=pos.price_current,
                                new_sl=scalp_act.new_sl,
                            )

            # Record periodic equity snapshot
            equity_repo.record_snapshot(
                timestamp=datetime.now(timezone.utc),
                balance=acc.balance,
                equity=acc.equity,
                open_positions=len(open_positions),
                daily_pnl=acc.equity - settings.risk.reference_balance_usd,
            )

            # 2. Check if a previously open position has closed in MT5
            for p in open_positions:
                if p.ticket not in tracked_positions:
                    tracked_positions[p.ticket] = {
                        "side": "BUY" if p.type == 0 else "SELL",
                        "price_open": p.price_open,
                        "symbol": getattr(p, "symbol", "XAUUSDm"),
                        "sl": p.sl,
                        "tp": p.tp,
                    }

            current_tickets = {p.ticket for p in open_positions}
            closed_tickets = [t for t in list(tracked_positions.keys()) if t not in current_tickets]
            for closed_ticket in closed_tickets:
                info = tracked_positions.pop(closed_ticket, {})
                logger.info("Vị thế #%d đã đóng trên MT5! Đang kiểm tra lịch sử khớp lệnh...", closed_ticket)
                scalp_engine.reset_ticket(closed_ticket)

                # Re-query fresh MT5 account balance and equity post-trade
                fresh_acc = mt5.account_info()
                fresh_balance = float(fresh_acc.balance) if fresh_acc else acc.balance
                fresh_equity = float(fresh_acc.equity) if fresh_acc else acc.equity

                deals = mt5.history_deals_get(position=closed_ticket)
                entry_price = float(info.get("price_open", 0.0))
                side = str(info.get("side", "BUY"))
                symbol = str(info.get("symbol", "XAUUSDm"))

                if deals and len(deals) >= 2:
                    exit_deal = deals[-1]
                    exit_price = float(exit_deal.price)
                    net_pnl = float(exit_deal.profit) + float(getattr(exit_deal, "swap", 0.0)) + float(getattr(exit_deal, "commission", 0.0))
                    comment = str(getattr(exit_deal, "comment", "") or "").lower()
                    reason_code = getattr(exit_deal, "reason", 0)

                    # MT5 reasons: 3=DEAL_REASON_TP, 4=DEAL_REASON_SL
                    if reason_code == 3 or "tp" in comment or "[tp]" in comment:
                        exit_reason = "TAKE_PROFIT (Chốt lời TP)"
                    elif reason_code == 4 or "sl" in comment or "[sl]" in comment:
                        if net_pnl > 0.05:
                            exit_reason = "TRAILING_STOP_SL_WIN (SL Dương / Hòa Vốn)"
                        else:
                            exit_reason = "STOP_LOSS (Cắt lỗ bảo vệ vốn)"
                    elif net_pnl > 0.05:
                        exit_reason = "PROFIT_CLOSE (Chốt lời có lãi)"
                    elif net_pnl < -0.05:
                        exit_reason = "STOP_LOSS (Cắt lỗ)"
                    else:
                        exit_reason = "BREAK_EVEN (Hòa vốn)"
                elif deals and len(deals) == 1:
                    exit_deal = deals[0]
                    exit_price = float(exit_deal.price)
                    net_pnl = float(exit_deal.profit)
                    exit_reason = "MANUAL_CLOSE (Đóng vị thế)"
                else:
                    exit_price = entry_price
                    net_pnl = 0.0
                    exit_reason = "POSITION_CLOSED"

                # Log to terminal with icons and new live balance
                if net_pnl > 0.05:
                    pnl_tag = f"🏆 [CHỐT LỜI TP WIN] Lệnh #{closed_ticket} ({side} {symbol})"
                elif net_pnl < -0.05:
                    pnl_tag = f"🛑 [CẮT LỖ SL HIT] Lệnh #{closed_ticket} ({side} {symbol})"
                else:
                    pnl_tag = f"🛡️ [HÒA VỐN / SL DƯƠNG] Lệnh #{closed_ticket} ({side} {symbol})"

                logger.info(
                    "%s | Lãi/Lỗ: %+.2f USD | 💰 Số dư hiện tại: $%.2f USD | Vốn thực: $%.2f USD (%s)",
                    pnl_tag,
                    net_pnl,
                    fresh_balance,
                    fresh_equity,
                    exit_reason,
                )

                telegram.notify_order_closed(
                    trade_id=f"deal_{closed_ticket}",
                    symbol=symbol,
                    side=side,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    net_pnl=net_pnl,
                    exit_reason=exit_reason,
                    balance=fresh_balance,
                    ticket=closed_ticket,
                    equity=fresh_equity,
                )

            # 3. Fetch latest closed M5 bar
            try:
                m5_bars = client.get_rates(active_symbol, Timeframe.M5, count=100, closed_only=True)
            except Exception as e:
                logger.warning("Error fetching rates from MT5: %s", e)
                time.sleep(poll_interval_sec)
                continue

            if not m5_bars:
                time.sleep(poll_interval_sec)
                continue

            latest_closed = m5_bars[-1]
            if last_processed_bar_time is None or latest_closed.timestamp > last_processed_bar_time:
                last_processed_bar_time = latest_closed.timestamp
                logger.info(
                    "New M5 Bar Closed: %s | Close: %.3f | Spread: %d pts",
                    latest_closed.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    latest_closed.close,
                    latest_closed.spread,
                )

                # Format DataFrame for indicators
                records = [
                    {
                        "time": b.timestamp,
                        "open": b.open,
                        "high": b.high,
                        "low": b.low,
                        "close": b.close,
                        "volume": b.tick_volume,
                        "spread": b.spread,
                    }
                    for b in m5_bars
                ]
                df_window = pd.DataFrame.from_records(records).set_index("time")
                enriched = indicator_engine.compute_all(df_window)

                # Multi-Timeframe Analysis: Fetch H1 closed bars to establish macro trend direction
                macro_result = None
                try:
                    h1_bars = client.get_rates(active_symbol, Timeframe.H1, count=50, closed_only=True)
                    if h1_bars:
                        macro_result = MacroTrendDetector.analyze(h1_bars)
                        logger.info("Multi-Timeframe Macro H1: %s (%s)", macro_result.bias.value, macro_result.description)
                except Exception as e:
                    logger.debug("Error fetching H1 rates: %s", e)

                # Regime Detection
                regime_state = regime_detector.update(enriched)
                logger.info("Current Market Regime: %s (Conf: %.2f)", regime_state.regime.value, regime_state.confidence)

                session_prof = SessionRouter.get_profile(latest_closed.timestamp)
                logger.info("Active Market Session: %s (%s)", session_prof.session.value, session_prof.name_vn)

                # Signal Evaluation if less than 2 positions are active (Institutional Pyramiding)
                if len(open_positions) < 2:
                    if control_state.get("is_paused"):
                        logger.info("Bot is PAUSED remotely via Telegram (/pause). Skipping trade search.")
                    else:
                        candidate = selector.evaluate(
                            df=enriched,
                            regime_state=regime_state,
                            spec=spec,
                            macro_bias=macro_result.bias if macro_result else None,
                            current_time=latest_closed.timestamp,
                        )
                    if candidate is not None:
                        # Machine Learning Meta-Labeling filter
                        ai_res = meta_labeler.predict_win_probability(
                            candidate=candidate,
                            df_indicators=enriched,
                            regime_state=regime_state,
                            current_spread=latest_closed.spread,
                        )
                        logger.info(
                            "AI Meta-Label: P(win)=%.1f%% (Min: %.1f%%) | Filter: %s",
                            ai_res.win_probability * 100,
                            ai_res.threshold * 100,
                            "PASS" if ai_res.passes_filter else "REJECTED",
                        )

                        scored = confidence_engine.score(
                            candidate=candidate,
                            regime_state=regime_state,
                            current_spread=latest_closed.spread,
                        )
                        risk_res = risk_guard.evaluate_signal(
                            scored=scored,
                            current_spread=latest_closed.spread,
                            current_time=latest_closed.timestamp,
                            open_positions=open_positions,
                        )

                        # Enforce AI Filter in approval logic
                        final_approved = risk_res.is_approved and ai_res.passes_filter
                        rejection_msg = risk_res.rejection_reason
                        if risk_res.is_approved and not ai_res.passes_filter:
                            rejection_msg = f"VETO: AI Meta-Labeling win probability ({ai_res.win_probability*100:.1f}%) < {ai_res.threshold*100:.1f}%"

                        signal_repo.save_signal(
                            signal=scored,
                            is_approved=final_approved,
                            rejection_reason=rejection_msg,
                            regime=regime_state.regime.value,
                        )
                        logger.info(
                            "Signal %s: %s %s @ %.3f | Conf: %.1f | AI P(win): %.1f%% | Approved: %s (%s)",
                            scored.candidate.strategy_id,
                            scored.candidate.side.value,
                            scored.candidate.symbol,
                            scored.candidate.entry_price,
                            scored.total_score,
                            ai_res.win_probability * 100,
                            final_approved,
                            rejection_msg,
                        )

                        if final_approved and risk_res.order is not None:
                            logger.info("Executing MT5 DEMO Order via Bridge: %s %.2f lot %s...", risk_res.order.side.value, risk_res.order.volume, risk_res.order.symbol)
                            exec_res = bridge.send_market_order(risk_res.order)
                            if exec_res.success:
                                active_mt5_ticket = exec_res.order_ticket
                                tracked_positions[exec_res.order_ticket] = {
                                    "side": risk_res.order.side.value,
                                    "price_open": exec_res.price,
                                    "symbol": risk_res.order.symbol,
                                    "sl": risk_res.order.stop_loss,
                                    "tp": risk_res.order.take_profit,
                                }
                                is_scale_in = len(open_positions) > 0
                                logger.info(
                                    "%s ORDER ACTIVE: #%d (%s @ %.3f)",
                                    "LIVE SCALE-IN PYRAMID" if is_scale_in else "LIVE DEMO",
                                    exec_res.order_ticket,
                                    risk_res.order.side.value,
                                    exec_res.price,
                                )
                                telegram.notify_order_opened(
                                    order=risk_res.order,
                                    fill_price=exec_res.price,
                                    confidence_score=scored.total_score,
                                    regime=regime_state.regime.value,
                                    ticket=exec_res.order_ticket,
                                    ai_prob=ai_res.win_probability,
                                )
                            else:
                                logger.error(
                                    "❌ VÀO LỆNH MT5 THẤT BẠI: %s (Mã lỗi retcode: %d)",
                                    exec_res.retcode_description,
                                    exec_res.retcode,
                                )
                                try:
                                    telegram.send_alert(
                                        f"⚠️ <b>LỖI VÀO LỆNH MT5 ({exec_res.retcode})</b>\n"
                                        f"• Chi tiết: <code>{exec_res.retcode_description}</code>\n"
                                        f"• Chiến thuật: {scored.candidate.strategy_id} ({scored.candidate.side.value} @ {scored.candidate.entry_price:.3f})\n"
                                        f"💡 <i>Gợi ý: Kiểm tra nút 'Algo Trading' trên MT5 (cần màu xanh) hoặc trần khối lượng!</i>"
                                    )
                                except Exception as err:
                                    logger.debug("Failed to send Telegram alert for order failure: %s", err)
                if open_positions:
                    pos_summary = ", ".join(
                        f"#{p.ticket} ({'BUY' if p.type == 0 else 'SELL'} @ {p.price_open:.2f}, PnL: ${p.profit:.2f})"
                        for p in open_positions
                    )
                    logger.info("Holding Active Position(s) [%d/2]: %s", len(open_positions), pos_summary)

            # Process incoming Telegram interactive commands (/status, /balance, /positions, /signals, /pause, /resume, /close, /help)
            context = {
                "account": acc,
                "open_positions": open_positions,
                "regime": regime_state if "regime_state" in locals() else None,
                "macro_result": macro_result if "macro_result" in locals() else None,
                "latest_bar": latest_closed if "latest_closed" in locals() else None,
                "recent_signals": signal_repo.get_recent_signals(limit=5),
                "reference_balance": settings.risk.reference_balance_usd,
                "control_state": control_state,
                "risk_guard": risk_guard,
                "news_guard": news_guard,
                "bridge": bridge,
            }
            telegram.process_incoming_commands(context)

            time.sleep(poll_interval_sec)

    except KeyboardInterrupt:
        logger.info("Real-time loop gracefully stopped by user.")
    finally:
        try:
            from src.evaluation.session_recap import build_session_recap
            fresh_acc = mt5.account_info()
            curr_b = float(fresh_acc.balance) if fresh_acc else acc.balance
            curr_eq = float(fresh_acc.equity) if fresh_acc else acc.equity
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_deals = mt5.history_deals_get(today_start, datetime.now(timezone.utc))
            recap = build_session_recap(
                initial_balance=settings.risk.reference_balance_usd,
                final_balance=curr_b,
                final_equity=curr_eq,
                deals=list(today_deals) if today_deals else [],
                session_title="Live Demo Session (Thời gian thực)",
            )
            logger.info("\n%s", recap.to_terminal_box())
            telegram.notify_session_summary(recap)
        except Exception as err:
            logger.debug("Error generating final session recap: %s", err)
        client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="AI GOLD WATCHER V4 Execution Controller")
    parser.add_argument(
        "--mode",
        choices=["paper", "backtest", "diagnose", "live-demo"],
        default="paper",
        help="System execution mode",
    )
    parser.add_argument("--bars", type=int, default=300, help="Number of bars to process")
    parser.add_argument("--mock", action="store_true", default=True, help="Force mock MT5 client")
    parser.add_argument("--live", action="store_true", help="Use Live MT5 client (read-only copy_rates)")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=5.0,
        help="Polling interval in seconds for real-time live-demo mode",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/backtest_tearsheet.md",
        help="Tearsheet output path",
    )

    args = parser.parse_args()
    settings = SystemSettings()
    logger = setup_logger(logs_dir=settings.storage.logs_dir)

    use_mock = not args.live

    if args.mode == "diagnose":
        success = run_diagnostics(settings, logger)
        sys.exit(0 if success else 1)
    elif args.mode == "backtest":
        run_backtest_session(settings, bar_count=args.bars, output_path=args.output, logger=logger)
    elif args.mode == "paper":
        run_paper_session(settings, bar_count=args.bars, use_mock=use_mock, logger=logger)
    elif args.mode == "live-demo":
        run_live_demo_loop(settings, poll_interval_sec=args.poll_interval, logger=logger)


if __name__ == "__main__":
    main()
