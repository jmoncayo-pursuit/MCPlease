"""Hardware-specific configuration management."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from ..utils.hardware import get_hardware_info, get_optimization_config

logger = logging.getLogger(__name__)


@dataclass
class HardwareConfig:
    """Hardware-specific configuration."""
    
    # Hardware detection
    memory_gb: float
    cpu_count: int
    architecture: str
    is_raspberry_pi: bool
    is_arm64: bool
    gpu_available: bool
    gpu_type: Optional[str] = None
    
    # Optimization settings
    optimization_profile: str = "default"
    recommended_workers: int = 1
    recommended_memory_limit: str = "2GB"
    quantization: str = "int8"
    context_length: int = 2048
    batch_size: int = 1
    
    # Platform-specific settings
    enable_gpu: bool = False
    temperature_monitoring: bool = False
    cpu_governor: str = "ondemand"


def get_hardware_config() -> HardwareConfig:
    """Get hardware-specific configuration.
    
    Returns:
        Hardware configuration based on detected hardware
    """
    try:
        # Get hardware info from utils
        hardware_info = get_hardware_info()
        optimization_config = get_optimization_config()
        
        return HardwareConfig(
            memory_gb=hardware_info.memory_gb,
            cpu_count=hardware_info.cpu_count,
            architecture=hardware_info.architecture,
            is_raspberry_pi=hardware_info.is_raspberry_pi,
            is_arm64=hardware_info.is_arm64,
            gpu_available=hardware_info.gpu_available,
            gpu_type=hardware_info.gpu_type,
            optimization_profile=hardware_info.optimization_profile,
            recommended_workers=hardware_info.recommended_workers,
            recommended_memory_limit=hardware_info.recommended_memory_limit,
            quantization=optimization_config.get("model_quantization", "int8"),
            context_length=optimization_config.get("context_length", 2048),
            batch_size=optimization_config.get("batch_size", 1),
            enable_gpu=optimization_config.get("enable_gpu", False),
            temperature_monitoring=optimization_config.get("temperature_monitoring", False),
            cpu_governor=optimization_config.get("cpu_governor", "ondemand")
        )
    except Exception as e:
        logger.warning(f"Failed to get hardware configuration: {e}")
        
        # Return default configuration
        return HardwareConfig(
            memory_gb=4.0,
            cpu_count=2,
            architecture="unknown",
            is_raspberry_pi=False,
            is_arm64=False,
            gpu_available=False,
            optimization_profile="default",
            recommended_workers=2,
            recommended_memory_limit="2GB"
        )


def create_hardware_optimized_config(base_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create hardware-optimized configuration.
    
    Args:
        base_config: Base configuration to optimize
        
    Returns:
        Hardware-optimized configuration
    """
    hardware_config = get_hardware_config()
    optimized_config = base_config.copy()
    
    # Apply hardware-specific optimizations
    optimized_config.update({
        "max_workers": hardware_config.recommended_workers,
        "memory_limit": hardware_config.recommended_memory_limit,
        "quantization": hardware_config.quantization,
        "context_length": hardware_config.context_length,
        "batch_size": hardware_config.batch_size,
        "enable_gpu": hardware_config.enable_gpu,
    })
    
    # Raspberry Pi specific optimizations
    if hardware_config.is_raspberry_pi:
        optimized_config.update({
            "ai_model": "disabled",  # Too resource intensive
            "transport": ["sse"],  # Better for remote access
            "enable_ngrok": True,
            "temperature_monitoring": True,
            "cpu_governor": "ondemand",
        })
    
    # High-memory system optimizations
    elif hardware_config.memory_gb >= 16:
        optimized_config.update({
            "ai_model": "openai/gpt-oss-20b",
            "transport": ["stdio", "sse", "websocket"],
            "security_level": "full",
            "quantization": "fp16",
        })
    
    # Medium-memory system optimizations
    elif hardware_config.memory_gb >= 8:
        optimized_config.update({
            "ai_model": "openai/gpt-oss-20b",
            "transport": ["stdio", "sse"],
            "security_level": "standard",
            "quantization": "int8",
        })
    
    return optimized_config