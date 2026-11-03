# ARCHITECTURE — AI GOLD WATCHER V4

**Document ID**: `AGW-V4-MEM-ARCH`  
**Classification**: Structural Blueprint & Interface Contract  
**Last Updated**: 2026-11-03  

---

## 1. System Topology & Data Flow

```
[MT5 Terminal / Mock Adapter]
            │
            ▼
   [M01: MT5 Data Engine] ──────────► [M08: Paper Trading Engine]
            │                                     ▲
            ▼                                     │
   [M02: Shared Indicator Engine]                  │ (Virtual Orders)
            │                                     │
       ┌────┴────────────────────────┐            │
       ▼                             ▼            │
[M03: Regime Detector]     [M04: Four Strategies] │
       │                    (Trend, Pullback,     │
       │                     Breakout, Range)     │
       ▼                             ▼            │
[M05: Adaptive Selector] ◄───────────┘            │
       │                                          │
       ▼                                          │
[M06: Confidence Scoring]                         │
       │                                          │
       ▼                                          │
[M07: Financial & Risk Engine] ───────────────────┘
       │
  ┌────┴────────────────────────┐
  ▼                             ▼
[M09: Backtest Engine]    [M12: Monitoring & Alerting]
  │
  ▼
[M10: Performance Evaluation]
  │
  ▼
[M11: Adaptive Research (CPCV/WFO)]
```

---

## 2. Module Responsibilities & Dependencies

| Module | Name | Responsibility | Dependencies | Output Interface |
| :--- | :--- | :--- | :--- | :--- |
| **M01** | MT5 Data Engine | Ingests OHLCV and ticks, normalizes to UTC, validates bar completeness (discards bar 0). | MT5 API / Mock Adapter | `BarData`, `TickData` |
| **M02** | Shared Indicator Engine | Computes EMA (20, 50, 200), ATR (14), RSI (14), ADX/DMI (14) across timeframes. | M01 (`BarData`) | `IndicatorFrame` |
| **M03** | Market Regime Detector | Classifies market into Bull Trend, Bear Trend, Range, or High Volatility with hysteresis. | M02 (`IndicatorFrame`) | `MarketRegimeState` |
| **M04** | Four Strategies | Generates unconstrained entry/exit signal candidates independently. | M02 (`IndicatorFrame`) | `SignalCandidate` |
| **M05** | Adaptive Strategy Selector | Routes signals matching confirmed regime; suppresses invalid strategies. | M03, M04 | `RoutedSignal` |
| **M06** | Confidence Scoring Engine | Scores signal quality using multi-timeframe concordance and meta-labeling. | M05, M02 | `ScoredSignal` |
| **M07** | Financial & Risk Engine | Enforces $1.00 risk budget, sizing (0.01 lot), spread gates, and circuit breakers. | M06, M01 | `ApprovedOrder` (or VETO) |
| **M08** | Paper Trading Engine | Simulates execution in virtual memory with realistic spread and slippage. | M07, M01 | `ExecutionReport` |
| **M09** | Backtesting Engine | Simulates historical event-driven bar-by-bar execution (next-bar fill). | M01, M02, M07, M08 | `BacktestResult` |
| **M10** | Performance Evaluation Engine | Computes Sharpe, Sortino, Calmar, Max Drawdown, and Deflated Sharpe Ratio (DSR). | M09 (`BacktestResult`) | `TearsheetReport` |
| **M11** | Adaptive Research Engine | Runs Walk-Forward Optimization (WFO) and Combinatorial Purged CV (CPCV). | M09, M10 | `OptimizationSurface` |
| **M12** | Monitoring & Alerting Engine | Emits structured JSON logs, system heartbeat, and emergency alert dispatches. | All Modules | Log Stream, Alerts |

---

## 3. Important Data Interfaces & Contracts

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class RegimeType(str, Enum):
    BULL_TRENDING = "BULL_TRENDING"
    BEAR_TRENDING = "BEAR_TRENDING"
    MEAN_REVERTING_RANGING = "MEAN_REVERTING_RANGING"
    HIGH_VOLATILITY_UNSTABLE = "HIGH_VOLATILITY_UNSTABLE"

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass(frozen=True)
class BarData:
    timestamp: datetime  # UTC
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int          # In points

@dataclass(frozen=True)
class SignalCandidate:
    strategy_id: str
    timestamp: datetime
    symbol: str          # "XAUUSDm"
    side: OrderSide
    entry_price: float
    stop_loss: float
    take_profit: float
    raw_confidence: float

@dataclass(frozen=True)
class ApprovedOrder:
    magic_number: int
    symbol: str
    side: OrderSide
    volume: float        # 0.01
    price: float
    stop_loss: float
    take_profit: float
    risk_usd: float      # Max $1.00
    timestamp: datetime
```

---

## 4. Agent Responsibilities & Delegation Topology

- **Quant Researcher**: Proves mathematical viability of feature families and indicators before implementation.
- **Market Regime Analyst**: Calibrates Wilder ADX and ATR $z$-score thresholds.
- **Strategy Developer**: Implements decoupled strategies emitting `SignalCandidate`.
- **Backtesting Engineer**: Ensures next-bar fill discipline ($t \to t+1$) and realistic transaction costs.
- **Risk Manager**: Exercises **absolute veto authority**; rejects trades with SL $> 100$ points or risk $> \$1.00$.
- **AI/ML Researcher**: Audits temporal leakage; calibrates meta-labeling models.
- **Software QA Engineer**: Enforces 100% test pass rate, mock MT5 reliability, and floating-point precision rules.
