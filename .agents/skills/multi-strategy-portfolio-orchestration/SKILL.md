---
name: multi-strategy-portfolio-orchestration
description: >-
  Orchestrates multiple independent trading strategy engines (Trend, Pullback, Breakout, Range Reversal)
  under dynamic market regime routing, conflict resolution, and confidence scoring.
license: Apache-2.0
metadata:
  domain: algorithmic-trading
  subdomain: strategy-orchestration
  tags: multi-strategy, portfolio-orchestration, strategy-switching, confidence-scoring
  version: "1.0.0"
---

# Multi-Strategy Portfolio Orchestration

This skill defines the coordination, signal routing, and conflict resolution mechanisms for the 4 independent trading strategies in **AI GOLD WATCHER V4**.

## The 4 Strategy Engines

Each strategy operates as an isolated, stateless evaluation function on closed bars:

1. **Trend Following Engine (`TrendStrategy`)**:
   - Optimal Regime: `BULL_TRENDING` or `BEAR_TRENDING` with strong ADX ($>25$) and directional DI separation.
   - Mechanism: Donchian channel breakout in direction of higher timeframe EMA trend.
   - Exit: Trailing stop at 2.0 * ATR or opposing directional crossover.

2. **Pullback Continuation Engine (`PullbackStrategy`)**:
   - Optimal Regime: Established `BULL_TRENDING` or `BEAR_TRENDING` with mild retracement.
   - Mechanism: Entry when price pulls back to the dynamic EMA 20/50 support/resistance zone while higher timeframe trend remains intact.
   - Exit: Structural swing high/low or fixed 1:2 R:R.

3. **Breakout Engine (`BreakoutStrategy`)**:
   - Optimal Regime: Transition from `MEAN_REVERTING_RANGING` to `TRENDING` with volatility surge ($z$-score $> 1.5$).
   - Mechanism: Price penetrates the $K$-bar consolidation channel on expanding volume and ATR.
   - Exit: Dynamic ATR bracket with fast breakeven trigger.

4. **Range Reversal Engine (`RangeStrategy`)**:
   - Optimal Regime: `MEAN_REVERTING_RANGING` ($ADX < 20$, low volatility).
   - Mechanism: Mean-reversion from Bollinger Band extremes (2.0 std) confirmed by RSI divergence ($<30$ or $>70$).
   - Exit: Return to the mean (20 SMA middle band).

## Regime-to-Strategy Routing Matrix

| Confirmed Regime | Primary Active Strategy | Secondary / Candidate | Suppressed Strategies |
| :--- | :--- | :--- | :--- |
| **`BULL_TRENDING`** | `PullbackStrategy` (Buy) | `TrendStrategy` (Buy) | Range Reversal, All Sells |
| **`BEAR_TRENDING`** | `PullbackStrategy` (Sell)| `TrendStrategy` (Sell)| Range Reversal, All Buys |
| **`MEAN_REVERTING_RANGING`** | `RangeStrategy` (Buy/Sell)| `BreakoutStrategy` (Watch) | Trend Following, Pullback |
| **`HIGH_VOLATILITY_UNSTABLE`**| **NONE (Risk-Off)** | None | **ALL STRATEGIES HALTED** |

## Conflict Resolution & Order Gate Rules

1. **Mutual Exclusivity**:
   At most **ONE** position is held at any time on XAUUSDm to adhere strictly to the $1.00 risk budget on $50 capital.
2. **Opposing Signal Cancellation**:
   If an open position receives an opposing signal from a different strategy, do NOT flip the position automatically. The open position must hit its Stop Loss, Take Profit, or valid strategy exit rule.
3. **Confidence Scoring Gate**:
   Each signal carries a confidence score $C \in [0.0, 1.0]$ computed from indicator concordance, volume confirmation, and spread tightness. Signals with $C < 0.65$ are dropped.
