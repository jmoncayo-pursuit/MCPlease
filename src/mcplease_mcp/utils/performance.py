"""
MCPlease MCP Server - Performance Monitoring and Optimization

This module provides comprehensive performance monitoring, request queuing,
concurrent request management, and resource optimization.
"""

import asyncio
import time
import psutil
import threading
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
from contextlib import asynccontextmanager
import weakref
from enum import Enum
import structlog

from ..utils.logging import get_performance_logger


class MetricType(Enum):
    """Types of performance metrics."""
    REQUEST_TIMING = "request_timing"
    RESOURCE_USAGE = "resource_usage"
    AI_INFERENCE = "ai_inference"
    QUEUE_METRICS = "queue_metrics"
    MEMORY_USAGE = "memory_usage"
    CONNECTION_METRICS = "connection_metrics"


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    timestamp: float
    metric_type: MetricType
    name: str
    value: float
    unit: str
    tags: Dict[str, str]
    details: Dict[str, Any]


@dataclass
class RequestMetrics:
    """Metrics for individual requests."""
    request_id: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    user_id: Optional[str] = None
    memory_start_mb: Optional[float] = None
    memory_end_mb: Optional[float] = None
    memory_delta_mb: Optional[float] = None


@dataclass
class ResourceSnapshot:
    """System resource usage snapshot."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    active_connections: int
    queue_size: int
    processing_requests: int


class RequestQueue:
    """Async request queue with priority and rate limiting."""
    
    def __init__(self, max_size: int = 1000, max_concurrent: int = 10):
        self.max_size = max_size
        self.max_concurrent = max_concurrent
        self.queue = asyncio.Queue(maxsize=max_size)
        self.processing = set()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.stats = {
            "total_queued": 0,
            "total_processed": 0,
            "total_failed": 0,
            "queue_full_count": 0,
            "average_wait_time": 0.0,
            "average_processing_time": 0.0
        }
        self.wait_times = deque(maxlen=1000)
        self.processing_times = deque(maxlen=1000)
    
    async def enqueue(self, request_func: Callable, priority: int = 0, timeout: float = 30.0):
        """Enqueue a request for processing."""
        if self.queue.full():
            self.stats["queue_full_count"] += 1
            raise asyncio.QueueFull("Request queue is full")
        
        request_item = {
            "func": request_func,
            "priority": priority,
            "enqueue_time": time.time(),
            "timeout": timeout
        }
        
        await self.queue.put(request_item)
        self.stats["total_queued"] += 1
        
        return await self._process_next()
    
    async def _process_next(self):
        """Process the next request in the queue."""
        async with self.semaphore:
            try:
                request_item = await self.queue.get()
                
                # Calculate wait time
                wait_time = time.time() - request_item["enqueue_time"]
                self.wait_times.append(wait_time)
                self.stats["average_wait_time"] = sum(self.wait_times) / len(self.wait_times)
                
                # Process request
                start_time = time.time()
                self.processing.add(id(request_item))
                
                try:
                    # Execute with timeout
                    result = await asyncio.wait_for(
                        request_item["func"](),
                        timeout=request_item["timeout"]
                    )
                    
                    # Calculate processing time
                    processing_time = time.time() - start_time
                    self.processing_times.append(processing_time)
                    self.stats["average_processing_time"] = sum(self.processing_times) / len(self.processing_times)
                    self.stats["total_processed"] += 1
                    
                    return result
                    
                except Exception as e:
                    self.stats["total_failed"] += 1
                    raise
                finally:
                    self.processing.discard(id(request_item))
                    self.queue.task_done()
                    
            except asyncio.TimeoutError:
                self.stats["total_failed"] += 1
                raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            **self.stats,
            "current_queue_size": self.queue.qsize(),
            "current_processing": len(self.processing),
            "max_size": self.max_size,
            "max_concurrent": self.max_concurrent
        }


class MemoryMonitor:
    """Memory usage monitoring and optimization."""
    
    def __init__(self, warning_threshold: float = 0.8, critical_threshold: float = 0.9):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.memory_history = deque(maxlen=100)
        self.cleanup_callbacks = []
        self.logger = structlog.get_logger(__name__)
    
    def register_cleanup_callback(self, callback: Callable[[], None]):
        """Register a callback for memory cleanup."""
        self.cleanup_callbacks.append(callback)
    
    def get_memory_info(self) -> Dict[str, float]:
        """Get current memory information."""
        memory = psutil.virtual_memory()
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "system_total_mb": memory.total / (1024 * 1024),
            "system_available_mb": memory.available / (1024 * 1024),
            "system_used_mb": memory.used / (1024 * 1024),
            "system_percent": memory.percent,
            "process_rss_mb": process_memory.rss / (1024 * 1024),
            "process_vms_mb": process_memory.vms / (1024 * 1024)
        }
    
    def check_memory_pressure(self) -> Dict[str, Any]:
        """Check for memory pressure and trigger cleanup if needed."""
        memory_info = self.get_memory_info()
        self.memory_history.append(memory_info)
        
        system_usage = memory_info["system_percent"] / 100.0
        pressure_level = "normal"
        actions_taken = []
        
        if system_usage >= self.critical_threshold:
            pressure_level = "critical"
            actions_taken = self._trigger_cleanup("critical")
            self.logger.warning(
                "Critical memory pressure detected",
                system_usage=system_usage,
                actions_taken=actions_taken
            )
        elif system_usage >= self.warning_threshold:
            pressure_level = "warning"
            actions_taken = self._trigger_cleanup("warning")
            self.logger.info(
                "Memory pressure warning",
                system_usage=system_usage,
                actions_taken=actions_taken
            )
        
        return {
            "pressure_level": pressure_level,
            "system_usage": system_usage,
            "memory_info": memory_info,
            "actions_taken": actions_taken
        }
    
    def _trigger_cleanup(self, level: str) -> List[str]:
        """Trigger memory cleanup callbacks."""
        actions_taken = []
        
        # Run garbage collection
        import gc
        collected = gc.collect()
        if collected > 0:
            actions_taken.append(f"garbage_collection_{collected}_objects")
        
        # Run registered cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
                actions_taken.append(f"cleanup_callback_{callback.__name__}")
            except Exception as e:
                self.logger.warning(
                    "Cleanup callback failed",
                    callback=callback.__name__,
                    error=str(e)
                )
        
        return actions_taken


class PerformanceMonitor:
    """Comprehensive performance monitoring system."""
    
    def __init__(self, collection_interval: float = 60.0):
        self.collection_interval = collection_interval
        self.metrics = deque(maxlen=10000)  # Keep last 10k metrics
        self.active_requests = {}
        self.request_queue = RequestQueue()
        self.memory_monitor = MemoryMonitor()
        self.logger = get_performance_logger()
        self.running = False
        self.collection_task = None
        
        # Performance counters
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        
        # Resource thresholds
        self.cpu_warning_threshold = 80.0
        self.memory_warning_threshold = 80.0
        self.response_time_warning_ms = 5000.0
    
    async def start(self):
        """Start performance monitoring."""
        if self.running:
            return
        
        self.running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        self.logger.info("Performance monitoring started")
    
    async def stop(self):
        """Stop performance monitoring."""
        if not self.running:
            return
        
        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Performance monitoring stopped")
    
    async def _collection_loop(self):
        """Main collection loop for system metrics."""
        while self.running:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in performance collection", error=str(e))
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self):
        """Collect system-wide performance metrics."""
        timestamp = time.time()
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self._add_metric(
            MetricType.RESOURCE_USAGE,
            "cpu_percent",
            cpu_percent,
            "percent",
            {"resource": "cpu"}
        )
        
        # Memory usage
        memory = psutil.virtual_memory()
        self._add_metric(
            MetricType.RESOURCE_USAGE,
            "memory_percent",
            memory.percent,
            "percent",
            {"resource": "memory"}
        )
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        self._add_metric(
            MetricType.RESOURCE_USAGE,
            "disk_percent",
            disk_percent,
            "percent",
            {"resource": "disk"}
        )
        
        # Queue metrics
        queue_stats = self.request_queue.get_stats()
        self._add_metric(
            MetricType.QUEUE_METRICS,
            "queue_size",
            queue_stats["current_queue_size"],
            "count",
            {"queue": "main"}
        )
        
        # Check for warnings
        await self._check_performance_warnings(cpu_percent, memory.percent)
        
        # Memory pressure check
        memory_pressure = self.memory_monitor.check_memory_pressure()
        if memory_pressure["pressure_level"] != "normal":
            self._add_metric(
                MetricType.MEMORY_USAGE,
                "memory_pressure",
                1.0 if memory_pressure["pressure_level"] == "critical" else 0.5,
                "level",
                {"pressure": memory_pressure["pressure_level"]}
            )
    
    async def _check_performance_warnings(self, cpu_percent: float, memory_percent: float):
        """Check for performance warnings and log them."""
        if cpu_percent > self.cpu_warning_threshold:
            self.logger.warning(
                "High CPU usage detected",
                cpu_percent=cpu_percent,
                threshold=self.cpu_warning_threshold
            )
        
        if memory_percent > self.memory_warning_threshold:
            self.logger.warning(
                "High memory usage detected",
                memory_percent=memory_percent,
                threshold=self.memory_warning_threshold
            )
    
    def _add_metric(
        self,
        metric_type: MetricType,
        name: str,
        value: float,
        unit: str,
        tags: Optional[Dict[str, str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Add a performance metric."""
        metric = PerformanceMetric(
            timestamp=time.time(),
            metric_type=metric_type,
            name=name,
            value=value,
            unit=unit,
            tags=tags or {},
            details=details or {}
        )
        
        self.metrics.append(metric)
        
        # Update counters and timers
        if metric_type == MetricType.REQUEST_TIMING:
            self.timers[name].append(value)
            if len(self.timers[name]) > 1000:  # Keep last 1000 values
                self.timers[name] = self.timers[name][-1000:]
    
    @asynccontextmanager
    async def track_request(
        self,
        request_id: str,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Context manager to track request performance."""
        start_time = time.time()
        memory_info = self.memory_monitor.get_memory_info()
        
        request_metrics = RequestMetrics(
            request_id=request_id,
            start_time=start_time,
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            memory_start_mb=memory_info["process_rss_mb"]
        )
        
        self.active_requests[request_id] = request_metrics
        
        try:
            yield request_metrics
        finally:
            # Complete request tracking
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            memory_info_end = self.memory_monitor.get_memory_info()
            
            request_metrics.end_time = end_time
            request_metrics.duration_ms = duration_ms
            request_metrics.memory_end_mb = memory_info_end["process_rss_mb"]
            request_metrics.memory_delta_mb = (
                request_metrics.memory_end_mb - request_metrics.memory_start_mb
            )
            
            # Add timing metric
            self._add_metric(
                MetricType.REQUEST_TIMING,
                f"{endpoint or 'unknown'}_duration",
                duration_ms,
                "ms",
                {
                    "endpoint": endpoint or "unknown",
                    "method": method or "unknown",
                    "user_id": user_id or "anonymous"
                },
                {"request_id": request_id}
            )
            
            # Log performance data
            self.logger.request_timing(
                endpoint=endpoint or "unknown",
                method=method or "unknown",
                duration_ms=duration_ms,
                status_code=getattr(request_metrics, 'status_code', 200),
                user_id=user_id
            )
            
            # Check for slow requests
            if duration_ms > self.response_time_warning_ms:
                self.logger.warning(
                    "Slow request detected",
                    request_id=request_id,
                    duration_ms=duration_ms,
                    threshold_ms=self.response_time_warning_ms,
                    endpoint=endpoint,
                    method=method
                )
            
            # Remove from active requests
            self.active_requests.pop(request_id, None)
    
    def get_performance_summary(self, time_window_seconds: int = 3600) -> Dict[str, Any]:
        """Get performance summary for the specified time window."""
        cutoff_time = time.time() - time_window_seconds
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"message": "No metrics available for the specified time window"}
        
        # Group metrics by type
        metrics_by_type = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_type[metric.metric_type].append(metric)
        
        summary = {
            "time_window_seconds": time_window_seconds,
            "total_metrics": len(recent_metrics),
            "active_requests": len(self.active_requests),
            "queue_stats": self.request_queue.get_stats(),
        }
        
        # Request timing summary
        if MetricType.REQUEST_TIMING in metrics_by_type:
            timing_metrics = metrics_by_type[MetricType.REQUEST_TIMING]
            durations = [m.value for m in timing_metrics]
            
            summary["request_timing"] = {
                "total_requests": len(durations),
                "average_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "p95_duration_ms": self._percentile(durations, 95),
                "p99_duration_ms": self._percentile(durations, 99)
            }
        
        # Resource usage summary
        if MetricType.RESOURCE_USAGE in metrics_by_type:
            resource_metrics = metrics_by_type[MetricType.RESOURCE_USAGE]
            
            cpu_metrics = [m.value for m in resource_metrics if m.name == "cpu_percent"]
            memory_metrics = [m.value for m in resource_metrics if m.name == "memory_percent"]
            
            if cpu_metrics:
                summary["cpu_usage"] = {
                    "average_percent": sum(cpu_metrics) / len(cpu_metrics),
                    "max_percent": max(cpu_metrics),
                    "samples": len(cpu_metrics)
                }
            
            if memory_metrics:
                summary["memory_usage"] = {
                    "average_percent": sum(memory_metrics) / len(memory_metrics),
                    "max_percent": max(memory_metrics),
                    "samples": len(memory_metrics)
                }
        
        return summary
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        memory_info = self.memory_monitor.get_memory_info()
        cpu_percent = psutil.cpu_percent()
        queue_stats = self.request_queue.get_stats()
        
        # Determine health status
        health_issues = []
        
        if cpu_percent > self.cpu_warning_threshold:
            health_issues.append(f"High CPU usage: {cpu_percent:.1f}%")
        
        if memory_info["system_percent"] > self.memory_warning_threshold:
            health_issues.append(f"High memory usage: {memory_info['system_percent']:.1f}%")
        
        if queue_stats["current_queue_size"] > queue_stats["max_size"] * 0.8:
            health_issues.append("Request queue nearly full")
        
        if len(self.active_requests) > 50:  # Arbitrary threshold
            health_issues.append("High number of active requests")
        
        status = "healthy" if not health_issues else "warning" if len(health_issues) < 3 else "critical"
        
        return {
            "status": status,
            "issues": health_issues,
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_info["system_percent"],
                "active_requests": len(self.active_requests),
                "queue_size": queue_stats["current_queue_size"],
                "total_processed": queue_stats["total_processed"],
                "total_failed": queue_stats["total_failed"]
            }
        }


# Global performance monitor instance
_global_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    return _global_performance_monitor


def setup_performance_monitor(collection_interval: float = 60.0) -> PerformanceMonitor:
    """Setup and configure the global performance monitor."""
    global _global_performance_monitor
    _global_performance_monitor = PerformanceMonitor(collection_interval)
    return _global_performance_monitor


# Convenience decorators
def track_performance(endpoint: str, method: str = "unknown"):
    """Decorator to track function performance."""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                monitor = get_performance_monitor()
                request_id = f"{endpoint}_{int(time.time() * 1000)}"
                
                async with monitor.track_request(request_id, endpoint, method):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                # For sync functions, we'll just time them
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    monitor = get_performance_monitor()
                    monitor._add_metric(
                        MetricType.REQUEST_TIMING,
                        f"{endpoint}_duration",
                        duration_ms,
                        "ms",
                        {"endpoint": endpoint, "method": method}
                    )
                    
                    return result
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    monitor = get_performance_monitor()
                    monitor._add_metric(
                        MetricType.REQUEST_TIMING,
                        f"{endpoint}_duration",
                        duration_ms,
                        "ms",
                        {"endpoint": endpoint, "method": method, "error": str(e)}
                    )
                    raise
            return sync_wrapper
    return decorator