"""
Safety alert notification system for AI GOLD WATCHER V4.
"""

from dataclasses import dataclass
from enum import Enum
import logging
from typing import Callable, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"


@dataclass(frozen=True)
class AlertMessage:
    timestamp: pd.Timestamp
    severity: AlertSeverity
    source: str
    message: str
    details: Optional[dict] = None


class AlertManager:
    """Manages safety alerts and routes notifications to handlers."""

    def __init__(self):
        self._handlers: List[Callable[[AlertMessage], None]] = []
        self._alert_history: List[AlertMessage] = []

    def register_handler(self, handler: Callable[[AlertMessage], None]) -> None:
        self._handlers.append(handler)

    def trigger_alert(
        self,
        severity: AlertSeverity,
        source: str,
        message: str,
        details: Optional[dict] = None,
    ) -> AlertMessage:
        alert = AlertMessage(
            timestamp=pd.Timestamp.now(tz="UTC"),
            severity=severity,
            source=source,
            message=message,
            details=details,
        )
        self._alert_history.append(alert)

        log_level = logging.INFO
        if severity == AlertSeverity.WARNING:
            log_level = logging.WARNING
        elif severity in (AlertSeverity.CRITICAL, AlertSeverity.CIRCUIT_BREAKER):
            log_level = logging.CRITICAL

        logger.log(
            log_level,
            "ALERT [%s] from %s: %s | details=%s",
            severity.value,
            source,
            message,
            details,
        )

        for handler in self._handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error("Error invoking alert handler: %s", e)

        return alert

    def get_recent_alerts(self, limit: int = 50) -> List[AlertMessage]:
        return self._alert_history[-limit:]
