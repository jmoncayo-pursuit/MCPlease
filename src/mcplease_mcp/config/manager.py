"""Configuration management for MCPlease MCP Server."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class MCPConfig(BaseModel):
    """Main MCP server configuration."""
    
    # Server settings
    host: str = Field(default="127.0.0.1", description="Server host address")
    port: int = Field(default=8000, description="Server port")
    transport: List[str] = Field(default=["stdio"], description="Transport protocols")
    max_workers: int = Field(default=4, description="Maximum worker processes")
    
    # AI model settings
    ai_model: str = Field(default="disabled", description="AI model name")
    memory_limit: str = Field(default="2GB", description="Memory limit for AI model")
    quantization: str = Field(default="int8", description="Model quantization")
    device: str = Field(default="auto", description="Device for AI model")
    
    # Security settings
    security_level: str = Field(default="basic", description="Security level")
    require_auth: bool = Field(default=False, description="Require authentication")
    enable_tls: bool = Field(default=False, description="Enable TLS/SSL")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # Hardware-specific settings
    hardware_profile: Optional[str] = Field(default=None, description="Hardware optimization profile")
    is_raspberry_pi: bool = Field(default=False, description="Running on Raspberry Pi")
    enable_ngrok: bool = Field(default=False, description="Enable ngrok tunneling")
    
    class Config:
        """Pydantic configuration."""
        extra = "allow"  # Allow additional fields


@dataclass
class HardwareInfo:
    """Hardware information detected during installation."""
    
    memory_gb: float
    cpu_count: int
    architecture: str
    platform: str
    is_raspberry_pi: bool = False
    gpu_available: bool = False
    gpu_type: Optional[str] = None
    gpu_memory_gb: float = 0.0
    optimization_profile: str = "default"


class ConfigManager:
    """Manages configuration for MCPlease MCP Server."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            project_root: Project root directory (auto-detected if None)
        """
        self.project_root = project_root or self._find_project_root()
        self.config_dir = self.project_root / ".mcplease"
        self.config_file = self.config_dir / "config.json"
        self.env_file = self.project_root / ".env"
        
        self._config: Optional[MCPConfig] = None
        self._hardware_info: Optional[HardwareInfo] = None
    
    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        # Start from current file and walk up
        current = Path(__file__).parent
        
        while current != current.parent:
            # Look for project markers
            if any((current / marker).exists() for marker in ["pyproject.toml", "setup.py", ".git"]):
                return current
            current = current.parent
        
        # Fallback to current working directory
        return Path.cwd()
    
    def load_config(self) -> MCPConfig:
        """Load configuration from files and environment.
        
        Returns:
            Loaded configuration
        """
        if self._config is not None:
            return self._config
        
        # Start with default config
        config_data = {}
        
        # Load from JSON config file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    file_config = json.load(f)
                    config_data.update(self._flatten_config(file_config))
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
        
        # Override with environment variables
        env_config = self._load_env_config()
        config_data.update(env_config)
        
        # Create and cache config
        self._config = MCPConfig(**config_data)
        return self._config
    
    def _flatten_config(self, config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested configuration dictionary.
        
        Args:
            config: Nested configuration dictionary
            prefix: Key prefix for flattening
            
        Returns:
            Flattened configuration dictionary
        """
        flattened = {}
        
        for key, value in config.items():
            full_key = f"{prefix}_{key}" if prefix else key
            
            if isinstance(value, dict) and key not in ["hardware", "installation"]:
                # Recursively flatten nested dicts (except metadata)
                flattened.update(self._flatten_config(value, full_key))
            else:
                # Map nested keys to flat keys
                if key == "host" and prefix == "server":
                    flattened["host"] = value
                elif key == "port" and prefix == "server":
                    flattened["port"] = value
                elif key == "transport" and prefix == "server":
                    flattened["transport"] = value
                elif key == "max_workers" and prefix == "server":
                    flattened["max_workers"] = value
                elif key == "model" and prefix == "ai":
                    flattened["ai_model"] = value
                elif key == "memory_limit" and prefix == "ai":
                    flattened["memory_limit"] = value
                elif key == "quantization" and prefix == "ai":
                    flattened["quantization"] = value
                elif key == "device" and prefix == "ai":
                    flattened["device"] = value
                elif key == "level" and prefix == "security":
                    flattened["security_level"] = value
                elif key == "require_auth" and prefix == "security":
                    flattened["require_auth"] = value
                elif key == "enable_tls" and prefix == "security":
                    flattened["enable_tls"] = value
                elif key == "is_raspberry_pi" and "hardware" in config:
                    flattened["is_raspberry_pi"] = config["hardware"].get("is_raspberry_pi", False)
                elif key == "enable_ngrok" and "raspberry_pi" in config:
                    flattened["enable_ngrok"] = config["raspberry_pi"].get("enable_ngrok", False)
        
        return flattened
    
    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables.
        
        Returns:
            Configuration from environment variables
        """
        env_config = {}
        
        # Define environment variable mappings
        env_mappings = {
            "MCPLEASE_HOST": "host",
            "MCPLEASE_PORT": ("port", int),
            "MCPLEASE_TRANSPORT": ("transport", lambda x: x.split(",")),
            "MCPLEASE_MAX_WORKERS": ("max_workers", int),
            "MCPLEASE_AI_MODEL": "ai_model",
            "MCPLEASE_MEMORY_LIMIT": "memory_limit",
            "MCPLEASE_QUANTIZATION": "quantization",
            "MCPLEASE_DEVICE": "device",
            "MCPLEASE_SECURITY_LEVEL": "security_level",
            "MCPLEASE_REQUIRE_AUTH": ("require_auth", lambda x: x.lower() in ["true", "1", "yes"]),
            "MCPLEASE_ENABLE_TLS": ("enable_tls", lambda x: x.lower() in ["true", "1", "yes"]),
            "MCPLEASE_LOG_LEVEL": "log_level",
            "MCPLEASE_LOG_FILE": "log_file",
            "MCPLEASE_ENABLE_NGROK": ("enable_ngrok", lambda x: x.lower() in ["true", "1", "yes"]),
        }
        
        for env_var, mapping in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                if isinstance(mapping, tuple):
                    key, converter = mapping
                    try:
                        env_config[key] = converter(value)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid value for {env_var}: {value} ({e})")
                else:
                    env_config[mapping] = value
        
        return env_config
    
    def save_config(self, config: MCPConfig) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration to save
        """
        # Create config directory
        self.config_dir.mkdir(exist_ok=True)
        
        # Convert to nested structure for saving
        config_data = {
            "server": {
                "host": config.host,
                "port": config.port,
                "transport": config.transport,
                "max_workers": config.max_workers
            },
            "ai": {
                "model": config.ai_model,
                "memory_limit": config.memory_limit,
                "quantization": config.quantization,
                "device": config.device
            },
            "security": {
                "level": config.security_level,
                "require_auth": config.require_auth,
                "enable_tls": config.enable_tls
            },
            "logging": {
                "level": config.log_level,
                "file": config.log_file
            }
        }
        
        # Add hardware-specific settings
        if config.is_raspberry_pi:
            config_data["raspberry_pi"] = {
                "enable_ngrok": config.enable_ngrok,
                "temperature_monitoring": True,
                "cpu_governor": "ondemand"
            }
        
        # Save to file
        with open(self.config_file, "w") as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"Configuration saved to {self.config_file}")
        
        # Update cached config
        self._config = config
    
    def load_hardware_info(self) -> Optional[HardwareInfo]:
        """Load hardware information from config file.
        
        Returns:
            Hardware information if available
        """
        if self._hardware_info is not None:
            return self._hardware_info
        
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file) as f:
                config_data = json.load(f)
            
            hardware_data = config_data.get("hardware", {})
            if not hardware_data:
                return None
            
            self._hardware_info = HardwareInfo(
                memory_gb=hardware_data.get("memory_gb", 0.0),
                cpu_count=hardware_data.get("cpu_count", 1),
                architecture=hardware_data.get("architecture", "unknown"),
                platform=hardware_data.get("platform", "unknown"),
                is_raspberry_pi=hardware_data.get("is_raspberry_pi", False),
                gpu_available=hardware_data.get("gpu", {}).get("available", False),
                gpu_type=hardware_data.get("gpu", {}).get("type"),
                gpu_memory_gb=hardware_data.get("gpu", {}).get("memory_gb", 0.0),
                optimization_profile=hardware_data.get("recommended_config", {}).get("optimization_profile", "default")
            )
            
            return self._hardware_info
        except Exception as e:
            logger.warning(f"Failed to load hardware info: {e}")
            return None
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration.
        
        Returns:
            Configuration summary
        """
        config = self.load_config()
        hardware_info = self.load_hardware_info()
        
        summary = {
            "server": {
                "host": config.host,
                "port": config.port,
                "transport": config.transport,
                "max_workers": config.max_workers
            },
            "ai": {
                "model": config.ai_model,
                "memory_limit": config.memory_limit,
                "quantization": config.quantization
            },
            "security": {
                "level": config.security_level,
                "auth_required": config.require_auth,
                "tls_enabled": config.enable_tls
            }
        }
        
        if hardware_info:
            summary["hardware"] = {
                "memory_gb": hardware_info.memory_gb,
                "cpu_count": hardware_info.cpu_count,
                "architecture": hardware_info.architecture,
                "platform": hardware_info.platform,
                "is_raspberry_pi": hardware_info.is_raspberry_pi,
                "gpu_available": hardware_info.gpu_available
            }
        
        return summary
    
    def validate_config(self) -> List[str]:
        """Validate the current configuration.
        
        Returns:
            List of validation warnings/errors
        """
        config = self.load_config()
        warnings = []
        
        # Validate AI model settings
        if config.ai_model != "disabled":
            if config.memory_limit == "2GB":
                warnings.append("AI model enabled but memory limit is only 2GB - consider increasing")
        
        # Validate security settings
        if config.require_auth and not config.enable_tls:
            warnings.append("Authentication enabled but TLS disabled - credentials may be transmitted insecurely")
        
        # Validate transport settings
        if "websocket" in config.transport and not config.enable_tls:
            warnings.append("WebSocket transport without TLS may be insecure for remote connections")
        
        # Validate Raspberry Pi settings
        if config.is_raspberry_pi:
            if config.ai_model != "disabled":
                warnings.append("AI model enabled on Raspberry Pi - this may cause performance issues")
            if config.max_workers > 2:
                warnings.append("High worker count on Raspberry Pi may cause overheating")
        
        return warnings


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance.
    
    Returns:
        Configuration manager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> MCPConfig:
    """Get the current configuration.
    
    Returns:
        Current configuration
    """
    return get_config_manager().load_config()


def get_hardware_info() -> Optional[HardwareInfo]:
    """Get hardware information.
    
    Returns:
        Hardware information if available
    """
    return get_config_manager().load_hardware_info()