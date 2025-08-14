"""Integration tests for model downloading and caching."""

import asyncio
import tempfile
import json
from pathlib import Path
from datetime import datetime

from src.models.manager import ModelManager


async def test_model_integrity_check():
    """Test model integrity checking with a fake model."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ModelManager(data_dir=Path(temp_dir))
        
        # Create a fake model directory
        model_dir = Path(temp_dir) / "models" / "test_model"
        model_dir.mkdir(parents=True)
        
        print("Testing invalid model (missing files)...")
        is_valid = await manager._verify_model_integrity(model_dir)
        print(f"Invalid model result: {is_valid}")
        assert not is_valid
        
        # Add config.json
        config = {
            "model_type": "test",
            "vocab_size": 50257,
            "n_positions": 2048
        }
        (model_dir / "config.json").write_text(json.dumps(config, indent=2))
        
        print("Testing model with config but no weights...")
        is_valid = await manager._verify_model_integrity(model_dir)
        print(f"Config-only model result: {is_valid}")
        assert not is_valid
        
        # Add a substantial model file (2GB fake data)
        print("Creating fake model weights (2GB)...")
        model_file = model_dir / "model.safetensors"
        with open(model_file, "wb") as f:
            # Write 2GB of fake data in chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            chunk = b"x" * chunk_size
            for _ in range(2048):  # 2048 * 1MB = 2GB
                f.write(chunk)
        
        print("Testing valid model...")
        is_valid = await manager._verify_model_integrity(model_dir)
        print(f"Valid model result: {is_valid}")
        assert is_valid
        
        # Test hash calculation
        print("Calculating model hash...")
        model_hash = manager._calculate_directory_hash(model_dir)
        print(f"Model hash: {model_hash[:16]}...")
        assert len(model_hash) == 64
        
        # Test hash consistency
        model_hash2 = manager._calculate_directory_hash(model_dir)
        assert model_hash == model_hash2
        
        print("✅ Model integrity checks passed!")


async def test_cache_functionality():
    """Test model cache functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ModelManager(data_dir=Path(temp_dir))
        
        # Test empty cache
        cache_info = manager.get_cache_info()
        print(f"Empty cache info: {cache_info}")
        assert cache_info['total_models'] == 0
        
        # Create fake model and add to cache
        model_dir = Path(temp_dir) / "models" / "test_model"
        model_dir.mkdir(parents=True)
        
        config = {"model_type": "test"}
        (model_dir / "config.json").write_text(json.dumps(config))
        (model_dir / "model.safetensors").write_bytes(b"x" * (1024 * 1024 * 1024))  # 1GB
        
        # Get model info (should add to cache)
        model_info = manager.get_model_info("test/model")
        print(f"Model info: {model_info}")
        assert model_info is not None
        assert model_info.name == "test/model"
        assert model_info.size_gb > 0.9  # Should be close to 1GB
        
        # Check cache was updated
        cache_info = manager.get_cache_info()
        print(f"Updated cache info: {cache_info}")
        assert cache_info['total_models'] == 1
        assert "test/model" in cache_info['models']
        
        # Test cache persistence
        manager._save_cache()
        new_manager = ModelManager(data_dir=Path(temp_dir))
        
        cached_models = new_manager.list_models()
        print(f"Loaded models from cache: {[m.name for m in cached_models]}")
        assert len(cached_models) == 1
        assert cached_models[0].name == "test/model"
        
        print("✅ Cache functionality tests passed!")


async def test_model_health_status():
    """Test model health status checking."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ModelManager(data_dir=Path(temp_dir))
        
        # Test non-existent model
        status = await manager.get_model_health_status("nonexistent/model")
        print(f"Non-existent model status: {status}")
        assert not status['exists']
        assert status['needs_repair']
        
        # Create valid model
        model_dir = Path(temp_dir) / "models" / "test_model"
        model_dir.mkdir(parents=True)
        
        config = {"model_type": "test"}
        (model_dir / "config.json").write_text(json.dumps(config))
        (model_dir / "model.safetensors").write_bytes(b"x" * (1024 * 1024 * 1024))  # 1GB
        
        # Test valid model
        status = await manager.get_model_health_status("test/model")
        print(f"Valid model status: {status}")
        assert status['exists']
        assert status['integrity_verified']
        assert not status['needs_repair']
        assert status['size_gb'] > 0.9
        
        print("✅ Model health status tests passed!")


async def main():
    """Run all integration tests."""
    print("🧪 Running model manager integration tests...\n")
    
    try:
        await test_model_integrity_check()
        print()
        
        await test_cache_functionality()
        print()
        
        await test_model_health_status()
        print()
        
        print("🎉 All integration tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())