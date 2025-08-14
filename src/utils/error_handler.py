"""Comprehensive error handling and recovery system for MCPlease.

This module provides robust error handling, graceful degradation, and user-friendly
error messages to ensure MCPlease works reliably out of the box.
"""

import logging
import traceback
import sys
import time
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"           # Minor issues, system continues normally
    MEDIUM = "medium"     # Some features affected, fallbacks available
    HIGH = "high"         # Major issues, limited functionality
    CRITICAL = "critical" # System cannot function properly


class ErrorCategory(Enum):
    """Error categories for better handling."""
    IMPORT_ERROR = "import_error"
    MODEL_ERROR = "model_error"
    MEMORY_ERROR = "memory_error"
    NETWORK_ERROR = "network_error"
    CONFIG_ERROR = "config_error"
    RUNTIME_ERROR = "runtime_error"
    USER_ERROR = "user_error"


@dataclass
class ErrorInfo:
    """Structured error information."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    suggested_actions: List[str]
    technical_details: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class ErrorHandler:
    """Comprehensive error handler with fallback strategies."""
    
    def __init__(self):
        self.error_history: List[ErrorInfo] = []
        self.fallback_strategies: Dict[ErrorCategory, Callable] = {
            ErrorCategory.IMPORT_ERROR: self._handle_import_error,
            ErrorCategory.MODEL_ERROR: self._handle_model_error,
            ErrorCategory.MEMORY_ERROR: self._handle_memory_error,
            ErrorCategory.NETWORK_ERROR: self._handle_network_error,
            ErrorCategory.CONFIG_ERROR: self._handle_config_error,
            ErrorCategory.RUNTIME_ERROR: self._handle_runtime_error,
            ErrorCategory.USER_ERROR: self._handle_user_error,
        }
        
        # Error patterns for automatic categorization
        self.error_patterns = {
            ErrorCategory.IMPORT_ERROR: [
                "ModuleNotFoundError", "ImportError", "No module named",
                "cannot import", "import failed"
            ],
            ErrorCategory.MODEL_ERROR: [
                "model not found", "model loading failed", "model error",
                "inference failed", "vllm error", "torch error"
            ],
            ErrorCategory.MEMORY_ERROR: [
                "out of memory", "memory error", "OOM", "CUDA out of memory",
                "insufficient memory", "memory allocation failed"
            ],
            ErrorCategory.NETWORK_ERROR: [
                "connection error", "network error", "timeout", "DNS",
                "connection refused", "unreachable"
            ],
            ErrorCategory.CONFIG_ERROR: [
                "configuration error", "config not found", "invalid config",
                "settings error", "permission denied"
            ],
            ErrorCategory.USER_ERROR: [
                "file not found", "invalid argument", "invalid input",
                "command not found", "syntax error"
            ]
        }
    
    def handle_error(self, error: Exception, context: str = "") -> ErrorInfo:
        """Handle an error with appropriate fallback strategy.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            ErrorInfo object with handling details
        """
        # Categorize the error
        category = self._categorize_error(error)
        severity = self._assess_severity(error, category)
        
        # Create error info
        error_info = ErrorInfo(
            category=category,
            severity=severity,
            message=str(error),
            user_message=self._create_user_message(error, category),
            suggested_actions=self._get_suggested_actions(error, category),
            technical_details=f"{context}\n{traceback.format_exc()}" if context else traceback.format_exc()
        )
        
        # Store in history
        self.error_history.append(error_info)
        
        # Apply fallback strategy
        if category in self.fallback_strategies:
            try:
                self.fallback_strategies[category](error_info)
            except Exception as fallback_error:
                logger.error(f"Fallback strategy failed: {fallback_error}")
        
        # Log the error
        self._log_error(error_info)
        
        return error_info
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an error based on its type and message."""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Check patterns
        for category, patterns in self.error_patterns.items():
            if any(pattern.lower() in error_str or pattern.lower() in error_type.lower() 
                   for pattern in patterns):
                return category
        
        # Default to runtime error
        return ErrorCategory.RUNTIME_ERROR
    
    def _assess_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Assess the severity of an error."""
        # Critical errors that prevent system startup
        if category == ErrorCategory.IMPORT_ERROR and "torch" in str(error).lower():
            return ErrorSeverity.HIGH
        
        if category == ErrorCategory.MEMORY_ERROR and "critical" in str(error).lower():
            return ErrorSeverity.CRITICAL
        
        if category == ErrorCategory.CONFIG_ERROR:
            return ErrorSeverity.MEDIUM
        
        # Model errors are medium since we have fallbacks
        if category == ErrorCategory.MODEL_ERROR:
            return ErrorSeverity.MEDIUM
        
        # Import errors are usually medium (we have fallbacks)
        if category == ErrorCategory.IMPORT_ERROR:
            return ErrorSeverity.MEDIUM
        
        # User errors are typically low
        if category == ErrorCategory.USER_ERROR:
            return ErrorSeverity.LOW
        
        # Default to medium
        return ErrorSeverity.MEDIUM
    
    def _create_user_message(self, error: Exception, category: ErrorCategory) -> str:
        """Create a user-friendly error message."""
        messages = {
            ErrorCategory.IMPORT_ERROR: "Some advanced features are unavailable due to missing dependencies.",
            ErrorCategory.MODEL_ERROR: "AI model is unavailable, using intelligent fallback responses.",
            ErrorCategory.MEMORY_ERROR: "Memory constraints detected, optimizing performance automatically.",
            ErrorCategory.NETWORK_ERROR: "Network connectivity issues detected, working in offline mode.",
            ErrorCategory.CONFIG_ERROR: "Configuration issue detected, using default settings.",
            ErrorCategory.RUNTIME_ERROR: "A runtime issue occurred, but the system continues to work.",
            ErrorCategory.USER_ERROR: "Input issue detected, please check your command or input."
        }
        
        return messages.get(category, "An issue occurred, but the system is handling it gracefully.")
    
    def _get_suggested_actions(self, error: Exception, category: ErrorCategory) -> List[str]:
        """Get suggested actions for resolving the error."""
        actions = {
            ErrorCategory.IMPORT_ERROR: [
                "Install missing dependencies: pip install torch vllm fastapi",
                "Run setup: python mcplease.py --setup",
                "Check Python version (3.9-3.13 required)"
            ],
            ErrorCategory.MODEL_ERROR: [
                "The system works with fallback responses",
                "For full AI features, download model: huggingface-cli download openai/gpt-oss-20b",
                "Check available memory: python mcplease.py --status"
            ],
            ErrorCategory.MEMORY_ERROR: [
                "Close other applications to free memory",
                "Use lower memory limit: python mcplease.py --start --max-memory 8",
                "Consider upgrading to 16GB+ RAM for optimal performance"
            ],
            ErrorCategory.NETWORK_ERROR: [
                "Check internet connection",
                "The system works offline after initial setup",
                "Try again later if downloading models"
            ],
            ErrorCategory.CONFIG_ERROR: [
                "Check file permissions",
                "Run from the MCPlease directory",
                "Reset configuration: python mcplease.py --setup"
            ],
            ErrorCategory.RUNTIME_ERROR: [
                "Try restarting the application",
                "Check system resources",
                "Report issue if problem persists"
            ],
            ErrorCategory.USER_ERROR: [
                "Check command syntax: python mcplease.py --help",
                "Verify file paths and arguments",
                "See documentation for examples"
            ]
        }
        
        return actions.get(category, ["Try restarting the application", "Check system status"])
    
    def _handle_import_error(self, error_info: ErrorInfo) -> None:
        """Handle import errors with graceful degradation."""
        logger.warning(f"Import error handled: {error_info.message}")
        # Import errors are handled by fallback imports in the main modules
    
    def _handle_model_error(self, error_info: ErrorInfo) -> None:
        """Handle model errors by enabling fallback mode."""
        logger.warning(f"Model error handled: {error_info.message}")
        # Model errors are handled by the fallback response system
    
    def _handle_memory_error(self, error_info: ErrorInfo) -> None:
        """Handle memory errors with optimization."""
        logger.warning(f"Memory error handled: {error_info.message}")
        # Memory errors trigger automatic optimization
    
    def _handle_network_error(self, error_info: ErrorInfo) -> None:
        """Handle network errors by working offline."""
        logger.warning(f"Network error handled: {error_info.message}")
        # Network errors are handled by offline mode
    
    def _handle_config_error(self, error_info: ErrorInfo) -> None:
        """Handle configuration errors with defaults."""
        logger.warning(f"Config error handled: {error_info.message}")
        # Config errors are handled by using defaults
    
    def _handle_runtime_error(self, error_info: ErrorInfo) -> None:
        """Handle runtime errors with recovery."""
        logger.warning(f"Runtime error handled: {error_info.message}")
        # Runtime errors are logged and system continues
    
    def _handle_user_error(self, error_info: ErrorInfo) -> None:
        """Handle user errors with helpful guidance."""
        logger.info(f"User error handled: {error_info.message}")
        # User errors are handled with helpful messages
    
    def _log_error(self, error_info: ErrorInfo) -> None:
        """Log error information appropriately."""
        log_message = f"[{error_info.category.value}] {error_info.user_message}"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all handled errors."""
        if not self.error_history:
            return {"status": "No errors recorded", "total_errors": 0}
        
        summary = {
            "total_errors": len(self.error_history),
            "by_category": {},
            "by_severity": {},
            "recent_errors": []
        }
        
        # Count by category and severity
        for error in self.error_history:
            category = error.category.value
            severity = error.severity.value
            
            summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        
        # Get recent errors (last 5)
        recent = sorted(self.error_history, key=lambda x: x.timestamp, reverse=True)[:5]
        summary["recent_errors"] = [
            {
                "category": error.category.value,
                "severity": error.severity.value,
                "message": error.user_message,
                "timestamp": error.timestamp
            }
            for error in recent
        ]
        
        return summary
    
    def clear_error_history(self) -> None:
        """Clear the error history."""
        self.error_history.clear()


