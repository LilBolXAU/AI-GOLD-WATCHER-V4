# EVENT-DRIVEN BACKTESTING & VALIDATION GUIDE — AI GOLD WATCHER V4

## 1. Zero-Lookahead Philosophy
Unlike vectorized backtests that look at current or future bar closes, AI GOLD WATCHER V4 enforces a strict event-driven playback harness:
1. Signal decisions at bar $t$ are made solely using closed candles $\{1, \dots, t\}$.
2. Execution occurs at open price of bar $t+1$ plus half-spread and slippage.
3. Intrabar high and low prices of bar $t+1$ are evaluated for Stop Loss and Take Profit breaches.

---

## 2. Realistic Transaction Cost Modeling

### Floating Spread Simulation
The `SpreadModel` simulates Exness Gold floating spreads:
- Normal market regime: 15 to 25 points (\$0.15 to \$0.25).
- High volatility / news regime: 35 to 80+ points.

### Slippage Simulation
The `SlippageModel` models execution delays:
- Fixed slippage: 1 point ($0.01).
- Stochastic slippage: Gamma or Gaussian distributed based on volatility.

### Conservative Intrabar Tie-Breaking
When a single bar's price range spans both the Stop Loss and the Take Profit levels (e.g. during an extreme spike), the `FillSimulator` conservatively assumes the Stop Loss was hit first, preventing optimistic backtest artifacts.

---

## 3. Walk-Forward Cross-Validation
To prevent data-mining and overfitting, the `WalkForwardOptimizer`:
1. Partitions historical time-series into chronologically sequential folds.
2. In-sample (train) and out-of-sample (test) windows are disjoint.
3. An embargo buffer (5 bars default) is placed between train and test windows to prevent serial correlation leakage.

---

## 4. Deflated Sharpe Ratio (DSR)
Following Bailey and Lopez de Prado (2014), the evaluation engine computes the Deflated Sharpe Ratio to adjust for:
- Multiple testing bias (searching across parameter grids).
- Non-normality (skewness and kurtosis of gold returns).
- Finite sample size length.

A strategy requires a DSR p-value $\ge 0.95$ (statistically significant at the 5% level) before consideration for forward paper trading.

---

## 5. Running Backtests
Execute from terminal:
```powershell
python src/main.py --mode backtest --bars 500 --output reports/backtest_tearsheet.md
```
Output tearsheets are generated in markdown format in `reports/`.
