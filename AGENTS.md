# AI GOLD WATCHER V4 — WORKSPACE RULES & TRADING SAFETY GUARDRAILS

## Project Identity & Parameters
- **Project Name**: AI GOLD WATCHER V4
- **Trading Market**: Gold (`XAUUSDm`)
- **Broker**: Exness
- **Platform**: MetaTrader 5 (MT5 Python API, Windows 11)
- **Language**: Python 3.13.7
- **Development Environment**: Google Antigravity
- **Initial Development Mode**: Demo & Paper Trading (Zero live order execution)
- **Reference Balance**: $50.00 USD
- **Initial Volume**: 0.01 lot (1 troy ounce; contract size 100)
- **Target Risk Budget**: ~$1.00 per trade (2% of reference balance)
- **Max Stop Loss Distance**: 100 points ($1.00) at 0.01 lot
- **Max Concurrent Positions**: 1 (Mutual exclusivity)
- **Daily Loss Circuit Breaker**: $2.00 (4% of reference balance) -> Halt trading for session
- **Consecutive Loss Breaker**: 3 consecutive losses -> Automatic strategy pause

---

## Strict Trading Safety Rules (Zero-Tolerance)
1. **NO LIVE TRADING DURING DEVELOPMENT**: Live trading is strictly forbidden in this development environment.
2. **NO EXECUTABLE LIVE `order_send` CALLS**: During research, backtesting, and paper trading, all orders must route through the `PaperTradingEngine` or simulated mock adapters. Real `mt5.order_send` calls are gated behind an explicit dry-run safety latch (`DRY_RUN_ENABLED=True`).
3. **NO MARTINGALE**: Never double down after a loss. Sizing is governed by strict volatility/dollar risk budgets.
4. **NO GRID TRADING**: Never place uncontrolled ladders of open orders into losing moves.
5. **NO UNCONTROLLED AVERAGING DOWN**: Adding to losing positions is strictly prohibited.
6. **NO AUTOMATIC LEVERAGE INCREASES**: Account leverage must never be increased programmatically.
7. **NO AUTOMATIC RISK-BUDGET INCREASES**: Risk per trade is capped at ~$1.00 until human quantitative review.
8. **NO HARDCODED CREDENTIALS**: Never write account numbers, MT5 passwords, or API keys in source code or commits. Always use `.env` or system environment variables.
9. **NO GUARANTEED-PROFIT CLAIMS**: Every strategy is treated as a probabilistic hypothesis requiring out-of-sample statistical verification.

---

## 12-Module Decoupled Architecture
1. **MT5 Data Engine** (`src/data/`)
2. **Shared Indicator Engine** (`src/indicators/`)
3. **Market Regime Detector** (`src/regime/`)
4. **Four Independent Strategies** (`src/strategies/`):
   - Trend Following Engine
   - Pullback Continuation Engine
   - Breakout Engine
   - Range Reversal Engine
5. **Adaptive Strategy Selector** (`src/selector/`)
6. **Confidence Scoring Engine** (`src/scoring/`)
7. **Financial & Risk Engine** (`src/risk/`)
8. **Paper Trading Engine** (`src/execution/`)
9. **Backtesting Engine** (`src/backtest/`)
10. **Performance Evaluation Engine** (`src/evaluation/`)
11. **Adaptive Research & Optimization Engine** (`src/research/`)
12. **Monitoring & Reporting Engine** (`src/monitoring/`)

---

## Quantitative Quality Standards
- **Zero Lookahead**: Signals decided on closed bar $t$ fill at bar $t+1$ open. Never use current forming bar (bar 0).
- **Realistic Transaction Costs**: Model floating spreads (15–30 points normal, 100+ points news), slippage, and overnight swap financing.
- **Statistical Significance**: Require Deflated Sharpe Ratio (DSR) and Combinatorial Purged Cross-Validation (CPCV) to reject data-mining artifacts.

---

## Persistent Project Memory Protocol (`project_memory/`)
1. **Reading Sequence**: At the start of any task, agents must read:
   - `AGENTS.md` and `GEMINI.md`
   - `project_memory/PROJECT_MASTER.md`
   - `project_memory/CURRENT_STATE.md`
   - `project_memory/SESSION_HANDOFF.md`
2. **Automatic Maintenance**: At task completion, agents must update:
   - `project_memory/CURRENT_STATE.md` (Stage progress and module matrix)
   - `project_memory/NEXT_TASKS.md` (Check off finished tasks)
   - `project_memory/DECISIONS.md` (Append new ADRs; never overwrite past decisions)
   - `project_memory/TEST_HISTORY.md` (Log real test commands; never fabricate results)
   - `project_memory/BUGS_AND_FIXES.md` (Log newly diagnosed/fixed defects)
   - `project_memory/SESSION_HANDOFF.md` (Synthesize compact handoff for next session)

---

## Token Optimization & Context Efficiency Rules
1. **Progressive Disclosure**: Never dump the full text of all skills into context. The prompt exposes skill summaries; agents read full `SKILL.md` files only on demand.
2. **Selective File Reading**: Avoid reading full multi-hundred line files when inspecting specific code; use `StartLine` and `EndLine` in `read_file`.
3. **No Unbounded Repo Scans**: Consult `project_memory/ARCHITECTURE.md` for exact paths instead of repeatedly executing recursive directory scans.
4. **Minimal Subagent Delegation**: Pass typed contracts, schemas, and file paths when delegating tasks; never pipe raw multi-file source code.
5. **Incompressible Guardrails**: Prompt compression must never omit or weaken financial risk limits ($1 risk, $2 daily loss), safety rules (zero live orders, no martingale/grid), or active bugs.
