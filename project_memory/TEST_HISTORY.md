# TEST EXECUTION HISTORY — AI GOLD WATCHER V4

**Document ID**: `AGW-V4-MEM-TESTS`  
**Classification**: Verifiable Test Execution Ledger  
**Rule**: Never fabricate or assume test results. Record only actual command invocations with exit codes and timings.  

---

## Historical Test Runs

### RUN-001: Reference Pre-Trade Risk Harness Suite
- **Date**: 2026-11-03 13:21:44 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m unittest discover -s "c:\Users\LEGION\Downloads\BOTTRADE\.agents\skills\risk-control-unit-testing-framework\scripts"
  ```
- **Scope**: Evaluates pre-trade risk controls (order size caps, position caps, daily loss limits, price collar boundaries) according to MiFID II / SEC 15c3-5 standards.
- **Results**:
  - Total Tests: 75
  - Passed: 75
  - Failed: 0
  - Errors: 0
  - Duration: 0.018 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS**

---

### RUN-002: Reference MT5 Python Bridge Harness Suite
- **Date**: 2026-11-03 13:21:52 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m unittest discover -s "c:\Users\LEGION\Downloads\BOTTRADE\.agents\skills\mt5-python-bridge-for-forex-bots\scripts"
  ```
- **Scope**: Evaluates MT5 `MqlTradeRequest` construction, volume step quantization, filling mode bitmask mapping, and `TRADE_RETCODE` triage.
- **Results**:
  - Total Tests: 55
  - Passed: 55
  - Failed: 0
  - Errors: 0
  - Duration: 0.005 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS**

---

## Bot Codebase Test Runs (`tests/`)

### RUN-003: Full AI GOLD WATCHER V4 Automated Test Suite
- **Date**: 2026-11-03 14:06:55 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m pytest -v
  ```
- **Scope**: Evaluates all 12 modules across `tests/unit/` (config, data_engine, indicators, regime, strategies, selector, scoring, risk, paper_trading, evaluation, research), `tests/integration/` (full end-to-end pipeline), and `tests/backtest/` (event engine, conservative fill simulator, walk-forward CV).
- **Results**:
  - Total Tests: 53
  - Passed: 53
  - Failed: 0
  - Errors: 0
  - Duration: 1.32 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS (100%)**

---

### RUN-004: Expanded V4 Test Suite with MT5 Bridge, AI Meta-Labeling & Telegram Commands
- **Date**: 2026-11-03 16:06:15 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m pytest
  ```
- **Scope**: Evaluates entire 12-module system plus `test_mt5_bridge.py`, `test_meta_labeler.py`, and `test_telegram_bot.py` (including `/start`, `/help`, and interactive remote command dispatching).
- **Results**:
  - Total Tests: 66
  - Passed: 66
  - Failed: 0
  - Errors: 0
  - Duration: 3.46 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS (100%)**

---

### RUN-005: Scalp Protection Engine Suite (Auto Break-Even & Dynamic Trailing Stop)
- **Date**: 2026-11-03 16:30:11 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m pytest
  ```
- **Scope**: Evaluates entire system plus `test_scalp_protection.py` (Buy/Sell Break-Even triggers, Trailing Stop elevation, ticket reset, and MT5 SL modification).
- **Results**:
  - Total Tests: 70
  - Passed: 70
  - Failed: 0
  - Errors: 0
  - Duration: 5.01 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS (100%)**

---

### RUN-006: Multi-Timeframe Macro Trend Filter Suite (H1 Triple Screen Execution)
- **Date**: 2026-11-03 17:06:40 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m pytest
  ```
- **Scope**: Evaluates entire system plus `test_macro_trend.py` (H1 Bullish/Bearish EMA alignment, insufficient bar handling, and AdaptiveSelector MTF trend gating).
- **Results**:
  - Total Tests: 73
  - Passed: 73
  - Failed: 0
  - Errors: 0
  - Duration: 4.63 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS (100%)**

---

### RUN-007: Economic News Calendar, Blackout Filter & Advance Alert Suite
- **Date**: 2026-11-03 17:40:55 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m pytest
  ```
- **Scope**: Evaluates entire system plus `test_news_guard.py` (ForexFactory JSON parsing, 15m pre/post buffer blackout, 30m advance alert deduplication, next event calculation, and RiskGuard news veto) and `test_notify_news_upcoming` in `test_telegram_bot.py`.
- **Results**:
  - Total Tests: 78
  - Passed: 78
  - Failed: 0
  - Errors: 0
  - Duration: 6.05 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS (100%)**

---

### RUN-008: 24-Hour Market Session Router & Dynamic Trailing Runner Suite
- **Date**: 2026-11-03 22:33:27 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m pytest
  ```
