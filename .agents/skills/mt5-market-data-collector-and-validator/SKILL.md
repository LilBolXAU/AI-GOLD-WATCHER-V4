---
name: mt5-market-data-collector-and-validator
description: >-
  Collects, normalizes, and validates historical and real-time market data from MetaTrader 5,
  handling bar completion, timezone offsets, missing tick gaps, and data integrity checks.
license: Apache-2.0
metadata:
  domain: algorithmic-trading
  subdomain: data-engineering
  tags: mt5, data-collection, ohlcv, data-integrity, timezone-reconciliation
  version: "1.0.0"
---

# MetaTrader 5 Market Data Collector & Validator

This skill establishes a reliable, leakage-safe pipeline for ingesting market data from MetaTrader 5 for **AI GOLD WATCHER V4**.

## Core Data Engineering Rules

### 1. Closed-Bar Discipline (Zero Lookahead)
- The current, forming bar (`bar[0]` in standard MT5 indexing where 0 is newest) is **incomplete**.
- Indicators, signals, and regime classifiers **MUST ONLY** use closed bars (`bar[1]` and older).
- Ingesting bar 0 into strategy logic creates lookahead bias and phantom fills that collapse in live execution.

### 2. Timezone & Server Synchronization
- Exness MT5 server operates on Eastern European Time (EET / EEST):
  - Winter: UTC+2
  - Summer: UTC+3 (Daylight Saving Time)
- All timestamps must be explicitly converted to UTC before persistence or feature engineering.
- Verify timestamp continuity: $\Delta t = \text{Timeframe duration}$. Flag missing bars caused by weekend closures (Friday 22:00 UTC to Sunday 22:00 UTC) versus unexpected server disconnection.

### 3. Data Integrity & Validation Gates
Before passing OHLCV arrays to indicators or models:
- **Price Consistency**: Check $High \ge Low$, $High \ge Open$, $High \ge Close$, $Low \le Open$, $Low \le Close$.
- **Finite Check**: Ensure zero NaN, Inf, or negative price values.
- **Volume Check**: Ensure `tick_volume >= 0`.
- **Bad Tick Filtering**: Detect spikes exceeding 5 * ATR(14) that revert immediately in the subsequent bar (bad ticks from demo feeds).

### 4. Canonical MT5 Python Extraction Pattern

```python
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone

def fetch_closed_rates(symbol: str, timeframe: int, count: int) -> pd.DataFrame:
    """Fetch completed bars excluding the currently open bar."""
    # count + 1 to fetch current forming bar and slice it off
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 1, count)
    if rates is None or len(rates) == 0:
        error_code = mt5.last_error()
        raise RuntimeError(f"Failed to fetch rates for {symbol}: {error_code}")
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    
    # Validation checks
    assert (df['high'] >= df['low']).all(), "Corrupt bar: High < Low"
    assert not df[['open', 'high', 'low', 'close']].isna().any().any(), "NaN values found"
    
    return df
```
