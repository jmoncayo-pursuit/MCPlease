"""Hardware detection and optimization utilities."""

import logging
import platform
import psutil
import subprocess
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import os

logger = logging.getLogger(__name__)


@dataclass
class HardwareInfo:
    """Hardware information and capabilities."""
    
    architecture: str
    cpu_count: int
    memory_gb: float
    is_raspberry_pi: bool
    is_arm64: bool
    is_x86_64: bool
    gpu_available: bool
    gpu_type: Optional[str] = None
    optimization_profile: str = "default"
    recommended_workers: int = 1
    recommended_memory_limit: str = "2GB"


class HardwareDetector:
    """Hardware detection and optimization recommendations."""
    
    def __init__(self):
        """Initialize hardware detector."""
        self._hardware_info: Optional[HardwareInfo] = None
    
    def detect_hardware(self) -> HardwareInfo:
        """Detect hardware capabilities and return optimization recommendations.
        
        Returns:
            Hardware information and optimization recommendations
        """
        if self._hardware_info is not None:
            return self._hardware_info
        
        # Basic system info
        architecture = platform.machine().lower()
        cpu_count = psutil.cpu_count(logical=True)
        memory_bytes = psutil.virtual_memory().total
        memory_gb = memory_bytes / (1024**3)
        
        # Architecture detection
        is_arm64 = architecture in ['aarch64', 'arm64']
        is_x86_64 = architecture in ['x86_64', 'amd64']
        
        # Raspberry Pi detection
        is_raspberry_pi = self._detect_raspberry_pi()
        
        # GPU detection
        gpu_available, gpu_type = self._detect_gpu()
        
        # Determine optimization profile
        optimization_profile = self._determine_optimization_profile(
            is_raspberry_pi, is_arm64, memory_gb, cpu_count
        )
        
        # Resource recommendations
        recommended_workers = self._calculate_recommended_workers(
            cpu_count, memory_gb, is_raspberry_pi
        )
        recommended_memory_limit = self._calculate_memory_limit(
            memory_gb, is_raspberry_pi
        )
        
        self._hardware_info = HardwareInfo(
            architecture=architecture,
            cpu_count=cpu_count,
            memory_gb=memory_gb,
            is_raspberry_pi=is_raspberry_pi,
            is_arm64=is_arm64,
            is_x86_64=is_x86_64,
            gpu_available=gpu_available,
            gpu_type=gpu_type,
            optimization_profile=optimization_profile,
            recommended_workers=recommended_workers,
            recommended_memory_limit=recommended_memory_limit
        )
        
        logger.info(f"Detected hardware: {self._hardware_info}")
        return self._hardware_info
    
    def _detect_raspberry_pi(self) -> bool:
        """Detect if running on Raspberry Pi.
        
        Returns:
            True if running on Raspberry Pi
        """
        try:
            # Check /proc/cpuinfo for Raspberry Pi
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read().lower()
                if 'raspberry pi' in cpuinfo or 'bcm' in cpuinfo:
                    return True
            
            # Check /proc/device-tree/model
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read().lower()
                    if 'raspberry pi' in model:
                        return True
            
            # Check for Pi-specific files
            pi_files = [
                '/boot/config.txt',
                '/boot/cmdline.txt',
                '/opt/vc/bin/vcgencmd'
            ]
            
            for pi_file in pi_files:
                if os.path.exists(pi_file):
                    return True
                    
        except Exception as e:
            logger.debug(f"Error detecting Raspberry Pi: {e}")
        
        return False
    
    def _detect_gpu(self) -> tuple[bool, Optional[str]]:
        """Detect GPU availability and type.
        
        Returns:
            Tuple of (gpu_available, gpu_type)
        """
        try:
            # Try to detect NVIDIA GPU
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return True, f"NVIDIA {result.stdout.strip()}"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # Try to detect AMD GPU
            result = subprocess.run(
                ['rocm-smi', '--showproductname'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and 'GPU' in result.stdout:
                return True, "AMD GPU"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # Check for integrated GPU on Raspberry Pi
            if self._detect_raspberry_pi():
                result = subprocess.run(
                    ['vcgencmd', 'get_mem', 'gpu'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and 'gpu=' in result.stdout:
                    gpu_mem = result.stdout.strip()
                    if int(gpu_mem.split('=')[1].replace('M', '')) > 64:
                        return True, "VideoCore GPU"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return False, None
    
    def _determine_optimization_profile(
        self, 
        is_raspberry_pi: bool, 
        is_arm64: bool, 
        memory_gb: float, 
        cpu_count: int
    ) -> str:
        """Determine optimization profile based on hardware.
        
        Args:
            is_raspberry_pi: Whether running on Raspberry Pi
            is_arm64: Whether running on ARM64
            memory_gb: Available memory in GB
            cpu_count: Number of CPU cores
            
        Returns:
            Optimization profile name
        """
        if is_raspberry_pi:
            if memory_gb >= 8:
                return "pi5_high_memory"
            elif memory_gb >= 4:
                return "pi5_standard"
            else:
                return "pi4_low_memory"
        elif is_arm64:
            if memory_gb >= 16:
                return "arm64_high_performance"
            else:
                return "arm64_standard"
        elif memory_gb >= 32:
            return "x86_high_performance"
        elif memory_gb >= 16:
            return "x86_standard"
        else:
            return "x86_low_memory"
    
    def _calculate_recommended_workers(
        self, 
        cpu_count: int, 
        memory_gb: float, 
        is_raspberry_pi: bool
    ) -> int:
        """Calculate recommended number of workers.
        
        Args:
            cpu_count: Number of CPU cores
            memory_gb: Available memory in GB
            is_raspberry_pi: Whether running on Raspberry Pi
            
        Returns:
            Recommended number of workers
        """
        if is_raspberry_pi:
            # Conservative for Pi to avoid overheating
            return min(2, max(1, cpu_count // 2))
        else:
            # More aggressive for other systems
            memory_workers = int(memory_gb // 2)  # 2GB per worker
            cpu_workers = max(1, cpu_count - 1)  # Leave one core free
            return min(memory_workers, cpu_workers, 8)  # Cap at 8 workers
    
    def _calculate_memory_limit(self, memory_gb: float, is_raspberry_pi: bool) -> str:
        """Calculate recommended memory limit.
        
        Args:
            memory_gb: Available memory in GB
            is_raspberry_pi: Whether running on Raspberry Pi
            
        Returns:
            Memory limit string (e.g., "4GB")
        """
        if is_raspberry_pi:
            # Conservative memory usage for Pi
            limit_gb = max(1, int(memory_gb * 0.6))  # Use 60% of available memory
        else:
            # More aggressive for other systems
            limit_gb = max(2, int(memory_gb * 0.8))  # Use 80% of available memory
        
        return f"{limit_gb}GB"
    
    def get_optimization_config(self) -> Dict[str, Any]:
        """Get optimization configuration based on detected hardware.
        
        Returns:
            Dictionary with optimization settings
        """
        hardware = self.detect_hardware()
        
        config = {
            "hardware_profile": hardware.optimization_profile,
            "workers": hardware.recommended_workers,
            "memory_limit": hardware.recommended_memory_limit,
            "cpu_count": hardware.cpu_count,
            "memory_gb": hardware.memory_gb,
            "architecture": hardware.architecture,
        }
        
        # Profile-specific optimizations
        if hardware.is_raspberry_pi:
            config.update({
                "model_quantization": "int8",
                "context_length": 2048,  # Reduced for Pi
                "batch_size": 1,
                "enable_gpu": hardware.gpu_available,
                "temperature_monitoring": True,
                "cpu_governor": "ondemand",
            })
        elif hardware.is_arm64:
            config.update({
                "model_quantization": "fp16",
                "context_length": 4096,
                "batch_size": 2,
                "enable_gpu": hardware.gpu_available,
                "cpu_governor": "performance",
            })
        else:
            config.update({
                "model_quantization": "fp16" if hardware.memory_gb < 16 else "fp32",
                "context_length": 8192,
                "batch_size": 4,
                "enable_gpu": hardware.gpu_available,
                "cpu_governor": "performance",
            })
        
        return config
    
    def apply_system_optimizations(self) -> None:
        """Apply system-level optimizations based on detected hardware."""
        hardware = self.detect_hardware()
        
        try:
            if hardware.is_raspberry_pi:
                self._apply_pi_optimizations()
            elif hardware.is_arm64:
                self._apply_arm64_optimizations()
            else:
                self._apply_x86_optimizations()
        except Exception as e:
            logger.warning(f"Failed to apply system optimizations: {e}")
    
    def _apply_pi_optimizations(self) -> None:
        """Apply Raspberry Pi specific optimizations."""
        logger.info("Applying Raspberry Pi optimizations")
        
        # Set environment variables for Pi optimization
        os.environ.update({
            "OMP_NUM_THREADS": "2",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
            "TRANSFORMERS_CACHE": "/tmp/transformers_cache",
        })
        
        # Try to set CPU governor (requires sudo)
        try:
            subprocess.run([
                "sudo", "cpufreq-set", "-g", "ondemand"
            ], check=False, capture_output=True)
        except FileNotFoundError:
            logger.debug("cpufreq-set not available")
    
    def _apply_arm64_optimizations(self) -> None:
        """Apply ARM64 specific optimizations."""
        logger.info("Applying ARM64 optimizations")
        
        os.environ.update({
            "OMP_NUM_THREADS": str(min(4, psutil.cpu_count())),
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        })
    
    def _apply_x86_optimizations(self) -> None:
        """Apply x86_64 specific optimizations."""
        logger.info("Applying x86_64 optimizations")
        
        os.environ.update({
            "OMP_NUM_THREADS": str(psutil.cpu_count()),
        })


# Global hardware detector instance
hardware_detector = HardwareDetector()


def get_hardware_info() -> HardwareInfo:
    """Get hardware information.
    
    Returns:
        Hardware information
    """
    return hardware_detector.detect_hardware()


def get_optimization_config() -> Dict[str, Any]:
    """Get optimization configuration.
    
    Returns:
        Optimization configuration
    """
    return hardware_detector.get_optimization_config()


def apply_optimizations() -> None:
    """Apply system optimizations."""
    hardware_detector.apply_system_optimizations()