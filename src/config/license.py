"""
License & Whitelist Authorization for AI GOLD WATCHER V4.
Administered by LilBoiXAU.
"""

import json
from pathlib import Path
import logging

logger = logging.getLogger("v4_trading.license")

LICENSE_FILE = Path("allowed_accounts.json")


def get_allowed_accounts() -> list[int]:
    """Return list of authorized MT5 account numbers."""
    if not LICENSE_FILE.exists():
        return []
    try:
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [int(acc) for acc in data.get("allowed_mt5_accounts", []) if str(acc).isdigit()]
    except Exception as e:
        logger.warning("Error reading license file: %s", e)
        return []


def add_allowed_account(login: int) -> bool:
    """Add a new MT5 account login to the whitelist."""
    try:
        data = {}
        if LICENSE_FILE.exists():
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        accounts = [int(acc) for acc in data.get("allowed_mt5_accounts", []) if str(acc).isdigit()]
        if int(login) not in accounts:
            accounts.append(int(login))
        data["allowed_mt5_accounts"] = accounts
        data["license_active"] = True
        data["admin"] = data.get("admin", "LilBoiXAU")
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error("Failed to add account: %s", e)
        return False


def remove_allowed_account(login: int) -> bool:
    """Remove an MT5 account login from the whitelist."""
    try:
        if not LICENSE_FILE.exists():
            return False
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        accounts = [int(acc) for acc in data.get("allowed_mt5_accounts", []) if str(acc).isdigit()]
        accounts = [a for a in accounts if a != int(login)]
        data["allowed_mt5_accounts"] = accounts
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error("Failed to remove account: %s", e)
        return False


def verify_account_authorized(login: int) -> bool:
    """Check if the given MT5 account login is in the authorized whitelist."""
    if not LICENSE_FILE.exists():
        return True

    try:
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data.get("license_active", True):
            return True

        allowed = data.get("allowed_mt5_accounts", [])
        allowed_normalized = [int(acc) for acc in allowed if str(acc).isdigit()]
        return int(login) in allowed_normalized
    except Exception as e:
        logger.warning("Error reading license file: %s", e)
        return True
