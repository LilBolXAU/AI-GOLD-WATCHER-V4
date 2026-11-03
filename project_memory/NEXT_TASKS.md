# NEXT TASKS — AI GOLD WATCHER V4

**Document ID**: `AGW-V4-MEM-TASKS`  
**Classification**: Mutable Work Breakdown Ledger  
**Last Updated**: 2026-11-03  

---

## 1. Completed Tasks (V4 Complete System Implementation)
- [x] Configure 42 skills and 7 agent definitions.
- [x] Implement Module 00: Configuration & Safety Guardrails (`src/config/`).
- [x] Implement Module 01: MT5 Data Engine with closed-bar discipline & UTC normalization (`src/data/`).
- [x] Implement Module 02: Shared Indicator Engine (`src/indicators/`).
- [x] Implement Module 03: Market Regime Detector with 3-bar hysteresis & shock override (`src/regime/`).
- [x] Implement Module 04: Four Independent Strategies (Trend, Pullback, Breakout, Range Reversal) (`src/strategies/`).
- [x] Implement Module 05: Adaptive Strategy Selector with regime gating & mutual exclusivity (`src/selector/`).
- [x] Implement Module 06: Confidence Scoring Engine with 5-factor scoring (`src/scoring/`).
- [x] Implement Module 07: Financial & Risk Engine with $1 risk budget & $2 circuit breaker (`src/risk/`).
- [x] Implement Module 08: Paper Trading Engine with floating spread & slippage (`src/execution/`).
- [x] Implement Module 09: Event-Driven Backtesting Engine with walk-forward CV (`src/backtest/`).
- [x] Implement Module 10: Performance Evaluation with Deflated Sharpe Ratio (`src/evaluation/`).
- [x] Implement Module 11: Research & Optimization with parameter cliff detection (`src/research/`).
- [x] Implement Module 12: Monitoring, SQLite storage & Streamlit Dashboard (`src/monitoring/`, `src/storage/`).
- [x] Implement Main CLI entry point (`src/main.py`).
- [x] Implement full test suite: 53 tests in `tests/` passing with 100% success rate.
- [x] Author full documentation suite (`README.md`, `WINDOWS_SETUP.md`, `ARCHITECTURE.md`, `STRATEGY_DOCUMENTATION.md`, `RISK_DOCUMENTATION.md`, `BACKTESTING_GUIDE.md`, `TEST_REPORT.md`, `IMPLEMENTATION_STATUS.md`).
- [x] Create Windows batch launch scripts (`install.bat`, `run_tests.bat`, `run_paper.bat`, `run_paper_live.bat`, `run_live_demo.bat`, `run_backtest.bat`, `run_dashboard.bat`, `diagnose.bat`).
- [x] Implement Live MT5 Order Bridge (`src/execution/mt5_order_bridge.py`) with DEMO-only guardrails and IOC filling mode.
- [x] Implement Local Machine Learning Meta-Labeling Engine (`src/scoring/meta_labeler.py`) with 13-feature vector and P(win) >= 65% filter.
- [x] Implement 100% Free Telegram Bot Notifier (`src/monitoring/telegram_bot.py`) for live entry, exit, and emergency circuit breaker alerts.
- [x] Implement Option 1 Dynamic Equity Lot Sizing (4% SL, 6% TP, R:R 1:1.5, -8% dynamic daily circuit breaker).
- [x] Implement Scalp Protection Engine (Auto Break-Even Lệnh Bất Tử at 50% TP, Dynamic Trailing Stop at 70% TP).
- [x] Implement Multi-Timeframe Macro Trend Filter (H1 Triple Screen Execution gating M5 entries).
- [x] Implement High-Impact Economic News Calendar & Blackout Filter (ForexFactory integration, 15m pre/post blackout, 30m advance Telegram alerts).
- [x] Implement 24-Hour Market Session Router (`src/regime/session_router.py`) & Dynamic Trailing Runner ("Gồng Lãi Động" with +$5 TP expansion).
- [x] Implement Asian Range Scalper (`src/strategies/asian_scalp.py`) and London Liquidity Sweep (`src/strategies/london_sweep.py`).
- [x] Implement Price Action & Market Structure Engine (`src/indicators/price_action.py`) with Fractal Swing Pivots, BOS/CHoCH, Pinbars, and Engulfing patterns.
- [x] Implement Smart Money Concepts Strategy (`src/strategies/smc_structure.py`) with dynamic Scalp vs Swing target adaptation (1:1.5 vs 1:2.5 R:R).
- [x] Decouple H1 Macro Trend filter to allow structural reversal/bounce strategies to execute confirmed shifts, eliminating counter-trend selling into rallies.
- [x] Synchronize live MT5 terminal account balance and real-time closed bars into paper trading mode.
- [x] Resolve 3-digit broker tick rounding false veto with $0.02 buffer in `position_sizing.py` and fix Telegram `/signals` timestamp display.
- [x] Implement Market Exhaustion & Climax Filter (`src/regime/exhaustion_filter.py`) preventing bottom-chasing SELLs and top-chasing BUYs via RSI extremes, band stretch, 45% rejection wicks, $50 round levels, and post-climax bounce protection.
- [x] Implement Institutional Risk-Free Pyramiding & Scale-In Engine (`src/risk/risk_guard.py`, `src/execution/paper_trade_manager.py`) with max 2 positions gated by Break-Even protection.
- [x] Expand automated test suite to 100 passed tests with 100% pass rate.

---

## 2. Next Horizon Tasks (Forward Research & Iteration)
- [ ] Connect Live MT5 Demo terminal session during London/NY trading hours to record real Exness tick volatility.
- [ ] Run parameter sensitivity surface mapping across ATR multipliers (1.0 to 3.0) and ADX thresholds (20 to 30) using historical Exness M5 data.
- [ ] Evaluate Deflated Sharpe Ratio across out-of-sample walk-forward folds to identify highest-conviction strategy parameters.
- [ ] Monitor paper trading PnL curve and circuit breaker telemetry in real-time via the Streamlit dashboard.
