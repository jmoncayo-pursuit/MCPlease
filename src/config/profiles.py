"""System profiles for different hardware configurations."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from .hardware import HardwareProfile


@dataclass
class SystemProfile:
    """System profile with optimized settings."""
    
    name: str
    description: str
    min_memory_gb: float
    max_memory_gb: float
    quantization: str
    max_context_length: int
    gpu_memory_utilization: float
    max_concurrent_requests: int
    
    def is_compatible(self, hardware: HardwareProfile) -> bool:
        """Check if this profile is compatible with given hardware."""
        return (
            self.min_memory_gb <= hardware.total_memory_gb <= self.max_memory_gb
        )
    
    def get_config(self, hardware: HardwareProfile) -> Dict[str, Any]:
        """Get configuration for this profile."""
        return {
            "quantization": self.quantization,
            "max_context_length": self.max_context_length,
            "gpu_memory_utilization": self.gpu_memory_utilization,
            "max_concurrent_requests": self.max_concurrent_requests,
            "workers": min(self.max_concurrent_requests, hardware.cpu_cores // 2)
        }


class ProfileManager:
    """Manages system profiles."""
    
    def __init__(self):
        self.profiles = [
            SystemProfile(
                name="high_performance",
                description="High performance for 32GB+ systems",
                min_memory_gb=32.0,
                max_memory_gb=float('inf'),
                quantization="bf16",
                max_context_length=8192,
                gpu_memory_utilization=0.85,
                max_concurrent_requests=4
            ),
            SystemProfile(
                name="balanced",
                description="Balanced performance for 16-32GB systems",
                min_memory_gb=16.0,
                max_memory_gb=32.0,
                quantization="mxfp4",
                max_context_length=4096,
                gpu_memory_utilization=0.8,
                max_concurrent_requests=2
            ),
            SystemProfile(
                name="memory_efficient",
                description="Memory efficient for 8-16GB systems",
                min_memory_gb=8.0,
                max_memory_gb=16.0,
                quantization="int4",
                max_context_length=2048,
                gpu_memory_utilization=0.7,
                max_concurrent_requests=1
            )
        ]
    
    def get_compatible_profiles(self, hardware: HardwareProfile) -> List[SystemProfile]:
        """Get all profiles compatible with given hardware."""
        return [p for p in self.profiles if p.is_compatible(hardware)]
    
    def select_optimal_profile(self, hardware: HardwareProfile) -> Optional[SystemProfile]:
        """Select the optimal profile for given hardware."""
        compatible = self.get_compatible_profiles(hardware)
        if not compatible:
            return None
        
        # Select the profile with highest memory requirement that's still compatible
        return max(compatible, key=lambda p: p.min_memory_gb)
    
    def get_profile_by_name(self, name: str) -> Optional[SystemProfile]:
        """Get profile by name."""
        for profile in self.profiles:
            if profile.name == name:
                return profile
        return None