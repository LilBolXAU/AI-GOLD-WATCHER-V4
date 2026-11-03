"""
Emergency Kill Switch for AI GOLD WATCHER V4.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class KillSwitchStatus:
    is_active: bool = False
    triggered_at: Optional[datetime] = None
    reason: str = ""


class KillSwitch:
    """
    Emergency fail-closed circuit breaker.
    Instantly halts all signal processing and virtual execution when triggered.
    """

    def __init__(self):
        self._status = KillSwitchStatus()

    @property
    def is_triggered(self) -> bool:
        return self._status.is_active

    @property
    def reason(self) -> str:
        return self._status.reason

    def trigger(self, reason: str) -> None:
        """Trip the kill switch."""
        self._status.is_active = True
        self._status.triggered_at = datetime.now(timezone.utc)
        self._status.reason = reason

    def reset(self) -> None:
        """Reset the kill switch (requires deliberate manual action)."""
        self._status.is_active = False
        self._status.triggered_at = None
        self._status.reason = ""
