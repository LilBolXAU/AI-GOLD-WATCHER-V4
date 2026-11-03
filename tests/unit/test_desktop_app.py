"""
Unit tests for Desktop Application UI components.
"""

from unittest.mock import MagicMock
import pytest

from src.config.license import (
    verify_account_authorized,
    get_allowed_accounts,
    add_allowed_account,
    remove_allowed_account,
)


def test_license_management_flow():
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
