---
name: broker-constraint-validation-exness
description: >-
  Validates Exness broker specifications and constraints for XAUUSDm (Gold) on MetaTrader 5,
  including lot sizing, tick value, spread filters, leverage rules, and safety latches.
license: Apache-2.0
metadata:
  domain: algorithmic-trading
  subdomain: broker-integration
  tags: exness, xauusd, xauusdm, gold, mt5, symbol-info, lot-sizing
  version: "1.0.0"
---

# Exness XAUUSDm Broker Constraint Validation

This skill enforces strict broker-level parameter validation for Gold trading on Exness MT5 (`XAUUSDm`), preventing invalid trade requests, miscalculated financial risk, and execution rejections.

## Exness XAUUSDm Specifications

| Property | Value | Notes |
| :--- | :--- | :--- |
| **Symbol Suffix** | `XAUUSDm` | Exness standard accounts append `m` (mini/standard). Never hardcode `XAUUSD`. |
| **Contract Size** | `100` | 1 standard lot = 100 troy ounces. 0.01 lot = 1 troy ounce. |
| **Digits** | `2` | Price quoted to 2 decimal places (e.g., $2654.85). |
| **Point Value** | `0.01` | 1 point = $0.01 price move. |
| **Min Volume** | `0.01` lot | Represents 1 troy ounce of gold. |
| **Volume Step** | `0.01` lot | Orders must be integer multiples of 0.01. |
| **P&L per $1.00 Move** | **$1.00 per 0.01 lot** | A $1.00 move in gold price = exactly $1.00 P&L for a 0.01 lot position. |
| **Reference Balance** | `$50.00` | Target risk budget: approximately $1.00 per trade (2% of balance). |
| **Max Stop Loss Distance** | `100 points ($1.00)` | At 0.01 lot, a $1.00 SL equals the maximum $1.00 risk budget. |

## Pre-Trade Validation Rules

1. **Symbol Resolution**:
   - Query `mt5.symbol_info("XAUUSDm")`.
   - If `None`, probe `mt5.symbol_select("XAUUSDm", True)` and verify again.
   - If still `None`, fail immediately with `SymbolNotFoundError`. Never guess fallback symbol settings.

2. **Volume & Lot Quantization**:
   - Verify `volume >= symbol_info.volume_min` (0.01).
   - Verify `volume <= symbol_info.volume_max`.
   - Ensure `round(volume / symbol_info.volume_step, 6).is_integer()`.

3. **Spread Threshold Gate**:
   - Gold spreads on Exness fluctuate dynamically (normally 15–30 points / $0.15–$0.30), but can spike over 100 points during rollover (21:00–23:00 UTC) or high-impact news (NFP, CPI, FOMC).
   - Rule: If `current_spread > max_spread_limit` (e.g. 35 points / $0.35), reject all entry signals.

4. **Stop Loss & Risk Budget Enforcement**:
   - Risk Dollar Amount = `abs(entry_price - stop_loss) * contract_size * volume`.
   - For 0.01 lot on XAUUSDm: Risk = `abs(entry_price - stop_loss) * 1.00`.
   - If required Stop Loss (e.g. 1.5 * ATR) exceeds $1.00 on a $50 account, the trade **MUST BE REJECTED**.
   - Do NOT reduce volume below 0.01 (broker minimum); do NOT widen risk budget above $1.00.

5. **Filling Mode & Execution**:
   - Exness MT5 typically uses `SYMBOL_FILLING_IOC` or `SYMBOL_FILLING_FOK`.
   - Map bitmask to enum: `ORDER_FILLING_IOC` (1) or `ORDER_FILLING_FOK` (0).
   - In research/paper mode, bypass `mt5.order_send` entirely and log virtual execution.
