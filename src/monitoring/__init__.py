"""
Monitoring and telemetry module for AI GOLD WATCHER V4.
"""

from src.monitoring.logger import setup_logger
from src.monitoring.alerts import (
    AlertSeverity,
    AlertMessage,
    AlertManager,
)
from src.monitoring.health_monitor import (
    SystemHealthStatus,
    HealthMonitor,
)

__all__ = [
    "setup_logger",
    "AlertSeverity",
    "AlertMessage",
    "AlertManager",
    "SystemHealthStatus",
    "HealthMonitor",
]
