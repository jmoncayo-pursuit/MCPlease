"""Installer-specific configuration management."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class InstallerConfig:
    """Configuration created during installation."""
    
    # Installation metadata
    installer_version: str = "1.0.0"
    installation_date: str = ""
    python_version: str = ""
    uv_version: str = ""
    
    # Hardware detection results
    detected_memory_gb: float = 0.0
    detected_cpu_count: int = 0
    detected_architecture: str = ""
    detected_platform: str = ""
    detected_gpu: Dict[str, Any] = None
    is_raspberry_pi: bool = False
    
    # Installation choices
    dev_dependencies: bool = False
    ai_model_downloaded: bool = False
    selected_ai_model: str = "disabled"
    selected_transport: List[str] = None
    selected_security_level: str = "basic"
    
    # Installation results
    installation_successful: bool = False
    failed_components: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.installation_date == "":
            self.installation_date = datetime.now().isoformat()
        if self.detected_gpu is None:
            self.detected_gpu = {"available": False, "type": None, "memory_gb": 0}
        if self.selected_transport is None:
            self.selected_transport = ["stdio"]
        if self.failed_components is None:
            self.failed_components = []
        if self.warnings is None:
            self.warnings = []


class InstallerConfigManager:
    """Manages installer-specific configuration."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize installer config manager.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or self._find_project_root()
        self.config_dir = self.project_root / ".mcplease"
        self.installer_config_file = self.config_dir / "installer.json"
    
    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        current = Path(__file__).parent
        
        while current != current.parent:
            if any((current / marker).exists() for marker in ["pyproject.toml", "setup.py", ".git"]):
                return current
            current = current.parent
        
        return Path.cwd()
    
    def save_installer_config(self, config: InstallerConfig) -> None:
        """Save installer configuration.
        
        Args:
            config: Installer configuration to save
        """
        self.config_dir.mkdir(exist_ok=True)
        
        with open(self.installer_config_file, "w") as f:
            json.dump(asdict(config), f, indent=2)
        
        logger.info(f"Installer configuration saved to {self.installer_config_file}")
    
    def load_installer_config(self) -> Optional[InstallerConfig]:
        """Load installer configuration.
        
        Returns:
            Installer configuration if available
        """
        if not self.installer_config_file.exists():
            return None
        
        try:
            with open(self.installer_config_file) as f:
                data = json.load(f)
            
            return InstallerConfig(**data)
        except Exception as e:
            logger.warning(f"Failed to load installer config: {e}")
            return None
    
    def get_installation_summary(self) -> Dict[str, Any]:
        """Get installation summary.
        
        Returns:
            Installation summary
        """
        config = self.load_installer_config()
        if not config:
            return {"status": "not_installed", "message": "No installation found"}
        
        summary = {
            "status": "installed" if config.installation_successful else "failed",
            "installation_date": config.installation_date,
            "installer_version": config.installer_version,
            "python_version": config.python_version,
            "hardware": {
                "memory_gb": config.detected_memory_gb,
                "cpu_count": config.detected_cpu_count,
                "architecture": config.detected_architecture,
                "platform": config.detected_platform,
                "is_raspberry_pi": config.is_raspberry_pi,
                "gpu": config.detected_gpu
            },
            "configuration": {
                "ai_model": config.selected_ai_model,
                "transport": config.selected_transport,
                "security_level": config.selected_security_level,
                "dev_dependencies": config.dev_dependencies
            }
        }
        
        if config.failed_components:
            summary["failed_components"] = config.failed_components
        
        if config.warnings:
            summary["warnings"] = config.warnings
        
        return summary
    
    def check_installation_health(self) -> Dict[str, Any]:
        """Check installation health.
        
        Returns:
            Installation health status
        """
        config = self.load_installer_config()
        if not config:
            return {
                "healthy": False,
                "issues": ["No installation configuration found"],
                "recommendations": ["Run installation script"]
            }
        
        issues = []
        recommendations = []
        
        # Check if installation was successful
        if not config.installation_successful:
            issues.append("Installation was not completed successfully")
            recommendations.append("Re-run installation script")
        
        # Check for failed components
        if config.failed_components:
            issues.extend([f"Component failed: {comp}" for comp in config.failed_components])
            recommendations.append("Check logs and re-run installation")
        
        # Check if AI model was supposed to be downloaded but wasn't
        if config.selected_ai_model != "disabled" and not config.ai_model_downloaded:
            issues.append("AI model was not downloaded")
            recommendations.append("Run: uv run python download_model.py")
        
        # Check configuration files exist
        main_config_file = self.config_dir / "config.json"
        if not main_config_file.exists():
            issues.append("Main configuration file missing")
            recommendations.append("Re-run installation script")
        
        env_file = self.project_root / ".env"
        if not env_file.exists():
            issues.append("Environment file missing")
            recommendations.append("Re-run installation script")
        
        # Check virtual environment
        venv_path = self.project_root / ".venv"
        if not venv_path.exists():
            issues.append("Virtual environment missing")
            recommendations.append("Re-run installation script")
        
        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "warnings": config.warnings if config else []
        }
    
    def update_installation_status(self, successful: bool, failed_components: List[str] = None, warnings: List[str] = None) -> None:
        """Update installation status.
        
        Args:
            successful: Whether installation was successful
            failed_components: List of failed components
            warnings: List of warnings
        """
        config = self.load_installer_config()
        if not config:
            logger.warning("No installer config found to update")
            return
        
        config.installation_successful = successful
        if failed_components:
            config.failed_components.extend(failed_components)
        if warnings:
            config.warnings.extend(warnings)
        
        self.save_installer_config(config)


def get_installer_config() -> Optional[InstallerConfig]:
    """Get installer configuration.
    
    Returns:
        Installer configuration if available
    """
    manager = InstallerConfigManager()
    return manager.load_installer_config()


def create_installer_config_from_hardware(hardware_config: Dict[str, Any], installation_options: Dict[str, Any]) -> InstallerConfig:
    """Create installer configuration from hardware detection and options.
    
    Args:
        hardware_config: Hardware configuration from detection
        installation_options: Installation options chosen
        
    Returns:
        Installer configuration
    """
    import sys
    import subprocess
    
    # Get uv version if available
    uv_version = "unknown"
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            uv_version = result.stdout.strip()
    except Exception:
        pass
    
    return InstallerConfig(
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        uv_version=uv_version,
        detected_memory_gb=hardware_config.get("memory_gb", 0.0),
        detected_cpu_count=hardware_config.get("cpu_count", 0),
        detected_architecture=hardware_config.get("architecture", ""),
        detected_platform=hardware_config.get("platform", ""),
        detected_gpu=hardware_config.get("gpu", {"available": False, "type": None, "memory_gb": 0}),
        is_raspberry_pi=hardware_config.get("is_raspberry_pi", False),
        dev_dependencies=installation_options.get("dev", False),
        selected_ai_model=hardware_config.get("recommended_config", {}).get("ai_model", "disabled"),
        selected_transport=hardware_config.get("recommended_config", {}).get("transport", ["stdio"]),
        selected_security_level=hardware_config.get("recommended_config", {}).get("security", "basic"),
        ai_model_downloaded=False,  # Will be updated during installation
        installation_successful=False  # Will be updated at end of installation
    )