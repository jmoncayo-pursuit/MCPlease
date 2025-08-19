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

from src.utils.exceptions import (
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
        
        # Resource monitoring
        self.resource_constraints = {
            "memory_pressure": False,
            "high_error_rate": False,
            "degraded_mode": False
        }
        self.degradation_level = 0  # 0 = normal, 1 = light, 2 = moderate, 3 = severe
        
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
            
            # Try to free up memory by clearing error history if it's too large
            if len(self.error_history) > 500:
                self.error_history = self.error_history[-100:]  # Keep only recent 100 errors
                context.details["error_history_trimmed"] = True
            
            self.logger.info("Resource cleanup completed", cleaned_items=context.details)
            return True
        except Exception as cleanup_error:
            self.logger.warning("Resource cleanup failed", error=str(cleanup_error))
            return False
    
    async def _recover_resource_limit(self, error: Exception, context: ErrorContext) -> bool:
        """Reduce resource usage limits."""
        try:
            # Implement graceful degradation strategies
            degradation_applied = []
            
            # Reduce context size limits
            if "max_context_size" not in context.details:
                context.details["max_context_size"] = 1000  # Reduced from default
                degradation_applied.append("context_size_limited")
            
            # Reduce concurrent request limits
            if "max_concurrent_requests" not in context.details:
                context.details["max_concurrent_requests"] = 2  # Reduced from default
                degradation_applied.append("concurrent_requests_limited")
            
            # Enable memory-efficient mode
            context.details["memory_efficient_mode"] = True
            degradation_applied.append("memory_efficient_mode")
            
            # Reduce model precision if applicable
            context.details["reduced_precision"] = True
            degradation_applied.append("reduced_precision")
            
            context.details["degradation_applied"] = degradation_applied
            context.details["reduced_limits"] = True
            
            self.logger.info(
                "Resource limits reduced for graceful degradation",
                degradation_applied=degradation_applied
            )
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
            return {
                "total_errors": 0,
                "resource_constraints": self.resource_constraints,
                "degradation_level": self.degradation_level
            }
        
        # Count by category
        category_counts = {}
        severity_counts = {}
        recent_errors = []
        recovery_stats = {"attempted": 0, "successful": 0}
        
        # Look at last hour of errors
        one_hour_ago = time.time() - 3600
        
        for error in self.error_history:
            # Category counts
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Severity counts
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Recovery stats
            if error.recovery_attempted:
                recovery_stats["attempted"] += 1
                if error.recovery_successful:
                    recovery_stats["successful"] += 1
            
            # Recent errors
            if error.timestamp > one_hour_ago:
                recent_errors.append({
                    "error_code": error.error_code,
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "timestamp": error.timestamp,
                    "recovery_attempted": error.recovery_attempted,
                    "recovery_successful": error.recovery_successful
                })
        
        # Calculate error rate (errors per minute in last hour)
        # If we have recent errors, calculate based on actual time span of errors
        if recent_errors:
            # Find the actual time span of the recent errors
            timestamps = [e["timestamp"] for e in recent_errors]
            oldest_error_time = min(timestamps)
            newest_error_time = max(timestamps)
            
            # Calculate time span in minutes
            time_span_seconds = max(60, newest_error_time - oldest_error_time)  # At least 1 minute
            time_span_minutes = time_span_seconds / 60
            
            error_rate = len(recent_errors) / time_span_minutes
        else:
            error_rate = 0
        
        # Update resource constraints based on current state
        self._update_resource_constraints(error_rate, recent_errors)
        
        return {
            "total_errors": total_errors,
            "category_counts": category_counts,
            "severity_counts": severity_counts,
            "recent_errors": recent_errors,
            "most_frequent": dict(sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "recovery_stats": recovery_stats,
            "error_rate_per_minute": error_rate,
            "resource_constraints": self.resource_constraints,
            "degradation_level": self.degradation_level
        }
    
    def _update_resource_constraints(self, error_rate: float, recent_errors: List[Dict]) -> None:
        """Update resource constraints based on current error patterns."""
        # Check for high error rate
        self.resource_constraints["high_error_rate"] = error_rate > 5.0  # More than 5 errors per minute
        
        # Check for memory pressure indicators
        memory_errors = [e for e in recent_errors if "resource" in e["category"].lower()]
        self.resource_constraints["memory_pressure"] = len(memory_errors) > 3
        
        # Update degradation level
        if self.resource_constraints["high_error_rate"] and self.resource_constraints["memory_pressure"]:
            self.degradation_level = 3  # Severe
        elif self.resource_constraints["high_error_rate"] or self.resource_constraints["memory_pressure"]:
            self.degradation_level = 2  # Moderate
        elif error_rate > 2.0:
            self.degradation_level = 1  # Light
        else:
            self.degradation_level = 0  # Normal
        
        self.resource_constraints["degraded_mode"] = self.degradation_level > 0
    
    def should_apply_graceful_degradation(self) -> bool:
        """Check if graceful degradation should be applied."""
        return self.resource_constraints["degraded_mode"]
    
    def get_degradation_config(self) -> Dict[str, Any]:
        """Get configuration for graceful degradation."""
        if self.degradation_level == 0:
            return {"enabled": False}
        
        base_config = {"enabled": True, "level": self.degradation_level}
        
        if self.degradation_level == 1:  # Light degradation
            return {
                **base_config,
                "max_context_size": 2000,
                "max_concurrent_requests": 3,
                "enable_caching": True,
                "reduce_logging": False
            }
        elif self.degradation_level == 2:  # Moderate degradation
            return {
                **base_config,
                "max_context_size": 1000,
                "max_concurrent_requests": 2,
                "enable_caching": True,
                "reduce_logging": True,
                "use_fallback_responses": True
            }
        else:  # Severe degradation
            return {
                **base_config,
                "max_context_size": 500,
                "max_concurrent_requests": 1,
                "enable_caching": True,
                "reduce_logging": True,
                "use_fallback_responses": True,
                "disable_ai_features": True
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
                    import asyncio
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