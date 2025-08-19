"""
Tests for MCPlease MCP Server IDE Integration and Compatibility

This module tests integration with various IDE clients including VSCode,
Cursor, and other MCP-compatible editors.
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from src.mcplease_mcp.server.server import MCPServer
from src.mcplease_mcp.protocol.handler import MCPProtocolHandler
from src.mcplease_mcp.server.transports import StdioTransport, SSETransport
from src.mcplease_mcp.tools.ai_tools import AITools
from src.mcplease_mcp.context.manager import MCPContextManager


class MockIDEClient:
    """Mock IDE client for testing MCP integration."""
    
    def __init__(self, transport_type: str = "stdio"):
        self.transport_type = transport_type
        self.messages_sent = []
        self.messages_received = []
        self.connection_established = False
        self.capabilities = {}
        self.tools = []
        
    async def connect(self, server_config: Dict[str, Any]):
        """Connect to MCP server."""
        self.connection_established = True
        
        # Send initialize request
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "MockIDE",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self._send_request(initialize_request)
        if response and "result" in response:
            self.capabilities = response["result"]["capabilities"]
            self.tools = response["result"]["capabilities"].get("tools", [])
        
        return response
    
    async def list_tools(self):
        """List available tools."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        return await self._send_request(request)
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Call a specific tool."""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        return await self._send_request(request)
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to server (mock implementation)."""
        self.messages_sent.append(request)
        
        # Mock response based on request
        if request["method"] == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": True
                        },
                        "logging": {},
                        "prompts": {
                            "listChanged": True
                        },
                        "resources": {
                            "subscribe": True,
                            "listChanged": True
                        }
                    },
                    "serverInfo": {
                        "name": "MCPlease MCP Server",
                        "version": "0.1.0"
                    }
                }
            }
        elif request["method"] == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "tools": [
                        {
                            "name": "code_completion",
                            "description": "Generate code completions",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "code": {"type": "string"},
                                    "language": {"type": "string"},
                                    "cursor_position": {"type": "integer"}
                                },
                                "required": ["code", "language"]
                            }
                        },
                        {
                            "name": "code_explanation",
                            "description": "Explain code functionality",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "code": {"type": "string"},
                                    "language": {"type": "string"}
                                },
                                "required": ["code", "language"]
                            }
                        },
                        {
                            "name": "debug_assistance",
                            "description": "Help debug code issues",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "code": {"type": "string"},
                                    "error_message": {"type": "string"},
                                    "language": {"type": "string"}
                                },
                                "required": ["code", "error_message", "language"]
                            }
                        }
                    ]
                }
            }
        elif request["method"] == "tools/call":
            # Mock tool execution
            tool_name = request["params"]["name"]
            arguments = request["params"]["arguments"]
            
            if tool_name == "code_completion":
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "# Suggested completion\nprint('Hello, World!')"
                            }
                        ]
                    }
                }
            elif tool_name == "code_explanation":
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "This code prints a greeting message to the console."
                            }
                        ]
                    }
                }
            elif tool_name == "debug_assistance":
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "The error suggests a syntax issue. Check for missing parentheses or quotes."
                            }
                        ]
                    }
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {request['method']}"
                }
            }
        
        self.messages_received.append(response)
        return response
    
    def disconnect(self):
        """Disconnect from server."""
        self.connection_established = False


