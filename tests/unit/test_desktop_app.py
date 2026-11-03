"""
Unit tests for Desktop Application UI components and dynamic licensing.
"""

from unittest.mock import MagicMock, patch
import pytest

from src.config.license import (
    is_admin_account,
    verify_account_authorized,
    get_allowed_accounts,
    add_allowed_account,
    remove_allowed_account,
    sync_remote_license,
)


def test_license_management_flow():
    # Admin check
    assert is_admin_account(434467985) is True
    assert is_admin_account(12345678) is False
    assert is_admin_account(None) is False

    # Test adding an account
    test_acc = 88888888
    add_allowed_account(test_acc)
    assert verify_account_authorized(test_acc) is True
    assert test_acc in get_allowed_accounts()

    # Test removing account
    remove_allowed_account(test_acc)
    assert verify_account_authorized(test_acc) is False
    assert test_acc not in get_allowed_accounts()


def test_desktop_app_import():
    import src.ui.desktop_app as app_mod
    assert hasattr(app_mod, "AIGoldWatcherApp")
    assert hasattr(app_mod, "GuiLogHandler")


def test_sync_remote_license_graceful_fallback():
    # When URL is unreachable, it should gracefully return None without crashing
    with patch("urllib.request.urlopen", side_effect=Exception("Network error")):
        res = sync_remote_license(timeout=0.1)
        assert res is None


def test_run_paper_session_returns_summary():
    from src.main import run_paper_session
    from src.config.settings import SystemSettings
    import logging

    settings = SystemSettings()
    summary = run_paper_session(settings=settings, bar_count=70, use_mock=True, logger=logging.getLogger())
    assert isinstance(summary, dict)
    assert "initial_balance" in summary
    assert "final_balance" in summary
    assert "win_rate" in summary
    assert "total_trades" in summary
