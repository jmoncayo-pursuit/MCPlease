"""
Tests for MCPlease MCP Server Performance Monitoring System

This module tests the performance monitoring, request queuing,
and resource optimization features.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.mcplease_mcp.utils.performance import (
    PerformanceMonitor,
    RequestQueue,
    MemoryMonitor,
    MetricType,
    PerformanceMetric,
    RequestMetrics,
    ResourceSnapshot,
    get_performance_monitor,
    setup_performance_monitor,
    track_performance
)


class TestRequestQueue:
    """Test request queue functionality."""
    
    def setup_method(self):
        self.queue = RequestQueue(max_size=10, max_concurrent=3)
    
    @pytest.mark.asyncio
    async def test_basic_request_processing(self):
        """Test basic request processing."""
        async def test_request():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await self.queue.enqueue(test_request)
        assert result == "success"
        
        stats = self.queue.get_stats()
        assert stats["total_queued"] == 1
        assert stats["total_processed"] == 1
        assert stats["total_failed"] == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_request_limit(self):
        """Test concurrent request limiting."""
        results = []
        
        async def slow_request():
            await asyncio.sleep(0.2)
            results.append(time.time())
            return "done"
        
        # Start multiple requests
        tasks = [
            asyncio.create_task(self.queue.enqueue(slow_request))
            for _ in range(5)
        ]
        
        await asyncio.gather(*tasks)
        
        # Should have processed all requests
        stats = self.queue.get_stats()
        assert stats["total_processed"] == 5
        assert len(results) == 5
    
    @pytest.mark.asyncio
    async def test_queue_full_handling(self):
        """Test queue full condition."""
        # Fill the queue
        async def blocking_request():
            await asyncio.sleep(10)  # Very long request
        
        # Fill up the queue
        tasks = []
        for _ in range(10):  # max_size is 10
            tasks.append(asyncio.create_task(self.queue.enqueue(blocking_request)))
        
        # This should raise QueueFull
        with pytest.raises(asyncio.QueueFull):
            await self.queue.enqueue(blocking_request)
        
        # Cancel all tasks to clean up
        for task in tasks:
            task.cancel()
    
    @pytest.mark.asyncio
    async def test_request_timeout(self):
        """Test request timeout handling."""
        async def timeout_request():
            await asyncio.sleep(2)  # Longer than timeout
            return "should not reach here"
        
        with pytest.raises(asyncio.TimeoutError):
            await self.queue.enqueue(timeout_request, timeout=0.1)
        
        stats = self.queue.get_stats()
        assert stats["total_failed"] == 1
    
    @pytest.mark.asyncio
    async def test_queue_statistics(self):
        """Test queue statistics tracking."""
        async def quick_request():
            return "done"
        
        # Process several requests
        for _ in range(5):
            await self.queue.enqueue(quick_request)
        
        stats = self.queue.get_stats()
        assert stats["total_queued"] == 5
        assert stats["total_processed"] == 5
        assert stats["average_processing_time"] > 0
        assert stats["average_wait_time"] >= 0


class TestMemoryMonitor:
    """Test memory monitoring functionality."""
    
    def setup_method(self):
        self.monitor = MemoryMonitor(warning_threshold=0.7, critical_threshold=0.9)
    
    def test_memory_info_collection(self):
        """Test memory information collection."""
        memory_info = self.monitor.get_memory_info()
        
        required_keys = [
            "system_total_mb", "system_available_mb", "system_used_mb",
            "system_percent", "process_rss_mb", "process_vms_mb"
        ]
        
        for key in required_keys:
            assert key in memory_info
            assert isinstance(memory_info[key], (int, float))
            assert memory_info[key] >= 0
    
    def test_cleanup_callback_registration(self):
        """Test cleanup callback registration."""
        callback_called = False
        
        def cleanup_callback():
            nonlocal callback_called
            callback_called = True
        
        self.monitor.register_cleanup_callback(cleanup_callback)
        assert len(self.monitor.cleanup_callbacks) == 1
        
        # Trigger cleanup (simulate high memory usage)
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.percent = 95.0  # Above critical threshold
            
            result = self.monitor.check_memory_pressure()
            
            assert result["pressure_level"] == "critical"
            assert callback_called
    
    @patch('psutil.virtual_memory')
    def test_memory_pressure_levels(self, mock_memory):
        """Test different memory pressure levels."""
        # Normal memory usage
        mock_memory.return_value.percent = 50.0
        result = self.monitor.check_memory_pressure()
        assert result["pressure_level"] == "normal"
        
        # Warning level
        mock_memory.return_value.percent = 75.0  # Above 70% threshold
        result = self.monitor.check_memory_pressure()
        assert result["pressure_level"] == "warning"
        
        # Critical level
        mock_memory.return_value.percent = 95.0  # Above 90% threshold
        result = self.monitor.check_memory_pressure()
        assert result["pressure_level"] == "critical"


class TestPerformanceMonitor:
    """Test performance monitoring system."""
    
    def setup_method(self):
        self.monitor = PerformanceMonitor(collection_interval=0.1)  # Fast for testing
    
    @pytest.mark.asyncio
    async def test_monitor_start_stop(self):
        """Test starting and stopping the monitor."""
        assert not self.monitor.running
        
        await self.monitor.start()
        assert self.monitor.running
        assert self.monitor.collection_task is not None
        
        await self.monitor.stop()
        assert not self.monitor.running
    
    @pytest.mark.asyncio
    async def test_request_tracking(self):
        """Test request performance tracking."""
        request_id = "test_request_123"
        
        async with self.monitor.track_request(
            request_id=request_id,
            endpoint="/test",
            method="POST",
            user_id="test_user"
        ) as request_metrics:
            # Simulate some work
            await asyncio.sleep(0.1)
            request_metrics.status_code = 200
        
        # Check that metrics were recorded
        timing_metrics = [
            m for m in self.monitor.metrics 
            if m.metric_type == MetricType.REQUEST_TIMING
        ]
        
        assert len(timing_metrics) > 0
        timing_metric = timing_metrics[0]
        assert timing_metric.value >= 100  # At least 100ms
        assert timing_metric.tags["endpoint"] == "/test"
        assert timing_metric.tags["method"] == "POST"
        assert timing_metric.tags["user_id"] == "test_user"
    
    def test_metric_addition(self):
        """Test adding performance metrics."""
        self.monitor._add_metric(
            MetricType.RESOURCE_USAGE,
            "cpu_percent",
            75.5,
            "percent",
            {"resource": "cpu"},
            {"details": "test"}
        )
        
        assert len(self.monitor.metrics) == 1
        metric = self.monitor.metrics[0]
        assert metric.metric_type == MetricType.RESOURCE_USAGE
        assert metric.name == "cpu_percent"
        assert metric.value == 75.5
        assert metric.unit == "percent"
        assert metric.tags["resource"] == "cpu"
        assert metric.details["details"] == "test"
    
    @pytest.mark.asyncio
    async def test_performance_summary(self):
        """Test performance summary generation."""
        # Add some test metrics
        for i in range(10):
            self.monitor._add_metric(
                MetricType.REQUEST_TIMING,
                "test_endpoint_duration",
                100 + i * 10,  # 100, 110, 120, ... 190 ms
                "ms",
                {"endpoint": "test_endpoint"}
            )
        
        summary = self.monitor.get_performance_summary(time_window_seconds=3600)
        
        assert "request_timing" in summary
        timing_summary = summary["request_timing"]
        assert timing_summary["total_requests"] == 10
        assert timing_summary["average_duration_ms"] == 145.0  # Average of 100-190
        assert timing_summary["min_duration_ms"] == 100.0
        assert timing_summary["max_duration_ms"] == 190.0
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_health_status(self, mock_memory, mock_cpu):
        """Test health status assessment."""
        # Healthy system
        mock_cpu.return_value = 50.0
        mock_memory.return_value.percent = 60.0
        
        health = self.monitor.get_health_status()
        assert health["status"] == "healthy"
        assert len(health["issues"]) == 0
        
        # Warning conditions
        mock_cpu.return_value = 85.0  # Above 80% threshold
        health = self.monitor.get_health_status()
        assert health["status"] == "warning"
        assert len(health["issues"]) > 0
        assert any("High CPU usage" in issue for issue in health["issues"])
    
    @pytest.mark.asyncio
    async def test_slow_request_detection(self):
        """Test detection of slow requests."""
        self.monitor.response_time_warning_ms = 50.0  # Very low threshold for testing
        
        request_id = "slow_request_123"
        
        async with self.monitor.track_request(request_id, "/slow", "GET"):
            await asyncio.sleep(0.1)  # 100ms, above 50ms threshold
        
        # Should have logged a warning (we can't easily test logging here,
        # but we can check that the metric was recorded)
        timing_metrics = [
            m for m in self.monitor.metrics 
            if m.metric_type == MetricType.REQUEST_TIMING
        ]
        
        assert len(timing_metrics) > 0
        assert timing_metrics[0].value >= 50.0


class TestPerformanceDecorator:
    """Test performance tracking decorator."""
    
    @pytest.mark.asyncio
    async def test_async_function_tracking(self):
        """Test performance tracking for async functions."""
        @track_performance("test_endpoint", "GET")
        async def test_async_function():
            await asyncio.sleep(0.1)
            return "result"
        
        result = await test_async_function()
        assert result == "result"
        
        # Check that metrics were recorded
        monitor = get_performance_monitor()
        timing_metrics = [
            m for m in monitor.metrics 
            if m.metric_type == MetricType.REQUEST_TIMING
        ]
        
        assert len(timing_metrics) > 0
        metric = timing_metrics[0]
        assert metric.name == "test_endpoint_duration"
        assert metric.value >= 100  # At least 100ms
        assert metric.tags["endpoint"] == "test_endpoint"
        assert metric.tags["method"] == "GET"
    
    def test_sync_function_tracking(self):
        """Test performance tracking for sync functions."""
        @track_performance("sync_endpoint", "POST")
        def test_sync_function():
            time.sleep(0.1)
            return "sync_result"
        
        result = test_sync_function()
        assert result == "sync_result"
        
        # Check that metrics were recorded
        monitor = get_performance_monitor()
        timing_metrics = [
            m for m in monitor.metrics 
            if m.metric_type == MetricType.REQUEST_TIMING
        ]
        
        assert len(timing_metrics) > 0
        metric = timing_metrics[0]
        assert metric.name == "sync_endpoint_duration"
        assert metric.value >= 100  # At least 100ms
    
    def test_sync_function_error_tracking(self):
        """Test performance tracking when sync function raises error."""
        @track_performance("error_endpoint", "POST")
        def test_error_function():
            time.sleep(0.05)
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_error_function()
        
        # Check that metrics were still recorded
        monitor = get_performance_monitor()
        timing_metrics = [
            m for m in monitor.metrics 
            if m.metric_type == MetricType.REQUEST_TIMING
        ]
        
        assert len(timing_metrics) > 0
        metric = timing_metrics[0]
        assert metric.name == "error_endpoint_duration"
        assert "error" in metric.tags


class TestGlobalPerformanceMonitor:
    """Test global performance monitor functions."""
    
    def test_get_performance_monitor(self):
        """Test getting global performance monitor."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        # Should return same instance
        assert monitor1 is monitor2
    
    def test_setup_performance_monitor(self):
        """Test setting up global performance monitor."""
        monitor = setup_performance_monitor(collection_interval=30.0)
        
        assert monitor.collection_interval == 30.0
        
        # Should be the global instance
        global_monitor = get_performance_monitor()
        assert monitor is global_monitor


