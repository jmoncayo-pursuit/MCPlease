"""
MCPlease MCP Server - Health Monitoring and Diagnostics

This module provides comprehensive health monitoring, system diagnostics,
model integrity verification, and alerting capabilities.
"""

import asyncio
import time
import psutil
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, asdict
from enum import Enum
import structlog
from datetime import datetime, timedelta

from ..utils.logging import get_structured_logger
from ..utils.exceptions import ResourceError, ModelNotFoundError, ConfigurationError


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Types of system components to monitor."""
    AI_MODEL = "ai_model"
    MCP_SERVER = "mcp_server"
    NETWORK = "network"
    STORAGE = "storage"
    MEMORY = "memory"
    CPU = "cpu"
    SECURITY = "security"
    CONTEXT_MANAGER = "context_manager"
    TRANSPORT = "transport"


@dataclass
class HealthCheck:
    """Individual health check result."""
    component: ComponentType
    name: str
    status: HealthStatus
    message: str
    timestamp: float
    details: Dict[str, Any]
    duration_ms: float
    error: Optional[str] = None


@dataclass
class SystemHealth:
    """Overall system health status."""
    overall_status: HealthStatus
    timestamp: float
    checks: List[HealthCheck]
    summary: Dict[str, Any]
    uptime_seconds: float
    version: str


class HealthChecker:
    """Individual health check implementation."""
    
    def __init__(self, name: str, component: ComponentType, check_func: Callable[[], Awaitable[Dict[str, Any]]]):
        self.name = name
        self.component = component
        self.check_func = check_func
        self.last_result: Optional[HealthCheck] = None
        self.failure_count = 0
        self.success_count = 0
    
    async def run_check(self) -> HealthCheck:
        """Run the health check."""
        start_time = time.time()
        
        try:
            result = await self.check_func()
            duration_ms = (time.time() - start_time) * 1000
            
            status = HealthStatus(result.get("status", "unknown"))
            message = result.get("message", "Check completed")
            details = result.get("details", {})
            
            if status == HealthStatus.HEALTHY:
                self.success_count += 1
                self.failure_count = 0  # Reset failure count on success
            else:
                self.failure_count += 1
            
            check_result = HealthCheck(
                component=self.component,
                name=self.name,
                status=status,
                message=message,
                timestamp=time.time(),
                details=details,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.failure_count += 1
            
            check_result = HealthCheck(
                component=self.component,
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                timestamp=time.time(),
                details={"exception": str(e)},
                duration_ms=duration_ms,
                error=str(e)
            )
        
        self.last_result = check_result
        return check_result


class ModelIntegrityChecker:
    """AI model integrity verification."""
    
    def __init__(self, model_path: Path):
        self.model_path = model_path
        self.logger = get_structured_logger(__name__)
        self.known_checksums: Dict[str, str] = {}
        self.last_verification: Optional[float] = None
    
    async def verify_model_integrity(self) -> Dict[str, Any]:
        """Verify AI model file integrity."""
        if not self.model_path.exists():
            return {
                "status": "critical",
                "message": f"Model path does not exist: {self.model_path}",
                "details": {"path": str(self.model_path)}
            }
        
        try:
            # Check model files
            model_files = list(self.model_path.rglob("*.safetensors")) + \
                         list(self.model_path.rglob("*.bin")) + \
                         list(self.model_path.rglob("config.json"))
            
            if not model_files:
                return {
                    "status": "critical",
                    "message": "No model files found",
                    "details": {"path": str(self.model_path)}
                }
            
            # Verify checksums
            integrity_issues = []
            verified_files = 0
            
            for model_file in model_files:
                if model_file.stat().st_size == 0:
                    integrity_issues.append(f"Empty file: {model_file.name}")
                    continue
                
                # Calculate checksum for critical files
                if model_file.suffix in ['.json', '.safetensors']:
                    checksum = await self._calculate_file_checksum(model_file)
                    file_key = model_file.name
                    
                    if file_key in self.known_checksums:
                        if self.known_checksums[file_key] != checksum:
                            integrity_issues.append(f"Checksum mismatch: {model_file.name}")
                    else:
                        self.known_checksums[file_key] = checksum
                
                verified_files += 1
            
            self.last_verification = time.time()
            
            if integrity_issues:
                return {
                    "status": "warning",
                    "message": f"Model integrity issues detected: {len(integrity_issues)} issues",
                    "details": {
                        "issues": integrity_issues,
                        "verified_files": verified_files,
                        "total_files": len(model_files)
                    }
                }
            
            return {
                "status": "healthy",
                "message": f"Model integrity verified: {verified_files} files checked",
                "details": {
                    "verified_files": verified_files,
                    "last_verification": self.last_verification
                }
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Model integrity check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        
        # Read file in chunks to handle large files
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    async def repair_model(self) -> Dict[str, Any]:
        """Attempt to repair model issues."""
        # This would implement model repair logic
        # For now, just return a placeholder
        return {
            "status": "warning",
            "message": "Model repair not implemented",
            "details": {"action": "manual_intervention_required"}
        }


class SystemDiagnostics:
    """System diagnostics and monitoring."""
    
    def __init__(self):
        self.logger = get_structured_logger(__name__)
        self.start_time = time.time()
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        try:
            # CPU information
            cpu_info = {
                "count": psutil.cpu_count(),
                "percent": psutil.cpu_percent(interval=1),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_info = {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
                "swap": psutil.swap_memory()._asdict()
            }
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_info = {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": round((disk.used / disk.total) * 100, 2)
            }
            
            # Network information
            network_info = {
                "connections": len(psutil.net_connections()),
                "io_counters": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None
            }
            
            # Process information
            process = psutil.Process()
            process_info = {
                "pid": process.pid,
                "memory_mb": round(process.memory_info().rss / (1024**2), 2),
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            }
            
            return {
                "status": "healthy",
                "message": "System information collected",
                "details": {
                    "cpu": cpu_info,
                    "memory": memory_info,
                    "disk": disk_info,
                    "network": network_info,
                    "process": process_info,
                    "uptime_seconds": time.time() - self.start_time
                }
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Failed to collect system information: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def check_resource_limits(self) -> Dict[str, Any]:
        """Check if system is approaching resource limits."""
        try:
            issues = []
            warnings = []
            
            # Memory check
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                issues.append(f"Critical memory usage: {memory.percent:.1f}%")
            elif memory.percent > 80:
                warnings.append(f"High memory usage: {memory.percent:.1f}%")
            
            # CPU check
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 95:
                issues.append(f"Critical CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 85:
                warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            # Disk check
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 95:
                issues.append(f"Critical disk usage: {disk_percent:.1f}%")
            elif disk_percent > 85:
                warnings.append(f"High disk usage: {disk_percent:.1f}%")
            
            # Open files check
            try:
                process = psutil.Process()
                open_files = len(process.open_files())
                if open_files > 1000:
                    warnings.append(f"High number of open files: {open_files}")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            if issues:
                status = "critical"
                message = f"Critical resource issues: {len(issues)} issues"
            elif warnings:
                status = "warning"
                message = f"Resource warnings: {len(warnings)} warnings"
            else:
                status = "healthy"
                message = "Resource usage within normal limits"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "critical_issues": issues,
                    "warnings": warnings,
                    "memory_percent": memory.percent,
                    "cpu_percent": cpu_percent,
                    "disk_percent": disk_percent
                }
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Resource limit check failed: {str(e)}",
                "details": {"error": str(e)}
            }


class HealthMonitor:
    """Comprehensive health monitoring system."""
    
    def __init__(self, check_interval: float = 60.0):
        self.check_interval = check_interval
        self.checkers: Dict[str, HealthChecker] = {}
        self.model_integrity_checker: Optional[ModelIntegrityChecker] = None
        self.system_diagnostics = SystemDiagnostics()
        self.logger = get_structured_logger(__name__)
        self.running = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.alert_callbacks: List[Callable[[SystemHealth], Awaitable[None]]] = []
        self.health_history: List[SystemHealth] = []
        self.max_history = 1000
    
    def register_health_check(
        self,
        name: str,
        component: ComponentType,
        check_func: Callable[[], Awaitable[Dict[str, Any]]]
    ):
        """Register a health check."""
        self.checkers[name] = HealthChecker(name, component, check_func)
        self.logger.info(f"Registered health check: {name}")
    
    def register_alert_callback(self, callback: Callable[[SystemHealth], Awaitable[None]]):
        """Register an alert callback."""
        self.alert_callbacks.append(callback)
    
    def set_model_path(self, model_path: Path):
        """Set AI model path for integrity checking."""
        self.model_integrity_checker = ModelIntegrityChecker(model_path)
        
        # Register model integrity check
        self.register_health_check(
            "model_integrity",
            ComponentType.AI_MODEL,
            self.model_integrity_checker.verify_model_integrity
        )
    
    async def start_monitoring(self):
        """Start health monitoring."""
        if self.running:
            return
        
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Health monitoring started")
        
        # Register default health checks
        await self._register_default_checks()
    
    async def stop_monitoring(self):
        """Stop health monitoring."""
        if not self.running:
            return
        
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Health monitoring stopped")
    
    async def _register_default_checks(self):
        """Register default system health checks."""
        # System resource check
        self.register_health_check(
            "system_resources",
            ComponentType.CPU,
            self.system_diagnostics.check_resource_limits
        )
        
        # System info check
        self.register_health_check(
            "system_info",
            ComponentType.MEMORY,
            self.system_diagnostics.get_system_info
        )
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                health_status = await self.run_all_checks()
                
                # Store in history
                self.health_history.append(health_status)
                if len(self.health_history) > self.max_history:
                    self.health_history = self.health_history[-self.max_history:]
                
                # Send alerts if needed
                if health_status.overall_status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                    await self._send_alerts(health_status)
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    async def run_all_checks(self) -> SystemHealth:
        """Run all registered health checks."""
        start_time = time.time()
        check_results = []
        
        # Run all checks concurrently
        check_tasks = []
        for checker in self.checkers.values():
            check_tasks.append(checker.run_check())
        
        if check_tasks:
            check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
            
            # Handle exceptions
            valid_results = []
            for i, result in enumerate(check_results):
                if isinstance(result, Exception):
                    checker_name = list(self.checkers.keys())[i]
                    error_check = HealthCheck(
                        component=ComponentType.UNKNOWN,
                        name=checker_name,
                        status=HealthStatus.CRITICAL,
                        message=f"Check execution failed: {str(result)}",
                        timestamp=time.time(),
                        details={"error": str(result)},
                        duration_ms=0,
                        error=str(result)
                    )
                    valid_results.append(error_check)
                else:
                    valid_results.append(result)
            
            check_results = valid_results
        
        # Determine overall status
        overall_status = self._determine_overall_status(check_results)
        
        # Create summary
        summary = self._create_summary(check_results)
        
        return SystemHealth(
            overall_status=overall_status,
            timestamp=time.time(),
            checks=check_results,
            summary=summary,
            uptime_seconds=time.time() - self.system_diagnostics.start_time,
            version="0.1.0"  # Would be dynamically determined
        )
    
    def _determine_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Determine overall system health status."""
        if not checks:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in checks]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def _create_summary(self, checks: List[HealthCheck]) -> Dict[str, Any]:
        """Create health summary."""
        status_counts = {}
        component_status = {}
        
        for check in checks:
            # Count by status
            status = check.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Track component status
            component = check.component.value
            if component not in component_status:
                component_status[component] = check.status.value
            elif check.status == HealthStatus.CRITICAL:
                component_status[component] = HealthStatus.CRITICAL.value
            elif check.status == HealthStatus.WARNING and component_status[component] == HealthStatus.HEALTHY.value:
                component_status[component] = HealthStatus.WARNING.value
        
        return {
            "total_checks": len(checks),
            "status_counts": status_counts,
            "component_status": component_status,
            "failed_checks": [
                check.name for check in checks 
                if check.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]
            ]
        }
    
    async def _send_alerts(self, health_status: SystemHealth):
        """Send alerts for health issues."""
        for callback in self.alert_callbacks:
            try:
                await callback(health_status)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {str(e)}")
    
    async def get_health_report(self, include_history: bool = False) -> Dict[str, Any]:
        """Get comprehensive health report."""
        current_health = await self.run_all_checks()
        
        report = {
            "current_status": asdict(current_health),
            "monitoring_info": {
                "running": self.running,
                "check_interval": self.check_interval,
                "registered_checks": list(self.checkers.keys()),
                "alert_callbacks": len(self.alert_callbacks)
            }
        }
        
        if include_history:
            report["history"] = [
                asdict(health) for health in self.health_history[-10:]  # Last 10 entries
            ]
        
        return report
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics."""
        diagnostics = {
            "timestamp": time.time(),
            "system_info": await self.system_diagnostics.get_system_info(),
            "resource_limits": await self.system_diagnostics.check_resource_limits(),
        }
        
        # Add model diagnostics if available
        if self.model_integrity_checker:
            diagnostics["model_integrity"] = await self.model_integrity_checker.verify_model_integrity()
        
        return diagnostics


# Global health monitor instance
_global_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    global _global_health_monitor
    if _global_health_monitor is None:
        _global_health_monitor = HealthMonitor()
    return _global_health_monitor


def setup_health_monitor(check_interval: float = 60.0) -> HealthMonitor:
    """Setup and configure the global health monitor."""
    global _global_health_monitor
    _global_health_monitor = HealthMonitor(check_interval)
    return _global_health_monitor


# Convenience functions for common health checks
async def check_ai_model_health(model_manager) -> Dict[str, Any]:
    """Check AI model health."""
    try:
        if not hasattr(model_manager, 'model') or model_manager.model is None:
            return {
                "status": "critical",
                "message": "AI model not loaded",
                "details": {"model_loaded": False}
            }
        
        # Try a simple inference
        test_result = await model_manager.generate_text("test", max_tokens=1)
        
        return {
            "status": "healthy",
            "message": "AI model responding normally",
            "details": {
                "model_loaded": True,
                "test_inference": "successful"
            }
        }
        
    except Exception as e:
        return {
            "status": "critical",
            "message": f"AI model health check failed: {str(e)}",
            "details": {"error": str(e)}
        }


async def check_mcp_server_health(server) -> Dict[str, Any]:
    """Check MCP server health."""
    try:
        # Check if server is running
        if not hasattr(server, 'running') or not server.running:
            return {
                "status": "critical",
                "message": "MCP server not running",
                "details": {"server_running": False}
            }
        
        # Check transport status
        transport_status = {}
        if hasattr(server, 'transports'):
            for transport_name, transport in server.transports.items():
                transport_status[transport_name] = {
                    "active": getattr(transport, 'active', False),
                    "connections": getattr(transport, 'connection_count', 0)
                }
        
        return {
            "status": "healthy",
            "message": "MCP server running normally",
            "details": {
                "server_running": True,
                "transports": transport_status
            }
        }
        
    except Exception as e:
        return {
            "status": "critical",
            "message": f"MCP server health check failed: {str(e)}",
            "details": {"error": str(e)}
        }