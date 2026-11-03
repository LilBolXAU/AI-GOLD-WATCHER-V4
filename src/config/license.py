"""
License & Whitelist Authorization for AI GOLD WATCHER V4.
Administered by LilBoiXAU.
"""

import json
from pathlib import Path
import logging

logger = logging.getLogger("v4_trading.license")

LICENSE_FILE = Path("allowed_accounts.json")


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
