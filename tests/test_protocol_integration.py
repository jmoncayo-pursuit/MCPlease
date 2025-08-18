"""Tests for MCP protocol and tool integration."""

import pytest

from mcplease_mcp.protocol.handler import MCPProtocolHandler
from mcplease_mcp.tools.registry import MCPToolRegistry
from mcplease_mcp.protocol.models import MCPRequest, MCPMethods


class TestProtocolIntegration:
    """Test integration between protocol handler and tool registry."""

    @pytest.fixture
    def tool_registry(self):
        """Create a tool registry for testing."""
        return MCPToolRegistry()

    @pytest.fixture
    def handler_with_registry(self, tool_registry):
        """Create a protocol handler with tool registry."""
        return MCPProtocolHandler("Test Server", tool_registry)

    def test_handler_with_tool_registry_initialization(self, handler_with_registry):
        """Test handler initialization with tool registry."""
        assert handler_with_registry.tool_registry is not None
        assert len(handler_with_registry.tools) == 3  # Default AI tools
        assert "code_completion" in handler_with_registry.tools
        assert "code_explanation" in handler_with_registry.tools
        assert "debug_assistance" in handler_with_registry.tools

    @pytest.mark.asyncio
    async def test_tools_list_with_registry(self, handler_with_registry):
        """Test tools/list with tool registry."""
        request = MCPRequest(
            id="test-1",
            method=MCPMethods.TOOLS_LIST
        )
        
        response = await handler_with_registry.handle_tools_list(request)
        
        assert response.error is None
        assert response.result is not None
        assert "tools" in response.result
        assert len(response.result["tools"]) == 3
        
        tool_names = [tool["name"] for tool in response.result["tools"]]
        assert "code_completion" in tool_names
        assert "code_explanation" in tool_names
        assert "debug_assistance" in tool_names

    @pytest.mark.asyncio
    async def test_tools_call_with_registry(self, handler_with_registry):
        """Test tools/call with tool registry."""
        request = MCPRequest(
            id="test-2",
            method=MCPMethods.TOOLS_CALL,
            params={
                "name": "code_completion",
                "arguments": {
                    "code": "def hello():",
                    "language": "python"
                }
            }
        )
        
        response = await handler_with_registry.handle_tools_call(request)
        
        assert response.error is None
        assert response.result is not None
        assert "content" in response.result
        assert len(response.result["content"]) == 1
        assert response.result["content"][0]["type"] == "text"
        assert "python" in response.result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_tools_call_code_explanation(self, handler_with_registry):
        """Test code explanation tool call."""
        request = MCPRequest(
            id="test-3",
            method=MCPMethods.TOOLS_CALL,
            params={
                "name": "code_explanation",
                "arguments": {
                    "code": "print('Hello, World!')",
                    "language": "python",
                    "detail_level": "brief"
                }
            }
        )
        
        response = await handler_with_registry.handle_tools_call(request)
        
        assert response.error is None
        assert response.result is not None
        assert "content" in response.result
        text = response.result["content"][0]["text"]
        assert "python" in text.lower()
        assert "brief" in text.lower()

    @pytest.mark.asyncio
    async def test_tools_call_debug_assistance(self, handler_with_registry):
        """Test debug assistance tool call."""
        request = MCPRequest(
            id="test-4",
            method=MCPMethods.TOOLS_CALL,
            params={
                "name": "debug_assistance",
                "arguments": {
                    "code": "x = 1 / 0",
                    "language": "python",
                    "error_message": "ZeroDivisionError: division by zero"
                }
            }
        )
        
        response = await handler_with_registry.handle_tools_call(request)
        
        assert response.error is None
        assert response.result is not None
        assert "content" in response.result
        text = response.result["content"][0]["text"]
        assert "python" in text.lower()
        assert "zerodivisionerror" in text.lower()

    def test_set_tool_registry_after_init(self):
        """Test setting tool registry after handler initialization."""
        handler = MCPProtocolHandler("Test Server")
        registry = MCPToolRegistry()
        
        assert len(handler.tools) == 0
        
        handler.set_tool_registry(registry)
        
        assert handler.tool_registry == registry
        assert len(handler.tools) == 3

    @pytest.mark.asyncio
    async def test_handler_without_registry_fallback(self):
        """Test handler fallback when no registry is set."""
        handler = MCPProtocolHandler("Test Server")
        
        # Should use fallback implementation
        result = await handler._execute_tool("test_tool", {"arg": "value"})
        
        assert "content" in result
        assert "no registry" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_full_request_handling_integration(self, handler_with_registry):
        """Test full request handling with tool registry integration."""
        # Test initialize
        init_request = MCPRequest(
            id="init-1",
            method=MCPMethods.INITIALIZE,
            params={"protocolVersion": "2024-11-05"}
        )
        
        init_response = await handler_with_registry.handle_request(init_request)
        assert init_response.error is None
        
        # Test tools/list
        list_request = MCPRequest(
            id="list-1",
            method=MCPMethods.TOOLS_LIST
        )
        
        list_response = await handler_with_registry.handle_request(list_request)
        assert list_response.error is None
        assert len(list_response.result["tools"]) == 3
        
        # Test tools/call
        call_request = MCPRequest(
            id="call-1",
            method=MCPMethods.TOOLS_CALL,
            params={
                "name": "code_completion",
                "arguments": {
                    "code": "def test():",
                    "language": "python"
                }
            }
        )
        
        call_response = await handler_with_registry.handle_request(call_request)
        assert call_response.error is None
        assert "content" in call_response.result