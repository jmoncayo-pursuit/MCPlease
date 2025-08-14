"""Environment manager for Python version validation and virtual environment setup."""

import os
import sys
import subprocess
import venv
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """Manages Python environment validation and virtual environment setup."""
    
    SUPPORTED_PYTHON_VERSIONS = [(3, 9), (3, 10), (3, 11), (3, 12), (3, 13)]
    VENV_DIR = "venv"
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize environment manager.
        
        Args:
            project_root: Root directory of the project. Defaults to current working directory.
        """
        self.project_root = project_root or Path.cwd()
        self.venv_path = self.project_root / self.VENV_DIR
        
    def check_python_version(self) -> Tuple[bool, str]:
        """Check if current Python version is supported for vLLM.
        
        Returns:
            Tuple of (is_valid, message)
        """
        current_version = sys.version_info[:2]
        
        if current_version in self.SUPPORTED_PYTHON_VERSIONS:
            return True, f"Python {current_version[0]}.{current_version[1]} is supported"
        
        supported_versions_str = ", ".join([f"{v[0]}.{v[1]}" for v in self.SUPPORTED_PYTHON_VERSIONS])
        return False, f"Python {current_version[0]}.{current_version[1]} is not supported. Supported versions: {supported_versions_str}"
    
    def validate_environment(self) -> bool:
        """Validate the current Python environment.
        
        Returns:
            True if environment is valid, False otherwise
        """
        is_valid, message = self.check_python_version()
        if not is_valid:
            logger.error(f"Environment validation failed: {message}")
            return False
            
        logger.info(f"Environment validation passed: {message}")
        return True
    
    def setup_virtual_env(self) -> bool:
        """Create and setup virtual environment.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.venv_path.exists():
                logger.info(f"Virtual environment already exists at {self.venv_path}")
                return True
                
            logger.info(f"Creating virtual environment at {self.venv_path}")
            venv.create(self.venv_path, with_pip=True)
            
            # Verify the virtual environment was created successfully
            if not self.venv_path.exists():
                logger.error("Failed to create virtual environment")
                return False
                
            logger.info("Virtual environment created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create virtual environment: {e}")
            return False
    
    def get_python_executable(self) -> str:
        """Get the Python executable path for the virtual environment.
        
        Returns:
            Path to Python executable
        """
        if sys.platform == "win32":
            python_exe = self.venv_path / "Scripts" / "python.exe"
        else:
            python_exe = self.venv_path / "bin" / "python"
            
        if python_exe.exists():
            return str(python_exe)
        
        # Fallback to system Python if venv doesn't exist
        return sys.executable
    
    def get_pip_executable(self) -> str:
        """Get the pip executable path for the virtual environment.
        
        Returns:
            Path to pip executable
        """
        if sys.platform == "win32":
            pip_exe = self.venv_path / "Scripts" / "pip.exe"
        else:
            pip_exe = self.venv_path / "bin" / "pip"
            
        if pip_exe.exists():
            return str(pip_exe)
        
        # Fallback to system pip if venv doesn't exist
        return "pip"
    
    def install_dependencies(self, requirements_file: Optional[Path] = None) -> bool:
        """Install dependencies in the virtual environment using specialized installer.
        
        Args:
            requirements_file: Path to requirements file. Defaults to requirements.txt in project root.
            
        Returns:
            True if successful, False otherwise
        """
        from .installer import DependencyInstaller
        
        if not requirements_file:
            requirements_file = self.project_root / "requirements.txt"
            
        if not requirements_file.exists():
            logger.error(f"Requirements file not found: {requirements_file}")
            return False
        
        try:
            # Use specialized installer with proper error handling
            pip_exe = self.get_pip_executable()
            installer = DependencyInstaller(pip_exe)
            
            logger.info(f"Installing dependencies from {requirements_file}")
            results = installer.install_requirements_file(requirements_file)
            
            # Generate summary
            summary = installer.get_installation_summary(results)
            
            # Log results
            if summary['overall_success']:
                logger.info(f"All dependencies installed successfully ({summary['successful_packages']} packages)")
                for warning in summary['warnings']:
                    logger.warning(warning)
                return True
            else:
                logger.error(f"Dependency installation failed: {summary['failed_packages']} packages failed")
                for failed in summary['failed']:
                    logger.error(f"  {failed['package']}: {failed['error']}")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error during dependency installation: {e}")
            return False
    
    def setup_dependencies(self) -> bool:
        """Complete dependency setup including virtual environment and package installation.
        
        Returns:
            True if successful, False otherwise
        """
        # First validate the Python version
        if not self.validate_environment():
            return False
            
        # Create virtual environment
        if not self.setup_virtual_env():
            return False
            
        # Install dependencies
        if not self.install_dependencies():
            return False
            
        logger.info("Environment setup completed successfully")
        return True
    
    def is_venv_active(self) -> bool:
        """Check if we're running in the project's virtual environment.
        
        Returns:
            True if running in project venv, False otherwise
        """
        # Check if we're in any virtual environment
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            return False
            
        # Check if it's our project's virtual environment
        current_python = Path(sys.executable)
        expected_python = Path(self.get_python_executable())
        
        try:
            return current_python.resolve() == expected_python.resolve()
        except Exception:
            return False
    
    def activate_venv_command(self) -> str:
        """Get the command to activate the virtual environment.
        
        Returns:
            Shell command to activate the virtual environment
        """
        if sys.platform == "win32":
            activate_script = self.venv_path / "Scripts" / "activate.bat"
            return str(activate_script)
        else:
            activate_script = self.venv_path / "bin" / "activate"
            return f"source {activate_script}"