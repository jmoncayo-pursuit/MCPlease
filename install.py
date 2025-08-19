#!/usr/bin/env python3
"""
MCPlease MCP Server - One-Command Installation

This script provides a single command to install MCPlease MCP Server
with automatic hardware detection and optimal configuration.

Usage:
    python install.py                    # Full installation
    python install.py --dev             # Install with dev dependencies
    python install.py --skip-model      # Skip AI model download
    python install.py --help            # Show help
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Main installation entry point."""
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Path to the actual installer
    installer_script = project_root / "scripts" / "install_uv.py"
    
    if not installer_script.exists():
        print("❌ Installation script not found!")
        print(f"   Expected: {installer_script}")
        sys.exit(1)
    
    # Forward all arguments to the actual installer
    cmd = [sys.executable, str(installer_script)] + sys.argv[1:]
    
    try:
        # Run the installer
        result = subprocess.run(cmd, cwd=project_root)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\n⏹️  Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()