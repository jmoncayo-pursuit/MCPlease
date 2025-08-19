"""
Tests for Graceful Degradation Features

This module tests the graceful degradation capabilities of the error handling system,
including resource constraint detection and adaptive response strategies.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from src.mcplease_mcp.utils.error_handler import (
    MCPErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    get_error_handler,
    setup_error_handler
)
from src.utils.exceptions import (
    ResourceError,
    AIModelError,
    NetworkError
)


class TestGracefulDegradation:
    """Test graceful degradation features."""
    
    def setup_method(self):
        self.handler = MCPErrorHandler()
    
    @pytest.mark.asyncio
    async def test_resource_constraint_detection(self):
        """Test detection of resource constraints."""
        # Simulate high error rate with proper timestamps
        current_time = time.time()
        for i in range(10):
            await self.handler.handle_error(ResourceError(f"Memory error {i}"))
            # Set timestamps to be recent (within last minute)
            self.handler.error_history[-1].timestamp = current_time - (i * 5)  # Spread over last 45 seconds
        
        stats = self.handler.get_error_statistics()
        
        # Should detect high error rate and memory pressure
        assert stats["resource_constraints"]["high_error_rate"] is True
        assert stats["resource_constraints"]["memory_pressure"] is True
        assert stats["resource_constraints"]["degraded_mode"] is True
        assert stats["degradation_level"] >= 2  # Should be moderate or severe
    
    @pytest.mark.asyncio
    async def test_degradation_level_progression(self):
        """Test degradation level progression based on error patterns."""
        # Start with normal state
        assert self.handler.degradation_level == 0
        
        # Add some errors to trigger light degradation (3-5 errors per minute)
        current_time = time.time()
        for i in range(4):
            await self.handler.handle_error(NetworkError(f"Network error {i}"))
            # Set timestamps to create moderate error rate (recent)
            self.handler.error_history[-1].timestamp = current_time - (i * 10)  # Spread over last 30 seconds
        
        stats = self.handler.get_error_statistics()
        
        # Should be in light degradation mode
        assert stats["degradation_level"] >= 1
        
        # Add more severe errors for moderate degradation (resource errors)
        for i in range(5):
            await self.handler.handle_error(ResourceError(f"Resource error {i}"))
            # Set timestamps to create high error rate (recent)
            self.handler.error_history[-1].timestamp = current_time - (i * 3)  # Spread over last 12 seconds
        
        stats = self.handler.get_error_statistics()
        
        # Should be in moderate or severe degradation mode
        assert stats["degradation_level"] >= 2
    
    def test_degradation_config_levels(self):
        """Test degradation configuration for different levels."""
        # Test normal mode
        self.handler.degradation_level = 0
        config = self.handler.get_degradation_config()
        assert config["enabled"] is False
        
        # Test light degradation
        self.handler.degradation_level = 1
        config = self.handler.get_degradation_config()
        assert config["enabled"] is True
        assert config["level"] == 1
        assert config["max_context_size"] == 2000
        assert config["max_concurrent_requests"] == 3
        assert config["reduce_logging"] is False
        
        # Test moderate degradation
        self.handler.degradation_level = 2
        config = self.handler.get_degradation_config()
        assert config["enabled"] is True
        assert config["level"] == 2
        assert config["max_context_size"] == 1000
        assert config["max_concurrent_requests"] == 2
        assert config["use_fallback_responses"] is True
        
        # Test severe degradation
        self.handler.degradation_level = 3
        config = self.handler.get_degradation_config()
        assert config["enabled"] is True
        assert config["level"] == 3
        assert config["max_context_size"] == 500
        assert config["max_concurrent_requests"] == 1
        assert config["disable_ai_features"] is True
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_recovery(self):
        """Test resource cleanup recovery strategy."""
        error = ResourceError("Out of memory")
        context = Mock()
        context.details = {}
        
        # Mock error history to be large
        self.handler.error_history = [Mock() for _ in range(600)]
        
        success = await self.handler._recover_resource_cleanup(error, context)
        
        assert success is True
        assert context.details["resources_cleaned"] is True
        assert context.details["error_history_trimmed"] is True
        assert len(self.handler.error_history) == 100  # Should be trimmed
    
    @pytest.mark.asyncio
    async def test_resource_limit_recovery(self):
        """Test resource limit recovery strategy."""
        error = ResourceError("Resource exhausted")
        context = Mock()
        context.details = {}
        
        success = await self.handler._recover_resource_limit(error, context)
        
        assert success is True
        assert context.details["reduced_limits"] is True
        assert context.details["memory_efficient_mode"] is True
        assert "degradation_applied" in context.details
        assert len(context.details["degradation_applied"]) > 0
    
    def test_should_apply_graceful_degradation(self):
        """Test graceful degradation decision logic."""
        # Normal state - no degradation
        assert self.handler.should_apply_graceful_degradation() is False
        
        # Set degraded mode
        self.handler.resource_constraints["degraded_mode"] = True
        assert self.handler.should_apply_graceful_degradation() is True
    
    @pytest.mark.asyncio
    async def test_error_rate_calculation(self):
        """Test error rate calculation and thresholds."""
        # Add errors rapidly to simulate high error rate
        current_time = time.time()
        for i in range(8):
            error = NetworkError(f"Error {i}")
            await self.handler.handle_error(error)
            # Simulate errors happening within the last minute (recent)
            self.handler.error_history[-1].timestamp = current_time - (i * 5)  # Spread over last 35 seconds
        
        stats = self.handler.get_error_statistics()
        
        # Should detect high error rate (8 errors in less than 1 minute)
        assert stats["error_rate_per_minute"] > 5.0
        assert stats["resource_constraints"]["high_error_rate"] is True
    
    @pytest.mark.asyncio
    async def test_recovery_statistics(self):
        """Test recovery attempt and success statistics."""
        # Add errors with recovery
        await self.handler.handle_error(AIModelError("Model error 1"))
        await self.handler.handle_error(NetworkError("Network error 1"))
        await self.handler.handle_error(ResourceError("Resource error 1"))
        
        stats = self.handler.get_error_statistics()
        
        # Should have recovery statistics
        assert "recovery_stats" in stats
        assert stats["recovery_stats"]["attempted"] > 0
        assert stats["recovery_stats"]["successful"] >= 0
    
    @pytest.mark.asyncio
    async def test_memory_pressure_detection(self):
        """Test memory pressure detection from error patterns."""
        # Add multiple resource errors
        for i in range(5):
            await self.handler.handle_error(ResourceError(f"Memory error {i}"))
        
        stats = self.handler.get_error_statistics()
        
        # Should detect memory pressure
        assert stats["resource_constraints"]["memory_pressure"] is True
    
    def test_error_history_size_limit(self):
        """Test error history size management."""
        # Set a smaller max history for testing
        self.handler.max_history = 10
        
        # Add more errors than the limit
        for i in range(15):
            self.handler.error_history.append(Mock())
        
        # Trigger size management
        self.handler._store_error_history(Mock())
        
        # Should maintain size limit
        assert len(self.handler.error_history) <= self.handler.max_history


class TestIntegratedGracefulDegradation:
    """Test integrated graceful degradation with MCP components."""
    
    def setup_method(self):
        self.handler = setup_error_handler()
    
    @pytest.mark.asyncio
    async def test_ai_tool_fallback_integration(self):
        """Test AI tool fallback when degradation is active."""
        # Simulate degraded state
        self.handler.degradation_level = 2
        self.handler.resource_constraints["degraded_mode"] = True
        
        # Test that degradation config is available
        config = self.handler.get_degradation_config()
        assert config["enabled"] is True
        assert config["use_fallback_responses"] is True
    
    @pytest.mark.asyncio
    async def test_protocol_handler_degradation(self):
        """Test protocol handler behavior under degradation."""
        # Simulate high error rate to trigger degradation
        current_time = time.time()
        for i in range(10):
            await self.handler.handle_error(AIModelError(f"AI error {i}"))
            # Set timestamps to create high error rate (recent)
            self.handler.error_history[-1].timestamp = current_time - (i * 4)  # Spread over last 36 seconds
        
        # Force update of resource constraints
        stats = self.handler.get_error_statistics()
        
        # Check that degradation is active
        assert self.handler.should_apply_graceful_degradation() is True
        
        # Get degradation config for protocol handler
        config = self.handler.get_degradation_config()
        assert config["max_concurrent_requests"] <= 2
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test integration with performance monitoring."""
        # Add errors with different severities
        await self.handler.handle_error(AIModelError("Critical AI error"))
        await self.handler.handle_error(NetworkError("Network timeout"))
        await self.handler.handle_error(ResourceError("Memory exhausted"))
        
        stats = self.handler.get_error_statistics()
        
        # Should have comprehensive statistics
        assert "total_errors" in stats
        assert "category_counts" in stats
        assert "severity_counts" in stats
        assert "recovery_stats" in stats
        assert "error_rate_per_minute" in stats
        assert "resource_constraints" in stats
        assert "degradation_level" in stats


if __name__ == "__main__":
    pytest.main([__file__])