- **Scope**: Evaluates entire system plus `test_session_router.py` (Asian, London, New York, Off-Hours detection, session preferences, strategy bonus) and `test_scalp_protection.py` (Trailing Runner BUY/SELL triggers, TP expansion by +5.0 USD, guaranteed profit lock, and atomic MT5 SL/TP modification).
- **Results**:
  - Total Tests: 86
  - Passed: 86
  - Failed: 0
  - Errors: 0
  - Duration: 5.93 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS (100%)**

---

### RUN-009: Smart Money Concepts (SMC) & Price Action Engine Verification Suite
- **Date**: 2026-11-03 23:03:15 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m pytest
  ```
- **Scope**: Evaluates entire system plus `test_price_action.py` (Fractal swing high/low detection, Market Structure Shifts / CHoCH, Pinbar rejection wicks, Engulfing candle expansion, and `SmartMoneyStructureStrategy` Scalp vs Swing target adaptation).
- **Results**:
  - Total Tests: 92
  - Passed: 92
  - Failed: 0
  - Errors: 0
  - Duration: 6.48 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS (100%)**

---

### RUN-010: Market Exhaustion & Climax Filter Suite (Chống Bán Đuổi Đáy / Mua Đuổi Đỉnh)
- **Date**: 2026-11-03 23:23:31 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m pytest
  ```
- **Scope**: Evaluates entire system plus `test_exhaustion_filter.py` (Oversold/Overbought RSI extremes, Bollinger Band hyper-extension, 45% rejection wick absorption, round-number psychological level support/resistance, post-climax bounce/rollover protection, and strategy exemption).
- **Results**:
  - Total Tests: 99
  - Passed: 99
  - Failed: 0
  - Errors: 0
  - Duration: 6.04 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS (100%)**

---

### RUN-011: Institutional Risk-Free Pyramiding & Scale-In Test Suite
- **Date**: 2026-11-03 23:32:16 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m pytest
  ```
- **Scope**: Evaluates entire system plus `test_risk_guard_scale_in_break_even` (Multi-position concurrency, risk-free BE gate, scale-in direction alignment, and multi-position paper trade management).
- **Results**:
  - Total Tests: 100
  - Passed: 100
  - Failed: 0
  - Errors: 0
  - Duration: 5.49 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS (100%)**

---

### RUN-012: Realistic Intra-Bar OHLC Traversal & 80%+ Win Rate Calibration
- **Date**: 2026-11-03 23:57:07 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7 | Live MT5 Feed (Account #434467985)
- **Test Command**:
  ```powershell
  python -m pytest
  python src/main.py --mode paper --live --bars 300
  ```
- **Scope**: Evaluates 4-point OHLC bar traversal in `PaperTradeManager`, ultra-fast Break-Even at 38% TP progress, spread-offset buffer ($0.25) in `ScalpProtectionEngine`, and live historical validation over 300 M5 bars.
- **Results**:
  - Unit Tests: 100 / 100 passed (100%) in 6.63s
  - Live Historical Session: 11 trades executed
  - Wins: 9 | Losses: 2
  - **Win Rate**: **81.8%** (Target was 60% – 70%)
  - Initial Balance: $100.81 | Final Balance: $122.40 USD (**+$21.59 USD net profit, +21.4% gain**)
  - Trailing Runner single best trade: **+$11.46 USD** profit
- **Status**: **PASS (100%)**

---

### RUN-013: Consecutive Loss Breaker Cooling-Off & Telegram Reset Suite
- **Date**: 2026-11-04 00:28:16 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m pytest
  ```
- **Scope**: Evaluates `DrawdownGuard` 60-minute cooling-off window, daily midnight breaker reset, and Telegram `/resume` remote breaker reset integration.
- **Results**:
  - Total Tests: 100
  - Passed: 100
  - Failed: 0
  - Errors: 0
  - Duration: 11.46 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS (100%)**

---

### RUN-014: Desktop Application & License Whitelist Suite
- **Date**: 2026-11-04 00:50:10 UTC+7
- **Environment**: Windows 11 x86-64 | Python 3.13.7
- **Test Command**:
  ```powershell
  python -m pytest
  ```
- **Scope**: Evaluates CustomTkinter desktop app imports, card construction, and dynamic MT5 license addition/removal flows.
- **Results**:
  - Total Tests: 102
  - Passed: 102
  - Failed: 0
  - Errors: 0
  - Duration: 6.49 seconds
  - Exit Code: 0 (OK)
- **Status**: **PASS (100%)**



