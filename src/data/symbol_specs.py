"""
Broker symbol specifications and validation for Exness Gold (XAUUSDm).
"""

from typing import Any, Optional
from src.data.models import SymbolSpec, DataError


DEFAULT_EXNESS_XAUUSD = SymbolSpec(
    name="XAUUSDm",
    digits=2,
    point=0.01,
    contract_size=100.0,
    tick_size=0.01,
    tick_value=1.00,
    volume_min=0.01,
    volume_max=200.0,
    volume_step=0.01,
    stops_level=0,
    filling_mode=1,
    currency_base="XAU",
    currency_profit="USD",
    currency_margin="USD",
)


def validate_broker_symbol(symbol_info: Any) -> SymbolSpec:
    """
    Validate raw MT5 symbol_info object from broker and return typed SymbolSpec.
    Raises DataError if the symbol fails critical Exness Gold specifications.
    """
    if symbol_info is None:
        raise DataError("Broker symbol_info is None. Symbol may not be selected in Market Watch.")

    name = getattr(symbol_info, "name", "")
    if not (name.startswith("XAUUSD") or name == "GOLD"):
        raise DataError(f"Unexpected symbol name '{name}'. Expected Gold (XAUUSD / XAUUSDm).")

    digits = getattr(symbol_info, "digits", 2)
    point = getattr(symbol_info, "point", 0.01)
    contract_size = getattr(symbol_info, "trade_contract_size", 100.0)
    vol_min = getattr(symbol_info, "volume_min", 0.01)
    vol_max = getattr(symbol_info, "volume_max", 200.0)
    vol_step = getattr(symbol_info, "volume_step", 0.01)
    tick_size = getattr(symbol_info, "trade_tick_size", point)
    tick_value = getattr(symbol_info, "trade_tick_value", 1.0)
    stops_level = getattr(symbol_info, "trade_stops_level", 0)
    filling_mode = getattr(symbol_info, "filling_mode", 1)

    if contract_size <= 0:
        raise DataError(f"Invalid contract size: {contract_size}")
    if vol_min <= 0 or vol_step <= 0:
        raise DataError(f"Invalid volume min/step: min={vol_min}, step={vol_step}")

    return SymbolSpec(
        name=name,
        digits=digits,
        point=point,
        contract_size=contract_size,
        tick_size=tick_size,
        tick_value=tick_value,
        volume_min=vol_min,
        volume_max=vol_max,
        volume_step=vol_step,
        stops_level=stops_level,
        filling_mode=filling_mode,
        currency_base=getattr(symbol_info, "currency_base", "XAU"),
        currency_profit=getattr(symbol_info, "currency_profit", "USD"),
        currency_margin=getattr(symbol_info, "currency_margin", "USD"),
    )
