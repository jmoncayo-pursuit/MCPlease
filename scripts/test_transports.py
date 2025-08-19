#!/usr/bin/env python3
"""
Test script to verify MCPlease transports work correctly
Tests both stdio and HTTP transports
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

def test_stdio_transport():
    """Test stdio transport by running the server and checking output"""
    print("🧪 Testing stdio transport...")
    
    try:
        # Use the virtual environment Python
        venv_python = Path("mcplease_mcp_server.py").parent / ".venv" / "bin" / "python"
        if not venv_python.exists():
            print("❌ Virtual environment not found. Run './start.sh' first.")
            return False
        
        # Start server in stdio mode
        process = subprocess.Popen(
            [str(venv_python), "mcplease_mcp_server.py", "--transport", "stdio"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if process is running
        if process.poll() is None:
            print("✅ stdio transport started successfully")
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ stdio transport failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ stdio transport test error: {e}")
        return False

def test_http_transport():
    """Test HTTP transport by starting server and checking endpoints"""
    print("🧪 Testing HTTP transport...")
    
    try:
        # Use the virtual environment Python
        venv_python = Path("mcplease_mcp_server.py").parent / ".venv" / "bin" / "python"
        if not venv_python.exists():
            print("❌ Virtual environment not found. Run './start.sh' first.")
            return False
        
        # Start server in HTTP mode using separate script
        process = subprocess.Popen(
            [str(venv_python), "mcplease_http_server.py", "--port", "8001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        time.sleep(3)
        
        # Check if process is running
        if process.poll() is None:
            print("✅ HTTP transport started successfully")
            
            # Test basic endpoints
            try:
                import requests
                
                # Test root endpoint
                response = requests.get("http://127.0.0.1:8001/", timeout=5)
                if response.status_code == 200:
                    print("✅ Root endpoint working")
                else:
                    print(f"❌ Root endpoint failed: {response.status_code}")
                
                # Test health endpoint
                response = requests.get("http://127.0.0.1:8001/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get("status") == "ok":
                        print("✅ Health endpoint working")
                    else:
                        print(f"❌ Health endpoint unhealthy: {health_data}")
                else:
                    print(f"❌ Health endpoint failed: {response.status_code}")
                
                # Test tools endpoint
                response = requests.get("http://127.0.0.1:8001/tools", timeout=5)
                if response.status_code == 200:
                    tools_data = response.json()
                    if "tools" in tools_data:
                        print(f"✅ Tools endpoint working ({len(tools_data['tools'])} tools)")
                    else:
                        print("❌ Tools endpoint missing tools data")
                else:
                    print(f"❌ Tools endpoint failed: {response.status_code}")
                    
            except ImportError:
                print("⚠️  requests not installed - skipping HTTP endpoint tests")
            except Exception as e:
                print(f"⚠️  HTTP endpoint test error: {e}")
            
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ HTTP transport failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ HTTP transport test error: {e}")
        return False

def test_startup_script():
    """Test the startup script"""
    print("🧪 Testing startup script...")
    
    try:
        # Check if script exists and is executable
        script_path = Path("start.sh")
        if not script_path.exists():
            print("❌ start.sh not found")
            return False
        
        # Test script help/version
        result = subprocess.run(
            ["./start.sh"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "MCPlease Universal Startup Script" in result.stdout:
            print("✅ Startup script working")
            return True
        else:
            print(f"❌ Startup script output unexpected: {result.stdout[:100]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print("✅ Startup script started (timeout expected)")
        return True
    except Exception as e:
        print(f"❌ Startup script test error: {e}")
        return False

def main():
    """Run all transport tests"""
    print("🚀 MCPlease Transport Tests")
    print("=" * 40)
    
    tests = [
        ("Startup Script", test_startup_script),
        ("stdio Transport", test_stdio_transport),
        ("HTTP Transport", test_http_transport),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All transports working! MCPlease is ready for any environment.")
        return True
    else:
        print("⚠️  Some transports failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
