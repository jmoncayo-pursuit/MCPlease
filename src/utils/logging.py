"""
MCPlease MCP Server - Structured Logging Configuration

This module provides comprehensive structured logging configuration for the MCPlease MCP server
with security event tracking, performance metrics, and error categorization.
"""

import logging
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, Union
import structlog
from structlog.stdlib import LoggerFactory
from enum import Enum


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """Event types for categorized logging."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR = "error"
    AUDIT = "audit"
    SYSTEM = "system"
    USER_ACTION = "user_action"
    AI_INFERENCE = "ai_inference"
    NETWORK = "network"


class SecurityEventLogger:
    """Specialized logger for security events."""
    
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger
    
    def authentication_attempt(
        self,
        user_id: Optional[str],
        method: str,
        success: bool,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log authentication attempts."""
        self.logger.info(
            "Authentication attempt",
            event_type=EventType.SECURITY.value,
            security_event="authentication",
            user_id=user_id,
            method=method,
            success=success,
            ip_address=ip_address,
            details=details or {}
        )
    
    def authorization_check(
        self,
        user_id: Optional[str],
        resource: str,
        action: str,
        granted: bool,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log authorization checks."""
        self.logger.info(
            "Authorization check",
            event_type=EventType.SECURITY.value,
            security_event="authorization",
            user_id=user_id,
            resource=resource,
            action=action,
            granted=granted,
            details=details or {}
        )
    
    def rate_limit_exceeded(
        self,
        user_id: Optional[str],
        ip_address: Optional[str],
        limit_type: str,
        current_count: int,
        limit: int
    ):
        """Log rate limit violations."""
        self.logger.warning(
            "Rate limit exceeded",
            event_type=EventType.SECURITY.value,
            security_event="rate_limit",
            user_id=user_id,
            ip_address=ip_address,
            limit_type=limit_type,
            current_count=current_count,
            limit=limit
        )
    
    def suspicious_activity(
        self,
        user_id: Optional[str],
        ip_address: Optional[str],
        activity_type: str,
        details: Dict[str, Any]
    ):
        """Log suspicious activities."""
        self.logger.warning(
            "Suspicious activity detected",
            event_type=EventType.SECURITY.value,
            security_event="suspicious_activity",
            user_id=user_id,
            ip_address=ip_address,
            activity_type=activity_type,
            details=details
        )


class PerformanceLogger:
    """Specialized logger for performance metrics."""
    
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def request_timing(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: int,
        user_id: Optional[str] = None
    ):
        """Log request timing information."""
        self.logger.info(
            "Request completed",
            event_type=EventType.PERFORMANCE.value,
            endpoint=endpoint,
            method=method,
            duration_ms=duration_ms,
            status_code=status_code,
            user_id=user_id
        )
    
    def ai_inference_timing(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
        memory_usage_mb: Optional[float] = None
    ):
        """Log AI inference performance."""
        self.logger.info(
            "AI inference completed",
            event_type=EventType.AI_INFERENCE.value,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb
        )
    
    def resource_usage(
        self,
        cpu_percent: float,
        memory_percent: float,
        disk_usage_percent: float,
        active_connections: int
    ):
        """Log system resource usage."""
        self.logger.info(
            "Resource usage snapshot",
            event_type=EventType.PERFORMANCE.value,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_usage_percent=disk_usage_percent,
            active_connections=active_connections
        )


class AuditLogger:
    """Specialized logger for audit events."""
    
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger
    
    def user_action(
        self,
        user_id: Optional[str],
        action: str,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log user actions for audit trail."""
        self.logger.info(
            "User action",
            event_type=EventType.AUDIT.value,
            user_id=user_id,
            action=action,
            resource=resource,
            details=details or {}
        )
    
    def system_change(
        self,
        change_type: str,
        component: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        changed_by: Optional[str] = None
    ):
        """Log system configuration changes."""
        self.logger.info(
            "System change",
            event_type=EventType.AUDIT.value,
            change_type=change_type,
            component=component,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by
        )


def add_request_id_processor(logger, method_name, event_dict):
    """Add request ID to log entries if available."""
    # This would be set by middleware in actual requests
    request_id = getattr(logger._context, 'request_id', None)
    if request_id:
        event_dict['request_id'] = request_id
    return event_dict


def add_session_id_processor(logger, method_name, event_dict):
    """Add session ID to log entries if available."""
    session_id = getattr(logger._context, 'session_id', None)
    if session_id:
        event_dict['session_id'] = session_id
    return event_dict


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    enable_json: bool = False,
    enable_colors: bool = True,
    enable_security_logging: bool = True,
    enable_performance_logging: bool = True
) -> structlog.BoundLogger:
    """
    Setup comprehensive structured logging for the MCPlease MCP server.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        enable_json: Whether to use JSON formatting
        enable_colors: Whether to enable colored output (for console)
        enable_security_logging: Whether to enable security event logging
        enable_performance_logging: Whether to enable performance logging
    
    Returns:
        Configured structlog logger
    """
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Configure processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        add_request_id_processor,
        add_session_id_processor,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Add JSON or console formatting
    if enable_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        if enable_colors and sys.stdout.isatty():
            processors.append(structlog.dev.ConsoleRenderer(colors=True))
        else:
            processors.append(structlog.dev.ConsoleRenderer(colors=False))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup file logging if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create separate handlers for different log types
        handlers = []
        
        # Main log file
        main_handler = logging.FileHandler(log_file)
        main_handler.setLevel(getattr(logging, log_level.upper()))
        main_formatter = logging.Formatter('%(message)s')
        main_handler.setFormatter(main_formatter)
        handlers.append(main_handler)
        
        # Security log file
        if enable_security_logging:
            security_log_file = log_file.parent / f"security_{log_file.name}"
            security_handler = logging.FileHandler(security_log_file)
            security_handler.setLevel(logging.INFO)
            security_handler.addFilter(lambda record: 'security' in getattr(record, 'msg', ''))
            security_handler.setFormatter(main_formatter)
            handlers.append(security_handler)
        
        # Performance log file
        if enable_performance_logging:
            perf_log_file = log_file.parent / f"performance_{log_file.name}"
            perf_handler = logging.FileHandler(perf_log_file)
            perf_handler.setLevel(logging.INFO)
            perf_handler.addFilter(lambda record: 'performance' in getattr(record, 'msg', ''))
            perf_handler.setFormatter(main_formatter)
            handlers.append(perf_handler)
        
        # Add all handlers to root logger
        root_logger = logging.getLogger()
        for handler in handlers:
            root_logger.addHandler(handler)
    
    return structlog.get_logger("mcplease_mcp")


