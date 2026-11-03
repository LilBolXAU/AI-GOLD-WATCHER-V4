# AI GOLD WATCHER V4 — AGENT SKILL ARCHITECTURE & DEVELOPMENT ENVIRONMENT REPORT

**Document ID**: `AGW-V4-ARCH-001`  
**Project Name**: AI GOLD WATCHER V4  
**Instrument**: Gold (`XAUUSDm`)  
**Broker**: Exness  
**Platform**: MetaTrader 5 (Windows 11 x86-64, Python 3.13.7)  
**Execution Environment**: Google Antigravity  
**Initial State**: Demo / Paper Trading Only (Zero live order execution)  
**Reference Balance**: $50.00 USD  
**Reference Lot Size**: 0.01 lot (1 troy ounce; contract size 100)  
**Target Risk Budget**: ~$1.00 per trade (2.0% of reference balance)  

---

## 1. Executive Summary

This architecture document formally establishes the quantitative development workspace for **AI GOLD WATCHER V4** inside Google Antigravity. Rather than prematurely coding ad-hoc trading logic, the development environment has been systematically fortified with:

1. **36 Rigorously Audited Agent Skills** organized across 8 core quantitative domains.
2. **7 Specialized Autonomous Agent Roles** defined with unambiguous mandates, veto powers, and strict constraints.
3. **Workspace Rules & Safety Guardrails** (`AGENTS.md` and `GEMINI.md`) permanently prohibiting martingale, grid trading, uncontrolled averaging down, and unbacked leverage.
4. **Decoupled 12-Module System Topology** separating data ingestion, regime detection, strategy generation, confidence scoring, pre-trade risk gating, paper execution, backtesting, and performance monitoring.

---

## 2. Skill Discovery & Audit Summary

During Phase 1 and Phase 2, a comprehensive audit was executed across the premier quantitative and algorithmic trading agent repositories:

- **Total Discovered Skills**: 562 skills
  - `ml4t-skills` (Maintainer: Stefan Jansen / Applied AI, 3rd Edition ML4T): 61 skills
  - `algo-trading-skills` (Maintainer: HimanshuJ16 & Community Contributors): 501 skills
- **Total Audited & Installed Skills**: 36 curated, verified skills
- **Rejected Skills**: 526 skills (rejected due to redundancy, irrelevant asset classes, or violation of trading safety guardrails).

---

## 3. Detailed Installed Skill Stack (By Functional Area)

### Area 1: Quantitative Trading Research
| Skill Name | Source | Description | Why Selected |
| :--- | :--- | :--- | :--- |
| `ml4t-stationarity-tests` | Stefan Jansen / ML4T | ADF, KPSS, and variance ratio tests for financial time series stationarity. | Ensures indicators and price transformations are statistically stationary before model fitting. |
| `ml4t-feature-families` | Stefan Jansen / ML4T | Systematic computation of momentum, volatility, and volume indicators without leakage. | Standardizes technical feature calculation across timeframes. |
| `ml4t-triple-barrier` | Stefan Jansen / ML4T | Marcos Lopez de Prado's triple-barrier labeling (upper profit, lower stop, vertical time). | Replaces arbitrary fixed bars with dynamic, volatility-adjusted exit labeling for Gold. |
| `ml4t-meta-labels` | Stefan Jansen / ML4T | Secondary binary classification on trade viability to scale confidence and filter false positives. | Core engine for the Confidence Scoring module. |
| `adverse-selection-measurement-for-passive-orders` | Algo-Trading-Skills | Measures order book toxicity, spread capture, and adverse selection. | Critical for understanding Gold tick dynamics and spread widening during market opens. |

### Area 2: Algorithmic Trading Systems & Strategies
| Skill Name | Source | Description | Why Selected |
| :--- | :--- | :--- | :--- |
| `regime-detection-for-strategy-switching` | Algo-Trading-Skills | ADX/DMI + ATR volatility $z$-score with hysteresis transition filter. | Directly powers the Adaptive Strategy Selector for switching among the 4 strategies. |
| `multi-strategy-portfolio-orchestration` | Custom / Project | Orchestrates 4 independent strategy engines (Trend, Pullback, Breakout, Range) with conflict resolution. | Coordinates multiple strategies without state pollution or opposing order conflicts. |

### Area 3: Python Engineering & Modular Architecture
| Skill Name | Source | Description | Why Selected |
| :--- | :--- | :--- | :--- |
| `python-trading-system-architecture` | Custom / Project | Defines the 12-module decoupled architecture, unidirectional data flow, and type contracts. | Prevents monolithic code spaghettification and enforces strict module boundaries. |

