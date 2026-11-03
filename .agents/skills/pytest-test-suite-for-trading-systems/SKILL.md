---
name: pytest-test-suite-for-trading-systems
description: >-
  Pytest conventions and standards for quantitative trading systems, including floating-point
  tolerances, mock fixtures, regression suites, and financial calculation verification.
license: Apache-2.0
metadata:
  domain: algorithmic-trading
  subdomain: software-testing
  tags: pytest, unit-tests, floating-point, fixtures, regression-testing
  version: "1.0.0"
---

# Pytest Standards for Quantitative Trading Systems

This skill defines rigorous software quality assurance standards for testing trading bots, risk engines, and mathematical indicators.

## 1. Floating-Point Comparison Rules

In financial time series, floating-point arithmetic introduces microscopic precision artifacts (e.g. $0.1 + 0.2 = 0.30000000000000004$).
- **Rule**: Never use exact equality `assert a == b` for prices, returns, P&L, or technical indicators.
- **Correct Pattern**:
  ```python
  import pytest
  from math import isclose

  # Comparing prices or indicator values
  assert computed_price == pytest.approx(expected_price, rel=1e-5, abs=1e-4)

  # In pure functions without pytest dependency
  assert isclose(computed_pnl, expected_pnl, abs_tol=0.001)
  ```

## 2. Test Suite Organization

```
tests/
├── unit/
│   ├── test_data_engine.py       # Data validation, bar building
│   ├── test_indicators.py         # Numerical accuracy of EMA, ATR, RSI, ADX
│   ├── test_regime.py             # ADX/ATR regime transitions & hysteresis
│   ├── test_strategies.py         # Signal generation logic per strategy
│   ├── test_risk_engine.py        # Pre-trade risk gates, sizing caps
│   └── test_mt5_bridge.py         # MqlTradeRequest serialization & retcodes
├── integration/
│   ├── test_pipeline_replay.py   # Historical bar replay through full pipeline
│   └── test_paper_trading.py     # Paper engine order lifecycle
└── fixtures/
    ├── sample_xauusd_bars.py     # Deterministic OHLCV fixtures
    └── mock_mt5.py               # Mock MT5 adapter
```

## 3. Mandatory Invariants to Verify

1. **Conservation of Capital**:
   $\text{Cash}_t + \text{Unrealized P&L}_t = \text{Equity}_t$ across all backtest/paper bars.
2. **Non-Negative Risk Bounds**:
   Position size must never be negative or exceed max lot threshold (`0.01` lot for demo baseline).
3. **No Lookahead Leakage**:
   Signal at bar $t$ must be identical whether evaluated on `bars[:t]` or on the complete stream up to $t$.
4. **Order State Determinism**:
   Every generated order must have a unique, non-zero `magic_number` and valid timestamp.
