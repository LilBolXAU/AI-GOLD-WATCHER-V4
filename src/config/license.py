"""
License & Whitelist Authorization for AI GOLD WATCHER V4.
Administered by LilBoiXAU.
"""

import json
import logging
from pathlib import Path
from typing import Optional
import urllib.request

logger = logging.getLogger("v4_trading.license")

LICENSE_FILE = Path("allowed_accounts.json")
ADMIN_ACCOUNTS = [434467985]
GITHUB_RAW_LICENSE_URL = (
    "https://raw.githubusercontent.com/LilBolXAU/AI-GOLD-WATCHER-V4/main/allowed_accounts.json"
)


def is_admin_account(login: int | str | None) -> bool:
    """Return True if login belongs to the Master Admin (LilBoiXAU)."""
    if not login:
        return False
    try:
        return int(login) in ADMIN_ACCOUNTS
    except (ValueError, TypeError):
        return False


def get_allowed_accounts() -> list[int]:
    """Return list of authorized MT5 account numbers from local file."""
    if not LICENSE_FILE.exists():
        return []
    try:
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [int(acc) for acc in data.get("allowed_mt5_accounts", []) if str(acc).isdigit()]
    except Exception as e:
        logger.warning("Error reading license file: %s", e)
        return []


def sync_remote_license(timeout: float = 2.5) -> Optional[list[int]]:
    """
    Attempt to fetch the latest authorized accounts from the master GitHub repository.
    Saves to local allowed_accounts.json if successful.
    """
    try:
        req = urllib.request.Request(
            GITHUB_RAW_LICENSE_URL,
            headers={"User-Agent": "AIGoldWatcherV4-LicenseClient"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                raw_bytes = resp.read()
                data = json.loads(raw_bytes.decode("utf-8"))
                accounts = [int(acc) for acc in data.get("allowed_mt5_accounts", []) if str(acc).isdigit()]
                with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                logger.info("Successfully synchronized license whitelist from GitHub.")
                return accounts
    except Exception as e:
        logger.debug("Remote license sync skipped/unavailable: %s", e)
    return None


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


def get_registered_chat_ids() -> list[str]:
    """Return all registered Telegram chat IDs for system broadcasts."""
    if not LICENSE_FILE.exists():
        return []
    try:
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [str(cid).strip() for cid in data.get("telegram_chat_ids", []) if str(cid).strip()]
    except Exception:
        return []


def register_telegram_chat_id(chat_id: str) -> bool:
    """Register a new Telegram Chat ID into whitelist file for broadcasts."""
    clean_id = str(chat_id).strip()
    if not clean_id:
        return False
    try:
        data = {}
        if LICENSE_FILE.exists():
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        cids = [str(cid).strip() for cid in data.get("telegram_chat_ids", []) if str(cid).strip()]
        if clean_id not in cids:
            cids.append(clean_id)
        data["telegram_chat_ids"] = cids
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error("Failed to register Telegram chat ID: %s", e)
        return False


def verify_account_authorized(login: int, check_remote: bool = False) -> bool:
    """Check if the given MT5 account login is in the authorized whitelist."""
    if not login:
        return False

    # Master Admin is always authorized
    if is_admin_account(login):
        return True

    # Optionally attempt remote verification from master GitHub repo
    if check_remote:
        remote_accounts = sync_remote_license()
        if remote_accounts is not None:
            return int(login) in remote_accounts

    if not LICENSE_FILE.exists():
        return False

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
        return False
