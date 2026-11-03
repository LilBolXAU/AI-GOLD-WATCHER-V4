"""
Streamlit Monitoring & Research Dashboard for AI GOLD WATCHER V4.
Run using: streamlit run src/monitoring/dashboard.py
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# Add workspace root to sys.path so src imports work when launched via streamlit
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.config.settings import SystemSettings, RiskSettings, BrokerSettings
from src.storage.database import init_db
from src.storage.repositories import TradeRepository, SignalRepository, EquityRepository


def render_dashboard():
    st.set_page_config(
        page_title="AI GOLD WATCHER V4 — Quantitative Monitor",
        page_icon="🛡️",
        layout="wide",
    )

    st.title("🛡️ AI GOLD WATCHER V4 — Execution & Telemetry Monitor")
    st.caption("Asset: XAUUSDm (Gold) | Broker: Exness MT5 | Paper Mode: 100% Gated (Zero Live Orders)")

    # Sidebar: Safety Guardrails & Settings
    st.sidebar.header("🔒 Safety Guardrails")
    st.sidebar.markdown(
        """
        - **Reference Balance**: $50.00 USD
        - **Reference Lot**: 0.01 lot (1 oz)
        - **Risk Budget**: ~$1.00 / trade (2%)
        - **Max SL Distance**: 100 points ($1.00)
        - **Daily Loss Breaker**: $2.00 (4%)
        - **Consecutive Loss Breaker**: 3 trades
        - **Live Order Execution**: **DISABLED (MOCK/PAPER ONLY)**
        """
    )

    settings = SystemSettings()
    db = init_db(settings.storage.db_path)
    trade_repo = TradeRepository(db)
    signal_repo = SignalRepository(db)
    equity_repo = EquityRepository(db)

    # Top Metrics Bar
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Mode", settings.mode)
    with col2:
        st.metric("Reference Capital", f"${settings.risk.reference_balance_usd:.2f}")
    with col3:
        st.metric("Risk Budget / Trade", f"${settings.risk.target_risk_usd:.2f}")
    with col4:
        st.metric("Daily Loss Breaker", f"${settings.risk.daily_loss_limit_usd:.2f}")
    with col5:
        st.metric("Dry Run Latch", "ACTIVE 🟢")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Live Paper Equity",
        "🎯 Signals & Regimes",
        "📜 Closed Trades",
        "⚙️ System Diagnostics",
    ])

    with tab1:
        st.subheader("Equity Curve & Performance History")
        eq_data = equity_repo.get_equity_history()
        if eq_data:
            df_eq = pd.DataFrame(eq_data)
            df_eq["timestamp"] = pd.to_datetime(df_eq["timestamp"])
            st.line_chart(df_eq.set_index("timestamp")[["balance", "equity"]])
            st.dataframe(df_eq.tail(10), use_container_width=True)
        else:
            st.info("No equity snapshots recorded yet. Run bot paper session to generate history.")

    with tab2:
        st.subheader("Recent Multi-Timeframe Signals")
        signals = signal_repo.get_recent_signals(limit=25)
        if signals:
            df_sig = pd.DataFrame(signals)
            st.dataframe(df_sig, use_container_width=True)
        else:
            st.info("No signals generated yet.")

    with tab3:
        st.subheader("Paper Trading History")
        trades = trade_repo.get_all_trades()
        if trades:
            df_trades = pd.DataFrame(trades)
            st.dataframe(df_trades, use_container_width=True)
            # PnL metrics
            total_net = df_trades["net_pnl"].sum()
            n_wins = len(df_trades[df_trades["net_pnl"] > 0])
            st.write(f"**Total Closed Trades**: {len(df_trades)} | **Net PnL**: ${total_net:.2f} | **Win Rate**: {n_wins/len(df_trades):.1%}")
        else:
            st.info("No closed paper trades recorded yet.")

    with tab4:
        st.subheader("System Architecture & Diagnostic Verification")
        st.markdown(
            """
            ### Decoupled 12-Module Pipeline
            1. **MT5 Data Engine**: Multi-timeframe bar collector (M15/M5/M1), UTC normalization, closed-bar rule.
            2. **Indicator Engine**: Wilder ATR/RSI, EMA alignment, Bollinger Bands, Efficiency Ratio.
            3. **Regime Detector**: ADX + ATR Z-score + 3-bar hysteresis + volatility shock override.
            4. **4 Independent Strategies**: Trend Following, Pullback Continuation, Breakout, Range Reversal.
            5. **Adaptive Selector**: Regime-conditioned routing, mutual exclusivity, priority tie-breaker.
            6. **Confidence Engine**: Multi-factor scoring [0-100], minimum threshold 65.0.
            7. **Risk Guard**: Absolute veto authority, $1.00 risk cap, $2.00 daily loss breaker, 0.01 lot check.
            8. **Paper Engine**: Virtual fills with floating spread & slippage, intrabar SL/TP detection.
            9. **Backtesting Engine**: Event-driven bar-by-bar runner, zero lookahead, walk-forward validation.
            10. **Evaluation Engine**: Sharpe, Sortino, Profit Factor, Deflated Sharpe Ratio (DSR).
            11. **Research & Optimization**: Parameter sensitivity surfaces, cliff detection, regime attribution.
            12. **Monitoring & Reporting**: Structured logs, alerts, Streamlit dashboard.
            """
        )


if __name__ == "__main__":
    render_dashboard()
