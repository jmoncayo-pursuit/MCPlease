"""Environment validation utilities."""

import sys
import logging
from pathlib import Path
from typing import List, Tuple

from .manager import EnvironmentManager

logger = logging.getLogger(__name__)


class EnvironmentValidator:
    """Validates and reports on environment setup."""
    
    def __init__(self, project_root: Path = None):
        """Initialize validator.
        
        Args:
            project_root: Root directory of the project
        """
        self.env_manager = EnvironmentManager(project_root)
        self.issues: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validation checks.
        
        Returns:
            Tuple of (is_valid, issues, warnings)
        """
        self.issues.clear()
        self.warnings.clear()
        
        # Check Python version
        is_valid, message = self.env_manager.check_python_version()
        if not is_valid:
            self.issues.append(f"Python version issue: {message}")
        
        # Check virtual environment
        if not self.env_manager.venv_path.exists():
            self.warnings.append("Virtual environment not found - run setup to create it")
        else:
            if not self.env_manager.is_venv_active():
                self.warnings.append(f"Virtual environment exists but not active. Activate with: {self.env_manager.activate_venv_command()}")
        
        # Check requirements file
        requirements_file = self.env_manager.project_root / "requirements.txt"
        if not requirements_file.exists():
            self.issues.append("requirements.txt not found in project root")
        
        return len(self.issues) == 0, self.issues.copy(), self.warnings.copy()
    
    def print_validation_report(self) -> None:
        """Print a detailed validation report."""
        is_valid, issues, warnings = self.validate_all()
        
        print("=" * 50)
        print("ENVIRONMENT VALIDATION REPORT")
        print("=" * 50)
        
        # Python version info
        version_valid, version_msg = self.env_manager.check_python_version()
        status = "✓" if version_valid else "✗"
        print(f"{status} Python Version: {version_msg}")
        
        # Virtual environment info
        if self.env_manager.venv_path.exists():
            active_status = "✓ Active" if self.env_manager.is_venv_active() else "⚠ Inactive"
            print(f"✓ Virtual Environment: Found at {self.env_manager.venv_path} ({active_status})")
        else:
            print(f"✗ Virtual Environment: Not found at {self.env_manager.venv_path}")
        
        # Requirements file
        requirements_file = self.env_manager.project_root / "requirements.txt"
        req_status = "✓" if requirements_file.exists() else "✗"
        print(f"{req_status} Requirements File: {requirements_file}")
        
        # Issues
        if issues:
            print("\nISSUES (must be fixed):")
            for issue in issues:
                print(f"  ✗ {issue}")
        
        # Warnings
        if warnings:
            print("\nWARNINGS (recommended fixes):")
            for warning in warnings:
                print(f"  ⚠ {warning}")
        
        # Overall status
        print("\n" + "=" * 50)
        if is_valid:
            print("✓ ENVIRONMENT VALIDATION PASSED")
            if warnings:
                print("  Note: There are warnings that should be addressed")
        else:
            print("✗ ENVIRONMENT VALIDATION FAILED")
            print("  Fix the issues above before proceeding")
        print("=" * 50)


def main():
    """Main entry point for environment validation."""
    logging.basicConfig(level=logging.INFO)
    
    validator = EnvironmentValidator()
    validator.print_validation_report()
    
    is_valid, issues, warnings = validator.validate_all()
    
    if not is_valid:
        print("\nTo fix environment issues, run:")
        print("  python -m src.environment.setup")
        sys.exit(1)
    
    if warnings:
        sys.exit(2)  # Exit with warning code
    
    sys.exit(0)


if __name__ == "__main__":
    main()