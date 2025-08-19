#!/usr/bin/env python3
"""
MCPlease IDE Configuration Script
Auto-generates MCP configuration for Cursor, VS Code, and Continue.dev
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

def get_repo_root() -> Path:
    """Get the repository root directory"""
    current = Path(__file__).resolve()
    return current.parent.parent

def setup_cursor_mcp() -> bool:
    """Setup MCP configuration for Cursor"""
    cursor_dir = Path.home() / ".cursor"
    cursor_dir.mkdir(exist_ok=True)
    
    mcp_config = cursor_dir / "mcp.json"
    repo_root = get_repo_root()
    
    config = {
        "mcpServers": {
            "MCPlease": {
                "command": str(repo_root / ".venv" / "bin" / "python"),
                "args": ["-u", str(repo_root / "mcplease_mcp_server.py")],
                "cwd": str(repo_root),
                "env": {"PYTHONUNBUFFERED": "1"},
                "enabled": True
            }
        }
    }
    
    # Handle Windows paths
    if sys.platform == "win32":
        config["mcpServers"]["MCPlease"]["command"] = str(repo_root / ".venv" / "Scripts" / "python.exe")
    
    try:
        with open(mcp_config, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Cursor MCP config created: {mcp_config}")
        return True
    except Exception as e:
        print(f"❌ Failed to create Cursor config: {e}")
        return False

def setup_vscode_mcp() -> bool:
    """Setup MCP configuration for VS Code"""
    vscode_dir = Path.home() / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    
    mcp_config = vscode_dir / "mcp.json"
    repo_root = get_repo_root()
    
    config = {
        "mcpServers": {
            "MCPlease": {
                "command": str(repo_root / ".venv" / "bin" / "python"),
                "args": ["-u", str(repo_root / "mcplease_mcp_server.py")],
                "cwd": str(repo_root),
                "env": {"PYTHONUNBUFFERED": "1"},
                "enabled": True
            }
        }
    }
    
    # Handle Windows paths
    if sys.platform == "win32":
        config["mcpServers"]["MCPlease"]["command"] = str(repo_root / ".venv" / "Scripts" / "python.exe")
    
    try:
        with open(mcp_config, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ VS Code MCP config created: {mcp_config}")
        return True
    except Exception as e:
        print(f"❌ Failed to create VS Code config: {e}")
        return False

def setup_continue_dev() -> bool:
    """Setup Continue.dev configuration"""
    repo_root = get_repo_root()
    continue_config = repo_root / ".continue" / "config.json"
    continue_config.parent.mkdir(exist_ok=True)
    
    config = {
        "models": [
            {
                "title": "MCPlease Local",
                "provider": "openai",
                "model": "oss-20b-local",
                "apiBase": "http://localhost:8000/v1",
                "apiKey": "not-needed"
            }
        ],
        "defaultModel": "MCPlease Local"
    }
    
    try:
        with open(continue_config, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Continue.dev config created: {continue_config}")
        return True
    except Exception as e:
        print(f"❌ Failed to create Continue.dev config: {e}")
        return False

def create_startup_scripts() -> bool:
    """Create platform-specific startup scripts"""
    repo_root = get_repo_root()
    
    # Windows batch file
    if sys.platform == "win32":
        batch_file = repo_root / "start.bat"
        batch_content = """@echo off
REM MCPlease Windows Startup Script
echo Starting MCPlease MCP Server...
cd /d "%~dp0"
call .venv\\Scripts\\activate.bat
python mcplease_mcp_server.py --transport stdio
pause
"""
        try:
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            print(f"✅ Windows startup script created: {batch_file}")
        except Exception as e:
            print(f"❌ Failed to create Windows script: {e}")
    
    # Unix shell script (already exists as start.sh)
    unix_script = repo_root / "start.sh"
    if unix_script.exists():
        try:
            os.chmod(unix_script, 0o755)
            print(f"✅ Unix startup script permissions set: {unix_script}")
        except Exception as e:
            print(f"❌ Failed to set Unix script permissions: {e}")
    
    return True

def main():
    """Main setup function"""
    print("🚀 MCPlease IDE Configuration Setup")
    print("=" * 40)
    
    repo_root = get_repo_root()
    print(f"Repository: {repo_root}")
    
    # Check if virtual environment exists
    venv_path = repo_root / ".venv"
    if not venv_path.exists():
        print("⚠️  Virtual environment not found. Run './start.sh' first to create it.")
        return False
    
    print(f"Virtual environment: {venv_path}")
    
    # Setup configurations
    success_count = 0
    
    print("\n📝 Setting up IDE configurations...")
    
    if setup_cursor_mcp():
        success_count += 1
    
    if setup_vscode_mcp():
        success_count += 1
    
    if setup_continue_dev():
        success_count += 1
    
    if create_startup_scripts():
        success_count += 1
    
    print(f"\n✅ Setup complete! {success_count}/4 configurations created.")
    
    if success_count >= 2:
        print("\n🎯 Next steps:")
        print("1. Restart your IDE (Cursor/VS Code)")
        print("2. Look for 'MCPlease' in Workspace Tools → MCP")
        print("3. Or run './start.sh --http' for Continue.dev")
        print("4. Test with the 'health/check' tool")
        return True
    else:
        print("\n❌ Setup incomplete. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
