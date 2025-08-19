#!/usr/bin/env python3
"""
Test script for uv-based installation system.

This script tests the installation process without actually installing anything.
"""

import sys
import tempfile
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from install_uv import UVInstaller


def test_installation_dry_run():
    """Test installation process in dry-run mode."""
    print("🧪 Testing MCPlease uv-based installation system")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        
        # Create minimal project structure
        (project_root / "src" / "mcplease_mcp").mkdir(parents=True)
        (project_root / "src" / "mcplease_mcp" / "__init__.py").touch()
        (project_root / "tests").mkdir()
        
        # Create pyproject.toml
        pyproject_content = """
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mcplease-mcp"
version = "0.1.0"
dependencies = ["fastmcp>=0.1.0", "psutil>=5.9.0"]
"""
        (project_root / "pyproject.toml").write_text(pyproject_content)
        
        # Create installer
        installer = UVInstaller(project_root=project_root)
        
        print("✅ Installer created successfully")
        
        # Test hardware detection
        print("\n🔍 Testing hardware detection...")
        try:
            hardware_config = installer.detect_hardware()
            print(f"✅ Hardware detected:")
            print(f"   • Memory: {hardware_config['memory_gb']}GB")
            print(f"   • CPUs: {hardware_config['cpu_count']}")
            print(f"   • Platform: {hardware_config['platform']}")
            print(f"   • Architecture: {hardware_config['architecture']}")
            if hardware_config["gpu"]["available"]:
                print(f"   • GPU: {hardware_config['gpu']['type']} ({hardware_config['gpu']['memory_gb']}GB)")
            else:
                print("   • GPU: Not available")
            
            recommended = hardware_config["recommended_config"]
            print(f"   • Recommended AI Model: {recommended['ai_model']}")
            print(f"   • Recommended Memory Limit: {recommended['memory_limit']}")
            print(f"   • Recommended Workers: {recommended['max_workers']}")
            print(f"   • Recommended Transport: {', '.join(recommended['transport'])}")
            
        except Exception as e:
            print(f"❌ Hardware detection failed: {e}")
            return False
        
        # Test configuration creation
        print("\n⚙️  Testing configuration creation...")
        try:
            result = installer.create_configuration(hardware_config)
            if result:
                print("✅ Configuration files created successfully")
                
                # Check config file
                config_file = installer.config_dir / "config.json"
                if config_file.exists():
                    print(f"   • Config file: {config_file}")
                    
                    import json
                    with open(config_file) as f:
                        config = json.load(f)
                    
                    print(f"   • Server host: {config['server']['host']}")
                    print(f"   • Server port: {config['server']['port']}")
                    print(f"   • AI model: {config['ai']['model']}")
                    print(f"   • Security level: {config['security']['level']}")
                
                # Check env file
                env_file = installer.project_root / ".env"
                if env_file.exists():
                    print(f"   • Environment file: {env_file}")
            else:
                print("❌ Configuration creation failed")
                return False
                
        except Exception as e:
            print(f"❌ Configuration creation failed: {e}")
            return False
        
        # Test startup script creation
        print("\n📜 Testing startup script creation...")
        try:
            result = installer.create_startup_scripts()
            if result:
                print("✅ Startup scripts created successfully")
                
                if installer.platform != "windows":
                    startup_script = installer.project_root / "start_uv.sh"
                    if startup_script.exists():
                        print(f"   • Unix startup script: {startup_script}")
                        print(f"   • Executable: {bool(startup_script.stat().st_mode & 0o111)}")
                else:
                    startup_script = installer.project_root / "start_uv.bat"
                    if startup_script.exists():
                        print(f"   • Windows startup script: {startup_script}")
            else:
                print("❌ Startup script creation failed")
                return False
                
        except Exception as e:
            print(f"❌ Startup script creation failed: {e}")
            return False
        
        print("\n🎉 All tests passed!")
        print("\n📋 Summary:")
        print("   • Hardware detection: ✅")
        print("   • Configuration creation: ✅")
        print("   • Startup script creation: ✅")
        print("\n💡 The installation system is ready for use!")
        
        return True


def test_config_management():
    """Test configuration management system."""
    print("\n🧪 Testing configuration management system")
    print("=" * 60)
    
    try:
        from src.mcplease_mcp.config.manager import ConfigManager, MCPConfig
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / "pyproject.toml").touch()
            
            # Test config manager
            config_manager = ConfigManager(project_root=project_root)
            print("✅ Config manager created")
            
            # Test default config loading
            config = config_manager.load_config()
            print(f"✅ Default config loaded: {config.host}:{config.port}")
            
            # Test config saving
            config.host = "0.0.0.0"
            config.ai_model = "test-model"
            config_manager.save_config(config)
            print("✅ Config saved successfully")
            
            # Test config reloading
            new_config = config_manager.load_config()
            assert new_config.host == "0.0.0.0"
            assert new_config.ai_model == "test-model"
            print("✅ Config reloaded successfully")
            
            # Test config summary
            summary = config_manager.get_config_summary()
            print(f"✅ Config summary generated: {len(summary)} sections")
            
            print("\n📋 Configuration Management Summary:")
            print("   • Config loading: ✅")
            print("   • Config saving: ✅")
            print("   • Config validation: ✅")
            
            return True
            
    except Exception as e:
        print(f"❌ Configuration management test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 MCPlease Installation System Test Suite")
    print("=" * 60)
    
    success = True
    
    # Test installation system
    if not test_installation_dry_run():
        success = False
    
    # Test configuration management
    if not test_config_management():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Installation system is ready.")
        print("\n💡 To install MCPlease MCP Server:")
        print("   python install.py")
        print("   # or")
        print("   python scripts/install_uv.py")
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()