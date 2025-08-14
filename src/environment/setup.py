"""Automated environment setup script."""

import sys
import logging
from pathlib import Path

from .manager import EnvironmentManager
from .validator import EnvironmentValidator

logger = logging.getLogger(__name__)


class EnvironmentSetup:
    """Handles automated environment setup."""
    
    def __init__(self, project_root: Path = None):
        """Initialize setup handler.
        
        Args:
            project_root: Root directory of the project
        """
        self.env_manager = EnvironmentManager(project_root)
        self.validator = EnvironmentValidator(project_root)
    
    def run_setup(self, force: bool = False) -> bool:
        """Run the complete environment setup process.
        
        Args:
            force: Force recreation of virtual environment if it exists
            
        Returns:
            True if setup successful, False otherwise
        """
        print("Starting environment setup...")
        
        # Validate Python version first
        if not self.env_manager.validate_environment():
            print("❌ Environment validation failed - cannot proceed with setup")
            return False
        
        # Handle existing virtual environment
        if self.env_manager.venv_path.exists():
            if force:
                print(f"🔄 Removing existing virtual environment at {self.env_manager.venv_path}")
                import shutil
                shutil.rmtree(self.env_manager.venv_path)
            else:
                print(f"✓ Virtual environment already exists at {self.env_manager.venv_path}")
                print("  Use --force to recreate it")
        
        # Setup virtual environment
        if not self.env_manager.venv_path.exists():
            print("📦 Creating virtual environment...")
            if not self.env_manager.setup_virtual_env():
                print("❌ Failed to create virtual environment")
                return False
            print("✓ Virtual environment created successfully")
        
        # Install dependencies
        print("📥 Installing dependencies...")
        if not self.env_manager.install_dependencies():
            print("❌ Failed to install dependencies")
            return False
        print("✓ Dependencies installed successfully")
        
        # Final validation
        print("🔍 Running final validation...")
        is_valid, issues, warnings = self.validator.validate_all()
        
        if issues:
            print("❌ Setup completed but validation found issues:")
            for issue in issues:
                print(f"  • {issue}")
            return False
        
        if warnings:
            print("⚠️ Setup completed with warnings:")
            for warning in warnings:
                print(f"  • {warning}")
        
        print("✅ Environment setup completed successfully!")
        
        # Show activation instructions
        if not self.env_manager.is_venv_active():
            print(f"\n📋 To activate the virtual environment, run:")
            print(f"   {self.env_manager.activate_venv_command()}")
        
        return True
    
    def print_setup_info(self) -> None:
        """Print information about the setup process."""
        print("Environment Setup Information")
        print("=" * 40)
        print(f"Project Root: {self.env_manager.project_root}")
        print(f"Virtual Environment: {self.env_manager.venv_path}")
        print(f"Python Executable: {self.env_manager.get_python_executable()}")
        print(f"Pip Executable: {self.env_manager.get_pip_executable()}")
        
        # Show supported Python versions
        versions = [f"{v[0]}.{v[1]}" for v in EnvironmentManager.SUPPORTED_PYTHON_VERSIONS]
        print(f"Supported Python Versions: {', '.join(versions)}")
        
        # Current Python version
        current_version = sys.version_info[:2]
        print(f"Current Python Version: {current_version[0]}.{current_version[1]}")


def main():
    """Main entry point for environment setup."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Python environment for AI model integration")
    parser.add_argument("--force", action="store_true", help="Force recreation of virtual environment")
    parser.add_argument("--info", action="store_true", help="Show setup information only")
    parser.add_argument("--validate", action="store_true", help="Run validation only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    setup = EnvironmentSetup()
    
    if args.info:
        setup.print_setup_info()
        return
    
    if args.validate:
        validator = EnvironmentValidator()
        validator.print_validation_report()
        is_valid, issues, warnings = validator.validate_all()
        sys.exit(0 if is_valid else 1)
    
    # Run setup
    success = setup.run_setup(force=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()