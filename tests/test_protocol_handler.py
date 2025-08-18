"""Tests for MCP protocol handler."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from mcplease_mcp.protocol.handler import MCPProtocolHandler
from mcplease_mcp.protocol.models import (
    MCPRequest,
    MCPResponse,
    MCPError,
    MCPTool,
    MCPMethods,
    MCPErrorCodes,
)


class TestMCPProtocolHandler:
    """Test MCPProtocolHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a protocol handler for testing."""
        return MCPProtocolHandler("Test MCP Server")

    def test_handler_initialization(self, handler):
        """Test protocol handler initialization."""
        assert handler.server_name == "Test MCP Server"
        # handler.mcp may be None if FastMCP is not available
        assert isinstance(handler.tools, dict)
        assert len(handler.tools) == 0
        assert "tools" in handler.capabilities

    @pytest.mark.asyncio
    async def test_handle_initialize_success(self, handler):
        """Test successful initialize request handling."""
        request = MCPRequest(
            id="init-1",
            method=MCPMethods.INITIALIZE,
            params={
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "Test Client", "version": "1.0.0"}
            }
        )
        
        response = await handler.handle_initialize(request)
        
        assert response.id == "init-1"
        assert response.error is None
        assert response.result is not None
        assert response.result["protocolVersion"] == "2024-11-05"
        assert "capabilities" in response.result
        assert "serverInfo" in response.result
        assert response.result["serverInfo"]["name"] == "Test MCP Server"

    @pytest.mark.asyncio
    async def test_handle_initialize_unsupported_version(self, handler):
        """Test initialize with unsupported protocol version."""
        request = MCPRequest(
            id="init-2",
            method=MCPMethods.INITIALIZE,
            params={
                "protocolVersion": "2023-01-01",
                "clientInfo": {"name": "Test Client"}
            }
        )
        
        response = await handler.handle_initialize(request)
        
        assert response.id == "init-2"
        assert response.result is None
        assert response.error is not None
        assert response.error.code == MCPErrorCodes.INVALID_PARAMS
        assert "Unsupported protocol version" in response.error.message

    @pytest.mark.asyncio
    async def test_handle_tools_list_empty(self, handler):
        """Test tools/list with no registered tools."""
        request = MCPRequest(
            id="tools-1",
            method=MCPMethods.TOOLS_LIST
        )
        
        response = await handler.handle_tools_list(request)
        
        assert response.id == "tools-1"
        assert response.error is None
        assert response.result is not None
        assert response.result["tools"] == []

    @pytest.mark.asyncio
    async def test_handle_tools_list_with_tools(self, handler):
        """Test tools/list with registered tools."""
        # Register a test tool
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            inputSchema={
                "type": "object",
                "properties": {"input": {"type": "string"}},
                "required": ["input"]
            }
        )
        handler.register_tool(tool)
        
        request = MCPRequest(
            id="tools-2",
            method=MCPMethods.TOOLS_LIST
        )
        
        response = await handler.handle_tools_list(request)
        
        assert response.id == "tools-2"
        assert response.error is None
        assert response.result is not None
        assert len(response.result["tools"]) == 1
        assert response.result["tools"][0]["name"] == "test_tool"
        assert response.result["tools"][0]["description"] == "A test tool"

    @pytest.mark.asyncio
    async def test_handle_tools_call_missing_name(self, handler):
        """Test tools/call without tool name."""
        request = MCPRequest(
            id="call-1",
            method=MCPMethods.TOOLS_CALL,
            params={"arguments": {"input": "test"}}
        )
        
        response = await handler.handle_tools_call(request)
        
        assert response.id == "call-1"
        assert response.result is None
        assert response.error is not None
        assert response.error.code == MCPErrorCodes.INVALID_PARAMS
        assert "Tool name is required" in response.error.message

    @pytest.mark.asyncio
    async def test_handle_tools_call_unknown_tool(self, handler):
        """Test tools/call with unknown tool."""
        request = MCPRequest(
            id="call-2",
            method=MCPMethods.TOOLS_CALL,
            params={
                "name": "unknown_tool",
                "arguments": {"input": "test"}
            }
        )
        
        response = await handler.handle_tools_call(request)
        
        assert response.id == "call-2"
        assert response.result is None
        assert response.error is not None
        assert response.error.code == MCPErrorCodes.METHOD_NOT_FOUND
        assert "Tool 'unknown_tool' not found" in response.error.message

    @pytest.mark.asyncio
    async def test_handle_tools_call_success(self, handler):
        """Test successful tools/call."""
        # Register a test tool
        tool = MCPTool(
            name="echo_tool",
            description="Echoes input",
            inputSchema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"]
            }
        )
        handler.register_tool(tool)
        
        request = MCPRequest(
            id="call-3",
            method=MCPMethods.TOOLS_CALL,
            params={
                "name": "echo_tool",
                "arguments": {"message": "Hello, World!"}
            }
        )
        
        response = await handler.handle_tools_call(request)
        
        assert response.id == "call-3"
        assert response.error is None
        assert response.result is not None
        assert "content" in response.result

    @pytest.mark.asyncio
    async def test_handle_request_routing(self, handler):
        """Test request routing to appropriate handlers."""
        # Test initialize routing
        init_request = MCPRequest(
            id="route-1",
            method=MCPMethods.INITIALIZE,
            params={"protocolVersion": "2024-11-05"}
        )
        
        response = await handler.handle_request(init_request)
        assert response.id == "route-1"
        assert response.error is None
        
        # Test tools/list routing
        tools_request = MCPRequest(
            id="route-2",
            method=MCPMethods.TOOLS_LIST
        )
        
        response = await handler.handle_request(tools_request)
        assert response.id == "route-2"
        assert response.error is None

    @pytest.mark.asyncio
    async def test_handle_request_unknown_method(self, handler):
        """Test handling unknown method."""
        request = MCPRequest(
            id="unknown-1",
            method="unknown/method"
        )
        
        response = await handler.handle_request(request)
        
        assert response.id == "unknown-1"
        assert response.result is None
        assert response.error is not None
        assert response.error.code == MCPErrorCodes.METHOD_NOT_FOUND
        assert "Method 'unknown/method' not supported" in response.error.message

    def test_register_tool(self, handler):
        """Test tool registration."""
        tool = MCPTool(
            name="new_tool",
            description="A new tool",
            inputSchema={"type": "object"}
        )
        
        assert len(handler.tools) == 0
        handler.register_tool(tool)
        assert len(handler.tools) == 1
        assert "new_tool" in handler.tools
        assert handler.tools["new_tool"] == tool

    def test_get_available_tools(self, handler):
        """Test getting available tools."""
        # Initially empty
        tools = handler.get_available_tools()
        assert len(tools) == 0
        
        # Add some tools
        tool1 = MCPTool("tool1", "First tool", {"type": "object"})
        tool2 = MCPTool("tool2", "Second tool", {"type": "object"})
        
        handler.register_tool(tool1)
        handler.register_tool(tool2)
        
        tools = handler.get_available_tools()
        assert len(tools) == 2
        assert tool1 in tools
        assert tool2 in tools

    def test_get_fastmcp_instance(self, handler):
        """Test getting FastMCP instance."""
        mcp_instance = handler.get_fastmcp_instance()
        # May be None if FastMCP is not available
        assert mcp_instance == handler.mcp

    def test_is_protocol_version_supported(self, handler):
        """Test protocol version support checking."""
        assert handler._is_protocol_version_supported("2024-11-05") is True
        assert handler._is_protocol_version_supported("2023-01-01") is False
        assert handler._is_protocol_version_supported("invalid") is False

    @pytest.mark.asyncio
    async def test_execute_tool_placeholder(self, handler):
        """Test tool execution placeholder."""
        result = await handler._execute_tool("test_tool", {"arg": "value"})
        
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "test_tool" in result["content"][0]["text"]
        assert "arg" in result["content"][0]["text"]