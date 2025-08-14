"""Custom exceptions for MCPlease MVP."""


class MCPleaseError(Exception):
    """Base exception for MCPlease errors."""
    pass


class ModelDownloadError(MCPleaseError):
    """Exception raised when model download fails."""
    pass


class ModelLoadError(MCPleaseError):
    """Exception raised when model loading fails."""
    pass


class InferenceError(MCPleaseError):
    """Exception raised during model inference."""
    pass


class EnvironmentError(MCPleaseError):
    """Exception raised for environment setup issues."""
    pass


class ConfigurationError(MCPleaseError):
    """Exception raised for configuration issues."""
    pass