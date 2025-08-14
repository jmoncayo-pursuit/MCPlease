#!/usr/bin/env python3
"""
MCPlease Startup Script - The easiest way to start your AI coding assistant

This script provides the simplest possible way to start MCPlease with all
the right settings and error handling.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def print_banner():
    """Print startup banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                        MCPlease                             ║
║                 Starting Your AI Assistant                  ║
╚══════════════════════════════════════════════════════════════╝
""")

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        return True
    return False

def find_mcplease_directory():
    """Find the MCPlease directory."""
    current_dir = Path(__file__).parent
    
    # Check if we're in the right directory
    if (current_dir / "src" / "simple_ai_mcp_server.py").exists():
        return current_dir
    
    # Check common locations
    possible_locations = [
        Path.home() / "mcplease",
        Path.home() / "MCPlease",
        Path.home() / "mcplease-mvp",
        Path.cwd() / "mcplease",
        Path.cwd() / "MCPlease"
    ]
    
    for location in possible_locations:
        if location.exists() and (location / "src" / "simple_ai_mcp_server.py").exists():
            return location
    
    return None

def start_server(mcplease_dir: Path, enable_ai: bool = True, debug: bool = False):
    """Start the MCPlease server."""
    server_script = mcplease_dir / "src" / "simple_ai_mcp_server.py"
    
    if not server_script.exists():
        print(f"❌ Server script not found: {server_script}")
        return False
    
    # Build command
    cmd = [sys.executable, str(server_script)]
    
    if not enable_ai:
        cmd.append("--no-ai")
    
    if debug:
        cmd.append("--debug")
    
    print(f"🚀 Starting MCPlease server...")
    print(f"   Command: {' '.join(cmd)}")
    print(f"   Directory: {mcplease_dir}")
    print(f"   AI Enabled: {'Yes' if enable_ai else 'No (fallback mode)'}")
    print("")
    print("📝 Server is ready when you see 'Simple AI MCP server ready'")
    print("🔌 Connect your IDE to start coding with AI assistance")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Change to MCPlease directory
        os.chdir(mcplease_dir)
        
        # Start the server
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 MCPlease server stopped")
        return True
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        return False
    
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Start MCPlease AI Coding Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_mcplease.py                    # Start with AI (if available)
  python start_mcplease.py --no-ai           # Start with fallbacks only
  python start_mcplease.py --debug           # Start with debug logging
  python start_mcplease.py --find-only       # Just find MCPlease directory
        """
    )
    
    parser.add_argument("--no-ai", action="store_true",
                       help="Disable AI model, use fallback responses only")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug logging")
    parser.add_argument("--find-only", action="store_true",
                       help="Just find and display MCPlease directory")
    
    args = parser.parse_args()
    
    # Print banner
    if not args.find_only:
        print_banner()
    
    # Check Python version
    if not check_python_version():
        print("❌ Python 3.9+ required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    # Find MCPlease directory
    mcplease_dir = find_mcplease_directory()
    
    if not mcplease_dir:
        print("❌ MCPlease directory not found")
        print("")
        print("💡 Make sure you're running this from the MCPlease directory, or")
        print("   MCPlease is installed in one of these locations:")
        print("   • ~/mcplease")
        print("   • ~/MCPlease") 
        print("   • ~/mcplease-mvp")
        print("   • ./mcplease")
        print("   • ./MCPlease")
        sys.exit(1)
    
    if args.find_only:
        print(f"MCPlease directory: {mcplease_dir}")
        return
    
    print(f"✅ Found MCPlease at: {mcplease_dir}")
    
    # Start the server
    success = start_server(mcplease_dir, enable_ai=not args.no_ai, debug=args.debug)
    
    if not success:
        print("")
        print("💡 Troubleshooting tips:")
        print("   • Try: python start_mcplease.py --no-ai")
        print("   • Check: python start_mcplease.py --debug")
        print("   • Verify MCPlease installation")
        sys.exit(1)

if __name__ == "__main__":
    main()