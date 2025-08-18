#!/usr/bin/env python3
"""
Simple OSS-20B Model Downloader for MCPlease

This script downloads the OSS-20B model to your local machine.
It's designed to be simple and user-friendly.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if required packages are installed."""
    try:
        import huggingface_hub
        print("✅ huggingface_hub is installed")
        return True
    except ImportError:
        print("❌ huggingface_hub not found")
        print("Installing required packages...")
        
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
            print("✅ huggingface_hub installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install huggingface_hub")
            return False

def download_model():
    """Download the OSS-20B model."""
    print("🚀 Starting OSS-20B model download...")
    print("   This will download ~13GB of data")
    print("   Estimated time: 10-30 minutes (depending on internet speed)")
    print()
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Download the model
    try:
        from huggingface_hub import snapshot_download
        
        print("📥 Downloading from Hugging Face...")
        model_path = snapshot_download(
            repo_id="openai/gpt-oss-20b",
            local_dir=models_dir / "gpt-oss-20b",
            local_dir_use_symlinks=False,
            resume_download=True,
            max_workers=4
        )
        
        print(f"✅ Model downloaded successfully to: {model_path}")
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   • Check your internet connection")
        print("   • Ensure you have enough disk space (at least 15GB free)")
        print("   • Try running again (download will resume)")
        return False

def main():
    """Main download function."""
    print("=" * 60)
    print("🤖 MCPlease OSS-20B Model Downloader")
    print("=" * 60)
    print()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Cannot proceed without required packages")
        return
    
    print("📋 Requirements check passed!")
    print()
    
    # Check disk space
    models_dir = Path("models")
    if models_dir.exists():
        # Estimate space needed
        space_needed_gb = 15  # Conservative estimate
        
        # Get available space (simplified)
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free // (1024**3)
            
            if free_gb < space_needed_gb:
                print(f"⚠️  Warning: Only {free_gb}GB free space available")
                print(f"   Recommended: At least {space_needed_gb}GB free space")
                response = input("   Continue anyway? (y/N): ").lower().strip()
                if response != 'y':
                    print("Download cancelled.")
                    return
            else:
                print(f"✅ Sufficient disk space: {free_gb}GB available")
        except:
            print("⚠️  Could not check disk space - continuing anyway")
    
    print()
    
    # Start download
    if download_model():
        print("\n🎉 Model download completed successfully!")
        print("\n📁 Files downloaded to: models/gpt-oss-20b/")
        print("\n🚀 Next steps:")
        print("   1. Run: ./start.sh")
        print("   2. The system will automatically use the downloaded model")
        print("   3. Start coding with AI assistance!")
    else:
        print("\n❌ Model download failed")
        print("   Please check the error messages above and try again")

if __name__ == "__main__":
    main()
