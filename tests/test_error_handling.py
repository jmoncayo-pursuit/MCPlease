"""
Tests for MCPlease MCP Server Error Handling System

This module tests the comprehensive error handling, categorization,
and recovery mechanisms.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.mcplease_mcp.utils.error_handler import (
    MCPErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    get_error_handler,
    setup_error_handler,
    handle_error,
    error_context
)
from src.utils.exceptions import (
    MCPleaseError,
    MCPProtocolError,
    AIModelError,
    SecurityError,
    NetworkError,
    ConfigurationError,
    ResourceError,
    AuthenticationError,
    ModelNotFoundError,
    InferenceError
)


class TestErrorCategorization:
    """Test error categorization logic."""
    
    def setup_method(self):
        self.handler = MCPErrorHandler()
    
    def test_categorize_mcp_protocol_error(self):
        """Test MCP protocol error categorization."""
        error = MCPProtocolError("Invalid MCP message")
        category = self.handler.categorize_error(error)
        assert category == ErrorCategory.PROTOCOL
    
    def test_categorize_ai_model_error(self):
        """Test AI model error categorization."""
        error = AIModelError("Model inference failed")
        category = self.handler.categorize_error(error)
        assert category == ErrorCategory.AI_MODEL
    
    def test_categorize_security_error(self):
        """Test security error categorization."""
        error = SecurityError("Authentication failed")
        category = self.handler.categorize_error(error)
        assert category == ErrorCategory.SECURITY
    
    def test_categorize_network_error(self):
        """Test network error categorization."""
        error = NetworkError("Connection timeout")
        category = self.handler.categorize_error(error)
        assert category == ErrorCategory.NETWORK
    
    def test_categorize_configuration_error(self):
        """Test configuration error categorization."""
        error = ConfigurationError("Invalid config value")
        category = self.handler.categorize_error(error)
        assert category == ErrorCategory.CONFIGURATION
    
    def test_categorize_resource_error(self):
        """Test resource error categorization."""
        error = ResourceError("Out of memory")
        category = self.handler.categorize_error(error)
        assert category == ErrorCategory.RESOURCE
    
    def test_categorize_generic_errors(self):
        """Test categorization of generic Python errors."""
        # Connection errors should be network
        error = ConnectionError("Connection refused")
        category = self.handler.categorize_error(error)
        assert category == ErrorCategory.NETWORK
        
        # Memory errors should be resource
        error = MemoryError("Out of memory")
        category = self.handler.categorize_error(error)
        assert category == ErrorCategory.RESOURCE
        
        # Value errors should be user input
        error = ValueError("Invalid input")
        category = self.handler.categorize_error(error)
        assert category == ErrorCategory.USER_INPUT
        
        # Unknown errors should be system
        error = RuntimeError("Unknown error")
        category = self.handler.categorize_error(error)
        assert category == ErrorCategory.SYSTEM


class TestErrorSeverity:
    """Test error severity determination."""
    
    def setup_method(self):
        self.handler = MCPErrorHandler()
    
    def test_critical_severity_errors(self):
        """Test critical severity error detection."""
        # Memory errors are critical
        error = MemoryError("Out of memory")
        category = self.handler.categorize_error(error)
        severity = self.handler.determine_severity(error, category)
        assert severity == ErrorSeverity.CRITICAL
        
        # System exit is critical
        error = SystemExit(1)
        category = self.handler.categorize_error(error)
        severity = self.handler.determine_severity(error, category)
        assert severity == ErrorSeverity.CRITICAL
    
    def test_high_severity_errors(self):
        """Test high severity error detection."""
        # Security errors are high
        error = SecurityError("Authentication failed")
        category = self.handler.categorize_error(error)
        severity = self.handler.determine_severity(error, category)
        assert severity == ErrorSeverity.HIGH
        
        # Protocol errors are high
        error = MCPProtocolError("Invalid protocol")
        category = self.handler.categorize_error(error)
        severity = self.handler.determine_severity(error, category)
        assert severity == ErrorSeverity.HIGH
        
        # Model not found is high
        error = ModelNotFoundError("Model not found")
        category = self.handler.categorize_error(error)
        severity = self.handler.determine_severity(error, category)
        assert severity == ErrorSeverity.HIGH
    
    def test_medium_severity_errors(self):
        """Test medium severity error detection."""
        # AI model errors are typically medium
        error = InferenceError("Inference failed")
        category = self.handler.categorize_error(error)
        severity = self.handler.determine_severity(error, category)
        assert severity == ErrorSeverity.MEDIUM
        
        # Network errors are medium
        error = NetworkError("Connection timeout")
        category = self.handler.categorize_error(error)
        severity = self.handler.determine_severity(error, category)
        assert severity == ErrorSeverity.MEDIUM
    
    def test_low_severity_errors(self):
        """Test low severity error detection."""
        # Configuration errors are low
        error = ConfigurationError("Invalid config")
        category = self.handler.categorize_error(error)
        severity = self.handler.determine_severity(error, category)
        assert severity == ErrorSeverity.LOW
        
        # User input errors are low
        error = ValueError("Invalid input")
        category = self.handler.categorize_error(error)
        severity = self.handler.determine_severity(error, category)
        assert severity == ErrorSeverity.LOW


class TestErrorCodeGeneration:
    """Test error code generation."""
    
    def setup_method(self):
        self.handler = MCPErrorHandler()
    
    def test_error_code_format(self):
        """Test error code format."""
        error = AIModelError("Model failed")
        category = ErrorCategory.AI_MODEL
        error_code = self.handler.generate_error_code(category, error)
        
        # Should be in format: CATEGORY-ERRORTYPE-HASH
        parts = error_code.split('-')
        assert len(parts) == 3
        assert parts[0] == "AI_"  # Category prefix
        assert parts[1] == "AIMODELERR"  # Error type (truncated)
        assert len(parts[2]) == 4  # Hash should be 4 digits
        assert parts[2].isdigit()
    
    def test_error_code_consistency(self):
        """Test that same errors generate same codes."""
        error1 = AIModelError("Model failed")
        error2 = AIModelError("Model failed")
        category = ErrorCategory.AI_MODEL
        
        code1 = self.handler.generate_error_code(category, error1)
        code2 = self.handler.generate_error_code(category, error2)
        
        assert code1 == code2
    
    def test_error_code_uniqueness(self):
        """Test that different errors generate different codes."""
        error1 = AIModelError("Model failed")
        error2 = AIModelError("Different error")
        category = ErrorCategory.AI_MODEL
        
        code1 = self.handler.generate_error_code(category, error1)
        code2 = self.handler.generate_error_code(category, error2)
        
        assert code1 != code2


class TestErrorHandling:
    """Test comprehensive error handling."""
    
    def setup_method(self):
        self.handler = MCPErrorHandler()
    
    @pytest.mark.asyncio
    async def test_basic_error_handling(self):
        """Test basic error handling flow."""
        error = AIModelError("Model inference failed")
        context = {"model": "gpt-oss-20b", "input_tokens": 100}
        
        error_context = await self.handler.handle_error(
            error,
            context=context,
            user_id="test_user",
            session_id="test_session",
            request_id="test_request"
        )
        
        assert error_context.category == ErrorCategory.AI_MODEL
        assert error_context.severity == ErrorSeverity.MEDIUM
        assert error_context.message == "Model inference failed"
        assert error_context.details == context
        assert error_context.user_id == "test_user"
        assert error_context.session_id == "test_session"
        assert error_context.request_id == "test_request"
        assert error_context.stack_trace is not None
    
    @pytest.mark.asyncio
    async def test_error_recovery_attempt(self):
        """Test error recovery attempts."""
        # Mock a recovery strategy
        async def mock_recovery(error, context):
            return True
        
        self.handler.recovery_strategies[ErrorCategory.AI_MODEL] = [mock_recovery]
        
        error = AIModelError("Model failed")
        error_context = await self.handler.handle_error(error, attempt_recovery=True)
        
        assert error_context.recovery_attempted is True
        assert error_context.recovery_successful is True
    
    @pytest.mark.asyncio
    async def test_error_recovery_failure(self):
        """Test error recovery failure handling."""
        # Mock a failing recovery strategy
        async def mock_failing_recovery(error, context):
            return False
        
        self.handler.recovery_strategies[ErrorCategory.AI_MODEL] = [mock_failing_recovery]
        
        error = AIModelError("Model failed")
        error_context = await self.handler.handle_error(error, attempt_recovery=True)
        
        assert error_context.recovery_attempted is True
        assert error_context.recovery_successful is False
    
    @pytest.mark.asyncio
    async def test_error_history_tracking(self):
        """Test error history tracking."""
        error1 = AIModelError("First error")
        error2 = NetworkError("Second error")
        
        await self.handler.handle_error(error1)
        await self.handler.handle_error(error2)
        
        assert len(self.handler.error_history) == 2
        assert self.handler.error_history[0].category == ErrorCategory.AI_MODEL
        assert self.handler.error_history[1].category == ErrorCategory.NETWORK
    
    @pytest.mark.asyncio
    async def test_error_count_tracking(self):
        """Test error count tracking."""
        error = AIModelError("Repeated error")
        
        # Handle same error multiple times
        for _ in range(3):
            await self.handler.handle_error(error)
        
        # Should have one error code with count of 3
        assert len(self.handler.error_counts) == 1
        error_code = list(self.handler.error_counts.keys())[0]
        assert self.handler.error_counts[error_code] == 3


class TestRecoveryStrategies:
    """Test error recovery strategies."""
    
    def setup_method(self):
        self.handler = MCPErrorHandler()
    
    @pytest.mark.asyncio
    async def test_ai_model_fallback_recovery(self):
        """Test AI model fallback recovery."""
        error = AIModelError("Model failed")
        context = ErrorContext(
            timestamp=time.time(),
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.AI_MODEL,
            error_code="TEST-001",
            message="Test error",
            details={}
        )
        
        success = await self.handler._recover_ai_model_fallback(error, context)
        assert success is True
        assert context.details["use_fallback"] is True
    
    @pytest.mark.asyncio
    async def test_network_retry_recovery(self):
        """Test network retry recovery."""
        error = NetworkError("Connection failed")
        context = ErrorContext(
            timestamp=time.time(),
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.NETWORK,
            error_code="TEST-002",
            message="Test error",
            details={}
        )
        
        success = await self.handler._recover_network_retry(error, context)
        assert success is True
        assert context.details["retry_count"] == 1
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_recovery(self):
        """Test resource cleanup recovery."""
        error = ResourceError("Out of memory")
        context = ErrorContext(
            timestamp=time.time(),
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.RESOURCE,
            error_code="TEST-003",
            message="Test error",
            details={}
        )
        
        success = await self.handler._recover_resource_cleanup(error, context)
        assert success is True
        assert context.details["resources_cleaned"] is True


class TestErrorStatistics:
    """Test error statistics and monitoring."""
    
    def setup_method(self):
        self.handler = MCPErrorHandler()
    
    @pytest.mark.asyncio
    async def test_error_statistics_empty(self):
        """Test error statistics with no errors."""
        stats = self.handler.get_error_statistics()
        assert stats["total_errors"] == 0
    
    @pytest.mark.asyncio
    async def test_error_statistics_with_errors(self):
        """Test error statistics with various errors."""
        # Add some errors
        await self.handler.handle_error(AIModelError("AI error"))
        await self.handler.handle_error(NetworkError("Network error"))
        await self.handler.handle_error(AIModelError("Another AI error"))
        
        stats = self.handler.get_error_statistics()
        
        assert stats["total_errors"] == 3
        assert "ai_model" in stats["category_counts"]
        assert "network" in stats["category_counts"]
        assert stats["category_counts"]["ai_model"] == 2
        assert stats["category_counts"]["network"] == 1
        
        # Check severity counts
        assert "medium" in stats["severity_counts"]
        assert stats["severity_counts"]["medium"] == 3
    
    def test_clear_error_history(self):
        """Test clearing error history."""
        # Add some errors first
        self.handler.error_history.append(Mock())
        self.handler.error_counts["TEST"] = 5
        
        self.handler.clear_error_history()
        
        assert len(self.handler.error_history) == 0
        assert len(self.handler.error_counts) == 0


class TestErrorContext:
    """Test error context manager."""
    
    def setup_method(self):
        self.handler = MCPErrorHandler()
    
    def test_error_context_success(self):
        """Test error context manager with no errors."""
        with self.handler.error_context(context={"test": "value"}):
            # No error should occur
            pass
    
    def test_error_context_with_error(self):
        """Test error context manager with error."""
        with pytest.raises(ValueError):
            with self.handler.error_context(
                context={"test": "value"},
                user_id="test_user",
                suppress_errors=False
            ):
                raise ValueError("Test error")
    
    def test_error_context_suppress_errors(self):
        """Test error context manager with error suppression."""
        with self.handler.error_context(suppress_errors=True):
            raise ValueError("This should be suppressed")
        # Should not raise


class TestGlobalErrorHandler:
    """Test global error handler functions."""
    
    def test_get_error_handler(self):
        """Test getting global error handler."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        # Should return same instance
        assert handler1 is handler2
    
    def test_setup_error_handler(self):
        """Test setting up global error handler."""
        mock_logger = Mock()
        handler = setup_error_handler(mock_logger)
        
        assert handler.logger is mock_logger
        
        # Should be the global instance
        global_handler = get_error_handler()
        assert handler is global_handler
    
    @pytest.mark.asyncio
    async def test_handle_error_function(self):
        """Test global handle_error function."""
        error = AIModelError("Test error")
        context = {"test": "value"}
        
        error_context = await handle_error(
            error,
            context=context,
            user_id="test_user"
        )
        
        assert error_context.category == ErrorCategory.AI_MODEL
        assert error_context.details == context
        assert error_context.user_id == "test_user"
    
    def test_error_context_function(self):
        """Test global error_context function."""
        with pytest.raises(ValueError):
            with error_context(context={"test": "value"}):
                raise ValueError("Test error")


if __name__ == "__main__":
    pytest.main([__file__])