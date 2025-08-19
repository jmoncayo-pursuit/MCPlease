"""
Custom exception classes for MCPlease MCP Server.

This module defines all custom exceptions used throughout the application,
providing consistent error handling and meaningful error messages.
"""

from typing import Optional, Dict, Any, List


class MCPleaseError(Exception):
    """Base exception class for all MCPlease errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class MCPProtocolError(MCPleaseError):
    """Raised when MCP protocol errors occur."""
    pass


class ValidationError(MCPleaseError):
    """Raised when data validation fails."""
    pass


class ConfigurationError(MCPleaseError):
    """Raised when configuration is invalid or missing."""
    pass


class AuthenticationError(MCPleaseError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(MCPleaseError):
    """Raised when authorization fails."""
    pass


class SessionError(MCPleaseError):
    """Raised when session operations fail."""
    pass


class TransportError(MCPleaseError):
    """Raised when transport layer errors occur."""
    pass


class AIModelError(MCPleaseError):
    """Raised when AI model operations fail."""
    pass


class ModelNotFoundError(MCPleaseError):
    """Raised when a requested AI model is not found."""
    pass


class ModelDownloadError(MCPleaseError):
    """Raised when AI model download fails."""
    pass


class ModelLoadError(MCPleaseError):
    """Raised when AI model loading fails."""
    pass


class ModelInferenceError(MCPleaseError):
    """Raised when AI model inference fails."""
    pass


class ToolError(MCPleaseError):
    """Raised when tool execution fails."""
    pass


class ToolNotFoundError(MCPleaseError):
    """Raised when a requested tool is not found."""
    pass


class ToolExecutionError(MCPleaseError):
    """Raised when tool execution fails."""
    pass


class ContextError(MCPleaseError):
    """Raised when context operations fail."""
    pass


class ContextNotFoundError(MCPleaseError):
    """Raised when a requested context is not found."""
    pass


class ContextExpiredError(MCPleaseError):
    """Raised when a context has expired."""
    pass


class ResourceError(MCPleaseError):
    """Raised when resource operations fail."""
    pass


class ResourceNotFoundError(MCPleaseError):
    """Raised when a requested resource is not found."""
    pass


class ResourceAccessError(MCPleaseError):
    """Raised when resource access is denied."""
    pass


class PromptError(MCPleaseError):
    """Raised when prompt operations fail."""
    pass


class PromptNotFoundError(MCPleaseError):
    """Raised when a requested prompt is not found."""
    pass


class PromptValidationError(MCPleaseError):
    """Raised when prompt validation fails."""
    pass


class SecurityError(MCPleaseError):
    """Base class for security-related errors."""
    pass


class RateLimitError(SecurityError):
    """Raised when rate limiting is exceeded."""
    pass


class ConnectionLimitError(SecurityError):
    """Raised when connection limits are exceeded."""
    pass


class NetworkPolicyError(SecurityError):
    """Raised when network policy violations occur."""
    pass


class PerformanceError(MCPleaseError):
    """Raised when performance issues occur."""
    pass


class MemoryError(MCPleaseError):
    """Raised when memory-related issues occur."""
    pass


class QueueError(MCPleaseError):
    """Raised when queue operations fail."""
    pass


class HealthError(MCPleaseError):
    """Raised when health check failures occur."""
    pass


class DeploymentError(MCPleaseError):
    """Raised when deployment operations fail."""
    pass


class DockerError(DeploymentError):
    """Raised when Docker operations fail."""
    pass


class NgrokError(DeploymentError):
    """Raised when ngrok operations fail."""
    pass


class SystemdError(DeploymentError):
    """Raised when systemd operations fail."""
    pass


class SSLError(MCPleaseError):
    """Raised when SSL/TLS operations fail."""
    pass


class CertificateError(SSLError):
    """Raised when certificate operations fail."""
    pass


class KeyError(SSLError):
    """Raised when key operations fail."""
    pass


class FileError(MCPleaseError):
    """Raised when file operations fail."""
    pass


class FileNotFoundError(FileError):
    """Raised when a requested file is not found."""
    pass


class FilePermissionError(FileError):
    """Raised when file permission issues occur."""
    pass


class FileCorruptionError(FileError):
    """Raised when file corruption is detected."""
    pass


class DatabaseError(MCPleaseError):
    """Raised when database operations fail."""
    pass


class ConnectionError(MCPleaseError):
    """Raised when connection operations fail."""
    pass


class TimeoutError(MCPleaseError):
    """Raised when operations timeout."""
    pass


class RetryError(MCPleaseError):
    """Raised when retry attempts are exhausted."""
    pass


class GracefulDegradationError(MCPleaseError):
    """Raised when graceful degradation fails."""
    pass


class FallbackError(MCPleaseError):
    """Raised when fallback mechanisms fail."""
    pass


class MonitoringError(MCPleaseError):
    """Raised when monitoring operations fail."""
    pass


class MetricsError(MonitoringError):
    """Raised when metrics operations fail."""
    pass


class AlertingError(MonitoringError):
    """Raised when alerting operations fail."""
    pass


class LoggingError(MCPleaseError):
    """Raised when logging operations fail."""
    pass


class SerializationError(MCPleaseError):
    """Raised when serialization/deserialization fails."""
    pass


class DeserializationError(SerializationError):
    """Raised when deserialization fails."""
    pass


class EncodingError(MCPleaseError):
    """Raised when encoding/decoding fails."""
    pass


class DecodingError(EncodingError):
    """Raised when decoding fails."""
    pass


class CompressionError(MCPleaseError):
    """Raised when compression/decompression fails."""
    pass


class DecompressionError(CompressionError):
    """Raised when decompression fails."""
    pass


class CacheError(MCPleaseError):
    """Raised when cache operations fail."""
    pass


class CacheMissError(CacheError):
    """Raised when a cache miss occurs."""
    pass


class CacheExpiredError(CacheError):
    """Raised when cached data has expired."""
    pass


class BackupError(MCPleaseError):
    """Raised when backup operations fail."""
    pass


class RestoreError(MCPleaseError):
    """Raised when restore operations fail."""
    pass


class MigrationError(MCPleaseError):
    """Raised when migration operations fail."""
    pass


class VersionError(MCPleaseError):
    """Raised when version compatibility issues occur."""
    pass


class DependencyError(MCPleaseError):
    """Raised when dependency issues occur."""
    pass


class CircularDependencyError(DependencyError):
    """Raised when circular dependencies are detected."""
    pass


class MissingDependencyError(DependencyError):
    """Raised when required dependencies are missing."""
    pass


class IncompatibleDependencyError(DependencyError):
    """Raised when dependencies are incompatible."""
    pass


class EnvironmentError(MCPleaseError):
    """Raised when environment-related issues occur."""
    pass


class PlatformError(EnvironmentError):
    """Raised when platform-specific issues occur."""
    pass


class ArchitectureError(EnvironmentError):
    """Raised when architecture-specific issues occur."""
    pass


class HardwareError(EnvironmentError):
    """Raised when hardware-related issues occur."""
    pass


class InsufficientResourcesError(HardwareError):
    """Raised when insufficient hardware resources are available."""
    pass


class ResourceExhaustionError(HardwareError):
    """Raised when hardware resources are exhausted."""
    pass


# Exception mapping for error codes
EXCEPTION_MAP = {
    "MCP_PROTOCOL_ERROR": MCPProtocolError,
    "VALIDATION_ERROR": ValidationError,
    "CONFIGURATION_ERROR": ConfigurationError,
    "AUTHENTICATION_ERROR": AuthenticationError,
    "AUTHORIZATION_ERROR": AuthorizationError,
    "SESSION_ERROR": SessionError,
    "TRANSPORT_ERROR": TransportError,
    "AI_MODEL_ERROR": AIModelError,
    "MODEL_NOT_FOUND": ModelNotFoundError,
    "MODEL_DOWNLOAD_ERROR": ModelDownloadError,
    "MODEL_LOAD_ERROR": ModelLoadError,
    "MODEL_INFERENCE_ERROR": ModelInferenceError,
    "TOOL_ERROR": ToolError,
    "TOOL_NOT_FOUND": ToolNotFoundError,
    "TOOL_EXECUTION_ERROR": ToolExecutionError,
    "CONTEXT_ERROR": ContextError,
    "CONTEXT_NOT_FOUND": ContextNotFoundError,
    "CONTEXT_EXPIRED": ContextExpiredError,
    "RESOURCE_ERROR": ResourceError,
    "RESOURCE_NOT_FOUND": ResourceNotFoundError,
    "RESOURCE_ACCESS_ERROR": ResourceAccessError,
    "PROMPT_ERROR": PromptError,
    "PROMPT_NOT_FOUND": PromptNotFoundError,
    "PROMPT_VALIDATION_ERROR": PromptValidationError,
    "SECURITY_ERROR": SecurityError,
    "RATE_LIMIT_ERROR": RateLimitError,
    "CONNECTION_LIMIT_ERROR": ConnectionLimitError,
    "NETWORK_POLICY_ERROR": NetworkPolicyError,
    "PERFORMANCE_ERROR": PerformanceError,
    "MEMORY_ERROR": MemoryError,
    "QUEUE_ERROR": QueueError,
    "HEALTH_ERROR": HealthError,
    "DEPLOYMENT_ERROR": DeploymentError,
    "DOCKER_ERROR": DockerError,
    "NGROK_ERROR": NgrokError,
    "SYSTEMD_ERROR": SystemdError,
    "SSL_ERROR": SSLError,
    "CERTIFICATE_ERROR": CertificateError,
    "KEY_ERROR": KeyError,
    "FILE_ERROR": FileError,
    "FILE_NOT_FOUND": FileNotFoundError,
    "FILE_PERMISSION_ERROR": FilePermissionError,
    "FILE_CORRUPTION_ERROR": FileCorruptionError,
    "DATABASE_ERROR": DatabaseError,
    "CONNECTION_ERROR": ConnectionError,
    "TIMEOUT_ERROR": TimeoutError,
    "RETRY_ERROR": RetryError,
    "GRACEFUL_DEGRADATION_ERROR": GracefulDegradationError,
    "FALLBACK_ERROR": FallbackError,
    "MONITORING_ERROR": MonitoringError,
    "METRICS_ERROR": MetricsError,
    "ALERTING_ERROR": AlertingError,
    "LOGGING_ERROR": LoggingError,
    "SERIALIZATION_ERROR": SerializationError,
    "DESERIALIZATION_ERROR": DeserializationError,
    "ENCODING_ERROR": EncodingError,
    "DECODING_ERROR": DecodingError,
    "COMPRESSION_ERROR": CompressionError,
    "DECOMPRESSION_ERROR": DecompressionError,
    "CACHE_ERROR": CacheError,
    "CACHE_MISS_ERROR": CacheMissError,
    "CACHE_EXPIRED_ERROR": CacheExpiredError,
    "BACKUP_ERROR": BackupError,
    "RESTORE_ERROR": RestoreError,
    "MIGRATION_ERROR": MigrationError,
    "VERSION_ERROR": VersionError,
    "DEPENDENCY_ERROR": DependencyError,
    "CIRCULAR_DEPENDENCY_ERROR": CircularDependencyError,
    "MISSING_DEPENDENCY_ERROR": MissingDependencyError,
    "INCOMPATIBLE_DEPENDENCY_ERROR": IncompatibleDependencyError,
    "ENVIRONMENT_ERROR": EnvironmentError,
    "PLATFORM_ERROR": PlatformError,
    "ARCHITECTURE_ERROR": ArchitectureError,
    "HARDWARE_ERROR": HardwareError,
    "INSUFFICIENT_RESOURCES_ERROR": InsufficientResourcesError,
    "RESOURCE_EXHAUSTION_ERROR": ResourceExhaustionError,
}


def get_exception_class(error_code: str) -> type:
    """Get exception class by error code."""
    return EXCEPTION_MAP.get(error_code, MCPleaseError)


def create_exception(error_code: str, message: str, details: Optional[Dict[str, Any]] = None) -> MCPleaseError:
    """Create exception instance by error code."""
    exception_class = get_exception_class(error_code)
    return exception_class(message, details)


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable."""
    retryable_errors = (
        ConnectionError,
        TimeoutError,
        TransportError,
        FileError,
        DatabaseError,
        CacheError,
        MonitoringError,
        LoggingError,
    )
    return isinstance(error, retryable_errors)


def is_security_error(error: Exception) -> bool:
    """Check if an error is security-related."""
    return isinstance(error, SecurityError)


def is_performance_error(error: Exception) -> bool:
    """Check if an error is performance-related."""
    return isinstance(error, PerformanceError)


def is_resource_error(error: Exception) -> bool:
    """Check if an error is resource-related."""
    resource_errors = (
        ResourceError,
        ResourceNotFoundError,
        ResourceAccessError,
        InsufficientResourcesError,
        ResourceExhaustionError,
    )
    return isinstance(error, resource_errors)
