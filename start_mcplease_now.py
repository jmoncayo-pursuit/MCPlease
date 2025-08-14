#!/usr/bin/env python3
"""
MCPlease Launcher - One command to rule them all
"""

import subprocess
import sys
import time
from pathlib import Path

def main():
    print("🚀 Starting MCPlease...")
    
    # Start the API server
    api_file = Path("mcplease_api.py")
    if not api_file.exists():
        print("❌ API server not found. Run one_step.py first.")
        return
    
    try:
        print("📡 Starting API server on http://localhost:8000")
        print("🔌 VSCode Continue.dev should now work!")
        print("⏹️  Press Ctrl+C to stop")
        
        subprocess.run([sys.executable, str(api_file)])
        
    except KeyboardInterrupt:
        print("\n👋 MCPlease stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
