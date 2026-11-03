"""
Configuration validation routines for AI GOLD WATCHER V4.
Enforces that settings cannot violate safety boundaries.
"""

from src.config.settings import SystemSettings


class ConfigurationError(Exception):
    """Raised when configuration parameters violate risk or platform rules."""
    pass


def validate_settings(cfg: SystemSettings) -> bool:
    """
    Validate that configuration settings strictly obey financial safety constraints.
    Returns True if valid; raises ConfigurationError on failure.
    """
    # 1. Enforce dry run / no live trading
    if not cfg.risk.dry_run_enabled:
        raise ConfigurationError("Safety Lock: dry_run_enabled must remain True during development.")

    # 2. Enforce risk boundaries
    if cfg.risk.target_risk_usd > 2.00:
        raise ConfigurationError(
            f"Target risk ${cfg.risk.target_risk_usd:.2f} exceeds strict $2.00 development cap."
        )

    if cfg.risk.max_concurrent_positions > 1:
        raise ConfigurationError(
            f"Max concurrent positions ({cfg.risk.max_concurrent_positions}) exceeds 1. Mutual exclusivity required."
        )

    # 3. Enforce symbol constraints
    if cfg.broker.volume_min < 0.01:
        raise ConfigurationError("Volume min cannot be below 0.01 lot for standard MT5 Gold.")

    if cfg.broker.symbol != "XAUUSDm":
        raise ConfigurationError(
            f"Configured symbol '{cfg.broker.symbol}' does not match target 'XAUUSDm'."
        )

    # 4. Storage paths
    cfg.storage.logs_dir.mkdir(parents=True, exist_ok=True)
    cfg.storage.reports_dir.mkdir(parents=True, exist_ok=True)
    cfg.storage.db_path.parent.mkdir(parents=True, exist_ok=True)

    return True
