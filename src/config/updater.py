"""
Update & Admin Broadcast Announcement Engine for AI GOLD WATCHER V4.
Handles automatic update detection and real-time Admin broadcast notices.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import urllib.request

logger = logging.getLogger("v4_trading.updater")

VERSION_FILE = Path("version.json")
ANNOUNCEMENT_FILE = Path("announcements.json")

GITHUB_RAW_VERSION_URL = (
    "https://raw.githubusercontent.com/LilBolXAU/AI-GOLD-WATCHER-V4/main/version.json"
)
GITHUB_RAW_ANNOUNCEMENT_URL = (
    "https://raw.githubusercontent.com/LilBolXAU/AI-GOLD-WATCHER-V4/main/announcements.json"
)

DEFAULT_VERSION = {
    "version": "4.2.0",
    "build": 2026110401,
    "release_time": "2026-11-04 02:15:00",
    "description": "Khoi tao he thong thong bao tu dong va chat Admin cau vong",
}


def get_local_version() -> dict:
    """Read local version details from version.json."""
    if not VERSION_FILE.exists():
        save_local_version(DEFAULT_VERSION)
        return DEFAULT_VERSION.copy()
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Error reading local version file: %s", e)
        return DEFAULT_VERSION.copy()


def save_local_version(data: dict) -> bool:
    """Save version data to version.json."""
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error("Error saving local version file: %s", e)
        return False


def bump_version_on_push(description: str = "") -> dict:
    """Increment build number and update release timestamp for git push."""
    current = get_local_version()
    current["build"] = int(current.get("build", 2026110400)) + 1
    current["release_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if description:
        current["description"] = description
    save_local_version(current)
    return current


def check_remote_update(timeout: float = 2.5) -> Tuple[bool, Optional[dict]]:
    """
    Check GitHub repository for a newer version build.
    Returns (has_update, remote_info_dict).
    """
    local = get_local_version()
    local_build = int(local.get("build", 0))

    try:
        req = urllib.request.Request(
            GITHUB_RAW_VERSION_URL,
            headers={"User-Agent": "AIGoldWatcherV4-UpdaterClient"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                raw_bytes = resp.read()
                remote_data = json.loads(raw_bytes.decode("utf-8"))
                remote_build = int(remote_data.get("build", 0))
                if remote_build > local_build:
                    return True, remote_data
                return False, remote_data
    except Exception as e:
        logger.debug("Remote version check skipped: %s", e)
    return False, None


def get_local_announcement() -> Optional[dict]:
    """Read the latest local admin broadcast message."""
    if not ANNOUNCEMENT_FILE.exists():
        return None
    try:
        with open(ANNOUNCEMENT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Error reading announcements file: %s", e)
        return None


def publish_admin_announcement(message: str, sender: str = "LilBoiXAU") -> dict:
    """
    Master Admin publishes an announcement broadcast.
    Saves to announcements.json.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "id": f"ann_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": ts,
        "sender": sender,
        "message": message.strip(),
        "priority": "HIGH",
    }
    try:
        with open(ANNOUNCEMENT_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Error publishing admin announcement: %s", e)
    return payload


def check_remote_announcement(timeout: float = 2.5) -> Optional[dict]:
    """
    Fetch the latest Admin broadcast from GitHub master repo.
    """
    try:
        req = urllib.request.Request(
            GITHUB_RAW_ANNOUNCEMENT_URL,
            headers={"User-Agent": "AIGoldWatcherV4-AnnouncementClient"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                raw_bytes = resp.read()
                data = json.loads(raw_bytes.decode("utf-8"))
                return data
    except Exception as e:
        logger.debug("Remote announcement check skipped: %s", e)
    return None
