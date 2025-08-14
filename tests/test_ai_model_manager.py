"""Tests for AI Model Manager."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys

# Mock torch and vllm before importing our modules
sys.modules['torch'] = MagicMock()
sys.modules['torch.backends'] = MagicMock()
sys.modules['torch.backends.mps'] = MagicMock()
sys.modules['torch.cuda'] = MagicMock()
sys.modules['vllm'] = MagicMock()
sys.modules['vllm.engine'] = MagicMock()
sys.modules['vllm.engine.async_llm_engine'] = MagicMock()
sys.modules['vllm.engine.arg_utils'] = MagicMock()
sys.modules['vllm.outputs'] = MagicMock()

from src.models.ai_manager import AIModelManager, ModelConfig


class TestAIModelManager:
    """Test cases for AIModelManager."""
    
    @pytest.fixture
    def ai_manager(self):
        """Create AIModelManager instance for testing."""
        return AIModelManager(max_memory_gb=8)
    
    def test_initialization(self, ai_manager):
        """Test AIModelManager initialization."""
        assert ai_manager.config.max_memory_gb == 8
        assert ai_manager.model_manager is not None
        assert ai_manager.inference_engine is None
        assert not ai_manager.is_ready
        assert not ai_manager.is_loading
    
    def test_is_model_ready_false_initially(self, ai_manager):
        """Test is_model_ready returns False initially."""
        assert not ai_manager.is_model_ready()
    
    def test_model_config_defaults(self):
        """Test ModelConfig default values."""
        config = ModelConfig()
        assert config.model_name == "openai/gpt-oss-20b"
        assert config.max_model_len == 4096
        assert config.gpu_memory_utilization == 0.8
        assert config.max_memory_gb == 12
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.max_tokens == 256
    
    @pytest.mark.asyncio
    async def test_generate_text_not_ready(self, ai_manager):
        """Test generate_text raises error when model not ready."""
        with pytest.raises(RuntimeError, match="Model is not ready"):
            await ai_manager.generate_text("test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_code_completion_not_ready(self, ai_manager):
        """Test generate_code_completion raises error when model not ready."""
        with pytest.raises(RuntimeError, match="Model is not ready"):
            await ai_manager.generate_code_completion("def test():")
    
    @pytest.mark.asyncio
    async def test_explain_code_not_ready(self, ai_manager):
        """Test explain_code raises error when model not ready."""
        with pytest.raises(RuntimeError, match="Model is not ready"):
            await ai_manager.explain_code("print('hello')")
    
    def test_get_model_status(self, ai_manager):
        """Test get_model_status returns correct structure."""
        status = ai_manager.get_model_status()
        
        assert 'is_ready' in status
        assert 'is_loading' in status
        assert 'model_path' in status
        assert 'config' in status
        assert 'hardware' in status
        assert 'performance' in status
        
        # Check config structure
        config = status['config']
        assert 'model_name' in config
        assert 'quantization' in config
        assert 'max_memory_gb' in config
        
        # Check performance structure
        performance = status['performance']
        assert 'total_requests' in performance
        assert 'total_inference_time' in performance
        assert 'avg_inference_time' in performance
    
    def test_is_code_prompt_detection(self, ai_manager):
        """Test _is_code_prompt correctly detects code prompts."""
        # Code prompts
        assert ai_manager._is_code_prompt("def hello():")
        assert ai_manager._is_code_prompt("class MyClass:")
        assert ai_manager._is_code_prompt("import numpy as np")
        assert ai_manager._is_code_prompt("function test() {")
        assert ai_manager._is_code_prompt("const x = 5;")
        
        # Non-code prompts
        assert not ai_manager._is_code_prompt("What is Python?")
        assert not ai_manager._is_code_prompt("Explain this concept")
        assert not ai_manager._is_code_prompt("Hello world")
    
    def test_format_prompt_with_context_code(self, ai_manager):
        """Test _format_prompt_with_context for code prompts."""
        code_prompt = "def hello():"
        formatted = ai_manager._format_prompt_with_context(code_prompt)
        
        assert "expert programmer" in formatted.lower()
        assert "complete the following code" in formatted.lower()
        assert code_prompt in formatted
    
    def test_format_prompt_with_context_non_code(self, ai_manager):
        """Test _format_prompt_with_context for non-code prompts."""
        text_prompt = "What is Python?"
        formatted = ai_manager._format_prompt_with_context(text_prompt)
        
        assert "coding assistant" in formatted.lower()
        assert text_prompt in formatted
    
    @pytest.mark.asyncio
    async def test_unload_model(self, ai_manager):
        """Test unload_model resets state correctly."""
        # Set up some state
        ai_manager.is_ready = True
        ai_manager.is_loading = True
        ai_manager.inference_engine = Mock()
        ai_manager.inference_engine.unload_model = AsyncMock()
        
        await ai_manager.unload_model()
        
        assert not ai_manager.is_ready
        assert not ai_manager.is_loading
        assert ai_manager.inference_engine is None
        
    @pytest.mark.asyncio
    async def test_health_check_not_ready(self, ai_manager):
        """Test health_check when model is not ready."""
        health = await ai_manager.health_check()
        
        assert 'overall_status' in health
        assert 'model_manager' in health
        assert 'inference_engine' in health
        assert 'functionality' in health
        assert 'timestamp' in health
        assert 'details' in health
        
        assert health['overall_status'] == 'not_ready'
        assert health['inference_engine'] == 'not_loaded'
        assert health['functionality'] == 'not_available'


class TestAIModelManagerIntegration:
    """Integration tests for AIModelManager with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_load_model_success(self):
        """Test successful model loading flow."""
        ai_manager = AIModelManager(max_memory_gb=16)
        
        # Mock dependencies
        with patch.object(ai_manager.model_manager, 'ensure_model_available') as mock_ensure:
            mock_ensure.return_value = Path("/fake/model/path")
            
            with patch('src.models.ai_manager.InferenceEngine') as mock_engine_class:
                mock_engine = Mock()
                mock_engine.load_model = AsyncMock()
                mock_engine_class.return_value = mock_engine
                
                # Mock the verification step
                with patch.object(ai_manager, '_verify_model_functionality') as mock_verify:
                    mock_verify.return_value = None
                    
                    result = await ai_manager.load_model()
                    
                    assert result is True
                    assert ai_manager.is_ready
                    assert not ai_manager.is_loading
                    assert ai_manager.model_path == Path("/fake/model/path")
                    assert ai_manager.inference_engine == mock_engine
                    
                    # Verify calls
                    mock_ensure.assert_called_once()
                    mock_engine.load_model.assert_called_once()
                    mock_verify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_model_already_loaded(self):
        """Test load_model when model is already loaded."""
        ai_manager = AIModelManager()
        ai_manager.is_ready = True
        
        result = await ai_manager.load_model()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_load_model_already_loading(self):
        """Test load_model when loading is in progress."""
        ai_manager = AIModelManager()
        ai_manager.is_loading = True
        
        result = await ai_manager.load_model()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_generate_text_with_mocked_engine(self):
        """Test generate_text with mocked inference engine."""
        ai_manager = AIModelManager()
        ai_manager.is_ready = True
        
        # Mock inference engine
        mock_engine = Mock()
        mock_result = Mock()
        mock_result.text = "Generated response"
        
        async def mock_generate(*args, **kwargs):
            yield mock_result
        
        mock_engine.generate_completion = mock_generate
        ai_manager.inference_engine = mock_engine
        
        result = await ai_manager.generate_text("test prompt")
        
        assert result == "Generated response"
        assert ai_manager.total_requests == 1
        assert ai_manager.total_inference_time > 0
    
    @pytest.mark.asyncio
    async def test_restart_model(self):
        """Test model restart functionality."""
        ai_manager = AIModelManager()
        
        # Mock the load_model method
        with patch.object(ai_manager, 'load_model') as mock_load:
            mock_load.return_value = True
            
            with patch.object(ai_manager, 'unload_model') as mock_unload:
                mock_unload.return_value = None
                
                result = await ai_manager.restart_model()
                
                assert result is True
                mock_unload.assert_called_once()
                mock_load.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])