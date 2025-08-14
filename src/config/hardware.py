"""Hardware detection and profiling for optimal model configuration."""

import os
import platform
import psutil
import subprocess
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class HardwareProfile:
    """Hardware profile for system optimization."""
    
    total_memory_gb: float
    available_memory_gb: float
    cpu_cores: int
    cpu_threads: int
    system: str
    architecture: str
    is_apple_silicon: bool
    has_gpu: bool
    gpu_memory_gb: float
    gpu_type: Optional[str]
    
    @classmethod
    def detect(cls) -> 'HardwareProfile':
        """Detect current hardware configuration."""
        # Memory information
        memory = psutil.virtual_memory()
        total_memory_gb = memory.total / (1024**3)
        available_memory_gb = memory.available / (1024**3)
        
        # CPU information
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        
        # System information
        system = platform.system()
        architecture = platform.machine()
        
        # Apple Silicon detection
        is_apple_silicon = (
            system == "Darwin" and 
            architecture in ["arm64", "aarch64"]
        )
        
        # GPU detection
        has_gpu = False
        gpu_memory_gb = 0.0
        gpu_type = None
        
        if is_apple_silicon:
            # On Apple Silicon, GPU memory is shared with system memory
            has_gpu = True
            gpu_memory_gb = total_memory_gb * 0.7  # Estimate usable GPU memory
            gpu_type = "Apple Silicon"
        else:
            # Try to detect NVIDIA GPU
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    gpu_memory_mb = int(result.stdout.strip())
                    gpu_memory_gb = gpu_memory_mb / 1024
                    has_gpu = True
                    gpu_type = "NVIDIA"
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        return cls(
            total_memory_gb=total_memory_gb,
            available_memory_gb=available_memory_gb,
            cpu_cores=cpu_cores,
            cpu_threads=cpu_threads,
            system=system,
            architecture=architecture,
            is_apple_silicon=is_apple_silicon,
            has_gpu=has_gpu,
            gpu_memory_gb=gpu_memory_gb,
            gpu_type=gpu_type
        )
    
    def get_recommended_config(self) -> Dict[str, Any]:
        """Get recommended configuration for this hardware."""
        config = {}
        
        # Memory-based recommendations
        if self.total_memory_gb >= 32:
            config.update({
                "quantization": "bf16",
                "max_context_length": 8192,
                "gpu_memory_utilization": 0.85,
                "max_concurrent_requests": 4
            })
        elif self.total_memory_gb >= 16:
            config.update({
                "quantization": "mxfp4",
                "max_context_length": 4096,
                "gpu_memory_utilization": 0.8,
                "max_concurrent_requests": 2
            })
        else:
            config.update({
                "quantization": "int4",
                "max_context_length": 2048,
                "gpu_memory_utilization": 0.7,
                "max_concurrent_requests": 1
            })
        
        # CPU-based recommendations
        if self.cpu_cores >= 8:
            config["workers"] = min(4, self.cpu_cores // 2)
        else:
            config["workers"] = 1
        
        return config
    
    def is_compatible_with_model(self, model_size_gb: float) -> bool:
        """Check if hardware can run a model of given size."""
        # Rule of thumb: need 1.5x model size in RAM for loading + inference
        required_memory = model_size_gb * 1.5
        return self.available_memory_gb >= required_memory
    
    def __str__(self) -> str:
        return (
            f"HardwareProfile("
            f"memory={self.total_memory_gb:.1f}GB, "
            f"cpu={self.cpu_cores}c/{self.cpu_threads}t, "
            f"system={self.system}, "
            f"arch={self.architecture}, "
            f"gpu={self.gpu_type or 'None'}"
            f")"
        )