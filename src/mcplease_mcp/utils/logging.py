"""
Structured logging utilities for MCPlease MCP Server.

This module provides structured logging with security event tracking,
performance monitoring, and consistent log formatting.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional, Union
from pathlib import Path
import os

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record):
        # Add timestamp if not present
        if not hasattr(record, 'timestamp'):
            record.timestamp = datetime.utcnow().isoformat()
        
        # Format the message
        formatted = super().format(record)
        
        # Add structured data if available
        if hasattr(record, 'structured_data'):
            try:
                structured_json = json.dumps(record.structured_data, default=str)
                formatted += f" - {structured_json}"
            except (TypeError, ValueError):
                formatted += f" - {str(record.structured_data)}"
        
        return formatted


def get_structured_logger(name: str) -> logging.Logger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Configure logger if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = StructuredFormatter(LOG_FORMAT)
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
    
    return logger


def configure_logging(level: str = "INFO", log_file: Optional[Union[str, Path]] = None):
    """Configure global logging settings."""
    # Set root logger level
    logging.getLogger().setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
    
    # Configure root logger with console handler
    root_logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
    
    # Create formatter
    formatter = StructuredFormatter(LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add console handler to root logger
    root_logger.addHandler(console_handler)
    
    return root_logger


# Default logger instances
security_logger = get_structured_logger("security")
performance_logger = get_structured_logger("performance")
health_logger = get_structured_logger("health")
standard_logger = get_structured_logger("standard")

# Minimal wrappers to provide helper methods used across codebase
class SecurityLoggerWrapper:
    def __init__(self, base: logging.Logger):
        self._base = base

    def authentication_attempt(self, user_id: str, method: str, success: bool, details: Dict[str, Any]):
        self._base.info(
            "Authentication attempt",
            extra={"structured_data": {
                "event": "auth_attempt",
                "user_id": user_id,
                "method": method,
                "success": success,
                "details": details,
            }}
        )


class PerformanceLoggerWrapper:
    def __init__(self, base: logging.Logger):
        self._base = base

    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self._base.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self._base.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self._base.error(message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self._base.debug(message, *args, **kwargs)

    def request_timing(self, endpoint: str, method: str, duration_ms: float, status_code: int):
        self._base.info(
            "Request timing",
            extra={"structured_data": {
                "event": "request_timing",
                "endpoint": endpoint,
                "method": method,
                "duration_ms": round(duration_ms, 2) if isinstance(duration_ms, (int, float)) else duration_ms,
                "status_code": status_code,
            }}
        )

    def ai_inference_timing(self, model_name: str, input_tokens: int, output_tokens: int, duration_ms: float):
        self._base.info(
            "AI inference timing",
            extra={"structured_data": {
                "event": "ai_inference_timing",
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "duration_ms": round(duration_ms, 2) if isinstance(duration_ms, (int, float)) else duration_ms,
            }}
        )


# Helper accessors for named loggers (compat)
def get_security_logger():
    return SecurityLoggerWrapper(security_logger)

def get_performance_logger():
    return PerformanceLoggerWrapper(performance_logger)

def get_health_logger() -> logging.Logger:
    return health_logger

def get_standard_logger() -> logging.Logger:
    return standard_logger

# Configure logging based on environment
def _configure_from_environment():
    """Configure logging from environment variables."""
    log_level = os.getenv("MCPLEASE_LOG_LEVEL", "INFO")
    log_file = os.getenv("MCPLEASE_LOG_FILE")
    
    configure_logging(level=log_level)

# Auto-configure on import
try:
    _configure_from_environment()
except Exception:
    # Fallback to basic configuration if environment setup fails
    configure_logging() 
