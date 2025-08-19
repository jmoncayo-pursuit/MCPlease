#!/usr/bin/env python3
"""Comprehensive test script for MCP server setup issues.

This script tests:
1. Python environment and dependencies
2. File paths and working directory
3. Module imports
4. Basic MCP server functionality
5. Stdio communication

Run this to diagnose why the MCP server exits before responding to initialize.
"""

import json
import os
import sys
import subprocess
import time
from pathlib import Path


def test_environment():
    """Test Python environment and basic setup."""
    print("=== Environment Tests ===")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check if we're in a virtual environment
    venv = os.environ.get('VIRTUAL_ENV')
    if venv:
        print(f"Virtual environment: {venv}")
    else:
        print("No virtual environment detected")
    
    # Check PYTHONPATH
    pythonpath = os.environ.get('PYTHONPATH', '')
    if pythonpath:
        print(f"PYTHONPATH: {pythonpath}")
    else:
        print("PYTHONPATH: not set")
    
    print()


def test_dependencies():
    """Test if required packages are available."""
    print("=== Dependency Tests ===")
    
    required_packages = [
        'mcp',
        'json',
        'asyncio',
        'logging',
        'pathlib',
        'typing'
    ]
    
    for package in required_packages:
        try:
            if package == 'mcp':
                import mcp
                import mcp.server
                import mcp.types
                print(f"✓ {package}: {mcp.__version__ if hasattr(mcp, '__version__') else 'imported'}")
            else:
                __import__(package)
                print(f"✓ {package}: available")
        except ImportError as e:
            print(f"✗ {package}: {e}")
        except Exception as e:
            print(f"✗ {package}: {e}")
    
    print()


def test_file_paths():
    """Test if required files exist and are accessible."""
    print("=== File Path Tests ===")
    
    repo_root = Path.cwd()
    required_files = [
        'mcplease_mcp_server.py',
        '.venv/bin/python',
        'requirements.txt',
        'src/mcplease_mcp/__init__.py'
    ]
    
    for file_path in required_files:
        full_path = repo_root / file_path
        if full_path.exists():
            if full_path.is_file():
                print(f"✓ {file_path}: file exists")
            elif full_path.is_dir():
                print(f"✓ {file_path}: directory exists")
        else:
            print(f"✗ {file_path}: not found")
    
    # Check if we can read the main server file
    server_file = repo_root / 'mcplease_mcp_server.py'
    if server_file.exists():
        try:
            content = server_file.read_text()
            if 'class MCPleaseServer' in content:
                print("✓ mcplease_mcp_server.py: contains MCPleaseServer class")
            else:
                print("✗ mcplease_mcp_server.py: missing MCPleaseServer class")
        except Exception as e:
            print(f"✗ mcplease_mcp_server.py: cannot read - {e}")
    
    print()


def test_imports():
    """Test if we can import the server modules."""
    print("=== Import Tests ===")
    
    try:
        # Test basic imports
        import mcplease_mcp_server
        print("✓ mcplease_mcp_server: imported successfully")
        
        # Test if we can create the server class
        from mcplease_mcp_server import MCPleaseServer
        print("✓ MCPleaseServer class: imported successfully")
        
        # Test if we can instantiate it
        server = MCPleaseServer()
        print("✓ MCPleaseServer: instantiated successfully")
        
        # Test basic attributes
        print(f"  - workspace_root: {server.workspace_root}")
        print(f"  - server name: {server.name}")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
    except Exception as e:
        print(f"✗ Other error: {e}")
    
    print()


def test_stdio_communication():
    """Test basic stdio communication with the server."""
    print("=== Stdio Communication Tests ===")
    
    repo_root = Path.cwd()
    server_path = repo_root / 'mcplease_mcp_server.py'
    
    if not server_path.exists():
        print("✗ Server file not found")
        return
    
    try:
        # Start the server process
        print("Starting MCP server process...")
        proc = subprocess.Popen(
            [sys.executable, '-u', str(server_path)],
            cwd=repo_root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0
        )
        
        # Give it a moment to start
        time.sleep(1)
        
        # Check if process is still running
        if proc.poll() is None:
            print("✓ Server process started successfully")
            
            # Try to send a simple message
            try:
                # Send initialize message
                init_msg = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test-client", "version": "0.1.0"}
                    }
                }
                
                msg_data = json.dumps(init_msg).encode('utf-8')
                header = f"Content-Length: {len(msg_data)}\r\n\r\n".encode('ascii')
                
                proc.stdin.write(header)
                proc.stdin.write(msg_data)
                proc.stdin.flush()
                
                print("✓ Initialize message sent")
                
                # Wait a bit for response
                time.sleep(2)
                
                # Check if we got any output
                if proc.stdout.readable():
                    output = proc.stdout.read()
                    if output:
                        print(f"✓ Received output: {output[:100]}...")
                    else:
                        print("⚠ No output received yet")
                
            except Exception as e:
                print(f"✗ Error sending message: {e}")
            
            # Clean up
            proc.terminate()
            proc.wait()
            print("✓ Server process terminated")
            
        else:
            print(f"✗ Server process exited with code: {proc.returncode}")
            stderr_output = proc.stderr.read().decode()
            if stderr_output:
                print(f"Stderr output: {stderr_output}")
    
    except Exception as e:
        print(f"✗ Error testing stdio: {e}")
    
    print()


def test_cursor_config():
    """Test if the Cursor MCP configuration is correct."""
    print("=== Cursor MCP Config Tests ===")
    
    cursor_config_path = Path.home() / '.cursor' / 'mcp.json'
    
    if cursor_config_path.exists():
        try:
            with open(cursor_config_path) as f:
                config = json.load(f)
            
            print("✓ Cursor MCP config found")
            
            # Check MCPlease server config
            if 'mcpServers' in config and 'MCPlease' in config['mcpServers']:
                server_config = config['mcpServers']['MCPlease']
                print("✓ MCPlease server configured")
                
                # Check command
                command = server_config.get('command', '')
                if command:
                    print(f"  - command: {command}")
                    if Path(command).exists():
                        print("    ✓ Command path exists")
                    else:
                        print("    ✗ Command path not found")
                else:
                    print("  - command: not specified")
                
                # Check args
                args = server_config.get('args', [])
                if args:
                    print(f"  - args: {args}")
                else:
                    print("  - args: not specified")
                
                # Check cwd
                cwd = server_config.get('cwd', '')
                if cwd:
                    print(f"  - cwd: {cwd}")
                    if Path(cwd).exists():
                        print("    ✓ CWD path exists")
                    else:
                        print("    ✗ CWD path not found")
                else:
                    print("  - cwd: not specified")
                
                # Check enabled
                enabled = server_config.get('enabled', False)
                print(f"  - enabled: {enabled}")
                
            else:
                print("✗ MCPlease server not configured")
            
        except Exception as e:
            print(f"✗ Error reading config: {e}")
    else:
        print("✗ Cursor MCP config not found")
    
    print()


def main():
    """Run all tests."""
    print("MCP Server Setup Diagnostic Tests")
    print("=" * 50)
    print()
    
    test_environment()
    test_dependencies()
    test_file_paths()
    test_imports()
    test_stdio_communication()
    test_cursor_config()
    
    print("=== Test Summary ===")
    print("If you see any ✗ marks above, those are the issues to fix.")
    print("Common fixes:")
    print("1. Activate virtual environment: source .venv/bin/activate")
    print("2. Install missing packages: pip install mcp")
    print("3. Fix file paths in ~/.cursor/mcp.json")
    print("4. Ensure working directory is correct")


if __name__ == "__main__":
    main()
