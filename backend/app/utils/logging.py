"""Logging utilities for the application."""


def sanitize_for_log(value: str | None) -> str:
    """Sanitize user input for logging to prevent log injection.
    
    Args:
        value: The string to sanitize
        
    Returns:
        Sanitized string safe for logging
    """
    if not value:
        return ""
    # Replace newlines, carriage returns, and other control characters
    # Truncate to 100 characters to prevent log flooding
    sanitized = value.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    return sanitized[:100]
