#!/usr/bin/env python3
"""
MCP Integration Tester

A comprehensive tool to test MCPleasant MCP server integration.
This provides multiple ways to verify MCP tools are working correctly.
"""

import asyncio
import json
import subprocess
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPTester:
    """Comprehensive MCP server tester."""
    
    def __init__(self):
        self.server_process = None
        self.tools = []
        self.request_id = 0
        self.test_results = []
    
    async def start_mcp_server(self):
        """Start the MCPleasant MCP server."""
        # Look for MCP server files
        server_candidates = [
            "mcpleasant_mcp.py",
            "mcpleasant_mcp_fixed.py", 
            "src/mcp_server.py",
            "src/simple_mcp_server.py"
        ]
        
        server_file = None
        for candidate in server_candidates:
            if Path(candidate).exists():
                server_file = candidate
                break
        
        if not server_file:
            logger.error("❌ No MCP server file found!")
            logger.info("Looking for: " + ", ".join(server_candidates))
            return False
        
        logger.info(f"🚀 Starting MCP server: {server_file}")
        
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, server_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Give server time to start
            await asyncio.sleep(1)
            
            # Initialize the server
            init_response = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "MCPTester", "version": "1.0.0"}
            })
            
            if "result" in init_response:
                logger.info("✅ MCP server initialized successfully")
                
                # Get available tools
                tools_response = await self._send_request("tools/list", {})
                if "result" in tools_response and "tools" in tools_response["result"]:
                    self.tools = tools_response["result"]["tools"]
                    logger.info(f"✅ Found {len(self.tools)} MCP tools:")
                    for tool in self.tools:
                        logger.info(f"   • {tool['name']}: {tool.get('description', 'No description')}")
                    return True
                else:
                    logger.error(f"❌ Failed to get tools list: {tools_response}")
            else:
                logger.error(f"❌ Failed to initialize server: {init_response}")
                
        except Exception as e:
            logger.error(f"❌ Error starting server: {e}")
            
        return False
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request to MCP server."""
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.server_process.stdin.write(request_json)
            self.server_process.stdin.flush()
            
            # Read response with timeout
            response_line = await asyncio.wait_for(
                asyncio.to_thread(self.server_process.stdout.readline),
                timeout=10.0
            )
            
            if response_line.strip():
                return json.loads(response_line.strip())
            else:
                return {"error": "Empty response from server"}
                
        except asyncio.TimeoutError:
            return {"error": "Request timeout"}
        except Exception as e:
            return {"error": f"Request failed: {e}"}
    
    async def test_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific MCP tool."""
        logger.info(f"🧪 Testing tool: {tool_name}")
        
        start_time = time.time()
        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        end_time = time.time()
        
        test_result = {
            "tool": tool_name,
            "arguments": arguments,
            "response": response,
            "duration": end_time - start_time,
            "success": "result" in response and "error" not in response
        }
        
        self.test_results.append(test_result)
        
        if test_result["success"]:
            logger.info(f"✅ Tool {tool_name} succeeded in {test_result['duration']:.2f}s")
            if "result" in response and "content" in response["result"]:
                content = response["result"]["content"]
                if content and len(content) > 0:
                    text_content = content[0].get("text", "")
                    logger.info(f"   Response: {text_content[:100]}...")
        else:
            logger.error(f"❌ Tool {tool_name} failed: {response.get('error', 'Unknown error')}")
        
        return test_result
    
    async def run_comprehensive_tests(self):
        """Run comprehensive tests of all MCP tools."""
        logger.info("\n" + "="*60)
        logger.info("🧪 COMPREHENSIVE MCP TOOL TESTING")
        logger.info("="*60)
        
        if not await self.start_mcp_server():
            logger.error("❌ Failed to start MCP server - cannot run tests")
            return False
        
        # Test cases for each tool
        test_cases = [
            {
                "tool": "complete_code",
                "args": {
                    "code": "def fibonacci(n):",
                    "language": "python"
                },
                "description": "Python function completion"
            },
            {
                "tool": "complete_code", 
                "args": {
                    "code": "function calculateSum(a, b) {",
                    "language": "javascript"
                },
                "description": "JavaScript function completion"
            },
            {
                "tool": "explain_code",
                "args": {
                    "code": "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)"
                },
                "description": "Quicksort algorithm explanation"
            },
            {
                "tool": "debug_code",
                "args": {
                    "code": "def divide(a, b):\n    return a / b\n\nresult = divide(10, 0)",
                    "error": "ZeroDivisionError: division by zero"
                },
                "description": "Division by zero debugging"
            },
            {
                "tool": "debug_code",
                "args": {
                    "code": "my_list = [1, 2, 3]\nprint(my_list[5])",
                    "error": "IndexError: list index out of range"
                },
                "description": "Index error debugging"
            }
        ]
        
        # Run all test cases
        passed_tests = 0
        total_tests = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n--- Test {i}/{total_tests}: {test_case['description']} ---")
            
            result = await self.test_tool(test_case["tool"], test_case["args"])
            
            if result["success"]:
                passed_tests += 1
                logger.info(f"✅ PASSED")
            else:
                logger.error(f"❌ FAILED")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED! MCP integration is working perfectly!")
        else:
            logger.warning(f"⚠️  {total_tests - passed_tests} tests failed. Check MCP server implementation.")
        
        return passed_tests == total_tests
    
    async def interactive_test_session(self):
        """Run interactive testing session."""
        logger.info("\n" + "="*60)
        logger.info("💬 INTERACTIVE MCP TESTING SESSION")
        logger.info("="*60)
        
        if not await self.start_mcp_server():
            logger.error("❌ Failed to start MCP server")
            return
        
        logger.info("\n🎯 Available commands:")
        logger.info("  • 'complete <code>' - Test code completion")
        logger.info("  • 'explain <code>' - Test code explanation") 
        logger.info("  • 'debug <code> | <error>' - Test debugging")
        logger.info("  • 'tools' - List available tools")
        logger.info("  • 'results' - Show test results")
        logger.info("  • 'quit' - Exit")
        
        while True:
            try:
                user_input = input("\n🧪 Test Command: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if user_input.lower() == 'tools':
                    logger.info("Available MCP tools:")
                    for tool in self.tools:
                        logger.info(f"  • {tool['name']}: {tool.get('description', 'No description')}")
                    continue
                
                if user_input.lower() == 'results':
                    logger.info(f"Test results so far: {len(self.test_results)} tests run")
                    for result in self.test_results[-5:]:  # Show last 5
                        status = "✅" if result["success"] else "❌"
                        logger.info(f"  {status} {result['tool']} ({result['duration']:.2f}s)")
                    continue
                
                # Parse commands
                if user_input.startswith('complete '):
                    code = user_input[9:]
                    await self.test_tool("complete_code", {"code": code, "language": "python"})
                
                elif user_input.startswith('explain '):
                    code = user_input[8:]
                    await self.test_tool("explain_code", {"code": code})
                
                elif user_input.startswith('debug '):
                    parts = user_input[6:].split(' | ')
                    if len(parts) == 2:
                        code, error = parts
                        await self.test_tool("debug_code", {"code": code.strip(), "error": error.strip()})
                    else:
                        logger.warning("Debug format: debug <code> | <error>")
                
                else:
                    logger.warning("Unknown command. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                break
        
        logger.info("👋 Interactive session ended")
    
    def stop_server(self):
        """Stop the MCP server."""
        if self.server_process:
            logger.info("🛑 Stopping MCP server...")
            self.server_process.terminate()
            self.server_process.wait()
    
    def generate_report(self):
        """Generate detailed test report."""
        if not self.test_results:
            logger.info("No test results to report")
            return
        
        report_file = "mcp_test_report.json"
        
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for r in self.test_results if r["success"]),
            "failed_tests": sum(1 for r in self.test_results if not r["success"]),
            "average_duration": sum(r["duration"] for r in self.test_results) / len(self.test_results),
            "tools_tested": list(set(r["tool"] for r in self.test_results)),
            "detailed_results": self.test_results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"📄 Detailed test report saved to: {report_file}")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Integration Tester")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive automated tests")
    parser.add_argument("--interactive", action="store_true", help="Run interactive test session")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke test")
    
    args = parser.parse_args()
    
    tester = MCPTester()
    
    try:
        if args.comprehensive:
            await tester.run_comprehensive_tests()
        elif args.interactive:
            await tester.interactive_test_session()
        elif args.quick:
            # Quick smoke test
            logger.info("🚀 Running quick MCP smoke test...")
            if await tester.start_mcp_server():
                await tester.test_tool("complete_code", {"code": "def hello():", "language": "python"})
                logger.info("✅ Quick test completed")
            else:
                logger.error("❌ Quick test failed - server didn't start")
        else:
            # Default to comprehensive
            await tester.run_comprehensive_tests()
    
    finally:
        tester.stop_server()
        tester.generate_report()


if __name__ == "__main__":
    asyncio.run(main())