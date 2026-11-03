# TRADING STRATEGY DOCUMENTATION — AI GOLD WATCHER V4

## 1. Overview
AI GOLD WATCHER V4 deploys four independent, decoupled trading strategy engines. Each engine is specialized for specific market regimes, and is only permitted to generate active trade candidates when the `MarketRegimeDetector` confirms that regime.

---

## 2. Strategy Engine Specifications

### Strategy 1: Trend Following Engine (`TREND_FOLLOWING`)
- **Target Regime**: `BULL_TRENDING` and `BEAR_TRENDING`
- **Concept**: Rides confirmed directional trends using multiple moving averages and directional movement.
- **Entry Logic (BUY)**:
  - Fast EMA (9) > Mid EMA (20) > Slow EMA (50).
  - Normalised EMA 20 slope $> +0.10$ ATR.
  - ADX(14) $\ge 25.0$ with $+DI > -DI$.
  - Candle close above EMA 20.
- **Entry Logic (SELL)**:
  - Fast EMA (9) < Mid EMA (20) < Slow EMA (50).
  - Normalised EMA 20 slope $< -0.10$ ATR.
  - ADX(14) $\ge 25.0$ with $-DI > +DI$.
  - Candle close below EMA 20.
- **Stop Loss**: Recent swing point or $1.5 \times ATR(14)$, capped at 100 points ($1.00).
- **Take Profit**: Minimum $1.5 \times$ Stop Loss distance (enforcing minimum 1.5 R:R).

---

### Strategy 2: Pullback Continuation Engine (`PULLBACK_CONTINUATION`)
- **Target Regime**: `BULL_TRENDING` and `BEAR_TRENDING`
- **Concept**: Enters established trends on shallow pullbacks into the dynamic value zone between EMA 20 and EMA 50.
- **Entry Logic (BUY)**:
  - Macro trend bullish (EMA 50 > EMA 200).
  - Price pulls back such that candle Low dips into or near EMA 20.
  - Closed candle prints a bullish rejection (Close > Open and Close > EMA 20).
  - RSI(14) is between 40 and 55 (reset from overbought).
- **Entry Logic (SELL)**:
  - Macro trend bearish (EMA 50 < EMA 200).
  - Price rallies into or near EMA 20.
  - Closed candle prints a bearish rejection (Close < Open and Close < EMA 20).
  - RSI(14) is between 45 and 60 (reset from oversold).
- **Stop Loss**: Low/High of the pullback candle, capped at 100 points ($1.00).
- **Take Profit**: Retest of previous swing high/low, minimum 1.5 R:R.

---

### Strategy 3: Volatility Breakout Engine (`VOLATILITY_BREAKOUT`)
- **Target Regime**: `HIGH_VOLATILITY` and emerging trend transitions
- **Concept**: Exploits sharp volatility expansion beyond multi-candle consolidation ranges.
- **Entry Logic (BUY)**:
  - Closed bar crosses and closes strictly above 20-period Donchian High.
  - Normalized Rate of Change ($ROC / ATR$) $> 1.0$.
  - Volume $> 1.2 \times$ 20-period average volume.
- **Entry Logic (SELL)**:
  - Closed bar crosses and closes strictly below 20-period Donchian Low.
  - Normalized Rate of Change ($ROC / ATR$) $< -1.0$.
  - Volume $> 1.2 \times$ 20-period average volume.
- **Stop Loss**: Opposite side of breakout candle or $1.0 \times ATR(14)$, capped at 100 points.
- **Take Profit**: $2.0 \times$ Stop Loss distance (2.0 R:R).

---

### Strategy 4: Range Reversal Engine (`RANGE_REVERSAL`)
- **Target Regime**: `MEAN_REVERTING_RANGING`
- **Concept**: Fades structural price extremes within defined trading ranges.
- **Entry Logic (BUY)**:
  - Candle Low touches or penetrates Lower Bollinger Band (20, 2.0).
  - Candle Close re-enters inside the band.
  - RSI(14) is oversold ($< 30.0$) and curling upward.
  - ADX(14) $< 20.0$ (verifying absence of directional trend).
- **Entry Logic (SELL)**:
  - Candle High touches or penetrates Upper Bollinger Band (20, 2.0).
  - Candle Close re-enters inside the band.
  - RSI(14) is overbought ($> 70.0$) and curling downward.
  - ADX(14) $< 20.0$.
- **Stop Loss**: Extreme candle wick + 10 points buffer, capped at 100 points.
- **Take Profit**: Opposite Bollinger Band or Middle Band (SMA 20), minimum 1.5 R:R.

---

## 3. Conflict Resolution & Mutual Exclusivity
If multiple strategies emit valid candidates on the same bar, `AdaptiveStrategySelector` resolves conflicts:
1. Gating: Filters candidates whose strategy is not eligible under the active regime.
2. Direct Conflict Elimination: If both BUY and SELL candidates exist, all candidates on that bar are voided (NO_TRADE).
3. Ranking: Eligible non-conflicting candidates are ranked by raw confidence; the highest-ranked candidate is forwarded to the `ConfidenceEngine`.
