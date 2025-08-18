"""Tests for MCP tool registry."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from mcplease_mcp.tools.registry import MCPToolRegistry
from mcplease_mcp.protocol.models import MCPTool


class TestMCPToolRegistry:
    """Test MCP tool registry."""

    @pytest.fixture
    def registry(self):
        """Create a tool registry for testing."""
        return MCPToolRegistry()

    def test_registry_initialization(self, registry):
        """Test registry initialization."""
        assert isinstance(registry.tools, dict)
        assert isinstance(registry.tool_executors, dict)
        assert len(registry.tools) == 3  # Default AI tools
        assert len(registry.tool_executors) == 3
        
        # Check default tools are registered
        assert "code_completion" in registry.tools
        assert "code_explanation" in registry.tools
        assert "debug_assistance" in registry.tools

    def test_get_available_tools(self, registry):
        """Test getting available tools."""
        tools = registry.get_available_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 3
        
        for tool in tools:
            assert isinstance(tool, MCPTool)
            assert tool.name in ["code_completion", "code_explanation", "debug_assistance"]

    def test_get_tool(self, registry):
        """Test getting a specific tool."""
        tool = registry.get_tool("code_completion")
        
        assert tool is not None
        assert isinstance(tool, MCPTool)
        assert tool.name == "code_completion"
        
        # Test non-existent tool
        assert registry.get_tool("non_existent") is None

    def test_has_tool(self, registry):
        """Test checking if tool exists."""
        assert registry.has_tool("code_completion") is True
        assert registry.has_tool("code_explanation") is True
        assert registry.has_tool("debug_assistance") is True
        assert registry.has_tool("non_existent") is False

    @pytest.mark.asyncio
    async def test_execute_tool_code_completion(self, registry):
        """Test executing code completion tool."""
        result = await registry.execute_tool(
            "code_completion",
            {
                "code": "def hello():",
                "language": "python"
            }
        )
        
        assert isinstance(result, dict)
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "python" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_execute_tool_code_explanation(self, registry):
        """Test executing code explanation tool."""
        result = await registry.execute_tool(
            "code_explanation",
            {
                "code": "print('Hello')",
                "language": "python",
                "detail_level": "brief"
            }
        )
        
        assert isinstance(result, dict)
        assert "content" in result
        assert "python" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_execute_tool_debug_assistance(self, registry):
        """Test executing debug assistance tool."""
        result = await registry.execute_tool(
            "debug_assistance",
            {
                "code": "x = 1/0",
                "language": "python",
                "error_message": "ZeroDivisionError"
            }
        )
        
        assert isinstance(result, dict)
        assert "content" in result
        assert "python" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, registry):
        """Test executing non-existent tool."""
        with pytest.raises(ValueError, match="Tool 'non_existent' not found"):
            await registry.execute_tool("non_existent", {})

    def test_register_custom_tool(self, registry):
        """Test registering a custom tool."""
        def custom_executor(**kwargs):
            return {"content": [{"type": "text", "text": "Custom tool result"}]}
        
        custom_tool = MCPTool(
            name="custom_tool",
            description="A custom test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            }
        )
        
        initial_count = len(registry.tools)
        registry.register_tool(custom_tool, custom_executor)
        
        assert len(registry.tools) == initial_count + 1
        assert "custom_tool" in registry.tools
        assert registry.has_tool("custom_tool")
        assert registry.get_tool("custom_tool") == custom_tool

    @pytest.mark.asyncio
    async def test_execute_custom_tool(self, registry):
        """Test executing a custom tool."""
        def custom_executor(input_text: str):
            return {"content": [{"type": "text", "text": f"Processed: {input_text}"}]}
        
        custom_tool = MCPTool(
            name="echo_tool",
            description="Echoes input",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_text": {"type": "string"}
                },
                "required": ["input_text"]
            }
        )
        
        registry.register_tool(custom_tool, custom_executor)
        
        result = await registry.execute_tool(
            "echo_tool",
            {"input_text": "Hello World"}
        )
        
        assert result["content"][0]["text"] == "Processed: Hello World"

    def test_get_tool_list(self, registry):
        """Test getting formatted tool list."""
        tool_list = registry.get_tool_list()
        
        assert isinstance(tool_list, list)
        assert len(tool_list) == 3
        
        for tool_dict in tool_list:
            assert isinstance(tool_dict, dict)
            assert "name" in tool_dict
            assert "description" in tool_dict
            assert "inputSchema" in tool_dict

    def test_get_tool_names(self, registry):
        """Test getting tool names."""
        names = registry.get_tool_names()
        
        assert isinstance(names, list)
        assert len(names) == 3
        assert "code_completion" in names
        assert "code_explanation" in names
        assert "debug_assistance" in names

    def test_remove_tool(self, registry):
        """Test removing a tool."""
        initial_count = len(registry.tools)
        
        # Remove existing tool
        result = registry.remove_tool("code_completion")
        assert result is True
        assert len(registry.tools) == initial_count - 1
        assert not registry.has_tool("code_completion")
        
        # Try to remove non-existent tool
        result = registry.remove_tool("non_existent")
        assert result is False

    def test_clear_tools(self, registry):
        """Test clearing all tools."""
        assert len(registry.tools) > 0
        
        registry.clear_tools()
        
        assert len(registry.tools) == 0
        assert len(registry.tool_executors) == 0

    def test_get_registry_stats(self, registry):
        """Test getting registry statistics."""
        stats = registry.get_registry_stats()
        
        assert isinstance(stats, dict)
        assert "total_tools" in stats
        assert "tool_names" in stats
        assert "has_fastmcp" in stats
        assert "fastmcp_available" in stats
        
        assert stats["total_tools"] == 3
        assert len(stats["tool_names"]) == 3
        assert isinstance(stats["has_fastmcp"], bool)
        assert isinstance(stats["fastmcp_available"], bool)

    @pytest.mark.asyncio
    async def test_execute_tool_string_result_wrapping(self, registry):
        """Test that string results are properly wrapped in MCP format."""
        def string_executor():
            return "Simple string result"
        
        custom_tool = MCPTool(
            name="string_tool",
            description="Returns a string",
            inputSchema={"type": "object", "properties": {}}
        )
        
        registry.register_tool(custom_tool, string_executor)
        
        result = await registry.execute_tool("string_tool", {})
        
        assert isinstance(result, dict)
        assert "content" in result
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == "Simple string result"

    def test_registry_with_fastmcp_mock(self):
        """Test registry initialization with mocked FastMCP."""
        mock_mcp = MagicMock()
        registry = MCPToolRegistry(mock_mcp)
        
        assert registry.mcp_instance == mock_mcp
        assert len(registry.tools) == 3  # Should still have default tools