"""
Configuration settings for AI GOLD WATCHER V4.
Strict adherence to financial safety constraints and trading guardrails.
"""

from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class BrokerSettings(BaseModel):
    """Broker & Terminal specifications for Exness MetaTrader 5."""
    symbol: str = Field(default="XAUUSDm", description="Gold symbol on Exness Standard")
    contract_size: float = Field(default=100.0, description="1 lot = 100 troy ounces")
    digits: int = Field(default=2, description="Price digits (e.g. 2650.50)")
    point_value: float = Field(default=0.01, description="1 point = 0.01 price move")
    volume_min: float = Field(default=0.01, description="Minimum allowable volume")
    volume_max: float = Field(default=200.0, description="Maximum broker volume")
    volume_step: float = Field(default=0.01, description="Volume step quantization")
    max_spread_points: int = Field(default=35, description="Maximum allowable spread in points")
    server_timezone_offset_winter: int = Field(default=2, description="Exness EET (UTC+2)")
    server_timezone_offset_summer: int = Field(default=3, description="Exness EEST (UTC+3)")


class RiskSettings(BaseModel):
    """Financial and risk parameters (Stage 3 safety core)."""
    reference_balance_usd: float = Field(default=50.0, description="Demo reference capital")
    reference_volume: float = Field(default=0.01, description="Initial reference lot size")
    target_risk_usd: float = Field(default=2.00, description="Max dollar risk budget per trade (4% of $50)")
    max_risk_pct_balance: float = Field(default=0.04, description="4.0% max risk per trade")
    max_sl_points: int = Field(default=200, description="200 points ($2.00) max SL distance")
    min_risk_reward_ratio: float = Field(default=1.5, description="Minimum acceptable R:R (1:1.5 -> $3.00 TP)")
    max_concurrent_positions: int = Field(default=1, description="Mutual exclusivity: max 1 active position")
    daily_loss_limit_usd: float = Field(default=4.00, description="Daily loss circuit breaker ($4.00 / 8%)")
    max_consecutive_losses: int = Field(default=3, description="Pause strategy after 3 consecutive losses")
    dry_run_enabled: bool = Field(default=True, description="Strict safety latch: ZERO live orders")


class TimeframeSettings(BaseModel):
    """Multi-timeframe analysis parameters."""
    macro_tf: str = Field(default="M15", description="Higher-level market context")
    structure_tf: str = Field(default="M5", description="Strategy confirmation and structure")
    entry_tf: str = Field(default="M1", description="Closed-candle entry timing")
    required_history_bars: int = Field(default=300, description="Warm-up bars for indicator stability")


class StorageSettings(BaseModel):
    """Database and file persistence paths."""
    db_path: Path = Field(default=BASE_DIR / "data" / "v4_trading.db")
    logs_dir: Path = Field(default=BASE_DIR / "logs")
    reports_dir: Path = Field(default=BASE_DIR / "reports")


class SystemSettings(BaseModel):
    """Master application configuration."""
    project_name: str = "AI GOLD WATCHER V4"
    mode: Literal["PAPER_TRADING", "BACKTEST", "DEMO_MONITOR"] = "PAPER_TRADING"
    broker: BrokerSettings = Field(default_factory=BrokerSettings)
    risk: RiskSettings = Field(default_factory=RiskSettings)
    timeframes: TimeframeSettings = Field(default_factory=TimeframeSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)


# Singleton instance
settings = SystemSettings()