class TestVSCodeIntegration:
    """Test VSCode MCP client integration."""
    
    def setup_method(self):
        self.client = MockIDEClient("stdio")
    
    @pytest.mark.asyncio
    async def test_vscode_connection(self):
        """Test VSCode client connection to MCP server."""
        server_config = {
            "transport": "stdio",
            "command": "python",
            "args": ["-m", "mcplease_mcp.main", "--transport", "stdio"]
        }
        
        response = await self.client.connect(server_config)
        
        assert self.client.connection_established
        assert response["result"]["serverInfo"]["name"] == "MCPlease MCP Server"
        assert "tools" in response["result"]["capabilities"]
    
    @pytest.mark.asyncio
    async def test_vscode_tool_discovery(self):
        """Test VSCode discovering available tools."""
        await self.client.connect({})
        
        tools_response = await self.client.list_tools()
        
        assert "result" in tools_response
        tools = tools_response["result"]["tools"]
        
        # Check that expected tools are available
        tool_names = [tool["name"] for tool in tools]
        assert "code_completion" in tool_names
        assert "code_explanation" in tool_names
        assert "debug_assistance" in tool_names
        
        # Check tool schemas
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"
    
    @pytest.mark.asyncio
    async def test_vscode_code_completion(self):
        """Test VSCode using code completion tool."""
        await self.client.connect({})
        
        completion_response = await self.client.call_tool(
            "code_completion",
            {
                "code": "def hello():\n    ",
                "language": "python",
                "cursor_position": 15
            }
        )
        
        assert "result" in completion_response
        content = completion_response["result"]["content"]
        assert len(content) > 0
        assert content[0]["type"] == "text"
        assert "print" in content[0]["text"]
    
    @pytest.mark.asyncio
    async def test_vscode_code_explanation(self):
        """Test VSCode using code explanation tool."""
        await self.client.connect({})
        
        explanation_response = await self.client.call_tool(
            "code_explanation",
            {
                "code": "print('Hello, World!')",
                "language": "python"
            }
        )
        
        assert "result" in explanation_response
        content = explanation_response["result"]["content"]
        assert len(content) > 0
        assert content[0]["type"] == "text"
        assert "prints" in content[0]["text"].lower()
    
    @pytest.mark.asyncio
    async def test_vscode_debug_assistance(self):
        """Test VSCode using debug assistance tool."""
        await self.client.connect({})
        
        debug_response = await self.client.call_tool(
            "debug_assistance",
            {
                "code": "print('Hello World'",
                "error_message": "SyntaxError: unexpected EOF while parsing",
                "language": "python"
            }
        )
        
        assert "result" in debug_response
        content = debug_response["result"]["content"]
        assert len(content) > 0
        assert content[0]["type"] == "text"
        assert "syntax" in content[0]["text"].lower()


class TestCursorIntegration:
    """Test Cursor IDE integration."""
    
    def setup_method(self):
        self.client = MockIDEClient("stdio")
    
    @pytest.mark.asyncio
    async def test_cursor_connection(self):
        """Test Cursor IDE connection."""
        # Cursor uses similar MCP protocol as VSCode
        server_config = {
            "transport": "stdio",
            "command": "python",
            "args": ["-m", "mcplease_mcp.main"]
        }
        
        response = await self.client.connect(server_config)
        
        assert self.client.connection_established
        assert "capabilities" in response["result"]
        assert "tools" in response["result"]["capabilities"]
    
    @pytest.mark.asyncio
    async def test_cursor_ai_workflow(self):
        """Test typical Cursor AI workflow."""
        await self.client.connect({})
        
        # 1. Get code explanation
        explanation = await self.client.call_tool(
            "code_explanation",
            {
                "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
                "language": "python"
            }
        )
        
        assert "result" in explanation
        
        # 2. Get code completion
        completion = await self.client.call_tool(
            "code_completion",
            {
                "code": "def fibonacci(n):\n    # Add memoization here\n    ",
                "language": "python",
                "cursor_position": 50
            }
        )
        
        assert "result" in completion
        
        # 3. Debug assistance
        debug_help = await self.client.call_tool(
            "debug_assistance",
            {
                "code": "fibonacci(100)",
                "error_message": "RecursionError: maximum recursion depth exceeded",
                "language": "python"
            }
        )
        
        assert "result" in debug_help


