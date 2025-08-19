"""Tests for model manager with caching and integrity checks."""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.models.manager import ModelManager, ModelInfo, ModelCache
from src.utils.exceptions import ModelDownloadError


class TestModelManager:
    """Test cases for ModelManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def model_manager(self, temp_dir):
        """Create ModelManager instance for testing."""
        return ModelManager(data_dir=temp_dir)
    
    def test_init(self, model_manager, temp_dir):
        """Test ModelManager initialization."""
        assert model_manager.data_dir == temp_dir
        assert model_manager.models_dir == temp_dir / "models"
        assert model_manager.cache_dir == temp_dir / "cache"
        assert model_manager.models_dir.exists()
        assert model_manager.cache_dir.exists()
        assert isinstance(model_manager._cache, ModelCache)
    
    def test_cache_persistence(self, model_manager):
        """Test cache loading and saving."""
        # Create a model info
        model_info = ModelInfo(
            name="test/model",
            path=Path("/fake/path"),
            size_gb=1.5,
            quantization="mxfp4",
            context_length=4096,
            download_date=datetime.now(),
            integrity_hash="fake_hash"
        )
        
        # Add to cache and save
        model_manager._cache.models["test/model"] = model_info
        model_manager._save_cache()
        
        # Create new manager instance (should load cache)
        new_manager = ModelManager(data_dir=model_manager.data_dir)
        
        # Check cache was loaded
        assert "test/model" in new_manager._cache.models
        cached_info = new_manager._cache.models["test/model"]
        assert cached_info.name == "test/model"
        assert cached_info.size_gb == 1.5
        assert cached_info.integrity_hash == "fake_hash"
    
    def test_calculate_file_hash(self, model_manager, temp_dir):
        """Test file hash calculation."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")
        
        hash_value = model_manager._calculate_file_hash(test_file)
        
        # Should be consistent
        assert hash_value == model_manager._calculate_file_hash(test_file)
        assert len(hash_value) == 64  # SHA256 hex length
    
    def test_calculate_directory_hash(self, model_manager, temp_dir):
        """Test directory hash calculation."""
        # Create test directory structure
        test_dir = temp_dir / "test_model"
        test_dir.mkdir()
        
        (test_dir / "config.json").write_text('{"test": true}')
        (test_dir / "model.bin").write_bytes(b"fake model data")
        
        hash_value = model_manager._calculate_directory_hash(test_dir)
        
        # Should be consistent
        assert hash_value == model_manager._calculate_directory_hash(test_dir)
        assert len(hash_value) == 64  # SHA256 hex length
        
        # Should change if file content changes
        (test_dir / "config.json").write_text('{"test": false}')
        new_hash = model_manager._calculate_directory_hash(test_dir)
        assert new_hash != hash_value
    
    @pytest.mark.asyncio
    async def test_verify_model_integrity_valid(self, model_manager, temp_dir):
        """Test model integrity verification with valid model."""
        # Create fake model directory
        model_dir = temp_dir / "test_model"
        model_dir.mkdir()
        
        # Create essential files
        (model_dir / "config.json").write_text('{"model_type": "test"}')
        (model_dir / "model.safetensors").write_bytes(b"x" * (2 * 1024 * 1024 * 1024))  # 2GB
        
        # Should pass integrity check
        is_valid = await model_manager._verify_model_integrity(model_dir)
        assert is_valid
    
    @pytest.mark.asyncio
    async def test_verify_model_integrity_invalid(self, model_manager, temp_dir):
        """Test model integrity verification with invalid model."""
        # Create fake model directory
        model_dir = temp_dir / "test_model"
        model_dir.mkdir()
        
        # Missing essential files
        is_valid = await model_manager._verify_model_integrity(model_dir)
        assert not is_valid
        
        # Add config but invalid JSON
        (model_dir / "config.json").write_text('invalid json')
        is_valid = await model_manager._verify_model_integrity(model_dir)
        assert not is_valid
        
        # Fix JSON but model file too small
        (model_dir / "config.json").write_text('{"model_type": "test"}')
        (model_dir / "model.safetensors").write_bytes(b"tiny")
        is_valid = await model_manager._verify_model_integrity(model_dir)
        assert not is_valid
    
    @pytest.mark.asyncio
    async def test_should_redownload_model(self, model_manager, temp_dir):
        """Test logic for determining if model should be re-downloaded."""
        model_name = "test/model"
        model_path = temp_dir / "models" / "test_model"
        
        # Non-existent model should be downloaded
        should_redownload = await model_manager._should_redownload_model(model_name, model_path)
        assert should_redownload
        
        # Create model directory
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text('{"model_type": "test"}')
        (model_path / "model.safetensors").write_bytes(b"x" * (2 * 1024 * 1024 * 1024))
        
        # No cache info, should verify integrity
        should_redownload = await model_manager._should_redownload_model(model_name, model_path)
        assert not should_redownload  # Should pass integrity check
        
        # Add cache info with recent verification
        model_info = ModelInfo(
            name=model_name,
            path=model_path,
            size_gb=2.0,
            quantization="mxfp4",
            context_length=4096,
            last_verified=datetime.now() - timedelta(hours=1),  # Recent
            integrity_hash="fake_hash"
        )
        model_manager._cache.models[model_name] = model_info
        
        should_redownload = await model_manager._should_redownload_model(model_name, model_path)
        assert not should_redownload  # Recently verified
    
    @pytest.mark.asyncio
    @patch('src.models.manager.snapshot_download')
    async def test_download_model_success(self, mock_download, model_manager, temp_dir):
        """Test successful model download."""
        model_name = "test/model"
        model_path = temp_dir / "models" / "test_model"
        
        # Mock successful download
        mock_download.return_value = str(model_path)
        
        # Create fake downloaded model
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text('{"model_type": "test"}')
        (model_path / "model.safetensors").write_bytes(b"x" * (2 * 1024 * 1024 * 1024))
        
        # Mock remote info and force redownload
        with patch.object(model_manager, '_check_remote_model_info', return_value={}), \
             patch.object(model_manager, '_verify_model_integrity', return_value=True), \
             patch.object(model_manager, '_calculate_directory_hash', return_value="fake_hash"), \
             patch.object(model_manager, '_calculate_directory_size', return_value=2.0):
            result_path = await model_manager.download_model(model_name, force_redownload=True)
        
        assert result_path == model_path
        assert model_name in model_manager._cache.models
        
        cached_info = model_manager._cache.models[model_name]
        assert cached_info.name == model_name
        assert cached_info.integrity_hash is not None
        assert cached_info.download_date is not None
    
    @pytest.mark.asyncio
    async def test_ensure_model_available(self, model_manager, temp_dir):
        """Test ensuring model is available."""
        model_name = "test/model"
        model_path = temp_dir / "models" / "test_model"
        
        # Create valid model
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text('{"model_type": "test"}')
        (model_path / "model.safetensors").write_bytes(b"x" * (2 * 1024 * 1024 * 1024))
        
        # Add to cache as recently verified
        model_info = ModelInfo(
            name=model_name,
            path=model_path,
            size_gb=2.0,
            quantization="mxfp4",
            context_length=4096,
            last_verified=datetime.now(),
            integrity_hash="fake_hash"
        )
        model_manager._cache.models[model_name] = model_info
        
        result_path = await model_manager.ensure_model_available(model_name)
        assert result_path == model_path
    
    @pytest.mark.asyncio
    async def test_verify_model(self, model_manager, temp_dir):
        """Test model verification."""
        model_name = "test/model"
        model_path = temp_dir / "models" / "test_model"
        
        # Non-existent model
        is_valid = await model_manager.verify_model(model_name)
        assert not is_valid
        
        # Create valid model
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text('{"model_type": "test"}')
        (model_path / "model.safetensors").write_bytes(b"x" * (2 * 1024 * 1024 * 1024))
        
        is_valid = await model_manager.verify_model(model_name)
        assert is_valid
    
    def test_get_cache_info(self, model_manager):
        """Test getting cache information."""
        # Add some fake models to cache
        model_info1 = ModelInfo(
            name="test/model1",
            path=Path("/fake/path1"),
            size_gb=1.5,
            quantization="mxfp4",
            context_length=4096
        )
        model_info2 = ModelInfo(
            name="test/model2",
            path=Path("/fake/path2"),
            size_gb=2.5,
            quantization="bf16",
            context_length=8192
        )
        
        model_manager._cache.models["test/model1"] = model_info1
        model_manager._cache.models["test/model2"] = model_info2
        
        cache_info = model_manager.get_cache_info()
        
        assert cache_info['total_models'] == 2
        assert cache_info['total_size_gb'] == 4.0
        assert 'test/model1' in cache_info['models']
        assert 'test/model2' in cache_info['models']
    
    def test_clear_cache(self, model_manager):
        """Test clearing cache."""
        # Add fake model to cache
        model_info = ModelInfo(
            name="test/model",
            path=Path("/fake/path"),
            size_gb=1.5,
            quantization="mxfp4",
            context_length=4096
        )
        model_manager._cache.models["test/model"] = model_info
        
        # Clear cache
        model_manager.clear_cache()
        
        assert len(model_manager._cache.models) == 0
        
        # Should persist after save/load
        model_manager._save_cache()
        new_manager = ModelManager(data_dir=model_manager.data_dir)
        assert len(new_manager._cache.models) == 0


if __name__ == "__main__":
    pytest.main([__file__])