#!/usr/bin/env python3
"""
Environment setup script for AI model integration.

This script can be run from the project root to setup the Python environment.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from environment.setup import main
    
    if __name__ == "__main__":
        # Change to project root directory
        os.chdir(project_root)
        main()
        
except ImportError as e:
    print(f"Error importing environment setup modules: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)