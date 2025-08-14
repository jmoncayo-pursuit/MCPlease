#!/usr/bin/env python3
"""
MCPlease Demo - Show how easy it is to use out of the box

This demo shows the key features of MCPlease working immediately
without complex setup or model downloads.
"""

import json
import subprocess
import sys
from pathlib import Path

def print_banner():
    """Print demo banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                      MCPlease Demo                          ║
║              Easy AI Coding Assistant                       ║
╚══════════════════════════════════════════════════════════════╝
""")

def send_mcp_request(method: str, params: dict = None) -> dict:
    """Send a request to the MCP server and get response."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    
    # Start the server process
    server_path = Path(__file__).parent / "src" / "simple_ai_mcp_server.py"
    process = subprocess.Popen(
        [sys.executable, str(server_path), "--no-ai"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send request and get response
    stdout, stderr = process.communicate(json.dumps(request))
    
    # Parse response (skip any log lines)
    for line in stdout.strip().split('\n'):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    
    return {"error": "No valid response received"}

def demo_server_status():
    """Demo server status check."""
    print("🔍 Checking server status...")
    
    response = send_mcp_request("tools/call", {
        "name": "server_status",
        "arguments": {}
    })
    
    if "result" in response:
        status_text = response["result"]["content"][0]["text"]
        print("✅ Server is running!")
        print("\n📊 Status Report:")
        print(status_text)
    else:
        print("❌ Failed to get server status")
    
    print("-" * 60)

def demo_code_completion():
    """Demo code completion feature."""
    print("🤖 Testing code completion...")
    
    test_cases = [
        {
            "code": "def fibonacci(n):",
            "language": "python",
            "description": "Python function definition"
        },
        {
            "code": "class Calculator:",
            "language": "python", 
            "description": "Python class definition"
        },
        {
            "code": "if user_input == 'quit':",
            "language": "python",
            "description": "Python conditional statement"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"Input: {test_case['code']}")
        
        response = send_mcp_request("tools/call", {
            "name": "code_completion",
            "arguments": {
                "code": test_case["code"],
                "language": test_case["language"]
            }
        })
        
        if "result" in response:
            completion = response["result"]["content"][0]["text"]
            print(f"Output:\n{completion}")
        else:
            print("❌ Completion failed")
    
    print("-" * 60)

def demo_code_explanation():
    """Demo code explanation feature."""
    print("📚 Testing code explanation...")
    
    test_code = """def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)"""
    
    print(f"📝 Code to explain:")
    print(test_code)
    
    response = send_mcp_request("tools/call", {
        "name": "explain_code",
        "arguments": {
            "code": test_code
        }
    })
    
    if "result" in response:
        explanation = response["result"]["content"][0]["text"]
        print(f"\n🧠 Explanation:")
        print(explanation)
    else:
        print("❌ Explanation failed")
    
    print("-" * 60)

def demo_debugging_help():
    """Demo debugging assistance feature."""
    print("🐛 Testing debugging assistance...")
    
    buggy_code = """def divide_numbers(a, b):
    result = a / b
    return result

print(divide_numbers(10, 0))"""
    
    error_message = "ZeroDivisionError: division by zero"
    
    print(f"📝 Buggy code:")
    print(buggy_code)
    print(f"\n❌ Error: {error_message}")
    
    response = send_mcp_request("tools/call", {
        "name": "debug_code",
        "arguments": {
            "code": buggy_code,
            "error_message": error_message
        }
    })
    
    if "result" in response:
        debug_help = response["result"]["content"][0]["text"]
        print(f"\n🔧 Debugging help:")
        print(debug_help)
    else:
        print("❌ Debugging help failed")
    
    print("-" * 60)

def main():
    """Run the complete demo."""
    print_banner()
    
    print("🚀 MCPlease works out of the box with intelligent fallbacks!")
    print("   No model download required for basic functionality")
    print("   Full AI features available after model setup")
    print("")
    
    try:
        # Demo all features
        demo_server_status()
        demo_code_completion()
        demo_code_explanation()
        demo_debugging_help()
        
        print("🎉 Demo completed successfully!")
        print("")
        print("💡 Key Benefits:")
        print("   ✅ Works immediately without setup")
        print("   ✅ Intelligent fallback responses")
        print("   ✅ Multiple programming languages supported")
        print("   ✅ Easy integration with IDEs via MCP protocol")
        print("")
        print("🚀 To start using MCPlease:")
        print("   1. Run: python mcplease.py --start")
        print("   2. Connect your IDE to the MCP server")
        print("   3. Start coding with AI assistance!")
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("💡 Make sure you're running from the MCPlease directory")

if __name__ == "__main__":
    main()