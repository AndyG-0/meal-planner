"""Logging utilities for the application."""

import re


def sanitize_for_log(value: str | None) -> str:
    """Sanitize user input for logging to prevent log injection.
    
    Removes all control characters including ANSI escape sequences
    to prevent log injection and terminal manipulation attacks.
    
    Args:
        value: The string to sanitize
        
    Returns:
        Sanitized string safe for logging
    """
    if not value:
        return ""
    # Remove all control characters (0x00-0x1F and 0x7F-0x9F)
    # This includes newlines, carriage returns, tabs, ANSI escape sequences, etc.
    sanitized = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', value)
    # Truncate to 100 characters to prevent log flooding
    return sanitized[:100]