### Area 4: MetaTrader 5 Integration & Broker Constraints
| Skill Name | Source | Description | Why Selected |
| :--- | :--- | :--- | :--- |
| `broker-constraint-validation-exness` | Custom / Project | Validates Exness specifications for `XAUUSDm` (100 oz contract, 0.01 lot step, 2 decimals, spread spikes). | Guarantees exact mathematical alignment with Exness execution mechanics. |
| `mt5-python-bridge-for-forex-bots` | Algo-Trading-Skills | Handles MT5 `MqlTradeRequest` construction, filling mode bitmask mapping, and `TRADE_RETCODE` triage. | Prevents critical MT5 bridge bugs (e.g. FOK bitmask vs enum numbering, ambiguous retcodes). |
| `forex-broker-integration-oanda-mt5` | Algo-Trading-Skills | MT5 terminal connection lifecycle, silent disconnect detection, 24/5 hours, and triple swap accounting. | Ensures terminal disconnection is immediately caught without silent failures. |
| `mt5-market-data-collector-and-validator` | Custom / Project | Closed-bar rate collection, UTC timezone reconciliation (EET/EEST offset), and tick validation. | Guarantees zero lookahead in bar ingestion and eliminates corrupt/negative price bars. |

### Area 5: Backtesting, Cross-Validation & Strategy Validation
| Skill Name | Source | Description | Why Selected |
| :--- | :--- | :--- | :--- |
| `ml4t-run-backtest` | Stefan Jansen / ML4T | Event-driven bar-by-bar backtesting with strict next-bar fill (decide bar $t$, fill bar $t+1$). | Eliminates lookahead bias that artificially inflates vectorized backtest results. |
| `vectorized-vs-event-driven-backtest-tradeoffs` | Algo-Trading-Skills | Architectural trade-off analysis between vectorized screening and event-driven verification. | Guides when fast screening is safe versus when full event-driven simulation is mandatory. |
| `ml4t-cost-model` | Stefan Jansen / ML4T | Commission, floating spread, and market impact cost modeling. | Accurately models Exness Gold transaction costs and spread expansion. |
| `ml4t-sensitivity-analysis` | Stefan Jansen / ML4T | Tests strategy robustness to parameter variation; maps stability surfaces. | Prevents deploying strategies perched on fragile knife-edge parameter peaks. |
| `ml4t-walk-forward-cv` | Stefan Jansen / ML4T | Rolling and expanding window cross-validation preserving temporal sequencing. | Validates that strategies maintain edge out-of-sample across changing years. |
| `walk-forward-validation-setup` | Algo-Trading-Skills | Out-of-sample window management, train/test buffer sizing, and re-optimization schedules. | Operational runbook for walk-forward execution. |
| `ml4t-cpcv` | Stefan Jansen / ML4T | Combinatorial Purged Cross-Validation generating out-of-sample path distributions. | Provides robust statistical distributions of Sharpe ratios across market histories. |
| `ml4t-purging-embargo` | Stefan Jansen / ML4T | Purges overlapping training samples and embargos post-test data to remove serial correlation. | Essential for financial machine learning with multi-bar holding periods. |
| `ml4t-backtest-overfitting` | Stefan Jansen / ML4T | Multiple testing corrections to quantify Probability of Backtest Overfitting (PBO). | Detects false discoveries resulting from testing multiple strategy variants. |
| `ml4t-deflated-sharpe` | Stefan Jansen / ML4T | Computes Deflated Sharpe Ratio (DSR) adjusting for non-normality and trial count. | Rigorously discounts Sharpe ratios when multiple rules or parameters are evaluated. |

### Area 6: Risk Management & Capital Preservation
| Skill Name | Source | Description | Why Selected |
| :--- | :--- | :--- | :--- |
| `dynamic-position-sizing-based-on-realized-volatility` | Algo-Trading-Skills | ATR-based volatility sizing with hard currency risk bounds ($1.00 on $50 capital). | Protects micro accounts from volatility explosions; enforces 0.01 lot constraints. |
| `kill-switch-and-drawdown-circuit-breakers` | Algo-Trading-Skills | Unconditional multi-tier kill switch and daily drawdown circuit breakers. | Halts trading if daily loss hits $2.00 or if 3 consecutive losses occur. |
| `ml4t-position-sizing` | Stefan Jansen / ML4T | Volatility parity, Kelly criterion fractions, and risk-budget position allocation. | Mathematical framework for sizing signals according to confidence and volatility. |
| `ml4t-risk-metrics` | Stefan Jansen / ML4T | Computes VaR, Expected Shortfall, Maximum Drawdown, Calmar, and Sortino ratios. | Provides continuous risk telemetry during backtesting and paper trading. |
| `ml4t-kill-switch` | Stefan Jansen / ML4T | Automated portfolio risk limits and emergency liquidation logic. | Secondary portfolio-level circuit breaker. |

