---
name: python-trading-system-architecture
description: >-
  Defines the 12-module decoupled software architecture for AI GOLD WATCHER V4,
  enforcing unidirectional data flow, domain-driven boundaries, and strict type safety.
license: Apache-2.0
metadata:
  domain: algorithmic-trading
  subdomain: software-architecture
  tags: architecture, python, modular-design, trading-bot, 12-modules
  version: "1.0.0"
---

# AI GOLD WATCHER V4 System Architecture

This skill defines the decoupled 12-module software architecture for AI GOLD WATCHER V4, ensuring clear separation of concerns, testability, and zero cross-module coupling.

## System Topology & Data Flow

```
[MT5 Terminal / Feed]
        │
        ▼
[1. MT5 Data Engine] ──────────► [8. Paper Trading Engine]
        │                                  ▲
        ▼                                  │
[2. Shared Indicator Engine]                │ (Virtual Orders)
        │                                  │
        ├──────────────────────┐           │
        ▼                      ▼           │
[3. Regime Detector]  [4. Four Strategies] │
        │              (Trend, Pullback,   │
        │               Breakout, Range)   │
        │                      │           │
        ▼                      ▼           │
[5. Adaptive Selector] ◄───────┘           │
        │                                  │
        ▼                                  │
[6. Confidence Scoring]                    │
        │                                  │
        ▼                                  │
[7. Financial & Risk Engine] ──────────────┘
        │
        ├──────────────────────┐
        ▼                      ▼
[9. Backtesting Engine]  [12. Monitoring & Reporting]
        │
        ▼
[10. Performance Evaluation]
        │
        ▼
[11. Adaptive Research & Optimization]
```

## The 12 Architectural Modules

### 1. MT5 Data Engine (`src/data/`)
- Ingests ticks and bars from MetaTrader 5 via official API or Mock adapter.
- Normalizes server timestamps to UTC; validates bar continuity and tick ranges.
- Dispatches immutable bar objects downstream. Discards forming bar (bar 0) for signals.

### 2. Shared Indicator Engine (`src/indicators/`)
- Computes foundational technical indicators once across timeframes (EMA 20/50/200, ATR 14, RSI 14, ADX/DMI 14, Donchian Channels).
- Prevents redundant multi-strategy computation and guarantees indicator consistency.

### 3. Market Regime Detector (`src/regime/`)
- Classifies current market state into 4 distinct regimes:
  - `BULL_TRENDING`
  - `BEAR_TRENDING`
  - `MEAN_REVERTING_RANGING`
  - `HIGH_VOLATILITY_UNSTABLE`
- Employs Wilder ADX/DMI + ATR volatility z-score with a 3-bar hysteresis filter to prevent whipsaws.

### 4. Four Independent Strategy Engines (`src/strategies/`)
- **Trend Following Strategy**: Trades in direction of higher timeframe trend upon structural break.
- **Pullback Continuation Strategy**: Enters on retracements to key EMAs/pivots within confirmed trends.
- **Breakout Strategy**: Captures expansion out of consolidation ranges during low-to-high volatility transitions.
- **Range Reversal Strategy**: Fades range boundaries (Bollinger Bands + RSI extremes) strictly in ranging regimes.
- *Strict Rule*: Strategies remain completely independent and generate raw `SignalCandidate` objects without knowledge of other strategies.

### 5. Adaptive Strategy Selector (`src/selector/`)
- Routes and activates strategy candidates strictly based on the confirmed regime.
- In `HIGH_VOLATILITY_UNSTABLE` regime, suppresses all trend and mean-reversion entries (risk-off state).

### 6. Confidence Scoring Engine (`src/scoring/`)
- Evaluates signal quality based on multi-timeframe alignment, volatility clearance, and volume confirmation.
- Produces a normalized confidence score $[0.0, 1.0]$. Rejects signals below minimum confidence threshold (e.g., 0.65).

### 7. Financial & Risk Engine (`src/risk/`)
- Computes exact position sizing based on ATR stop-loss distance and dollar risk budget ($1.00 on $50 reference balance).
- Enforces pre-trade risk controls: max daily drawdown ($2.00 / 4%), max concurrent exposure (0.01 lot), minimum Risk-to-Reward ratio (1:1.5).
- Rejects signals failing risk criteria without exception.

### 8. Paper Trading Engine (`src/execution/`)
- Executes orders in simulated/virtual memory without submitting live MT5 `order_send` calls during development.
- Tracks virtual slippage, spreads, fills, open positions, and virtual P&L.

### 9. Backtesting Engine (`src/backtest/`)
- Event-driven sequential simulator with strict next-bar fill logic (decide on bar $t$, fill on bar $t+1$).
- Incorporates realistic Exness XAUUSDm spread models and transaction costs.

### 10. Performance Evaluation Engine (`src/evaluation/`)
- Calculates risk-adjusted metrics: Sharpe Ratio, Sortino Ratio, Calmar Ratio, Maximum Drawdown, Profit Factor, Win Rate, Average R-multiple.
- Computes Deflated Sharpe Ratio (DSR) to penalize data mining bias.

### 11. Adaptive Research & Optimization Engine (`src/research/`)
- Performs Combinatorial Purged Cross-Validation (CPCV) and walk-forward optimization.
- Evaluates parameter sensitivity surfaces to prevent overfitting cliffs.

### 12. Monitoring & Reporting Engine (`src/monitoring/`)
- Emits structured JSON logs and real-time console/Slack/Telegram telemetry.
- Provides real-time heartbeat and alerts on system anomalies.
