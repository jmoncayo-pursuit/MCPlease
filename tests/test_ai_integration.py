"""Tests for AI adapter integration with MCP tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from mcplease_mcp.adapters.ai_adapter import MCPAIAdapter
from mcplease_mcp.tools.registry import MCPToolRegistry
from mcplease_mcp.tools.ai_tools import set_ai_adapter, get_ai_adapter
from mcplease_mcp.protocol.handler import MCPProtocolHandler
from mcplease_mcp.protocol.models import MCPRequest, MCPMethods


class TestAIIntegration:
    """Test AI adapter integration with MCP components."""

    @pytest.fixture
    def mock_ai_manager(self):
        """Create a mock AI manager."""
        mock = AsyncMock()
        mock.load_model = AsyncMock(return_value=True)
        mock.generate_text = AsyncMock(return_value="AI generated response")
        mock.get_model_status = MagicMock(return_value={"status": "ready"})
        return mock

    @pytest.fixture
    def ai_adapter(self, mock_ai_manager):
        """Create AI adapter with mock manager."""
        return MCPAIAdapter(ai_manager=mock_ai_manager)

    @pytest.fixture
    def tool_registry_with_ai(self, ai_adapter):
        """Create tool registry with AI adapter."""
        return MCPToolRegistry(ai_adapter=ai_adapter)

    @pytest.fixture
    def handler_with_ai(self, tool_registry_with_ai):
        """Create protocol handler with AI-enabled tool registry."""
        return MCPProtocolHandler("Test Server", tool_registry_with_ai)

    def test_ai_adapter_setup_in_registry(self, tool_registry_with_ai, ai_adapter):
        """Test that AI adapter is properly set up in tool registry."""
        assert tool_registry_with_ai.ai_adapter == ai_adapter
        assert get_ai_adapter() == ai_adapter

    @pytest.mark.asyncio
    async def test_code_completion_with_ai(self, tool_registry_with_ai, mock_ai_manager):
        """Test code completion tool with AI adapter."""
        mock_ai_manager.generate_text = AsyncMock(return_value="    print('Hello, World!')")
        
        result = await tool_registry_with_ai.execute_tool(
            "code_completion",
            {
                "code": "def hello():",
                "language": "python"
            }
        )
        
        assert "content" in result
        assert "Hello, World!" in result["content"][0]["text"]
        mock_ai_manager.generate_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_code_explanation_with_ai(self, tool_registry_with_ai, mock_ai_manager):
        """Test code explanation tool with AI adapter."""
        mock_ai_manager.generate_text = AsyncMock(
            return_value="This function prints a greeting message to the console."
        )
        
        result = await tool_registry_with_ai.execute_tool(
            "code_explanation",
            {
                "code": "print('Hello')",
                "language": "python",
                "detail_level": "detailed"
            }
        )
        
        assert "content" in result
        assert "greeting message" in result["content"][0]["text"]
        mock_ai_manager.generate_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_debug_assistance_with_ai(self, tool_registry_with_ai, mock_ai_manager):
        """Test debug assistance tool with AI adapter."""
        mock_ai_manager.generate_text = AsyncMock(
            return_value="The error occurs because you're dividing by zero. Use a try-except block."
        )
        
        result = await tool_registry_with_ai.execute_tool(
            "debug_assistance",
            {
                "code": "x = 1/0",
                "language": "python",
                "error_message": "ZeroDivisionError: division by zero"
            }
        )
        
        assert "content" in result
        assert "dividing by zero" in result["content"][0]["text"]
        mock_ai_manager.generate_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_mcp_workflow_with_ai(self, handler_with_ai, mock_ai_manager):
        """Test full MCP workflow with AI integration."""
        mock_ai_manager.generate_text = AsyncMock(return_value="AI completion result")
        
        # Test initialize
        init_request = MCPRequest(
            id="init-1",
            method=MCPMethods.INITIALIZE,
            params={"protocolVersion": "2024-11-05"}
        )
        
        init_response = await handler_with_ai.handle_request(init_request)
        assert init_response.error is None
        
        # Test tools/list
        list_request = MCPRequest(
            id="list-1",
            method=MCPMethods.TOOLS_LIST
        )
        
        list_response = await handler_with_ai.handle_request(list_request)
        assert list_response.error is None
        assert len(list_response.result["tools"]) == 3
        
        # Test tools/call with AI
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
        
        call_response = await handler_with_ai.handle_request(call_request)
        assert call_response.error is None
        assert "content" in call_response.result
        assert "AI completion result" in call_response.result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_ai_adapter_initialization_in_workflow(self, tool_registry_with_ai, mock_ai_manager):
        """Test that AI adapter is initialized when tools are executed."""
        # AI should not be initialized yet
        assert not tool_registry_with_ai.ai_adapter.is_initialized
        
        # Execute a tool - this should trigger AI initialization
        await tool_registry_with_ai.execute_tool(
            "code_completion",
            {"code": "test", "language": "python"}
        )
        
        # AI should now be initialized
        mock_ai_manager.load_model.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_error_handling_in_tools(self, tool_registry_with_ai, mock_ai_manager):
        """Test error handling when AI fails."""
        mock_ai_manager.generate_text = AsyncMock(side_effect=Exception("AI model error"))
        
        result = await tool_registry_with_ai.execute_tool(
            "code_completion",
            {"code": "def test():", "language": "python"}
        )
        
        # Should still return a result with fallback
        assert "content" in result
        # Should contain fallback message
        assert "AI model not available" in result["content"][0]["text"]

    def test_registry_stats_with_ai(self, tool_registry_with_ai, ai_adapter):
        """Test registry statistics include AI adapter info."""
        stats = tool_registry_with_ai.get_registry_stats()
        
        assert stats["has_ai_adapter"] is True
        assert stats["ai_adapter_status"] is not None
        assert stats["ai_adapter_status"]["ai_manager_available"] is True

    def test_registry_without_ai_adapter(self):
        """Test registry without AI adapter."""
        registry = MCPToolRegistry()
        
        stats = registry.get_registry_stats()
        assert stats["has_ai_adapter"] is False
        assert stats["ai_adapter_status"] is None

    @pytest.mark.asyncio
    async def test_ai_adapter_context_formatting(self, ai_adapter, mock_ai_manager):
        """Test that AI adapter formats prompts correctly."""
        mock_ai_manager.generate_text = AsyncMock(return_value="formatted response")
        
        # Test completion prompt formatting
        result = await ai_adapter.generate_completion(
            "def hello():",
            {"language": "python", "cursor_position": 12}
        )
        
        # Check that generate_text was called with formatted prompt
        call_args = mock_ai_manager.generate_text.call_args
        prompt = call_args[1]["prompt"]  # keyword argument
        
        assert "python" in prompt.lower()
        assert "def hello():" in prompt
        assert "complete" in prompt.lower()

    @pytest.mark.asyncio
    async def test_ai_adapter_prompt_cleaning(self, ai_adapter, mock_ai_manager):
        """Test that AI adapter cleans completion results."""
        # Mock AI returning markdown code block
        mock_ai_manager.generate_text = AsyncMock(
            return_value="```python\ndef hello():\n    print('Hello')\n```"
        )
        
        result = await ai_adapter.generate_completion("def hello():", {"language": "python"})
        
        # Should have markdown removed
        assert "```" not in result
        assert "def hello():" in result
        assert "print('Hello')" in result