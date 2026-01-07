"""Logging configuration for the application."""

import logging
import logging.handlers
import sys
from pathlib import Path


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
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
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