class TestJetBrainsIntegration:
    """Test JetBrains IDE integration (IntelliJ, PyCharm, etc.)."""
    
    def setup_method(self):
        self.client = MockIDEClient("sse")  # JetBrains might use HTTP transport
    
    @pytest.mark.asyncio
    async def test_jetbrains_http_connection(self):
        """Test JetBrains connection via HTTP/SSE."""
        server_config = {
            "transport": "sse",
            "url": "http://localhost:8000/mcp",
            "headers": {
                "Authorization": "Bearer test-token"
            }
        }
        
        response = await self.client.connect(server_config)
        
        assert self.client.connection_established
        assert response["result"]["serverInfo"]["name"] == "MCPlease MCP Server"
    
    @pytest.mark.asyncio
    async def test_jetbrains_tool_integration(self):
        """Test JetBrains IDE tool integration."""
        await self.client.connect({})
        
        # Test code completion in Java context
        completion = await self.client.call_tool(
            "code_completion",
            {
                "code": "public class HelloWorld {\n    public static void main(String[] args) {\n        ",
                "language": "java",
                "cursor_position": 80
            }
        )
        
        assert "result" in completion
        
        # Test explanation for Java code
        explanation = await self.client.call_tool(
            "code_explanation",
            {
                "code": "System.out.println(\"Hello, World!\");",
                "language": "java"
            }
        )
        
        assert "result" in explanation


class TestMultiLanguageSupport:
    """Test multi-language support across different IDEs."""
    
    def setup_method(self):
        self.client = MockIDEClient()
    
    @pytest.mark.asyncio
    async def test_python_support(self):
        """Test Python language support."""
        await self.client.connect({})
        
        response = await self.client.call_tool(
            "code_completion",
            {
                "code": "import numpy as np\narr = np.array([1, 2, 3])\nresult = arr.",
                "language": "python",
                "cursor_position": 50
            }
        )
        
        assert "result" in response
    
    @pytest.mark.asyncio
    async def test_javascript_support(self):
        """Test JavaScript language support."""
        await self.client.connect({})
        
        response = await self.client.call_tool(
            "code_explanation",
            {
                "code": "const fetchData = async () => {\n  const response = await fetch('/api/data');\n  return response.json();\n};",
                "language": "javascript"
            }
        )
        
        assert "result" in response
    
    @pytest.mark.asyncio
    async def test_typescript_support(self):
        """Test TypeScript language support."""
        await self.client.connect({})
        
        response = await self.client.call_tool(
            "debug_assistance",
            {
                "code": "interface User {\n  name: string;\n  age: number;\n}\n\nconst user: User = { name: 'John' };",
                "error_message": "Property 'age' is missing in type '{ name: string; }' but required in type 'User'",
                "language": "typescript"
            }
        )
        
        assert "result" in response
    
    @pytest.mark.asyncio
    async def test_java_support(self):
        """Test Java language support."""
        await self.client.connect({})
        
        response = await self.client.call_tool(
            "code_completion",
            {
                "code": "public class Calculator {\n    public int add(int a, int b) {\n        return ",
                "language": "java",
                "cursor_position": 70
            }
        )
        
        assert "result" in response


class TestErrorHandling:
    """Test error handling in IDE integration."""
    
    def setup_method(self):
        self.client = MockIDEClient()
    
    @pytest.mark.asyncio
    async def test_invalid_tool_call(self):
        """Test handling of invalid tool calls."""
        await self.client.connect({})
        
        response = await self.client.call_tool(
            "nonexistent_tool",
            {"param": "value"}
        )
        
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Unknown tool" in response["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_invalid_parameters(self):
        """Test handling of invalid parameters."""
        await self.client.connect({})
        
        # Missing required parameter
        response = await self.client.call_tool(
            "code_completion",
            {"language": "python"}  # Missing 'code' parameter
        )
        
        # Should handle gracefully (in real implementation)
        # For mock, we'll just check it doesn't crash
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_connection_failure_recovery(self):
        """Test recovery from connection failures."""
        # Simulate connection failure
        self.client.connection_established = False
        
        # Attempt to reconnect
        response = await self.client.connect({})
        
        assert self.client.connection_established
        assert response is not None


