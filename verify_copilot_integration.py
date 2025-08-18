#!/usr/bin/env python3
"""
MCPlease Copilot Integration Verifier

This script verifies that MCPlease is properly integrated with GitHub Copilot
and provides step-by-step troubleshooting.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║              MCPlease Copilot Verification                ║
║                                                              ║
║  🔍 Checking if MCPlease works with GitHub Copilot       ║
╚══════════════════════════════════════════════════════════════╝
""")

def check_vscode_version():
    """Check if VSCode version supports MCP."""
    print("🔍 Checking VSCode version...")
    
    try:
        result = subprocess.run(["code", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.strip().split('\n')[0]
            print(f"✅ VSCode version: {version_line}")
            
            # Extract version number
            version_parts = version_line.split('.')
            if len(version_parts) >= 2:
                major = int(version_parts[0])
                minor = int(version_parts[1])
                
                if major > 1 or (major == 1 and minor >= 102):
                    print("✅ VSCode version supports MCP")
                    return True
                else:
                    print("❌ VSCode version too old for MCP (need 1.102+)")
                    print("   Update VSCode: https://code.visualstudio.com/")
                    return False
        else:
            print("❌ VSCode not found or not in PATH")
            return False
    except Exception as e:
        print(f"❌ Error checking VSCode: {e}")
        return False

def check_copilot_subscription():
    """Check if GitHub Copilot is available."""
    print("\n🔍 Checking GitHub Copilot...")
    
    print("📝 Manual check required:")
    print("   1. Open VSCode")
    print("   2. Look for GitHub Copilot icon in status bar (bottom right)")
    print("   3. If you see it, Copilot is active")
    print("   4. If not, you need a Copilot subscription")
    
    response = input("\n❓ Do you see the GitHub Copilot icon in VSCode? (y/n): ").lower().strip()
    
    if response == 'y':
        print("✅ GitHub Copilot is available")
        return True
    else:
        print("❌ GitHub Copilot not available")
        print("   Get Copilot: https://github.com/features/copilot")
        return False

def check_mcp_files():
    """Check if MCP files were created correctly."""
    print("\n🔍 Checking MCP files...")
    
    # Check MCP server file
    server_file = Path("mcplease_server.py")
    if server_file.exists():
        print("✅ MCP server file exists")
    else:
        print("❌ MCP server file missing")
        print("   Run: python mcplease_mcp_fixed.py")
        return False
    
    # Check VSCode MCP config
    config_file = Path(".vscode/mcp.json")
    if config_file.exists():
        print("✅ VSCode MCP config exists")
        
        # Verify config content
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if "servers" in config and "mcplease" in config["servers"]:
                print("✅ MCP config is valid")
                return True
            else:
                print("❌ MCP config is invalid")
                return False
        except Exception as e:
            print(f"❌ Error reading MCP config: {e}")
            return False
    else:
        print("❌ VSCode MCP config missing")
        print("   Run: python mcplease_mcp_fixed.py")
        return False

def test_mcp_server():
    """Test if MCP server responds correctly."""
    print("\n🔍 Testing MCP server...")
    
    server_file = Path("mcplease_server.py")
    if not server_file.exists():
        print("❌ MCP server file not found")
        return False
    
    try:
        # Start server process
        process = subprocess.Popen(
            [sys.executable, str(server_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Test initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        # Send request
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response with timeout
        import select
        ready, _, _ = select.select([process.stdout], [], [], 5.0)
        
        if ready:
            response_line = process.stdout.readline()
            response = json.loads(response_line.strip())
            
            if "result" in response and "serverInfo" in response["result"]:
                print("✅ MCP server responds correctly")
                print(f"   Server: {response['result']['serverInfo']['name']}")
                
                # Test tools list
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
                
                process.stdin.write(json.dumps(tools_request) + "\n")
                process.stdin.flush()
                
                ready, _, _ = select.select([process.stdout], [], [], 5.0)
                if ready:
                    tools_response_line = process.stdout.readline()
                    tools_response = json.loads(tools_response_line.strip())
                    
                    if "result" in tools_response and "tools" in tools_response["result"]:
                        tools = tools_response["result"]["tools"]
                        print(f"✅ MCP server provides {len(tools)} tools")
                        for tool in tools:
                            print(f"   • {tool['name']}: {tool['description']}")
                        
                        process.terminate()
                        return True
        
        process.terminate()
        print("❌ MCP server not responding correctly")
        return False
        
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

def check_mcp_in_vscode():
    """Guide user to check MCP integration in VSCode."""
    print("\n🔍 Checking MCP integration in VSCode...")
    
    print("📝 Manual verification steps:")
    print("   1. Open VSCode in this directory")
    print("   2. Press Ctrl+Shift+P (Cmd+Shift+P on Mac)")
    print("   3. Type: 'MCP: List Servers'")
    print("   4. You should see 'mcplease' in the list")
    print("   5. If it shows 'Running' status, integration works!")
    
    response = input("\n❓ Do you see 'mcplease' server in the MCP list? (y/n): ").lower().strip()
    
    if response == 'y':
        print("✅ MCP integration is working")
        return True
    else:
        print("❌ MCP integration not working")
        print("💡 Troubleshooting:")
        print("   • Restart VSCode")
        print("   • Check VSCode version (need 1.102+)")
        print("   • Verify .vscode/mcp.json exists")
        return False

def test_copilot_agent_mode():
    """Guide user to test Copilot Agent mode."""
    print("\n🔍 Testing Copilot Agent mode...")
    
    print("📝 Test steps:")
    print("   1. Open GitHub Copilot Chat in VSCode")
    print("   2. Switch to 'Agent' mode (dropdown at top)")
    print("   3. Type: 'Complete this function: def fibonacci(n):'")
    print("   4. Look for tool usage in the response")
    
    response = input("\n❓ Did Copilot mention using 'complete_code' tool? (y/n): ").lower().strip()
    
    if response == 'y':
        print("🎉 SUCCESS! MCPlease is working with GitHub Copilot!")
        return True
    else:
        print("❌ Tools not being used by Copilot")
        print("💡 Possible issues:")
        print("   • Not in Agent mode")
        print("   • MCP server not running")
        print("   • VSCode needs restart")
        return False

def provide_debugging_steps():
    """Provide detailed debugging steps."""
    print("\n🔧 Debugging Steps:")
    print("")
    
    print("1. **Check MCP Server Status:**")
    print("   • Command Palette → 'MCP: List Servers'")
    print("   • Should show 'mcplease' with 'Running' status")
    print("")
    
    print("2. **Check MCP Server Output:**")
    print("   • Command Palette → 'MCP: List Servers'")
    print("   • Select 'mcplease' → 'Show Output'")
    print("   • Look for errors in the log")
    print("")
    
    print("3. **Restart MCP Server:**")
    print("   • Command Palette → 'MCP: List Servers'")
    print("   • Select 'mcplease' → 'Restart'")
    print("")
    
    print("4. **Check Agent Mode:**")
    print("   • Open Copilot Chat")
    print("   • Dropdown should show 'Agent' option")
    print("   • If not, update VSCode or check Copilot subscription")
    print("")
    
    print("5. **Force Tool Usage:**")
    print("   • In Agent mode, type: '#complete_code'")
    print("   • This directly references the MCPlease tool")
    print("")

def main():
    """Run complete verification."""
    print_banner()
    
    print("🎯 This script will verify MCPlease works with GitHub Copilot")
    print("   We'll check each component step by step")
    print("")
    
    all_good = True
    
    # Check VSCode version
    if not check_vscode_version():
        all_good = False
    
    # Check Copilot subscription
    if not check_copilot_subscription():
        all_good = False
    
    # Check MCP files
    if not check_mcp_files():
        all_good = False
    
    # Test MCP server
    if not test_mcp_server():
        all_good = False
    
    if all_good:
        # Check VSCode integration
        if not check_mcp_in_vscode():
            all_good = False
        
        # Test Copilot integration
        if not test_copilot_agent_mode():
            all_good = False
    
    print("")
    if all_good:
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                🎉 VERIFICATION COMPLETE! 🎉                ║")
        print("║                                                              ║")
        print("║  MCPlease is working with GitHub Copilot!                ║")
        print("║                                                              ║")
        print("║  You can now use MCPlease tools in Copilot Agent mode    ║")
        print("╚══════════════════════════════════════════════════════════════╝")
    else:
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                ⚠️  ISSUES DETECTED ⚠️                      ║")
        print("║                                                              ║")
        print("║  Some components are not working correctly.                ║")
        print("║  Follow the debugging steps above to fix issues.          ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        
        provide_debugging_steps()

if __name__ == "__main__":
    main()