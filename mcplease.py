#!/usr/bin/env python3
"""
MCPlease - Easy-to-use offline AI coding assistant

This is the main entry point that makes MCPlease work out of the box with minimal setup.
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add src to Python path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from simple_ai_mcp_server import SimpleAIMCPServer
    from environment.manager import EnvironmentManager
    from utils.logging import get_logger
except ImportError as e:
    # Fallback to basic functionality if imports fail
    print(f"⚠️  Some advanced features unavailable: {e}")
    print("Running in basic mode...")
    SimpleAIMCPServer = None
    EnvironmentManager = None

logger = get_logger(__name__)


def print_banner():
    """Print MCPlease banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                          MCPlease MVP                        ║
║                 Offline AI Coding Assistant                  ║
║                                                              ║
║  🤖 Powered by gpt-oss-20b (21.5B parameters)              ║
║  🔒 100% Offline & Private                                   ║
║  💻 Optimized for Mac (16GB+ RAM)                           ║
║  ⚡ Zero-configuration setup                                 ║
╚══════════════════════════════════════════════════════════════╝
""")


async def check_system_requirements():
    """Check if system meets requirements."""
    print("🔍 Checking system requirements...")
    
    if EnvironmentManager:
        env_manager = EnvironmentManager()
        
        # Check Python version
        is_valid, message = env_manager.check_python_version()
        if not is_valid:
            print(f"❌ {message}")
            return False
        
        print(f"✅ {message}")
    else:
        print("✅ Python version check skipped (basic mode)")
    
    # Check memory
    import psutil
    memory_gb = psutil.virtual_memory().total / (1024**3)
    if memory_gb < 12:
        print(f"⚠️  Warning: Only {memory_gb:.1f}GB RAM detected. 16GB+ recommended")
    else:
        print(f"✅ Memory: {memory_gb:.1f}GB RAM detected")
    
    return True


async def setup_environment():
    """Set up the environment if needed."""
    print("🔧 Setting up environment...")
    
    if not EnvironmentManager:
        print("⚠️  Advanced environment management not available")
        print("📦 Please install dependencies manually:")
        print("   pip install torch vllm fastapi psutil requests tqdm")
        return True
    
    env_manager = EnvironmentManager()
    
    try:
        # Set up virtual environment and install dependencies
        print("📦 Setting up virtual environment and dependencies...")
        success = env_manager.setup_dependencies()
        if not success:
            print("❌ Failed to set up dependencies")
            print("💡 Try manual installation:")
            print("   pip install torch vllm fastapi psutil requests tqdm")
            return False
        print("✅ Dependencies set up successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        print("💡 Try manual installation:")
        print("   pip install torch vllm fastapi psutil requests tqdm")
        return False


async def download_model_if_needed():
    """Download model if not already present."""
    print("🤖 Checking AI model...")
    
    # Check if model exists
    model_path = Path("models/gpt-oss-20b")
    if model_path.exists():
        print("✅ AI model already downloaded")
        return str(model_path)
    
    print("📥 AI model not found - server will use fallback responses")
    print("💡 To enable full AI features, download the model manually:")
    print("   1. Install huggingface-hub: pip install huggingface-hub")
    print("   2. Download model: huggingface-cli download openai/gpt-oss-20b --local-dir models/gpt-oss-20b")
    print("   3. Restart MCPlease")
    
    # Return None to indicate fallback mode
    return None


async def start_server(model_path: str, max_memory: int, debug: bool = False):
    """Start the AI MCP server."""
    print("🚀 Starting AI MCP server...")
    
    if not SimpleAIMCPServer:
        print("❌ Server components not available. Please check installation.")
        sys.exit(1)
    
    try:
        # Determine if AI should be enabled
        enable_ai = model_path is not None and Path(model_path).exists()
        
        server = SimpleAIMCPServer(enable_ai=enable_ai)
        
        print("✅ AI MCP server is ready!")
        print("\n📋 Server Information:")
        if enable_ai:
            print(f"   Mode: AI-powered with fallback")
            print(f"   Model: gpt-oss-20b")
            print(f"   Model Path: {model_path}")
        else:
            print(f"   Mode: Fallback responses only")
            print(f"   Note: AI model not found, using intelligent fallbacks")
        print(f"   Memory Limit: {max_memory}GB")
        print("\n🔌 Connect your IDE using MCP protocol")
        print("   The server is listening on stdin/stdout")
        print("\n💡 Tip: Use Ctrl+C to stop the server")
        print("-" * 60)
        
        await server.handle_stdio()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down MCPlease...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


async def run_setup_mode():
    """Run in setup mode to prepare the system."""
    print_banner()
    print("🛠️  Running MCPlease setup...")
    
    # Check system requirements
    if not await check_system_requirements():
        sys.exit(1)
    
    # Set up environment
    if not await setup_environment():
        sys.exit(1)
    
    # Download model
    model_path = await download_model_if_needed()
    if not model_path:
        sys.exit(1)
    
    print("\n🎉 MCPlease setup completed successfully!")
    print("\n🚀 To start the server, run:")
    print("   python mcplease.py --start")
    print("\n📖 For more options, run:")
    print("   python mcplease.py --help")


async def run_server_mode(args):
    """Run in server mode."""
    if not args.quiet:
        print_banner()
    
    # Quick system check
    if not await check_system_requirements():
        if not args.force:
            print("Use --force to start anyway")
            sys.exit(1)
    
    # Find model path
    model_path = args.model_path
    if not model_path:
        default_path = Path("models/gpt-oss-20b")
        if default_path.exists():
            model_path = str(default_path)
        else:
            print("❌ No model found. Run setup first:")
            print("   python mcplease.py --setup")
            sys.exit(1)
    
    # Start server
    await start_server(model_path, args.max_memory, args.debug)


def show_status():
    """Show system status."""
    print_banner()
    print("📊 MCPlease System Status")
    print("-" * 40)
    
    # Check Python
    import sys
    print(f"Python: {sys.version.split()[0]} ✅")
    
    # Check memory
    import psutil
    memory = psutil.virtual_memory()
    print(f"Memory: {memory.total / (1024**3):.1f}GB total, {memory.available / (1024**3):.1f}GB available")
    
    # Check model
    model_path = Path("models/gpt-oss-20b")
    if model_path.exists():
        print(f"Model: Downloaded ✅")
    else:
        print(f"Model: Not downloaded ❌")
    
    # Check dependencies
    try:
        import torch
        import vllm
        import fastapi
        print("Dependencies: Installed ✅")
    except ImportError as e:
        print(f"Dependencies: Missing ({e}) ❌")
    
    print("\n💡 Run 'python mcplease.py --setup' to fix any issues")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCPlease - Offline AI Coding Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mcplease.py --setup          # First-time setup
  python mcplease.py --start          # Start the server
  python mcplease.py --status         # Check system status
  python mcplease.py --start --debug  # Start with debug logging
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--setup", action="store_true", 
                           help="Run first-time setup")
    mode_group.add_argument("--start", action="store_true", 
                           help="Start the MCP server")
    mode_group.add_argument("--status", action="store_true", 
                           help="Show system status")
    
    # Server options
    parser.add_argument("--model-path", 
                       help="Path to model directory")
    parser.add_argument("--max-memory", type=int, default=12, 
                       help="Maximum memory to use in GB (default: 12)")
    parser.add_argument("--debug", action="store_true", 
                       help="Enable debug logging")
    parser.add_argument("--quiet", action="store_true", 
                       help="Suppress banner and non-essential output")
    parser.add_argument("--force", action="store_true", 
                       help="Force start even if requirements not met")
    
    args = parser.parse_args()
    
    try:
        if args.setup:
            asyncio.run(run_setup_mode())
        elif args.start:
            asyncio.run(run_server_mode(args))
        elif args.status:
            show_status()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()