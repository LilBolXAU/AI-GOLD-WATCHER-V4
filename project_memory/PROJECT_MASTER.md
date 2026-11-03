# PROJECT MASTER — AI GOLD WATCHER V4

**Document ID**: `AGW-V4-MEM-MASTER`  
**Classification**: Immutable Core Charter  
**Status**: Active  
**Last Updated**: 2026-11-03  

---

## 1. Project Purpose & Philosophy

**AI GOLD WATCHER V4** is a quantitative, adaptive, multi-strategy algorithmic trading bot engineered specifically for the Gold (`XAUUSDm`) market. 

The system treats trading strategies as probabilistic scientific hypotheses rather than static magic formulas. The bot combines:
- Statistical price action and market microstructure analysis.
- Multi-regime classification (Wilder ADX/DMI + ATR volatility $z$-scores with hysteresis).
- Four completely decoupled strategy engines (Trend, Pullback, Breakout, Range Reversal).
- Pre-trade risk controls and strict volatility-budgeted position sizing.
- Lopez de Prado's Meta-Labeling for dynamic confidence scoring.
- Combinatorial Purged Cross-Validation (CPCV) and Deflated Sharpe Ratio (DSR) to eliminate data-mining bias.

---

## 2. Market, Broker & Platform Specifications

| Dimension | Specification | Notes |
| :--- | :--- | :--- |
| **Market Instrument** | `XAUUSDm` (Gold vs US Dollar) | Exness suffix `m` (Standard / Standard Cent). Never hardcode `XAUUSD`. |
| **Broker** | Exness | MetaTrader 5 server (EET/EEST timezone, UTC+2/+3). |
| **Platform** | MetaTrader 5 | Python API (`MetaTrader5` 5.0.6231). |
| **Operating System** | Windows 11 x86-64 | Native MT5 terminal host. |
| **Language & Runtime** | Python 3.13.7 | Strict type hinting, Pydantic schemas, NumPy 2.4, Pandas 3.1. |
| **Execution Mode** | Demo & Paper Trading | **Zero live executable orders permitted** during development. |

---

## 3. Financial & Trading Risk Constraints (Zero-Tolerance)

- **Reference Account Capital**: `$50.00 USD` (Demo baseline).
- **Fixed Position Sizing**: `0.01 lot` (1 troy ounce of Gold; contract size 100).
- **Mathematical Sensitivity**: A `$1.00` price movement in Gold = exactly `$1.00` P&L at 0.01 lot.
- **Target Risk Budget**: `~$1.00 per trade` (2.0% of reference balance).
- **Maximum Stop Loss Distance**: `100 points ($1.00)` at 0.01 lot. If market ATR demands an SL wider than $1.00, the trade **must be skipped**.
- **Maximum Concurrent Positions**: `1` (Mutual exclusivity; zero simultaneous multi-position risk).
- **Daily Loss Circuit Breaker**: `$2.00` (4.0% of reference balance). If breached, trading halts for the remainder of the session.
- **Consecutive Loss Breaker**: `3 consecutive losses` triggers an automatic strategy pause and quantitative review.
- **Strict Strategy Prohibitions**:
  - **NO MARTINGALE**: Never increase lot size after a loss.
  - **NO GRID TRADING**: Never place unmanaged ladders of orders into losing moves.
  - **NO AVERAGING DOWN**: Adding to losing positions is strictly prohibited.
  - **NO AUTOMATIC LEVERAGE INCREASES**: Account leverage is fixed and never modified programmatically.

---

## 4. Overall Development Roadmap

The development follows a rigorous, sequential, test-gated 5-stage progression:

- **Stage 0 — Environment & Skill Fortification** (COMPLETED):
  - 42 audited Agent Skills installed in `.agents/skills/`.
  - 7 specialized agent roles configured in `.agents/agents/`.
  - Workspace rules (`AGENTS.md`, `GEMINI.md`) established.
  - Verification audit completed (`V4_ENVIRONMENT_VERIFICATION.md`).
  - Persistent memory system instantiated (`project_memory/`).

- **Stage 1 — Foundational Infrastructure** (PENDING):
  - `src/data/`: MT5 Data Engine with closed-bar discipline and UTC normalization.
  - `src/indicators/`: Shared Indicator Engine (EMA, ATR, RSI, ADX).
  - Headless Mock MT5 adapter and comprehensive `pytest` unit test suite.

- **Stage 2 — Market Regime Detector & Decoupled Strategies**:
  - `src/regime/`: ADX/ATR $z$-score classifier with 3-bar hysteresis.
  - `src/strategies/`: 4 decoupled engines (Trend, Pullback, Breakout, Range Reversal).
  - `src/selector/` & `src/scoring/`: Regime routing and confidence scoring.

- **Stage 3 — Financial Risk Core & Paper Trading Engine**:
  - `src/risk/`: Pre-trade risk gates ($1 risk cap, Exness spread checks, circuit breakers).
  - `src/execution/`: Paper trading engine with realistic fill and slippage modeling.
  - MiFID II / SEC 15c3-5 boundary test suite.

- **Stage 4 — Event-Driven Backtesting & Validation**:
  - `src/backtest/`: Next-bar fill event simulator.
  - `src/evaluation/` & `src/research/`: CPCV, Walk-Forward Optimization, Deflated Sharpe Ratio.
  - Out-of-sample Gold data validation (2020–2026).

- **Stage 5 — Telemetry & Demo Integration**:
  - `src/monitoring/`: Structured JSON logging, heartbeat, and alerting.
  - Live Exness MT5 demo feed connection (read-only data, paper fills).
