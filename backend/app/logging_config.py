"""Logging configuration for the application."""

import logging
import logging.handlers
import re
import sys
from pathlib import Path


class SanitizingFilter(logging.Filter):
    """Filter that sanitizes log record arguments to prevent log injection attacks."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitize all arguments in the log record.

        Args:
            record: The log record to filter

        Returns:
            True to allow the record to be logged
        """
        # Sanitize the message if it's a string
        if isinstance(record.msg, str):
            record.msg = self._sanitize(record.msg)

        # Sanitize all arguments
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._sanitize(v) if isinstance(v, str) else v
                             for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self._sanitize(arg) if isinstance(arg, str) else arg
                                  for arg in record.args)

        return True

    @staticmethod
    def _sanitize(value) -> str:
        """Sanitize a string value for logging.

        Removes all control characters including ANSI escape sequences
        to prevent log injection and terminal manipulation attacks.

        Args:
            value: The value to sanitize (can be any type)

        Returns:
            Sanitized string safe for logging
        """
        # Preserve None explicitly so it is not masked as an empty string in logs
        if value is None:
            return "None"

        # Convert to string if not already
        str_value = str(value)

        # Preserve empty strings as empty strings without further processing
        if str_value == "":
            return ""

        # Remove all control characters (0x00-0x1F and 0x7F-0x9F)
        # This includes newlines, carriage returns, tabs, ANSI escape sequences, etc.
        sanitized = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', str_value)
        # Truncate to 1000 characters to prevent log flooding
        # (increased from 100 to allow for longer messages)
        return sanitized[:1000]


def setup_logging(debug: bool = False) -> logging.Logger:
    """Set up logging for the application.

    Args:
        debug: Whether to enable debug logging.

    Returns:
        Configured logger instance.
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Create formatters
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create sanitizing filter
    sanitizing_filter = SanitizingFilter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sanitizing_filter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(sanitizing_filter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "app") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: The logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)
