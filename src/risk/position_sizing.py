"""
Position sizing engine for AI GOLD WATCHER V4.
Enforces volatility-based dollar risk budgeting calibrated for Gold (XAUUSDm).
Option 1: 100% Dynamic Lot Sizing based on real-time Equity and ATR stop loss distance.
"""

from typing import Tuple, Optional
from src.data.models import SymbolSpec


def calculate_position_size(
    sl_distance: float,
    balance: float,
    spec: SymbolSpec,
    target_risk_usd: Optional[float] = None,
    max_risk_pct: float = 0.04,
    max_sl_distance: float = 3.50,
    max_lot_cap: float = 0.50,
) -> Tuple[float, float, bool, str]:
    """
    Calculate position size in lots dynamically based on dollar risk budget (Equity * max_risk_pct).

    Args:
        sl_distance: Stop loss distance in price points/USD.
        balance: Current account balance or equity.
        spec: Symbol broker specifications (contract size, min lot, step).
        target_risk_usd: Optional fixed risk cap in USD. If None, scales dynamically with balance * max_risk_pct.
        max_risk_pct: Maximum risk fraction of balance (default 4.0% = 0.04).
        max_sl_distance: Maximum allowable technical SL distance in USD (default $3.50 = 350 pts).
        max_lot_cap: Absolute hard cap on volume for safety (default 0.50 lot).

    Returns:
        (volume, actual_dollar_risk, is_allowed, reason)
    """
    if sl_distance <= 0:
        return 0.0, 0.0, False, "Stop loss distance must be positive."

    if balance <= 0:
        return 0.0, 0.0, False, "Account balance must be positive."

    # Dynamic risk budget: balance * max_risk_pct (e.g. $50 * 0.04 = $2.00, $100 * 0.04 = $4.00)
    # If target_risk_usd is explicitly set, use min(target_risk_usd, balance * max_risk_pct)
    if target_risk_usd is not None and target_risk_usd > 0:
        risk_budget = min(target_risk_usd, balance * max_risk_pct)
    else:
        risk_budget = balance * max_risk_pct

    # If stop loss distance exceeds allowable technical maximum ($2.00 / $3.50), reject.
    # Use rounded 2-decimal distance with 2-cent tolerance ($0.02) to prevent false vetoes
    # caused by broker 3-digit sub-cent rounding (e.g. 2.002 > 2.000).
    rounded_sl_dist = round(sl_distance, 2)
    if rounded_sl_dist > max_sl_distance + 0.02:
        return (
            0.0,
            0.0,
            False,
            f"SL distance ${sl_distance:.2f} exceeds max allowable ${max_sl_distance:.2f}.",
        )

    # Dollar loss per 1.0 standard lot for this SL distance: sl_distance * contract_size (100)
    loss_per_lot = sl_distance * spec.contract_size

    # Raw volume required to risk exactly risk_budget
    raw_volume = risk_budget / loss_per_lot

    # Quantize steps conservatively to broker volume_step (0.01)
    steps = int(raw_volume / spec.volume_step)
    if steps < 1:
        steps = 1
    quantized_vol = round(steps * spec.volume_step, 2)

    # Enforce broker minimum lot (0.01)
    if quantized_vol < spec.volume_min:
        quantized_vol = spec.volume_min

    # Enforce safety max lot cap
    if quantized_vol > max_lot_cap:
        quantized_vol = max_lot_cap

    # Calculate actual dollar risk for the quantized lot size
    actual_risk = round(quantized_vol * loss_per_lot, 2)

    # CRITICAL SAFETY CHECK:
    # If the minimum volume (0.01) still produces risk exceeding the allowable risk budget (+ 15% tolerance),
    # REJECT the trade rather than taking an uncalculated outsize risk.
    if actual_risk > (risk_budget * 1.15) + 1e-4:
        return (
            0.0,
            actual_risk,
            False,
            f"Minimum volume {quantized_vol} lot risks ${actual_risk:.2f}, exceeds dynamic budget ${risk_budget:.2f} (4% of ${balance:.2f}).",
        )

    return quantized_vol, actual_risk, True, "Position size validated."
