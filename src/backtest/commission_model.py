"""
Commission models for event-driven backtesting in AI GOLD WATCHER V4.
"""

class ZeroCommissionModel:
    """Exness Standard / Standard Cent accounts have 0 raw commission (all spread)."""
    def calculate_commission(self, volume: float) -> float:
        return 0.0


class PerLotCommissionModel:
    """For Pro/Raw Spread accounts with explicit per-lot commission (e.g. $3.50/lot/side)."""
    def __init__(self, commission_per_lot_round_turn: float = 7.0):
        self.rate = commission_per_lot_round_turn

    def calculate_commission(self, volume: float) -> float:
        return round(self.rate * volume, 2)
