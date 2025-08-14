"""Configuration settings for MCPlease MVP."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings
import logging

from .hardware import HardwareProfile
from .profiles import ProfileManager

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server configuration
    host: str = Field(default="localhost", env="MCPLEASE_HOST")
    port: int = Field(default=8000, env="MCPLEASE_PORT")
    workers: int = Field(default=1, env="MCPLEASE_WORKERS")
    
    # Model configuration
    model_name: str = Field(default="gpt-oss-20b", env="MCPLEASE_MODEL_NAME")
    model_path: Optional[str] = Field(default=None, env="MCPLEASE_MODEL_PATH")
    quantization: str = Field(default="auto", env="MCPLEASE_QUANTIZATION")
    max_context_length: int = Field(default=8192, env="MCPLEASE_MAX_CONTEXT_LENGTH")
    
    # Performance tuning
    max_concurrent_requests: int = Field(default=4, env="MCPLEASE_CONCURRENT_REQUESTS")
    batch_size: int = Field(default=1, env="MCPLEASE_BATCH_SIZE")
    gpu_memory_utilization: float = Field(default=0.85, env="MCPLEASE_GPU_MEMORY_UTILIZATION")
    
    # Cache configuration
    cache_size_mb: int = Field(default=512, env="MCPLEASE_CACHE_SIZE_MB")
    disk_cache_gb: int = Field(default=2, env="MCPLEASE_DISK_CACHE_GB")
    enable_semantic_cache: bool = Field(default=True, env="MCPLEASE_ENABLE_SEMANTIC_CACHE")
    
    # Paths
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".mcplease")
    log_dir: Path = Field(default_factory=lambda: Path.home() / ".mcplease" / "logs")
    cache_dir: Path = Field(default_factory=lambda: Path.home() / ".mcplease" / "cache")
    
    # Logging
    log_level: str = Field(default="INFO", env="MCPLEASE_LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="MCPLEASE_LOG_FILE")
    
    # Security
    allowed_origins: list = Field(default_factory=lambda: ["localhost", "127.0.0.1", "::1"])
    max_request_size_mb: int = Field(default=10, env="MCPLEASE_MAX_REQUEST_SIZE_MB")
    rate_limit_per_minute: int = Field(default=60, env="MCPLEASE_RATE_LIMIT_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        env_prefix = "MCPLEASE_"
    
    def __post_init__(self):
        """Create necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_optimal_config(self, hardware: Optional[HardwareProfile] = None) -> Dict[str, Any]:
        """Get optimal configuration for detected hardware."""
        if hardware is None:
            hardware = HardwareProfile.detect()
        
        # Use profile manager to get optimal configuration
        profile_manager = ProfileManager()
        profile = profile_manager.select_optimal_profile(hardware)
        
        if profile:
            config = profile.get_config(hardware)
            logger.info(f"Selected profile: {profile.name} for hardware: {hardware}")
            return config
        else:
            logger.warning(f"No suitable profile found for hardware: {hardware}")
            return hardware.get_recommended_config()
    
    def apply_profile_config(self, profile_name: str) -> None:
        """Apply configuration from a specific profile."""
        hardware = HardwareProfile.detect()
        profile_manager = ProfileManager()
        profile = profile_manager.get_profile_by_name(profile_name)
        
        if not profile:
            raise ValueError(f"Profile '{profile_name}' not found")
        
        if not profile.is_compatible(hardware):
            logger.warning(
                f"Profile '{profile_name}' may not be optimal for current hardware: {hardware}"
            )
        
        config = profile.get_config(hardware)
        
        # Update settings with profile configuration
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Applied {key}={value} from profile {profile_name}")
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """Get current hardware information."""
        hardware = HardwareProfile.detect()
        profile_manager = ProfileManager()
        optimal_profile = profile_manager.select_optimal_profile(hardware)
        
        return {
            "hardware": {
                "total_memory_gb": hardware.total_memory_gb,
                "available_memory_gb": hardware.available_memory_gb,
                "cpu_cores": hardware.cpu_cores,
                "cpu_threads": hardware.cpu_threads,
                "system": hardware.system,
                "architecture": hardware.architecture,
                "is_apple_silicon": hardware.is_apple_silicon,
                "has_gpu": hardware.has_gpu,
                "gpu_memory_gb": hardware.gpu_memory_gb,
                "gpu_type": hardware.gpu_type
            },
            "optimal_profile": optimal_profile.name if optimal_profile else None,
            "compatible_profiles": [
                p.name for p in profile_manager.get_compatible_profiles(hardware)
            ]
        }


# Global settings instance
settings = Settings()