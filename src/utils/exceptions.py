"""
MCPlease MCP Server - Custom Exceptions

This module defines custom exception classes for different error scenarios
in the MCPlease MCP server with comprehensive error categorization.
"""

from typing import Optional, Dict, Any


class MCPleaseError(Exception):
    """Base exception for MCPlease-specific errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class MCPProtocolError(MCPleaseError):
    """Raised when MCP protocol operations fail."""
    pass


class AIModelError(MCPleaseError):
    """Raised when AI model operations fail."""
    pass


class ConfigurationError(MCPleaseError):
    """Raised when configuration is invalid or missing."""
    pass


class SecurityError(MCPleaseError):
    """Raised when security validation fails."""
    pass


class NetworkError(MCPleaseError):
    """Raised when network operations fail."""
    pass


class ResourceError(MCPleaseError):
    """Raised when resource constraints are exceeded."""
    pass


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(SecurityError):
    """Raised when authorization fails."""
    pass


class RateLimitError(SecurityError):
    """Raised when rate limits are exceeded."""
    pass


class ModelNotFoundError(AIModelError):
    """Raised when AI model is not found or unavailable."""
    pass


class ModelLoadError(AIModelError):
    """Raised when AI model fails to load."""
    pass


class InferenceError(AIModelError):
    """Raised when AI inference fails."""
    pass


class ContextError(MCPleaseError):
    """Raised when context management fails."""
    pass


class TransportError(NetworkError):
    """Raised when transport layer fails."""
    pass


class ValidationError(MCPleaseError):
    """Raised when input validation fails."""
    pass


class PromptError(MCPleaseError):
    """Raised when prompt operations fail."""
    pass


# Legacy exceptions for backward compatibility
class ModelDownloadError(AIModelError):
    """Exception raised when model download fails."""
    pass


class EnvironmentError(ConfigurationError):
    """Exception raised for environment setup issues."""
    pass