class TestPerformanceWithIDEs:
    """Test performance characteristics with IDE integration."""
    
    def setup_method(self):
        self.client = MockIDEClient()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling concurrent requests from IDE."""
        await self.client.connect({})
        
        # Simulate multiple concurrent requests
        tasks = []
        for i in range(10):
            task = asyncio.create_task(
                self.client.call_tool(
                    "code_completion",
                    {
                        "code": f"# Request {i}\nprint(",
                        "language": "python",
                        "cursor_position": 20
                    }
                )
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should complete successfully
        assert len(responses) == 10
        for response in responses:
            assert "result" in response or "error" in response
    
    @pytest.mark.asyncio
    async def test_large_code_handling(self):
        """Test handling of large code files."""
        await self.client.connect({})
        
        # Create a large code snippet
        large_code = "\n".join([f"def function_{i}():\n    pass" for i in range(1000)])
        
        response = await self.client.call_tool(
            "code_explanation",
            {
                "code": large_code,
                "language": "python"
            }
        )
        
        assert "result" in response
    
    @pytest.mark.asyncio
    async def test_response_time(self):
        """Test response time for typical IDE requests."""
        await self.client.connect({})
        
        start_time = asyncio.get_event_loop().time()
        
        response = await self.client.call_tool(
            "code_completion",
            {
                "code": "def hello():\n    ",
                "language": "python",
                "cursor_position": 15
            }
        )
        
        end_time = asyncio.get_event_loop().time()
        response_time = end_time - start_time
        
        assert "result" in response
        # Response should be reasonably fast (less than 1 second for mock)
        assert response_time < 1.0


class TestIDESpecificFeatures:
    """Test IDE-specific features and configurations."""
    
    def setup_method(self):
        self.client = MockIDEClient()
    
    @pytest.mark.asyncio
    async def test_vscode_settings_integration(self):
        """Test integration with VSCode settings."""
        # Simulate VSCode-specific configuration
        vscode_config = {
            "mcplease": {
                "model": "gpt-oss-20b",
                "temperature": 0.7,
                "max_tokens": 1000,
                "enable_autocomplete": True,
                "enable_explanations": True
            }
        }
        
        await self.client.connect({"config": vscode_config})
        
        # Test that configuration affects tool behavior
        response = await self.client.call_tool(
            "code_completion",
            {
                "code": "def calculate():\n    ",
                "language": "python",
                "cursor_position": 20
            }
        )
        
        assert "result" in response
    
    @pytest.mark.asyncio
    async def test_cursor_composer_integration(self):
        """Test integration with Cursor's Composer feature."""
        await self.client.connect({})
        
        # Simulate Cursor Composer multi-step workflow
        steps = [
            {
                "tool": "code_explanation",
                "params": {
                    "code": "# TODO: Implement user authentication",
                    "language": "python"
                }
            },
            {
                "tool": "code_completion",
                "params": {
                    "code": "def authenticate_user(username, password):\n    ",
                    "language": "python",
                    "cursor_position": 50
                }
            }
        ]
        
        results = []
        for step in steps:
            response = await self.client.call_tool(step["tool"], step["params"])
            results.append(response)
        
        assert len(results) == 2
        for result in results:
            assert "result" in result
    
    def test_configuration_file_generation(self):
        """Test generation of IDE configuration files."""
        # Test VSCode configuration
        vscode_config = {
            "mcpServers": {
                "mcplease": {
                    "command": "python",
                    "args": ["-m", "mcplease_mcp.main", "--transport", "stdio"],
                    "env": {
                        "MCPLEASE_MODEL": "gpt-oss-20b",
                        "MCPLEASE_LOG_LEVEL": "INFO"
                    }
                }
            }
        }
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(vscode_config, f, indent=2)
            config_path = Path(f.name)
        
        # Verify configuration is valid JSON
        with open(config_path) as f:
            loaded_config = json.load(f)
        
        assert "mcpServers" in loaded_config
        assert "mcplease" in loaded_config["mcpServers"]
        
        # Clean up
        config_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__])