"""
Structured logging with credential redaction for AI GOLD WATCHER V4.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Optional


class SensitiveFilter(logging.Filter):
    """Filter that strips API keys, passwords, and sensitive credentials from log records."""

    PATTERNS = [
        re.compile(r"password=([^\s&]+)", re.IGNORECASE),
        re.compile(r"token=([^\s&]+)", re.IGNORECASE),
        re.compile(r"api_key=([^\s&]+)", re.IGNORECASE),
        re.compile(r"login=([^\s&]+)", re.IGNORECASE),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pat in self.PATTERNS:
                record.msg = pat.sub(r"\1=[REDACTED]", record.msg)
        return True


def setup_logger(
    name: str = "v4_trading",
    logs_dir: Optional[Path] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Configures structured logger with console output and optional file logging."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sens_filter = SensitiveFilter()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sens_filter)
    logger.addHandler(console_handler)

    # File Handler
    if logs_dir:
        logs_dir = Path(logs_dir)
        logs_dir.mkdir(parents=True, exist_ok=True)
        file_path = logs_dir / "bot_activity.log"
        file_handler = logging.FileHandler(str(file_path), encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(sens_filter)
        logger.addHandler(file_handler)

    return logger
