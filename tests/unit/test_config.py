"""
Unit tests for configuration and safety validation.
"""

import pytest
from src.config.settings import SystemSettings, RiskSettings, BrokerSettings
from src.config.validation import validate_settings, ConfigurationError


def test_default_settings_valid(default_settings: SystemSettings):
    assert validate_settings(default_settings) is True
    assert default_settings.risk.dry_run_enabled is True
    assert default_settings.risk.reference_balance_usd == 50.0
    assert default_settings.risk.target_risk_usd == 2.00
    assert default_settings.broker.symbol == "XAUUSDm"


def test_safety_latch_dry_run_rejection():
    cfg = SystemSettings()
    cfg.risk.dry_run_enabled = False  # Violation!
    with pytest.raises(ConfigurationError, match="Safety Lock: dry_run_enabled must remain True"):
        validate_settings(cfg)


def test_risk_budget_cap_violation():
    cfg = SystemSettings()
    cfg.risk.target_risk_usd = 5.00  # Exceeds $2.00 cap!
    with pytest.raises(ConfigurationError, match="exceeds strict \\$2.00 development cap"):
        validate_settings(cfg)


def test_max_concurrent_positions_violation():
    cfg = SystemSettings()
    cfg.risk.max_concurrent_positions = 2  # Mutual exclusivity violated!
    with pytest.raises(ConfigurationError, match="Mutual exclusivity required"):
        validate_settings(cfg)


def test_broker_symbol_violation():
    cfg = SystemSettings()
    cfg.broker.symbol = "EURUSD"  # Must be XAUUSDm
    with pytest.raises(ConfigurationError, match="does not match target 'XAUUSDm'"):
        validate_settings(cfg)