### Area 7: AI and Machine Learning for Trading
| Skill Name | Source | Description | Why Selected |
| :--- | :--- | :--- | :--- |
| `ml4t-regime-awareness` | Stefan Jansen / ML4T | Uses market regimes as risk conditioning factors and strategy selectors. | Enforces regime conditioning over raw prediction. |
| `ml4t-regime-features` | Stefan Jansen / ML4T | Generates Markov regime switching and clustering features. | Feature pipeline for unsupervised regime identification. |
| `ml4t-data-leakage` | Stefan Jansen / ML4T | Audit rules to detect and prevent temporal and target leakage in ML pipelines. | Ensures feature transformers fit strictly on training splits. |
| `ml4t-drift-detection` | Stefan Jansen / ML4T | Detects covariate shift and concept drift using PSI and Kolmogorov-Smirnov tests. | Alerts when Gold market dynamics deviate from training distributions. |
| `ml4t-shap-analysis` | Stefan Jansen / ML4T | TreeSHAP feature attribution to explain model predictions. | Verifies model decisions align with economic fundamentals; rejects spurious features. |

### Area 8: Testing, Software Quality & Verification
| Skill Name | Source | Description | Why Selected |
| :--- | :--- | :--- | :--- |
| `pytest-test-suite-for-trading-systems` | Custom / Project | Pytest conventions, floating-point tolerances (`pytest.approx`), and invariants. | Ensures numerical precision and deterministic test suite execution. |
| `risk-control-unit-testing-framework` | Algo-Trading-Skills | Boundary, threshold, and breach testing of pre-trade risk controls (MiFID II / SEC 15c3-5). | Formally verifies that the Risk Engine rejects every prohibited order. |
| `mocking-mt5-and-broker-apis` | Custom / Project | Comprehensive mock adapter for the `MetaTrader5` API. | Enables 100% automated CI testing without live terminal or Windows dependency. |
| `market-data-replay-harness-for-integration-testing` | Algo-Trading-Skills | Deterministic bar/tick replay harness for full-pipeline integration tests. | Validates complete system behavior under simulated historical market conditions. |

---

## 4. Quality Control Audit & Rejected Skills

During Phase 2, 526 candidate skills were audited and deliberately rejected based on strict quality control and safety criteria:

1. **Dangerous & Prohibited Strategies**:
   - `grid-trading-rebalancing-engine`: **REJECTED**. Violates Phase 5 safety rules. Grid trading on Gold (a trending, highly volatile metal) carries near-certain probability of account ruin for a $50 account.
   - `martingale-recovery-ladder`: **REJECTED**. Violates Phase 5 safety rules. Martingale doubles down on losses, which exhausts a $50 balance in 3–4 losing trades.
   - `dca-averaging-down-logic`: **REJECTED**. Adding to losing trades is explicitly prohibited.

2. **Irrelevant Asset Classes & Venues**:
   - Crypto DEX/CEX skills (`binance-futures-websocket-feed`, `uniswap-v3-liquidity-provision`, `solana-dex-arbitrage`): **REJECTED**. Irrelevant to Gold trading on Exness MT5.
   - Equities/Options specific skills (`sec-edgar-filing-scraper`, `american-vs-european-style-option-exercise`, `us-reg-sho-short-sale`): **REJECTED**. Introduces unnecessary complexity and context bloating.
   - Non-relevant regional exchanges (`b3-brazil-exchange-api`, `australian-securities-exchange-asx`): **REJECTED**.

3. **Promissory & Unscientific Claims**:
   - Unvetted prompt packs claiming guaranteed win rates or "infinite alpha": **REJECTED**. Only skills enforcing statistical testing and out-of-sample validation were admitted.

4. **Duplicates & Redundancies**:
   - Redundant tearsheet generators and overlapping walk-forward helpers were pruned to maintain a lean, high-signal skill inventory.

