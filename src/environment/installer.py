"""Dependency installer with specialized handling for vLLM and torch."""

import os
import sys
import subprocess
import platform
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InstallationResult:
    """Result of a package installation attempt."""
    success: bool
    package: str
    version: Optional[str] = None
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class DependencyInstaller:
    """Handles installation of AI model dependencies with error handling."""
    
    # Critical packages that need special handling
    CRITICAL_PACKAGES = {
        'torch': {
            'version': '2.1.2',
            'install_args': ['--index-url', 'https://download.pytorch.org/whl/cpu'],
            'verify_import': 'torch',
            'mac_metal_support': True
        },
        'vllm': {
            'version': '0.2.7',
            'install_args': [],
            'verify_import': 'vllm',
            'requires_python': [(3, 9), (3, 10), (3, 11), (3, 12)],
            'mac_compatibility': True
        }
    }
    
    def __init__(self, pip_executable: str = None):
        """Initialize dependency installer.
        
        Args:
            pip_executable: Path to pip executable. Defaults to system pip.
        """
        self.pip_executable = pip_executable or self._find_pip_executable()
        self.system_info = self._get_system_info()
        
    def _find_pip_executable(self) -> str:
        """Find the appropriate pip executable."""
        # Try common pip locations
        pip_candidates = ['pip', 'pip3', sys.executable + ' -m pip']
        
        for pip_cmd in pip_candidates:
            try:
                result = subprocess.run(
                    pip_cmd.split() + ['--version'], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    return pip_cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
                
        raise RuntimeError("Could not find pip executable")
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system information for compatibility checks."""
        return {
            'platform': platform.system(),
            'machine': platform.machine(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
            'is_mac': platform.system() == 'Darwin',
            'is_apple_silicon': platform.machine() == 'arm64' and platform.system() == 'Darwin'
        }
    
    def check_python_compatibility(self, package: str) -> Tuple[bool, str]:
        """Check if current Python version is compatible with package.
        
        Args:
            package: Package name to check
            
        Returns:
            Tuple of (is_compatible, message)
        """
        if package not in self.CRITICAL_PACKAGES:
            return True, "Package not in critical list"
            
        package_info = self.CRITICAL_PACKAGES[package]
        required_versions = package_info.get('requires_python', [])
        
        if not required_versions:
            return True, "No specific Python version requirements"
            
        current_version = (sys.version_info.major, sys.version_info.minor)
        
        if current_version in required_versions:
            return True, f"Python {current_version[0]}.{current_version[1]} is supported"
        
        supported_versions = ", ".join([f"{v[0]}.{v[1]}" for v in required_versions])
        return False, f"Python {current_version[0]}.{current_version[1]} not supported. Supported: {supported_versions}"
    
    def install_torch(self) -> InstallationResult:
        """Install PyTorch with Mac Metal support if available.
        
        Returns:
            InstallationResult with installation details
        """
        logger.info("Installing PyTorch with optimizations for Mac hardware")
        
        package_info = self.CRITICAL_PACKAGES['torch']
        package_spec = f"torch=={package_info['version']}"
        
        # Build install command
        cmd = self.pip_executable.split() + ['install', package_spec]
        
        # Add Mac-specific optimizations
        if self.system_info['is_mac']:
            logger.info("Detected Mac system - using CPU-optimized PyTorch build")
            cmd.extend(package_info['install_args'])
        
        try:
            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=True
            )
            
            # Verify installation
            if self._verify_package_import('torch'):
                logger.info("PyTorch installed and verified successfully")
                return InstallationResult(
                    success=True,
                    package='torch',
                    version=package_info['version']
                )
            else:
                return InstallationResult(
                    success=False,
                    package='torch',
                    error_message="Installation completed but package import failed"
                )
                
        except subprocess.CalledProcessError as e:
            logger.error(f"PyTorch installation failed: {e}")
            return InstallationResult(
                success=False,
                package='torch',
                error_message=f"Installation command failed: {e.stderr}"
            )
        except subprocess.TimeoutExpired:
            return InstallationResult(
                success=False,
                package='torch',
                error_message="Installation timed out after 5 minutes"
            )
        except Exception as e:
            return InstallationResult(
                success=False,
                package='torch',
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def install_vllm(self) -> InstallationResult:
        """Install vLLM with compatibility checks.
        
        Returns:
            InstallationResult with installation details
        """
        logger.info("Installing vLLM inference server")
        
        # Check Python compatibility first
        is_compatible, message = self.check_python_compatibility('vllm')
        if not is_compatible:
            return InstallationResult(
                success=False,
                package='vllm',
                error_message=f"Python compatibility check failed: {message}"
            )
        
        package_info = self.CRITICAL_PACKAGES['vllm']
        package_spec = f"vllm=={package_info['version']}"
        
        # Build install command
        cmd = self.pip_executable.split() + ['install', package_spec]
        cmd.extend(package_info['install_args'])
        
        # Add Mac-specific warnings
        warnings = []
        if self.system_info['is_mac']:
            warnings.append("vLLM on Mac may have limited GPU acceleration")
            if self.system_info['is_apple_silicon']:
                warnings.append("Apple Silicon detected - ensure sufficient RAM (16GB+)")
        
        try:
            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout for vLLM
                check=True
            )
            
            # Verify installation
            if self._verify_package_import('vllm'):
                logger.info("vLLM installed and verified successfully")
                return InstallationResult(
                    success=True,
                    package='vllm',
                    version=package_info['version'],
                    warnings=warnings
                )
            else:
                return InstallationResult(
                    success=False,
                    package='vllm',
                    error_message="Installation completed but package import failed",
                    warnings=warnings
                )
                
        except subprocess.CalledProcessError as e:
            logger.error(f"vLLM installation failed: {e}")
            error_msg = self._parse_vllm_error(e.stderr)
            return InstallationResult(
                success=False,
                package='vllm',
                error_message=error_msg,
                warnings=warnings
            )
        except subprocess.TimeoutExpired:
            return InstallationResult(
                success=False,
                package='vllm',
                error_message="Installation timed out after 10 minutes",
                warnings=warnings
            )
        except Exception as e:
            return InstallationResult(
                success=False,
                package='vllm',
                error_message=f"Unexpected error: {str(e)}",
                warnings=warnings
            )
    
    def install_requirements_file(self, requirements_file: Path) -> List[InstallationResult]:
        """Install packages from requirements file with error handling.
        
        Args:
            requirements_file: Path to requirements.txt file
            
        Returns:
            List of InstallationResult for each package group
        """
        if not requirements_file.exists():
            return [InstallationResult(
                success=False,
                package='requirements.txt',
                error_message=f"Requirements file not found: {requirements_file}"
            )]
        
        logger.info(f"Installing packages from {requirements_file}")
        
        # Install critical packages first with special handling
        results = []
        
        # Install torch first (required by vLLM)
        torch_result = self.install_torch()
        results.append(torch_result)
        
        if not torch_result.success:
            logger.error("PyTorch installation failed - cannot proceed with vLLM")
            return results
        
        # Install vLLM second
        vllm_result = self.install_vllm()
        results.append(vllm_result)
        
        # Install remaining packages
        remaining_result = self._install_remaining_packages(requirements_file)
        results.append(remaining_result)
        
        return results
    
    def _install_remaining_packages(self, requirements_file: Path) -> InstallationResult:
        """Install non-critical packages from requirements file.
        
        Args:
            requirements_file: Path to requirements.txt file
            
        Returns:
            InstallationResult for remaining packages
        """
        cmd = self.pip_executable.split() + ['install', '-r', str(requirements_file)]
        
        try:
            logger.info("Installing remaining packages from requirements.txt")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=True
            )
            
            return InstallationResult(
                success=True,
                package='requirements.txt',
                version='latest'
            )
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Requirements installation failed: {e}")
            return InstallationResult(
                success=False,
                package='requirements.txt',
                error_message=f"Installation failed: {e.stderr}"
            )
        except subprocess.TimeoutExpired:
            return InstallationResult(
                success=False,
                package='requirements.txt',
                error_message="Installation timed out after 5 minutes"
            )
        except Exception as e:
            return InstallationResult(
                success=False,
                package='requirements.txt',
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _verify_package_import(self, package_name: str) -> bool:
        """Verify that a package can be imported.
        
        Args:
            package_name: Name of package to import
            
        Returns:
            True if package imports successfully, False otherwise
        """
        try:
            __import__(package_name)
            return True
        except ImportError as e:
            logger.warning(f"Package {package_name} import failed: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error importing {package_name}: {e}")
            return False
    
    def _parse_vllm_error(self, stderr: str) -> str:
        """Parse vLLM installation error and provide helpful message.
        
        Args:
            stderr: Error output from pip install
            
        Returns:
            Parsed error message with suggestions
        """
        if not stderr:
            return "vLLM installation failed with unknown error"
        
        # Common vLLM installation issues
        if "Microsoft Visual C++" in stderr:
            return "vLLM installation failed: Microsoft Visual C++ Build Tools required"
        elif "CUDA" in stderr and self.system_info['is_mac']:
            return "vLLM installation failed: CUDA not available on Mac (this is expected)"
        elif "memory" in stderr.lower() or "ram" in stderr.lower():
            return "vLLM installation failed: Insufficient memory during compilation"
        elif "python" in stderr.lower() and "version" in stderr.lower():
            return f"vLLM installation failed: Python version incompatibility (current: {self.system_info['python_version']})"
        else:
            # Return first few lines of error for debugging
            error_lines = stderr.strip().split('\n')[:3]
            return f"vLLM installation failed: {' '.join(error_lines)}"
    
    def get_installation_summary(self, results: List[InstallationResult]) -> Dict[str, any]:
        """Generate installation summary from results.
        
        Args:
            results: List of installation results
            
        Returns:
            Summary dictionary with success status and details
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        all_warnings = []
        
        for result in results:
            all_warnings.extend(result.warnings)
        
        return {
            'overall_success': len(failed) == 0,
            'successful_packages': len(successful),
            'failed_packages': len(failed),
            'successful': [r.package for r in successful],
            'failed': [{'package': r.package, 'error': r.error_message} for r in failed],
            'warnings': all_warnings,
            'system_info': self.system_info
        }