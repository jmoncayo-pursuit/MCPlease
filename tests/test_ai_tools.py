"""Tests for AI-powered MCP tools."""

import pytest
from unittest.mock import MagicMock

from mcplease_mcp.tools.ai_tools import (
    create_ai_tools,
    code_completion_tool,
    code_explanation_tool,
    debug_assistance_tool,
)
from mcplease_mcp.protocol.models import MCPTool


class TestAITools:
    """Test AI-powered MCP tools."""

    def test_create_ai_tools(self):
        """Test creating AI tools."""
        tools = create_ai_tools()
        
        assert isinstance(tools, dict)
        assert len(tools) == 3
        assert "code_completion" in tools
        assert "code_explanation" in tools
        assert "debug_assistance" in tools
        
        # Check tool types
        for tool in tools.values():
            assert isinstance(tool, MCPTool)

    def test_code_completion_tool_definition(self):
        """Test code completion tool definition."""
        tools = create_ai_tools()
        tool = tools["code_completion"]
        
        assert tool.name == "code_completion"
        assert "intelligent code completion" in tool.description.lower()
        assert "type" in tool.inputSchema
        assert tool.inputSchema["type"] == "object"
        assert "properties" in tool.inputSchema
        assert "code" in tool.inputSchema["properties"]
        assert "language" in tool.inputSchema["properties"]
        assert "required" in tool.inputSchema
        assert "code" in tool.inputSchema["required"]
        assert "language" in tool.inputSchema["required"]

    def test_code_explanation_tool_definition(self):
        """Test code explanation tool definition."""
        tools = create_ai_tools()
        tool = tools["code_explanation"]
        
        assert tool.name == "code_explanation"
        assert "explains code" in tool.description.lower()
        assert "detail_level" in tool.inputSchema["properties"]
        assert tool.inputSchema["properties"]["detail_level"]["enum"] == ["brief", "detailed", "comprehensive"]

    def test_debug_assistance_tool_definition(self):
        """Test debug assistance tool definition."""
        tools = create_ai_tools()
        tool = tools["debug_assistance"]
        
        assert tool.name == "debug_assistance"
        assert "debugging help" in tool.description.lower()
        assert "error_message" in tool.inputSchema["properties"]
        assert "expected_behavior" in tool.inputSchema["properties"]
        assert "actual_behavior" in tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_code_completion_tool_execution(self):
        """Test code completion tool execution."""
        result = await code_completion_tool(
            code="def hello_world():",
            language="python",
            cursor_position=17,
            max_completions=3
        )
    
        assert isinstance(result, dict)
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "python" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_code_explanation_tool_execution(self):
        """Test code explanation tool execution."""
        result = await code_explanation_tool(
            code="print('Hello, World!')",
            language="python",
            detail_level="detailed"
        )
    
        assert isinstance(result, dict)
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "python" in result["content"][0]["text"].lower()
        assert "detailed" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_debug_assistance_tool_execution(self):
        """Test debug assistance tool execution."""
        result = await debug_assistance_tool(
            code="x = 1 / 0",
            language="python",
            error_message="ZeroDivisionError: division by zero",
            expected_behavior="Should handle division by zero",
            actual_behavior="Crashes with exception"
        )
        
        assert isinstance(result, dict)
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        text = result["content"][0]["text"]
        assert "python" in text.lower()
        assert "zerodivisionerror" in text.lower()
        assert "should handle division by zero" in text.lower()

    @pytest.mark.asyncio
    async def test_code_completion_tool_minimal_args(self):
        """Test code completion tool with minimal arguments."""
        result = await code_completion_tool(
            code="def test():",
            language="python"
        )
        
        assert isinstance(result, dict)
        assert "content" in result
        assert result["content"][0]["type"] == "text"

    @pytest.mark.asyncio
    async def test_code_explanation_tool_with_focus(self):
        """Test code explanation tool with focus parameter."""
        result = await code_explanation_tool(
            code="sorted(items, key=lambda x: x.value)",
            language="python",
            detail_level="comprehensive",
            focus="performance"
        )
        
        assert isinstance(result, dict)
        assert "content" in result
        text = result["content"][0]["text"]
        assert "comprehensive" in text.lower()

    @pytest.mark.asyncio
    async def test_debug_assistance_tool_minimal_args(self):
        """Test debug assistance tool with minimal arguments."""
        result = await debug_assistance_tool(
            code="broken_function()",
            language="python"
        )
        
        assert isinstance(result, dict)
        assert "content" in result
        assert "python" in result["content"][0]["text"].lower()

    def test_create_ai_tools_with_fastmcp_mock(self):
        """Test creating AI tools with mocked FastMCP instance."""
        mock_mcp = MagicMock()
        
        tools = create_ai_tools(mock_mcp)
        
        assert len(tools) == 3
        # Should still create tools even with mock FastMCP
        assert "code_completion" in tools
        assert "code_explanation" in tools
        assert "debug_assistance" in tools