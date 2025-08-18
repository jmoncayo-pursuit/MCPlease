"""Tests for AI adapter."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from mcplease_mcp.adapters.ai_adapter import MCPAIAdapter


class TestMCPAIAdapter:
    """Test MCP AI adapter."""

    @pytest.fixture
    def mock_ai_manager(self):
        """Create a mock AI manager."""
        mock = AsyncMock()
        mock.load_model = AsyncMock(return_value=True)
        mock.generate_text = AsyncMock(return_value="Generated text")
        mock.get_model_status = MagicMock(return_value={"status": "ready"})
        return mock

    @pytest.fixture
    def adapter_with_mock(self, mock_ai_manager):
        """Create adapter with mock AI manager."""
        return MCPAIAdapter(ai_manager=mock_ai_manager)

    @pytest.fixture
    def adapter_without_ai(self):
        """Create adapter without AI manager."""
        return MCPAIAdapter(ai_manager=None)

    def test_adapter_initialization_with_ai(self, adapter_with_mock):
        """Test adapter initialization with AI manager."""
        assert adapter_with_mock.ai_manager is not None
        assert adapter_with_mock.max_memory_gb == 12
        assert not adapter_with_mock.is_initialized
        assert not adapter_with_mock.model_ready

    def test_adapter_initialization_without_ai(self, adapter_without_ai):
        """Test adapter initialization without AI manager."""
        assert adapter_without_ai.ai_manager is None
        assert not adapter_without_ai.is_initialized
        assert not adapter_without_ai.model_ready

    @pytest.mark.asyncio
    async def test_initialize_with_ai_success(self, adapter_with_mock, mock_ai_manager):
        """Test successful initialization with AI manager."""
        result = await adapter_with_mock.initialize()
        
        assert result is True
        assert adapter_with_mock.is_initialized
        assert adapter_with_mock.model_ready
        mock_ai_manager.load_model.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_with_ai_failure(self, mock_ai_manager):
        """Test initialization failure with AI manager."""
        mock_ai_manager.load_model = AsyncMock(return_value=False)
        adapter = MCPAIAdapter(ai_manager=mock_ai_manager)
        
        result = await adapter.initialize()
        
        assert result is False
        assert adapter.is_initialized
        assert not adapter.model_ready

    @pytest.mark.asyncio
    async def test_initialize_without_ai(self, adapter_without_ai):
        """Test initialization without AI manager."""
        result = await adapter_without_ai.initialize()
        
        assert result is False
        assert adapter_without_ai.is_initialized
        assert not adapter_without_ai.model_ready

    @pytest.mark.asyncio
    async def test_generate_completion_with_ai(self, adapter_with_mock, mock_ai_manager):
        """Test code completion with AI manager."""
        mock_ai_manager.generate_text = AsyncMock(return_value="def hello():\n    print('Hello')")
        
        result = await adapter_with_mock.generate_completion(
            "def hello():",
            {"language": "python"}
        )
        
        assert "def hello():" in result or "print" in result
        mock_ai_manager.load_model.assert_called_once()
        mock_ai_manager.generate_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_completion_without_ai(self, adapter_without_ai):
        """Test code completion without AI manager."""
        result = await adapter_without_ai.generate_completion(
            "def hello():",
            {"language": "python"}
        )
        
        assert "AI model not available" in result
        assert "python" in result

    @pytest.mark.asyncio
    async def test_explain_code_with_ai(self, adapter_with_mock, mock_ai_manager):
        """Test code explanation with AI manager."""
        mock_ai_manager.generate_text = AsyncMock(return_value="This function prints hello")
        
        result = await adapter_with_mock.explain_code(
            "print('hello')",
            "python",
            "detailed"
        )
        
        assert "This function prints hello" in result
        mock_ai_manager.generate_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_explain_code_without_ai(self, adapter_without_ai):
        """Test code explanation without AI manager."""
        result = await adapter_without_ai.explain_code(
            "print('hello')",
            "python",
            "detailed"
        )
        
        assert "AI model not available" in result
        assert "python" in result
        assert "detailed" in result

    @pytest.mark.asyncio
    async def test_debug_code_with_ai(self, adapter_with_mock, mock_ai_manager):
        """Test debug assistance with AI manager."""
        mock_ai_manager.generate_text = AsyncMock(return_value="The error is caused by division by zero")
        
        result = await adapter_with_mock.debug_code(
            "x = 1/0",
            "python",
            "ZeroDivisionError"
        )
        
        assert "division by zero" in result
        mock_ai_manager.generate_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_debug_code_without_ai(self, adapter_without_ai):
        """Test debug assistance without AI manager."""
        result = await adapter_without_ai.debug_code(
            "x = 1/0",
            "python",
            "ZeroDivisionError"
        )
        
        assert "AI model not available" in result
        assert "python" in result
        assert "ZeroDivisionError" in result

    def test_format_completion_prompt(self, adapter_with_mock):
        """Test completion prompt formatting."""
        prompt = adapter_with_mock._format_completion_prompt(
            "def hello():",
            {"language": "python"}
        )
        
        assert "python" in prompt.lower()
        assert "def hello():" in prompt
        assert "complete" in prompt.lower()

    def test_format_explanation_prompt(self, adapter_with_mock):
        """Test explanation prompt formatting."""
        prompt = adapter_with_mock._format_explanation_prompt(
            "print('hello')",
            "python",
            "detailed",
            None
        )
        
        assert "python" in prompt.lower()
        assert "print('hello')" in prompt
        assert "detailed" in prompt.lower()

    def test_format_explanation_prompt_with_question(self, adapter_with_mock):
        """Test explanation prompt formatting with question."""
        prompt = adapter_with_mock._format_explanation_prompt(
            "print('hello')",
            "python",
            "brief",
            "What does this do?"
        )
        
        assert "What does this do?" in prompt
        assert "brief" in prompt.lower()

    def test_format_debug_prompt(self, adapter_with_mock):
        """Test debug prompt formatting."""
        prompt = adapter_with_mock._format_debug_prompt(
            "x = 1/0",
            "python",
            "ZeroDivisionError",
            "Should not crash",
            "Crashes with error"
        )
        
        assert "x = 1/0" in prompt
        assert "ZeroDivisionError" in prompt
        assert "Should not crash" in prompt
        assert "Crashes with error" in prompt

    def test_clean_completion_result(self, adapter_with_mock):
        """Test cleaning completion results."""
        # Test with markdown code blocks
        result_with_markdown = "```python\ndef hello():\n    print('hello')\n```"
        cleaned = adapter_with_mock._clean_completion_result(result_with_markdown)
        assert "```" not in cleaned
        assert "def hello():" in cleaned

        # Test with plain text
        result_plain = "def hello():\n    print('hello')"
        cleaned = adapter_with_mock._clean_completion_result(result_plain)
        assert cleaned == result_plain

    def test_get_model_status_with_ai(self, adapter_with_mock, mock_ai_manager):
        """Test getting model status with AI manager."""
        status = adapter_with_mock.get_model_status()
        
        assert status["ai_manager_available"] is True
        assert status["max_memory_gb"] == 12
        assert "ai_manager_status" in status

    def test_get_model_status_without_ai(self, adapter_without_ai):
        """Test getting model status without AI manager."""
        status = adapter_without_ai.get_model_status()
        
        assert status["ai_manager_available"] is False
        assert status["max_memory_gb"] == 12
        assert "ai_manager_status" not in status

    @pytest.mark.asyncio
    async def test_health_check_with_ai(self, adapter_with_mock):
        """Test health check with AI manager."""
        health = await adapter_with_mock.health_check()
        
        assert "adapter_status" in health
        assert "model_status" in health
        assert "timestamp" in health

    @pytest.mark.asyncio
    async def test_health_check_without_ai(self, adapter_without_ai):
        """Test health check without AI manager."""
        health = await adapter_without_ai.health_check()
        
        assert health["adapter_status"] == "degraded"
        assert health["model_status"] == "unavailable"

    @pytest.mark.asyncio
    async def test_ensure_model_ready_first_time(self, adapter_with_mock):
        """Test ensuring model is ready for first time."""
        result = await adapter_with_mock._ensure_model_ready()
        
        assert result is True
        assert adapter_with_mock.is_initialized
        assert adapter_with_mock.model_ready

    @pytest.mark.asyncio
    async def test_ensure_model_ready_already_initialized(self, adapter_with_mock):
        """Test ensuring model is ready when already initialized."""
        # Initialize first
        await adapter_with_mock.initialize()
        
        # Should not reinitialize
        result = await adapter_with_mock._ensure_model_ready()
        assert result is True

    @pytest.mark.asyncio
    async def test_generate_completion_with_ai_error(self, adapter_with_mock, mock_ai_manager):
        """Test completion generation with AI error."""
        mock_ai_manager.generate_text = AsyncMock(side_effect=Exception("AI error"))
        
        result = await adapter_with_mock.generate_completion("def test():", {"language": "python"})
        
        # The error should be logged and fallback should be used
        assert "AI model not available" in result or "Error generating" in result