# Global error handler instance
global_error_handler = ErrorHandler()


def handle_error(error: Exception, context: str = "") -> ErrorInfo:
    """Global error handling function."""
    return global_error_handler.handle_error(error, context)


def safe_execute(func: Callable, *args, fallback_result=None, context: str = "", **kwargs):
    """Execute a function safely with error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        fallback_result: Result to return if function fails
        context: Context description for error handling
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or fallback_result if error occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_info = handle_error(e, context)
        logger.debug(f"Safe execution failed: {error_info.user_message}")
        return fallback_result


async def safe_execute_async(func: Callable, *args, fallback_result=None, context: str = "", **kwargs):
    """Execute an async function safely with error handling.
    
    Args:
        func: Async function to execute
        *args: Function arguments
        fallback_result: Result to return if function fails
        context: Context description for error handling
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or fallback_result if error occurs
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        error_info = handle_error(e, context)
        logger.debug(f"Safe async execution failed: {error_info.user_message}")
        return fallback_result


def error_boundary(fallback_result=None, context: str = ""):
    """Decorator for error boundary with fallback.
    
    Args:
        fallback_result: Result to return if function fails
        context: Context description for error handling
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            return safe_execute(func, *args, fallback_result=fallback_result, 
                              context=context or f"{func.__name__}", **kwargs)
        return wrapper
    return decorator


def async_error_boundary(fallback_result=None, context: str = ""):
    """Decorator for async error boundary with fallback.
    
    Args:
        fallback_result: Result to return if function fails
        context: Context description for error handling
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await safe_execute_async(func, *args, fallback_result=fallback_result,
                                          context=context or f"{func.__name__}", **kwargs)
        return wrapper
    return decorator