---

## 5. Configured Specialized Agent Architecture

Seven specialized agent roles have been configured in `.agents/agents/` and registered dynamically as subagents in Google Antigravity:

```
                  ┌────────────────────────────────────────┐
                  │          Quant Researcher              │
                  │   (Hypothesis, Math, Microstructure)   │
                  └──────────────────┬─────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  Market Regime   │       │Strategy Developer│       │ AI/ML Researcher │
│     Analyst      │       │ (4 Independent   │       │(Meta-Labeling,   │
│ (Regime States)  │       │    Strategies)   │       │ Drift, SHAP)     │
└────────┬─────────┘       └─────────┬────────┘       └─────────┬────────┘
         │                           │                          │
         └───────────────────────────┼──────────────────────────┘
                                     ▼
                  ┌────────────────────────────────────────┐
                  │       Adaptive Strategy Selector       │
                  │       & Confidence Scoring Module      │
                  └──────────────────┬─────────────────────┘
                                     │ (Signal Candidates)
                                     ▼
                  ┌────────────────────────────────────────┐
                  │              Risk Manager              │
                  │ (VETO POWER, Sizing, Drawdown Circuit) │
                  └──────────────────┬─────────────────────┘
                                     │ (Approved Orders)
                         ┌───────────┴───────────┐
                         ▼                       ▼
              ┌─────────────────────┐ ┌─────────────────────┐
              │Backtesting Engineer │ │Software QA Engineer │
              │(Event-Driven, WFO)  │ │(Pytest, Mocks, CI)  │
              └─────────────────────┘ └─────────────────────┘
```

### Summary of Agent Roles:
1. **Quant Researcher**: Formulates trading hypotheses, tests stationarity (ADF/KPSS), analyzes session liquidity, and designs mathematical feature transforms.
2. **Market Regime Analyst**: Detects `BULL_TRENDING`, `BEAR_TRENDING`, `MEAN_REVERTING_RANGING`, and `HIGH_VOLATILITY_UNSTABLE` regimes using ADX/ATR $z$-scores with hysteresis.
3. **Strategy Developer**: Builds 4 completely independent strategy engines (Trend Following, Pullback Continuation, Breakout, Range Reversal) emitting standardized `SignalCandidate` objects.
4. **Backtesting Engineer**: Builds event-driven simulations, prevents lookahead bias (decide bar $t$, fill bar $t+1$), models realistic spreads and slippage, and executes WFO and CPCV.
5. **Risk Manager**: Holds **absolute veto authority**; enforces $1.00 risk budget on $50 capital (0.01 lot), max 1 concurrent position, $2.00 daily loss breaker, and 3-consecutive-loss pause.
6. **AI/ML Researcher**: Evaluates whether ML adds verified edge; builds regime classifiers and meta-labeling confidence scorers; audits temporal data leakage.
7. **Software QA Engineer**: Maintains pytest suites, validates numerical precision (`pytest.approx`), maintains mock MT5 adapters, and verifies pre-trade risk rule boundary conditions.

---

## 6. The 12-Module System Topology

The planned codebase architecture for `AI GOLD WATCHER V4` is partitioned into 12 decoupled packages under `src/`:

```
src/
├── data/           # Module 1: MT5 Data Engine & UTC normalizer
├── indicators/     # Module 2: Shared Indicator Engine (EMA, ATR, RSI, ADX)
├── regime/         # Module 3: Market Regime Detector (Hysteresis, z-score)
├── strategies/     # Module 4: 4 Independent Strategy Engines
│   ├── trend.py
│   ├── pullback.py
│   ├── breakout.py
│   └── range.py
├── selector/       # Module 5: Adaptive Strategy Selector (Regime router)
├── scoring/        # Module 6: Confidence Scoring Engine (Meta-labeling)
├── risk/           # Module 7: Financial & Pre-Trade Risk Engine
├── execution/      # Module 8: Paper Trading Engine & MT5 Bridge
├── backtest/       # Module 9: Event-Driven Backtesting Engine
├── evaluation/     # Module 10: Performance Evaluation (DSR, PBO, Tearsheet)
├── research/       # Module 11: Adaptive Research & Walk-Forward Optimizer
└── monitoring/     # Module 12: Logging, Heartbeat & Alerting
```

---

## 7. Security, Trading Safety & Capital Protection Rules