def get_logger(name: str, level: str = "INFO", log_file: Optional[Path] = None) -> logging.Logger:
    """Get a configured logger instance (legacy compatibility)."""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    # Set level
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_structured_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance for a specific module."""
    return structlog.get_logger(name)


def get_security_logger(base_logger: Optional[structlog.BoundLogger] = None) -> SecurityEventLogger:
    """Get a security event logger."""
    if base_logger is None:
        base_logger = structlog.get_logger("mcplease_mcp.security")
    return SecurityEventLogger(base_logger)


def get_performance_logger(base_logger: Optional[structlog.BoundLogger] = None) -> PerformanceLogger:
    """Get a performance logger."""
    if base_logger is None:
        base_logger = structlog.get_logger("mcplease_mcp.performance")
    return PerformanceLogger(base_logger)


def get_audit_logger(base_logger: Optional[structlog.BoundLogger] = None) -> AuditLogger:
    """Get an audit logger."""
    if base_logger is None:
        base_logger = structlog.get_logger("mcplease_mcp.audit")
    return AuditLogger(base_logger)


class LoggingContext:
    """Context manager for adding context to logs."""
    
    def __init__(self, logger: structlog.BoundLogger, **context):
        self.logger = logger
        self.context = context
        self.bound_logger = None
    
    def __enter__(self):
        self.bound_logger = self.logger.bind(**self.context)
        return self.bound_logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def with_context(logger: structlog.BoundLogger, **context) -> LoggingContext:
    """Create a logging context with additional fields."""
    return LoggingContext(logger, **context)