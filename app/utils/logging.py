"""
Logging utilities for structured application logging.
"""
import logging
import sys
from typing import Any, Dict


def setup_logging(app_name: str = "ZenvyDesk", level: str = "INFO") -> None:
    """
    Configure application logging.
    
    Args:
        app_name: Name of the application
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=f"%(asctime)s - {app_name} - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def safe_log_dict(data: Dict[str, Any], sensitive_keys: list = None) -> Dict[str, Any]:
    """
    Create a safe version of a dictionary for logging by masking sensitive keys.
    
    Args:
        data: Dictionary to sanitize
        sensitive_keys: List of keys to mask (default: common sensitive fields)
        
    Returns:
        Sanitized dictionary safe for logging
    """
    if sensitive_keys is None:
        sensitive_keys = [
            "password", "token", "secret", "access_token", 
            "refresh_token", "api_key", "authorization"
        ]
    
    safe_data = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            safe_data[key] = "***REDACTED***"
        else:
            safe_data[key] = value
    
    return safe_data
