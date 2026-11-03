# COMPLETE SYSTEM ARCHITECTURE — AI GOLD WATCHER V4

## 1. Architectural Philosophy
AI GOLD WATCHER V4 is engineered around four core quantitative design principles:
1. **Unidirectional Data Flow**: Data flows strictly downstream: Market -> Indicators -> Regime -> Strategy Candidates -> Selector -> Confidence -> Risk -> Execution -> Evaluation/Storage. No circular dependencies.
2. **Causal Closed-Bar Discipline**: All signals, features, and regimes are evaluated exclusively on closed candle $t$. Execution occurs at open of bar $t+1$. Current forming candle (bar 0) is never read for trading decisions.
3. **Decoupled Strategy & Risk Engines**: Strategy modules emit pure `SignalCandidate` objects with zero order-sending authority. Sizing, circuit breakers, and vetoes are governed entirely by the independent `RiskGuard`.
4. **Deterministic Reproducibility**: High-speed mocks allow identical simulation across unit tests, event-driven backtesting, and paper execution.

---

## 2. 12-Module Directory Structure & Domain Model

```
src/
├── __init__.py
├── main.py                     # CLI orchestrator (Paper, Backtest, Diagnostics)
│
├── config/                     # Module 00: Configuration & Constraints
│   ├── settings.py             # System, Broker, Risk, Timeframe, Storage models
│   └── validation.py           # Guardrail checks (rejection on dry_run=False)
│
├── data/                       # Module 01: MT5 Data Engine
│   ├── models.py               # BarData, TickData, SymbolSpec, Timeframe
│   ├── symbol_specs.py         # Exness XAUUSDm specs & broker validation
│   ├── data_validator.py       # OHLC invariants, spike filters, gap checks
│   ├── mt5_client.py           # MT5ClientBase, MockMT5Client, LiveMT5Client
│   └── data_engine.py          # Multi-timeframe fetcher (M15, M5, M1)
│
├── indicators/                 # Module 02: Shared Indicator Engine
│   ├── trend_indicators.py     # EMAs (9,20,50,200), normalized slope, alignment
│   ├── volatility_indicators.py# Wilder ATR(14), Bollinger Bands, rolling vol
│   ├── momentum_indicators.py  # Wilder RSI(14), ADX/DMI(14), Efficiency Ratio
│   └── indicator_engine.py     # SharedIndicatorEngine, swing point detection
│
├── regime/                     # Module 03: Market Regime Detector
│   ├── regime_features.py      # Regime feature extraction & ATR z-score
│   └── regime_detector.py      # 4 regimes + 3-bar hysteresis + shock override
│
├── strategies/                 # Module 04: Four Independent Strategies
│   ├── base_strategy.py        # BaseStrategy, SignalCandidate, OrderSide
│   ├── trend_following.py      # Trend Following (EMA alignment & slope)
│   ├── pullback.py             # Pullback Continuation (EMA retest)
│   ├── breakout.py             # Volatility Breakout (Donchian + ATR surge)
│   └── range_reversal.py       # Range Reversal (Bollinger + RSI extreme)
│
├── selector/                   # Module 05: Adaptive Strategy Selector
│   ├── strategy_eligibility.py # Regime-to-strategy mapping
│   └── adaptive_selector.py    # Conflict resolution & priority tie-breaker
│
├── scoring/                    # Module 06: Confidence Scoring Engine
│   ├── signal_quality.py       # ScoredSignal model
│   └── confidence_engine.py    # 5-factor scoring (0-100), 65.0 threshold
│
├── risk/                       # Module 07: Financial & Risk Engine (Stage 3)
│   ├── pnl_calculator.py       # Gross PnL & points calculation
│   ├── cost_calculator.py      # Spread cost, slippage cost, net PnL
│   ├── position_sizing.py      # Volatility sizing ($1 risk / $50 capital)
│   ├── drawdown_guard.py       # $2 daily loss breaker, 3 consecutive losses
│   ├── kill_switch.py          # Global trading halt switch
│   └── risk_guard.py           # Absolute pre-trade veto gate
│
├── execution/                  # Module 08: Paper Trading Engine
│   ├── virtual_position.py     # VirtualPosition lifecycle model
│   ├── trade_lifecycle.py      # ClosedTrade record, ExitReason
│   ├── paper_broker.py         # Realistic execution with spread/slippage
│   └── paper_trade_manager.py  # Intrabar SL/TP monitoring & exit triggers
│
├── backtest/                   # Module 09: Backtesting Engine
│   ├── spread_model.py         # Floating spread models
│   ├── slippage_model.py       # Fixed & stochastic slippage models
│   ├── commission_model.py     # Zero commission for standard account
│   ├── fill_simulator.py       # Conservative intrabar tie-breaking simulator
│   ├── event_engine.py         # Bar-by-bar backtest runner
│   ├── walk_forward.py         # Chronological walk-forward CV
│   └── backtest_runner.py      # High-level backtest entrypoint
│
├── evaluation/                 # Module 10: Performance Evaluation Engine
│   ├── performance_metrics.py  # Sharpe, Sortino, Drawdown, Profit Factor
│   ├── trade_analysis.py       # Long/Short & Strategy attribution
│   ├── robustness.py           # Deflated Sharpe Ratio (DSR p-value)
│   └── report_generator.py     # Markdown tearsheet generator
│
├── research/                   # Module 11: Research & Optimization Engine
│   ├── parameter_sensitivity.py# Parameter curve & cliff detection
│   ├── regime_analysis.py      # Trade return attribution by regime
│   ├── strategy_comparison.py  # Side-by-side strategy comparison
│   └── optimization.py         # Grid search with multiple-testing correction
│
├── storage/                    # Storage Layer
│   ├── migrations.py           # SQLite tables schema
│   ├── database.py             # WAL SQLite connection manager
│   └── repositories.py         # Trade, Signal, and Equity repositories
│
└── monitoring/                 # Module 12: Monitoring & Dashboard
    ├── logger.py               # Structured logger with credential redaction
    ├── alerts.py               # Circuit breaker and safety alerts
    ├── health_monitor.py       # Connection and feed continuity monitor
    └── dashboard.py            # Real-time Streamlit dashboard
```

---

## 3. Communication & Data Contracts
- `BarData`: Immutable UTC timestamp, Open, High, Low, Close, Volume, Spread.
- `SignalCandidate`: Emitted by strategy engines; includes strategy ID, timestamp, side, entry price, stop loss, take profit, raw confidence.
- `ScoredSignal`: Structural score [0-100] across regime alignment, trend slope, R:R, spread, and MTF confluence.
- `ApprovedOrder`: Emitted only by `RiskGuard` when all sizing and circuit breaker checks pass.
- `ClosedTrade`: Full record including duration, gross PnL, spread cost, slippage cost, net PnL, points PnL, and exit reason.
