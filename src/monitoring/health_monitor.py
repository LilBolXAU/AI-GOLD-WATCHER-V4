"""
System health and feed continuity monitor for AI GOLD WATCHER V4.
"""

from dataclasses import dataclass
from typing import Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SystemHealthStatus:
    is_terminal_connected: bool
    is_feed_live: bool
    last_bar_timestamp: Optional[pd.Timestamp]
    heartbeat_time: pd.Timestamp
    consecutive_feed_errors: int
    is_degraded: bool
    status_summary: str


class HealthMonitor:
    """Tracks MT5 connection status, bar arrival heartbeats, and data feed integrity."""

    def __init__(self, max_feed_gap_seconds: int = 180):
        self.max_feed_gap_seconds = max_feed_gap_seconds
        self._last_bar_time: Optional[pd.Timestamp] = None
        self._consecutive_feed_errors = 0
        self._is_terminal_connected = False

    def record_heartbeat(self, connected: bool) -> None:
        self._is_terminal_connected = connected

    def record_bar_arrival(self, bar_time: pd.Timestamp) -> None:
        self._last_bar_time = bar_time
        self._consecutive_feed_errors = 0

    def record_feed_error(self) -> None:
        self._consecutive_feed_errors += 1

    def get_status(self) -> SystemHealthStatus:
        now = pd.Timestamp.now(tz="UTC")
        feed_live = False
        if self._last_bar_time is not None:
            # Check elapsed seconds
            elapsed = (now - self._last_bar_time).total_seconds()
            feed_live = elapsed <= self.max_feed_gap_seconds

        degraded = (
            not self._is_terminal_connected
            or self._consecutive_feed_errors >= 3
            or (self._last_bar_time is not None and not feed_live)
        )

        summary = "OPERATIONAL"
        if not self._is_terminal_connected:
            summary = "TERMINAL_DISCONNECTED"
        elif self._consecutive_feed_errors >= 3:
            summary = f"FEED_DEGRADED ({self._consecutive_feed_errors} consecutive errors)"
        elif not feed_live and self._last_bar_time is not None:
            summary = "FEED_STALE"

        return SystemHealthStatus(
            is_terminal_connected=self._is_terminal_connected,
            is_feed_live=feed_live,
            last_bar_timestamp=self._last_bar_time,
            heartbeat_time=now,
            consecutive_feed_errors=self._consecutive_feed_errors,
            is_degraded=degraded,
            status_summary=summary,
        )