1. **Zero Live Orders During Development**: Real `mt5.order_send` calls are completely disabled. All trading is strictly routed through the `PaperTradingEngine` or simulated mock adapters.
2. **Mathematical Micro-Account Sizing**:
   - Instrument: `XAUUSDm` (1 standard lot = 100 troy ounces).
   - Minimum volume: 0.01 lot (1 troy ounce).
   - Point value: $0.01 per point.
   - Price sensitivity: A $1.00 price move in Gold = exactly $1.00 P&L on a 0.01 lot position.
   - For a $50 account with a $1.00 target risk budget (2%), the maximum allowable Stop Loss distance is **$1.00 (100 points)**.
   - If market volatility (e.g., ATR) demands a Stop Loss greater than $1.00, the trade **must be skipped** because MT5 does not support fractional lots below 0.01.
3. **Fail-Closed Architecture**: If any component fails (missing data, NaN indicator, network timeout), the system defaults to "Do Not Trade" and closes pending virtual orders.
4. **Credential Isolation**: Zero hardcoded account numbers or passwords. All configurations load from `.env` or system environment variables.

---

## 8. Missing Capabilities & Environmental Constraints

1. **MT5 Python Wheel Limitation**:
   - The official `MetaTrader5` package only supports Windows x86-64 with an active MT5 terminal installed.
   - *Mitigation*: Our `mocking-mt5-and-broker-apis` skill provides complete headless test mocks so unit and integration tests run independently of the live terminal.
2. **Exness Spread Dynamics During News**:
   - Gold spreads on Exness expand dramatically during high-impact news events (CPI, NFP, FOMC) and daily rollover (21:00–23:00 UTC), often from 18 points up to 120+ points.
   - *Mitigation*: The `broker-constraint-validation-exness` skill enforces a hard spread gate (e.g. reject all entries if spread exceeds 35 points).
3. **Tick History Volume on High-Frequency Feeds**:
   - Storing full tick histories for Gold requires gigabytes of disk storage.
   - *Mitigation*: The Data Engine ingests closed M1/M5/M15 bars for strategy generation, keeping tick feeds strictly for real-time spread tracking.

---

## 9. Potential Compatibility Issues

1. **Python 3.13 Compatibility**:
   - MetaTrader 5 version 5.0.6231 is already verified and installed in Python 3.13.7.
   - Certain older scientific packages may require pre-compiled wheels on Python 3.13. Numpy 2.4.4 and Pandas 3.1.0 are already installed and functional.
2. **Exness EET Timezone vs UTC**:
   - Exness server time is EET (UTC+2 in winter, UTC+3 in summer).
   - Historical bars fetched via `copy_rates_from_pos` carry server timestamps. The `mt5-market-data-collector-and-validator` skill normalizes all timestamps to UTC.

---

## 10. Recommended Next Development Roadmap

The development environment is now fully configured. The recommended execution sequence for developing **AI GOLD WATCHER V4** is:

- **Stage 1 — Data & Indicator Foundations**:
  - Implement `MT5DataEngine` (Module 1) with mock and live feeds.
  - Implement `SharedIndicatorEngine` (Module 2) calculating EMA, ATR, RSI, ADX.
  - Run unit tests with `pytest-test-suite-for-trading-systems`.

- **Stage 2 — Market Regime Detector & Strategy Engines**:
  - Implement `MarketRegimeDetector` (Module 3) with ADX/ATR $z$-score and 3-bar hysteresis.
  - Implement the 4 independent strategy engines (Module 4: Trend, Pullback, Breakout, Range).
  - Implement `AdaptiveStrategySelector` (Module 5) and `ConfidenceScoring` (Module 6).

- **Stage 3 — Financial Risk & Paper Trading Engine**:
  - Implement `FinancialRiskEngine` (Module 7) with $1.00 risk budget, Exness constraint checks, and circuit breakers.
  - Implement `PaperTradingEngine` (Module 8) with virtual order fills and spread simulation.
  - Run MiFID II / SEC 15c3-5 boundary test suite.

- **Stage 4 — Event-Driven Backtesting & Validation**:
  - Build `BacktestingEngine` (Module 9) with next-bar execution.
  - Run Walk-Forward Optimization (Module 11) and Deflated Sharpe Ratio calculation (Module 10).
  - Validate strategies across out-of-sample Gold data (2020–2026).

- **Stage 5 — Demo Integration & Telemetry**:
  - Connect paper trading engine to live Exness MT5 demo feed (read-only data, paper fills).
  - Activate `MonitoringEngine` (Module 12) for real-time alerting.
