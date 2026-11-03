# FINANCIAL & RISK MANAGEMENT MANUAL — AI GOLD WATCHER V4

## 1. Capital & Instrument Specifications
- **Instrument**: Gold on Exness (`XAUUSDm`)
- **Reference Capital**: $50.00 USD
- **Contract Size**: 100 troy ounces per 1.0 standard lot
- **Minimum Volume**: 0.01 lot (1 troy ounce)
- **Point Value**: 0.01 price move = $0.01 profit/loss per 0.01 lot
- **Target Risk Budget**: ~$1.00 USD per trade (2.0% of reference balance)

---

## 2. Quantitative Stop Loss & Sizing Math

### The 100-Point Sizing Invariant
Because the minimum order volume on Exness MT5 is 0.01 lot (1 oz), a \$1.00 move in gold price ($100 points) generates exactly \$1.00 of P&L:
$$\text{Dollar Loss} = \text{SL Distance (pts)} \times \text{Point} \times \text{Contract Size} \times \text{Volume}$$
$$\text{Dollar Loss} = 100 \times 0.01 \times 100.0 \times 0.01 = \$1.00$$

> [!IMPORTANT]
> If a trade setup requires a Stop Loss distance greater than 100 points (\$1.00), executing even the minimum lot size (0.01) would exceed the \$1.00 risk budget.
> **Therefore, any signal candidate with a Stop Loss distance > 100 points is strictly vetoed by the `RiskGuard`.**

---

## 3. Pre-Trade Risk Guard Veto Rules
The `RiskGuard` holds absolute veto authority over all signals. An order is approved if and only if all 6 pre-trade tests pass:

| Rule ID | Check Description | Threshold / Condition | Action on Breach |
| :---: | :--- | :--- | :--- |
| **RG-01** | Kill Switch Latch | `kill_switch.is_triggered == False` | Instant Veto |
| **RG-02** | Daily Loss Circuit Breaker | Cumulative daily realized loss $< \$2.00$ | Session Halt |
| **RG-03** | Consecutive Loss Breaker | Consecutive losses $< 3$ | Strategy Pause |
| **RG-04** | Mutual Exclusivity | Active positions $== 0$ (max 1 concurrent) | Veto Candidate |
| **RG-05** | Confidence Threshold | Multi-factor score $\ge 65.0 / 100.0$ | Veto Candidate |
| **RG-06** | Spread Filter | Current spread $\le 35$ points (\$0.35) | Veto Candidate |

---

## 4. Daily Loss & Drawdown Circuit Breakers

### Daily Loss Breaker ($2.00 / 4%)
- Evaluated on closed trades each session (resetting at 00:00 UTC).
- If cumulative realized daily PnL breaches $-\$2.00$, trading is halted until the next UTC day.

### Consecutive Loss Breaker (3 Losses)
- If 3 trades close at a loss consecutively, execution is paused for quantitative audit.

### Max Drawdown Guard (10%)
- If account equity drops 10% below peak equity, the engine halts further order approval.