class TestPerformanceMetrics:
    """Test performance metric data structures."""
    
    def test_performance_metric_creation(self):
        """Test creating performance metrics."""
        metric = PerformanceMetric(
            timestamp=time.time(),
            metric_type=MetricType.REQUEST_TIMING,
            name="test_metric",
            value=123.45,
            unit="ms",
            tags={"endpoint": "test"},
            details={"request_id": "123"}
        )
        
        assert metric.metric_type == MetricType.REQUEST_TIMING
        assert metric.name == "test_metric"
        assert metric.value == 123.45
        assert metric.unit == "ms"
        assert metric.tags["endpoint"] == "test"
        assert metric.details["request_id"] == "123"
    
    def test_request_metrics_creation(self):
        """Test creating request metrics."""
        start_time = time.time()
        
        metrics = RequestMetrics(
            request_id="test_123",
            start_time=start_time,
            endpoint="/api/test",
            method="GET",
            user_id="user_123"
        )
        
        assert metrics.request_id == "test_123"
        assert metrics.start_time == start_time
        assert metrics.endpoint == "/api/test"
        assert metrics.method == "GET"
        assert metrics.user_id == "user_123"
        assert metrics.end_time is None
        assert metrics.duration_ms is None


if __name__ == "__main__":
    pytest.main([__file__])