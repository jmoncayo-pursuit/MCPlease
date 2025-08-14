#!/usr/bin/env python3
"""Standalone dependency installation script with comprehensive error handling."""

import sys
import logging
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from environment.installer import DependencyInstaller, InstallationResult
from environment.manager import EnvironmentManager


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def print_installation_summary(results: list[InstallationResult], summary: dict) -> None:
    """Print a detailed installation summary."""
    print("\n" + "="*60)
    print("DEPENDENCY INSTALLATION SUMMARY")
    print("="*60)
    
    # System information
    print(f"System: {summary['system_info']['platform']} {summary['system_info']['machine']}")
    print(f"Python: {summary['system_info']['python_version']}")
    if summary['system_info']['is_apple_silicon']:
        print("Hardware: Apple Silicon Mac")
    elif summary['system_info']['is_mac']:
        print("Hardware: Intel Mac")
    
    print(f"\nOverall Status: {'✅ SUCCESS' if summary['overall_success'] else '❌ FAILED'}")
    print(f"Successful: {summary['successful_packages']}")
    print(f"Failed: {summary['failed_packages']}")
    
    # Successful installations
    if summary['successful']:
        print(f"\n✅ Successfully Installed:")
        for package in summary['successful']:
            print(f"  • {package}")
    
    # Failed installations
    if summary['failed']:
        print(f"\n❌ Failed Installations:")
        for failed in summary['failed']:
            print(f"  • {failed['package']}: {failed['error']}")
    
    # Warnings
    if summary['warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in summary['warnings']:
            print(f"  • {warning}")
    
    print("\n" + "="*60)


def install_critical_packages_only(installer: DependencyInstaller) -> list[InstallationResult]:
    """Install only critical packages (torch and vLLM)."""
    results = []
    
    print("🔥 Installing critical AI packages...")
    
    # Install torch first
    print("\n📦 Installing PyTorch...")
    torch_result = installer.install_torch()
    results.append(torch_result)
    
    if torch_result.success:
        print("✅ PyTorch installed successfully")
    else:
        print(f"❌ PyTorch installation failed: {torch_result.error_message}")
        return results  # Don't continue if torch fails
    
    # Install vLLM
    print("\n📦 Installing vLLM...")
    vllm_result = installer.install_vllm()
    results.append(vllm_result)
    
    if vllm_result.success:
        print("✅ vLLM installed successfully")
        for warning in vllm_result.warnings:
            print(f"⚠️  {warning}")
    else:
        print(f"❌ vLLM installation failed: {vllm_result.error_message}")
    
    return results


def main():
    """Main installation script."""
    parser = argparse.ArgumentParser(
        description="Install AI model dependencies with error handling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/install_dependencies.py                    # Install all dependencies
  python scripts/install_dependencies.py --critical-only   # Install only torch and vLLM
  python scripts/install_dependencies.py --verbose         # Verbose output
  python scripts/install_dependencies.py --dry-run         # Check compatibility only
        """
    )
    
    parser.add_argument(
        "--critical-only", 
        action="store_true",
        help="Install only critical packages (torch and vLLM)"
    )
    parser.add_argument(
        "--requirements", 
        type=Path,
        default=Path("requirements.txt"),
        help="Path to requirements file (default: requirements.txt)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check compatibility without installing"
    )
    parser.add_argument(
        "--use-venv",
        action="store_true",
        help="Use virtual environment pip (recommended)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    print("🚀 AI Model Dependency Installer")
    print("=" * 40)
    
    try:
        # Determine pip executable
        pip_executable = None
        if args.use_venv:
            env_manager = EnvironmentManager()
            if env_manager.venv_path.exists():
                pip_executable = env_manager.get_pip_executable()
                print(f"Using virtual environment pip: {pip_executable}")
            else:
                print("⚠️  Virtual environment not found, using system pip")
        
        # Create installer
        installer = DependencyInstaller(pip_executable)
        
        # Dry run - compatibility checks only
        if args.dry_run:
            print("\n🔍 Running compatibility checks...")
            
            # Check Python compatibility for critical packages
            for package in ['torch', 'vllm']:
                is_compatible, message = installer.check_python_compatibility(package)
                status = "✅" if is_compatible else "❌"
                print(f"{status} {package}: {message}")
            
            print(f"\n📋 System Information:")
            for key, value in installer.system_info.items():
                print(f"  {key}: {value}")
            
            return
        
        # Install packages
        if args.critical_only:
            results = install_critical_packages_only(installer)
        else:
            if not args.requirements.exists():
                logger.error(f"Requirements file not found: {args.requirements}")
                sys.exit(1)
            
            print(f"\n📦 Installing all dependencies from {args.requirements}")
            results = installer.install_requirements_file(args.requirements)
        
        # Generate and print summary
        summary = installer.get_installation_summary(results)
        print_installation_summary(results, summary)
        
        # Exit with appropriate code
        if summary['overall_success']:
            print("\n🎉 Installation completed successfully!")
            
            # Provide next steps
            if not args.critical_only:
                print("\n📋 Next Steps:")
                print("  1. Activate your virtual environment if not already active")
                print("  2. Run: python -c 'import torch, vllm; print(\"All imports successful!\")'")
                print("  3. Start the MCP server: python src/mcp_server.py")
            
            sys.exit(0)
        else:
            print("\n💥 Installation failed!")
            print("\n🔧 Troubleshooting:")
            print("  1. Check Python version (3.9-3.12 required)")
            print("  2. Ensure sufficient disk space (>10GB)")
            print("  3. Try installing critical packages only: --critical-only")
            print("  4. Check logs above for specific error messages")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()