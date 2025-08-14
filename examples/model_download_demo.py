#!/usr/bin/env python3
"""
Demo script showing model downloading and caching functionality.

This script demonstrates:
1. Model downloading with progress tracking
2. Integrity verification
3. Caching and cache persistence
4. Automatic re-download on corruption
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.manager import ModelManager
from src.utils.exceptions import ModelDownloadError


async def progress_callback(progress: float):
    """Progress callback for download tracking."""
    bar_length = 40
    filled_length = int(bar_length * progress)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\rProgress: |{bar}| {progress:.1%}', end='', flush=True)
    if progress >= 1.0:
        print()  # New line when complete


async def demo_model_download():
    """Demonstrate model downloading with a small test model."""
    print("🚀 Model Download and Caching Demo")
    print("=" * 50)
    
    # Use a small model for demo (microsoft/DialoGPT-small is ~117MB)
    model_name = "microsoft/DialoGPT-small"
    
    # Create model manager in current directory
    data_dir = Path("./demo_data")
    manager = ModelManager(data_dir=data_dir)
    
    print(f"📁 Data directory: {data_dir}")
    print(f"🖥️  Hardware: {manager.hardware_config}")
    print(f"⚙️  Optimal quantization: {manager.get_optimal_quantization()}")
    print()
    
    # Check initial cache state
    cache_info = manager.get_cache_info()
    print(f"📦 Initial cache state:")
    print(f"   - Total models: {cache_info['total_models']}")
    print(f"   - Total size: {cache_info['total_size_gb']:.2f} GB")
    print()
    
    try:
        # Check if model already exists
        model_info = manager.get_model_info(model_name)
        if model_info:
            print(f"✅ Model {model_name} already exists:")
            print(f"   - Size: {model_info.size_gb:.2f} GB")
            print(f"   - Path: {model_info.path}")
            print(f"   - Last verified: {model_info.last_verified}")
            print()
            
            # Verify integrity
            print("🔍 Verifying model integrity...")
            is_valid = await manager.verify_model(model_name)
            print(f"   - Integrity check: {'✅ PASSED' if is_valid else '❌ FAILED'}")
            print()
            
            if not is_valid:
                print("🔧 Model is corrupted, will repair...")
                success = await manager.repair_model(model_name)
                print(f"   - Repair result: {'✅ SUCCESS' if success else '❌ FAILED'}")
                print()
        else:
            print(f"📥 Downloading model: {model_name}")
            print("   This may take a few minutes for the first download...")
            print()
            
            # Download with progress tracking
            model_path = await manager.download_model(
                model_name=model_name,
                progress_callback=progress_callback
            )
            
            print(f"✅ Download completed!")
            print(f"   - Model path: {model_path}")
            print()
        
        # Get updated model info
        model_info = manager.get_model_info(model_name)
        if model_info:
            print(f"📊 Model Information:")
            print(f"   - Name: {model_info.name}")
            print(f"   - Size: {model_info.size_gb:.2f} GB")
            print(f"   - Quantization: {model_info.quantization}")
            print(f"   - Context length: {model_info.context_length}")
            print(f"   - Download date: {model_info.download_date}")
            print(f"   - Last verified: {model_info.last_verified}")
            print(f"   - Has integrity hash: {bool(model_info.integrity_hash)}")
            print()
        
        # Get health status
        health_status = await manager.get_model_health_status(model_name)
        print(f"🏥 Model Health Status:")
        print(f"   - Exists: {health_status['exists']}")
        print(f"   - Cached: {health_status['cached']}")
        print(f"   - Integrity verified: {health_status['integrity_verified']}")
        print(f"   - Needs repair: {health_status['needs_repair']}")
        print(f"   - Size: {health_status['size_gb']:.2f} GB")
        print()
        
        # Show final cache state
        cache_info = manager.get_cache_info()
        print(f"📦 Final cache state:")
        print(f"   - Total models: {cache_info['total_models']}")
        print(f"   - Total size: {cache_info['total_size_gb']:.2f} GB")
        print(f"   - Cache file: {cache_info['cache_file']}")
        print()
        
        # List all models
        all_models = manager.list_models()
        print(f"📋 All cached models ({len(all_models)}):")
        for model in all_models:
            print(f"   - {model.name}: {model.size_gb:.2f} GB")
        print()
        
        print("🎉 Demo completed successfully!")
        print()
        print("💡 Tips:")
        print("   - The model is now cached and won't be re-downloaded")
        print("   - Integrity checks happen automatically")
        print("   - Corrupted models are detected and can be repaired")
        print("   - Cache persists between runs")
        
    except ModelDownloadError as e:
        print(f"❌ Download failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True


async def demo_cache_management():
    """Demonstrate cache management features."""
    print("\n" + "=" * 50)
    print("🗂️  Cache Management Demo")
    print("=" * 50)
    
    data_dir = Path("./demo_data")
    manager = ModelManager(data_dir=data_dir)
    
    # Show cache info
    cache_info = manager.get_cache_info()
    print(f"📊 Cache Statistics:")
    print(f"   - Cache version: {cache_info['cache_version']}")
    print(f"   - Last updated: {cache_info['last_updated']}")
    print(f"   - Total models: {cache_info['total_models']}")
    print(f"   - Total size: {cache_info['total_size_gb']:.2f} GB")
    print()
    
    if cache_info['models']:
        print("📋 Cached Models:")
        for name, info in cache_info['models'].items():
            print(f"   - {name}:")
            print(f"     * Size: {info['size_gb']:.2f} GB")
            print(f"     * Downloaded: {info['download_date'] or 'Unknown'}")
            print(f"     * Last verified: {info['last_verified'] or 'Never'}")
            print(f"     * Has integrity hash: {info['has_integrity_hash']}")
        print()
    
    print("✨ Cache management features available:")
    print("   - manager.clear_cache() - Clear cache metadata")
    print("   - manager.cleanup_models(keep_latest=1) - Remove old models")
    print("   - manager.verify_model(name) - Verify model integrity")
    print("   - manager.repair_model(name) - Repair corrupted model")


if __name__ == "__main__":
    print("Starting model download and caching demo...")
    print("This demo uses a small model (~117MB) for demonstration.")
    print()
    
    try:
        # Run the demo
        success = asyncio.run(demo_model_download())
        
        if success:
            asyncio.run(demo_cache_management())
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)