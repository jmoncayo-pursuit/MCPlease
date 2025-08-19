"""
MCPlease MCP Server - Comprehensive Error Handling

This module provides structured error handling with proper categorization,
graceful degradation, and comprehensive logging for production use.
"""

import sys
import traceback
import logging
import structlog
from typing import Dict, Any, Optional, Type, Union, List
from enum import Enum
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import asyncio
import time
from pathlib import Path

from ...utils.exceptions import (
    MCPleaseError,
    MCPProtocolError,
    AIModelError,
    SecurityError,
    ConfigurationError,
    ResourceError,
    NetworkError
)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    PROTOCOL = "protocol"
    AI_MODEL = "ai_model"
    SECURITY = "security"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    EXTERNAL = "external"


@dataclass
class ErrorContext:
    """Context information for error handling."""
    timestamp: float
    severity: ErrorSeverity
    category: ErrorCategory
    error_code: str
    message: str
    details: Dict[str, Any]
    stack_trace: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False


class MCPErrorHandler:
    """Comprehensive error handler with categorization and recovery."""
    
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or structlog.get_logger(__name__)
        self.error_counts: Dict[str, int] = {}
        self.recovery_strategies: Dict[ErrorCategory, List[callable]] = {}
        self.error_history: List[ErrorContext] = []
        self.max_history = 1000
        
        # Initialize recovery strategies
        self._setup_recovery_strategies()
    
    def _setup_recovery_strategies(self):
        """Setup recovery strategies for different error categories."""
        self.recovery_strategies = {
            ErrorCategory.AI_MODEL: [
                self._recover_ai_model_fallback,
                self._recover_ai_model_restart,
            ],
            ErrorCategory.NETWORK: [
                self._recover_network_retry,
                self._recover_network_fallback,
            ],
            ErrorCategory.RESOURCE: [
                self._recover_resource_cleanup,
                self._recover_resource_limit,
            ],
            ErrorCategory.CONFIGURATION: [
                self._recover_config_default,
                self._recover_config_reload,
            ],
        }
    
    def categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an error based on its type and context."""
        if isinstance(error, MCPProtocolError):
            return ErrorCategory.PROTOCOL
        elif isinstance(error, AIModelError):
            return ErrorCategory.AI_MODEL
        elif isinstance(error, SecurityError):
            return ErrorCategory.SECURITY
        elif isinstance(error, NetworkError):
            return ErrorCategory.NETWORK
        elif isinstance(error, ConfigurationError):
            return ErrorCategory.CONFIGURATION
        elif isinstance(error, ResourceError):
            return ErrorCategory.RESOURCE
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorCategory.NETWORK
        elif isinstance(error, (MemoryError, OSError)):
            return ErrorCategory.RESOURCE
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorCategory.USER_INPUT
        else:
            return ErrorCategory.SYSTEM
    
    def determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity based on type and category."""
        # Critical errors that require immediate attention
        if isinstance(error, (MemoryError, SystemExit, KeyboardInterrupt)):
            return ErrorSeverity.CRITICAL
        
        # High severity errors by category
        if category in [ErrorCategory.SECURITY, ErrorCategory.PROTOCOL]:
            return ErrorSeverity.HIGH
        
        # AI model errors are medium unless they're critical
        if category == ErrorCategory.AI_MODEL:
            if "model not found" in str(error).lower():
                return ErrorSeverity.HIGH
            return ErrorSeverity.MEDIUM
        
        # Network and resource errors are typically medium
        if category in [ErrorCategory.NETWORK, ErrorCategory.RESOURCE]:
            return ErrorSeverity.MEDIUM
        
        # Configuration and user input errors are low
        if category in [ErrorCategory.CONFIGURATION, ErrorCategory.USER_INPUT]:
            return ErrorSeverity.LOW
        
        # Default to medium
        return ErrorSeverity.MEDIUM
    
    def generate_error_code(self, category: ErrorCategory, error: Exception) -> str:
        """Generate a unique error code for tracking."""
        error_type = type(error).__name__
        category_code = category.value.upper()[:3]
        error_hash = abs(hash(str(error))) % 10000
        return f"{category_code}-{error_type[:10].upper()}-{error_hash:04d}"
    
    async def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        attempt_recovery: bool = True
    ) -> ErrorContext:
        """Handle an error with comprehensive logging and recovery."""
        
        # Categorize and assess error
        category = self.categorize_error(error)
        severity = self.determine_severity(error, category)
        error_code = self.generate_error_code(category, error)
        
        # Create error context
        error_context = ErrorContext(
            timestamp=time.time(),
            severity=severity,
            category=category,
            error_code=error_code,
            message=str(error),
            details=context or {},
            stack_trace=traceback.format_exc(),
            user_id=user_id,
            session_id=session_id,
            request_id=request_id
        )
        
        # Log the error
        await self._log_error(error_context)
        
        # Track error frequency
        self.error_counts[error_code] = self.error_counts.get(error_code, 0) + 1
        
        # Attempt recovery if enabled
        if attempt_recovery and category in self.recovery_strategies:
            error_context.recovery_attempted = True
            recovery_success = await self._attempt_recovery(error, category, error_context)
            error_context.recovery_successful = recovery_success
        
        # Store in history
        self._store_error_history(error_context)
        
        return error_context
    
    async def _log_error(self, error_context: ErrorContext):
        """Log error with structured logging."""
        log_data = {
            "error_code": error_context.error_code,
            "severity": error_context.severity.value,
            "category": error_context.category.value,
            "message": error_context.message,
            "user_id": error_context.user_id,
            "session_id": error_context.session_id,
            "request_id": error_context.request_id,
            "details": error_context.details,
        }
        
        # Log based on severity
        if error_context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical("Critical error occurred", **log_data)
        elif error_context.severity == ErrorSeverity.HIGH:
            self.logger.error("High severity error", **log_data)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning("Medium severity error", **log_data)
        else:
            self.logger.info("Low severity error", **log_data)
        
        # Include stack trace for high/critical errors
        if error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            if error_context.stack_trace:
                self.logger.debug("Stack trace", stack_trace=error_context.stack_trace)
    
    async def _attempt_recovery(
        self,
        error: Exception,
        category: ErrorCategory,
        error_context: ErrorContext
    ) -> bool:
        """Attempt recovery using registered strategies."""
        strategies = self.recovery_strategies.get(category, [])
        
        for strategy in strategies:
            try:
                self.logger.info(
                    "Attempting error recovery",
                    strategy=strategy.__name__,
                    error_code=error_context.error_code
                )
                
                success = await strategy(error, error_context)
                if success:
                    self.logger.info(
                        "Error recovery successful",
                        strategy=strategy.__name__,
                        error_code=error_context.error_code
                    )
                    return True
                    
            except Exception as recovery_error:
                self.logger.warning(
                    "Recovery strategy failed",
                    strategy=strategy.__name__,
                    error_code=error_context.error_code,
                    recovery_error=str(recovery_error)
                )
        
        return False
    
    def _store_error_history(self, error_context: ErrorContext):
        """Store error in history with size limit."""
        self.error_history.append(error_context)
        
        # Maintain history size limit
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
    
    # Recovery strategies
    async def _recover_ai_model_fallback(self, error: Exception, context: ErrorContext) -> bool:
        """Fallback to basic responses when AI model fails."""
        try:
            # Set a flag to use fallback responses
            context.details["use_fallback"] = True
            return True
        except Exception:
            return False
    
    async def _recover_ai_model_restart(self, error: Exception, context: ErrorContext) -> bool:
        """Attempt to restart AI model."""
        try:
            # This would integrate with the AI model manager
            # For now, just simulate recovery
            await asyncio.sleep(1)
            return False  # Placeholder - would need actual model restart logic
        except Exception:
            return False
    
    async def _recover_network_retry(self, error: Exception, context: ErrorContext) -> bool:
        """Retry network operation with backoff."""
        try:
            retry_count = context.details.get("retry_count", 0)
            if retry_count < 3:
                context.details["retry_count"] = retry_count + 1
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return True
            return False
        except Exception:
            return False
    
    async def _recover_network_fallback(self, error: Exception, context: ErrorContext) -> bool:
        """Fallback to local-only mode."""
        try:
            context.details["local_only"] = True
            return True
        except Exception:
            return False
    
    async def _recover_resource_cleanup(self, error: Exception, context: ErrorContext) -> bool:
        """Clean up resources to free memory."""
        try:
            # Trigger garbage collection
            import gc
            gc.collect()
            
            # Clear caches if available
            context.details["resources_cleaned"] = True
            return True
        except Exception:
            return False
    
    async def _recover_resource_limit(self, error: Exception, context: ErrorContext) -> bool:
        """Reduce resource usage limits."""
        try:
            context.details["reduced_limits"] = True
            return True
        except Exception:
            return False
    
    async def _recover_config_default(self, error: Exception, context: ErrorContext) -> bool:
        """Use default configuration values."""
        try:
            context.details["use_defaults"] = True
            return True
        except Exception:
            return False
    
    async def _recover_config_reload(self, error: Exception, context: ErrorContext) -> bool:
        """Reload configuration from file."""
        try:
            # This would integrate with configuration manager
            context.details["config_reloaded"] = True
            return False  # Placeholder - would need actual config reload
        except Exception:
            return False
    
    # Utility methods
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        total_errors = len(self.error_history)
        if total_errors == 0:
            return {"total_errors": 0}
        
        # Count by category
        category_counts = {}
        severity_counts = {}
        recent_errors = []
        
        # Look at last hour of errors
        one_hour_ago = time.time() - 3600
        
        for error in self.error_history:
            # Category counts
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Severity counts
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Recent errors
            if error.timestamp > one_hour_ago:
                recent_errors.append({
                    "error_code": error.error_code,
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "timestamp": error.timestamp
                })
        
        return {
            "total_errors": total_errors,
            "category_counts": category_counts,
            "severity_counts": severity_counts,
            "recent_errors": recent_errors,
            "most_frequent": dict(sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def clear_error_history(self):
        """Clear error history (for testing or maintenance)."""
        self.error_history.clear()
        self.error_counts.clear()
    
    @contextmanager
    def error_context(
        self,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        suppress_errors: bool = False
    ):
        """Context manager for automatic error handling."""
        try:
            yield
        except Exception as e:
            if not suppress_errors:
                # Handle error asynchronously if we're in an async context
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Schedule error handling
                        asyncio.create_task(
                            self.handle_error(e, context, user_id, session_id, request_id)
                        )
                    else:
                        # Run synchronously
                        loop.run_until_complete(
                            self.handle_error(e, context, user_id, session_id, request_id)
                        )
                except RuntimeError:
                    # No event loop, handle synchronously
                    import asyncio
                    asyncio.run(
                        self.handle_error(e, context, user_id, session_id, request_id)
                    )
                
                # Re-raise unless suppressed
                raise


# Global error handler instance
_global_error_handler: Optional[MCPErrorHandler] = None


def get_error_handler() -> MCPErrorHandler:
    """Get the global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = MCPErrorHandler()
    return _global_error_handler


def setup_error_handler(logger: Optional[structlog.BoundLogger] = None) -> MCPErrorHandler:
    """Setup and configure the global error handler."""
    global _global_error_handler
    _global_error_handler = MCPErrorHandler(logger)
    return _global_error_handler


# Convenience functions
async def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> ErrorContext:
    """Handle an error using the global error handler."""
    handler = get_error_handler()
    return await handler.handle_error(error, context, user_id, session_id, request_id)


def error_context(
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    suppress_errors: bool = False
):
    """Context manager for automatic error handling."""
    handler = get_error_handler()
    return handler.error_context(context, user_id, session_id, request_id, suppress_errors)