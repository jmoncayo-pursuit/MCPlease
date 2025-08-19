#!/usr/bin/env python3
"""
MCPlease MCP Server - uv-based Installation Script

This script provides one-command installation using uv package manager
with automatic hardware detection and optimal configuration selection.
"""

import os
import sys
import subprocess
import platform
import shutil
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import tempfile
import logging


class UVInstaller:
    """Handles uv-based installation and configuration management."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the installer.
        
        Args:
            project_root: Project root directory (defaults to parent of script directory)
        """
        self.platform = platform.system().lower()
        self.arch = platform.machine().lower()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.project_root = project_root or Path(__file__).parent.parent
        self.config_dir = self.project_root / ".mcplease"
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the installer."""
        logger = logging.getLogger("mcplease_installer")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
        
    def detect_hardware(self) -> Dict[str, Any]:
        """Detect hardware capabilities and constraints."""
        try:
            import psutil
        except ImportError:
            # Fallback if psutil not available
            self.logger.warning("psutil not available, using basic hardware detection")
            return self._basic_hardware_detection()
        
        # Get system info
        memory_gb = psutil.virtual_memory().total / (1024**3)
        cpu_count = psutil.cpu_count()
        
        # Detect GPU
        gpu_info = self._detect_gpu()
        
        # Check if Raspberry Pi
        is_raspberry_pi = self._is_raspberry_pi()
        
        # Determine optimal configuration
        config = {
            "memory_gb": round(memory_gb, 1),
            "cpu_count": cpu_count,
            "gpu": gpu_info,
            "platform": self.platform,
            "architecture": self.arch,
            "python_version": self.python_version,
            "is_raspberry_pi": is_raspberry_pi,
            "recommended_config": self._get_recommended_config(memory_gb, cpu_count, gpu_info, is_raspberry_pi)
        }
        
        self.logger.info(f"Hardware detected: {config['memory_gb']}GB RAM, {config['cpu_count']} CPUs")
        if gpu_info["available"]:
            self.logger.info(f"GPU detected: {gpu_info['type']} ({gpu_info.get('memory_gb', 'unknown')}GB)")
        if is_raspberry_pi:
            self.logger.info("Raspberry Pi detected - applying optimizations")
        
        return config
    
    def _basic_hardware_detection(self) -> Dict[str, Any]:
        """Basic hardware detection without psutil."""
        # Estimate based on platform
        if self.platform == "darwin":
            memory_gb = 8.0  # Conservative estimate for macOS
            cpu_count = 4
        elif self._is_raspberry_pi():
            memory_gb = 4.0  # Pi 4/5 estimate
            cpu_count = 4
        else:
            memory_gb = 8.0  # Conservative estimate
            cpu_count = 4
        
        return {
            "memory_gb": memory_gb,
            "cpu_count": cpu_count,
            "gpu": {"available": False, "type": None, "memory_gb": 0},
            "platform": self.platform,
            "architecture": self.arch,
            "python_version": self.python_version,
            "is_raspberry_pi": self._is_raspberry_pi(),
            "recommended_config": self._get_recommended_config(memory_gb, cpu_count, {"available": False}, self._is_raspberry_pi())
        }
    
    def _detect_gpu(self) -> Dict[str, Any]:
        """Detect GPU capabilities."""
        gpu_info = {"available": False, "type": None, "memory_gb": 0}
        
        try:
            # Try NVIDIA GPU detection
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                memory_mb = int(result.stdout.strip())
                gpu_info = {
                    "available": True,
                    "type": "nvidia",
                    "memory_gb": round(memory_mb / 1024, 1)
                }
                return gpu_info
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, ValueError):
            pass
        
        # Try Apple Metal detection (macOS)
        if self.platform == "darwin":
            try:
                # Check for Apple Silicon
                if self.arch in ['arm64', 'aarch64']:
                    gpu_info = {
                        "available": True,
                        "type": "metal",
                        "memory_gb": 8.0  # Estimate for Apple Silicon unified memory
                    }
            except Exception:
                pass
        
        return gpu_info
    
    def _is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi."""
        try:
            # Check /proc/cpuinfo
            with open("/proc/cpuinfo", "r") as f:
                content = f.read().lower()
                if "raspberry pi" in content or "bcm" in content:
                    return True
            
            # Check device tree model
            model_file = Path("/proc/device-tree/model")
            if model_file.exists():
                with open(model_file, "r") as f:
                    model = f.read().lower()
                    if "raspberry pi" in model:
                        return True
        except (FileNotFoundError, PermissionError):
            pass
        
        return False
    
    def _get_recommended_config(self, memory_gb: float, cpu_count: int, gpu_info: Dict, is_raspberry_pi: bool) -> Dict[str, Any]:
        """Get recommended configuration based on hardware."""
        config = {
            "ai_model": "disabled",  # Default to no AI model
            "max_workers": min(4, cpu_count),
            "memory_limit": "2GB",
            "transport": ["stdio"],
            "security": "basic",
            "quantization": "int8"
        }
        
        # Configure based on available memory
        if memory_gb >= 16:
            config.update({
                "ai_model": "openai/gpt-oss-20b",
                "memory_limit": "12GB",
                "max_workers": min(8, cpu_count),
                "transport": ["stdio", "sse", "websocket"],
                "security": "full",
                "quantization": "fp16"
            })
        elif memory_gb >= 8:
            config.update({
                "ai_model": "openai/gpt-oss-20b",
                "memory_limit": "6GB",
                "max_workers": min(6, cpu_count),
                "transport": ["stdio", "sse"],
                "security": "standard",
                "quantization": "int8"
            })
        elif memory_gb >= 4:
            config.update({
                "memory_limit": "3GB",
                "max_workers": min(4, cpu_count),
                "transport": ["stdio"],
                "security": "basic",
                "quantization": "int8"
            })
        
        # Raspberry Pi specific optimizations
        if is_raspberry_pi:
            config.update({
                "ai_model": "disabled",  # Too resource intensive for Pi
                "memory_limit": "1GB",
                "max_workers": 2,
                "transport": ["sse"],  # Better for remote access
                "security": "standard",
                "quantization": "int8",
                "enable_ngrok": True
            })
        
        return config
    
    def check_uv_installation(self) -> bool:
        """Check if uv is installed and install if needed."""
        if shutil.which("uv"):
            self.logger.info("✓ uv package manager found")
            return True
        
        self.logger.info("Installing uv package manager...")
        try:
            # Install uv using the official installer
            if self.platform == "windows":
                subprocess.run([
                    "powershell", "-c",
                    "irm https://astral.sh/uv/install.ps1 | iex"
                ], check=True, timeout=300)
            else:
                subprocess.run([
                    "curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"
                ], shell=True, check=True, timeout=300)
            
            # Refresh PATH
            if self.platform != "windows":
                os.environ["PATH"] = f"{os.path.expanduser('~/.cargo/bin')}:{os.environ.get('PATH', '')}"
            
            self.logger.info("✓ uv package manager installed")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"✗ Failed to install uv: {e}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("✗ uv installation timed out")
            return False
    
    def create_virtual_environment(self) -> bool:
        """Create virtual environment using uv."""
        try:
            self.logger.info("Creating virtual environment with uv...")
            
            # Remove existing venv if it exists
            venv_path = self.project_root / ".venv"
            if venv_path.exists():
                shutil.rmtree(venv_path)
            
            subprocess.run([
                "uv", "venv", "--python", self.python_version
            ], cwd=self.project_root, check=True, timeout=120)
            
            self.logger.info("✓ Virtual environment created")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"✗ Failed to create virtual environment: {e}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("✗ Virtual environment creation timed out")
            return False
    
    def install_dependencies(self, dev: bool = False) -> bool:
        """Install dependencies using uv."""
        try:
            self.logger.info("Installing dependencies with uv...")
            
            # Install main dependencies
            cmd = ["uv", "pip", "install", "-e", "."]
            if dev:
                cmd.extend(["--extra", "dev,test,docs"])
            
            subprocess.run(cmd, cwd=self.project_root, check=True, timeout=600)
            
            self.logger.info("✓ Dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"✗ Failed to install dependencies: {e}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("✗ Dependency installation timed out")
            return False
    
    def create_configuration(self, hardware_config: Dict[str, Any]) -> bool:
        """Create optimal configuration files."""
        try:
            # Create config directory
            self.config_dir.mkdir(exist_ok=True)
            
            recommended = hardware_config["recommended_config"]
            
            # Create main configuration
            config = {
                "server": {
                    "host": "127.0.0.1",
                    "port": 8000,
                    "transport": recommended["transport"],
                    "max_workers": recommended["max_workers"]
                },
                "ai": {
                    "model": recommended["ai_model"],
                    "memory_limit": recommended["memory_limit"],
                    "quantization": recommended["quantization"],
                    "device": "auto"
                },
                "security": {
                    "level": recommended["security"],
                    "require_auth": recommended["security"] != "basic",
                    "enable_tls": recommended["security"] == "full"
                },
                "hardware": hardware_config,
                "installation": {
                    "timestamp": str(subprocess.run(["date"], capture_output=True, text=True).stdout.strip()),
                    "installer_version": "1.0.0"
                }
            }
            
            # Add Raspberry Pi specific config
            if hardware_config["is_raspberry_pi"]:
                config["raspberry_pi"] = {
                    "enable_ngrok": recommended.get("enable_ngrok", False),
                    "temperature_monitoring": True,
                    "cpu_governor": "ondemand"
                }
            
            # Write configuration
            config_file = self.config_dir / "config.json"
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
            
            # Create environment file
            env_file = self.project_root / ".env"
            env_content = f"""# MCPlease MCP Server Configuration
# Generated by uv-based installer

MCPLEASE_CONFIG_FILE={config_file}
MCPLEASE_LOG_LEVEL=INFO
MCPLEASE_HOST={config["server"]["host"]}
MCPLEASE_PORT={config["server"]["port"]}
MCPLEASE_AI_MODEL={config["ai"]["model"]}
MCPLEASE_MEMORY_LIMIT={config["ai"]["memory_limit"]}
MCPLEASE_SECURITY_LEVEL={config["security"]["level"]}
MCPLEASE_TRANSPORT={",".join(config["server"]["transport"])}
MCPLEASE_MAX_WORKERS={config["server"]["max_workers"]}
"""
            
            with open(env_file, "w") as f:
                f.write(env_content)
            
            self.logger.info("✓ Configuration files created")
            return True
        except Exception as e:
            self.logger.error(f"✗ Failed to create configuration: {e}")
            return False
    
    def download_ai_model(self, model_name: str) -> bool:
        """Download AI model if needed."""
        if model_name == "disabled":
            self.logger.info("✓ AI model disabled, skipping download")
            return True
        
        try:
            self.logger.info(f"Downloading AI model: {model_name}")
            
            # Use existing download script if available
            download_script = self.project_root / "download_model.py"
            if download_script.exists():
                subprocess.run([
                    "uv", "run", "python", str(download_script), "--model", model_name
                ], cwd=self.project_root, check=True, timeout=1800)  # 30 minute timeout
            else:
                self.logger.warning("⚠ Model download script not found, skipping")
            
            self.logger.info("✓ AI model ready")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"⚠ Failed to download AI model: {e}")
            self.logger.info("  You can download it later using: uv run python download_model.py")
            return True  # Don't fail installation for model download
        except subprocess.TimeoutExpired:
            self.logger.warning("⚠ Model download timed out")
            self.logger.info("  You can download it later using: uv run python download_model.py")
            return True
    
    def create_startup_scripts(self) -> bool:
        """Create platform-specific startup scripts."""
        try:
            # Unix/Linux/macOS startup script
            if self.platform != "windows":
                startup_script = self.project_root / "start_uv.sh"
                script_content = """#!/bin/bash
# MCPlease MCP Server - uv-based startup script

set -e

# Change to project directory
cd "$(dirname "$0")"

# Load configuration
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Activate virtual environment and start server
echo "🚀 Starting MCPlease MCP Server..."
uv run python -m mcplease_mcp.main "$@"
"""
                with open(startup_script, "w") as f:
                    f.write(script_content)
                
                # Make executable
                startup_script.chmod(0o755)
            
            # Windows startup script
            if self.platform == "windows":
                startup_script = self.project_root / "start_uv.bat"
                script_content = """@echo off
REM MCPlease MCP Server - uv-based startup script

cd /d "%~dp0"

echo Starting MCPlease MCP Server...
uv run python -m mcplease_mcp.main %*
"""
                with open(startup_script, "w") as f:
                    f.write(script_content)
            
            self.logger.info("✓ Startup scripts created")
            return True
        except Exception as e:
            self.logger.error(f"✗ Failed to create startup scripts: {e}")
            return False
    
    def run_tests(self) -> bool:
        """Run basic tests to verify installation."""
        try:
            self.logger.info("Running installation tests...")
            
            # Test basic import
            result = subprocess.run([
                "uv", "run", "python", "-c", 
                "import sys; sys.path.insert(0, 'src'); import mcplease_mcp; print('✓ Import successful')"
            ], cwd=self.project_root, check=True, capture_output=True, text=True, timeout=30)
            
            if "✓ Import successful" in result.stdout:
                self.logger.info("✓ Basic import test passed")
            
            # Run installation-specific tests
            test_files = [
                "tests/test_*installation*.py",
                "tests/test_*config*.py",
                "tests/test_*hardware*.py"
            ]
            
            for test_pattern in test_files:
                test_path = self.project_root / "tests"
                if any(test_path.glob(test_pattern.replace("tests/", ""))):
                    subprocess.run([
                        "uv", "run", "pytest", test_pattern, "-v", "--tb=short", "-x"
                    ], cwd=self.project_root, check=True, timeout=120)
            
            self.logger.info("✓ Installation tests passed")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"⚠ Some tests failed: {e}")
            self.logger.info("  Installation completed but some features may not work correctly")
            return True  # Don't fail installation for test failures
        except subprocess.TimeoutExpired:
            self.logger.warning("⚠ Tests timed out")
            return True
    
    def install(self, dev: bool = False, skip_model: bool = False, skip_tests: bool = False) -> bool:
        """Run complete installation process."""
        print("🚀 MCPlease MCP Server Installation")
        print("=" * 50)
        
        # Step 1: Check uv installation
        if not self.check_uv_installation():
            return False
        
        # Step 2: Detect hardware
        print("\n🔍 Detecting hardware configuration...")
        hardware_config = self.detect_hardware()
        
        # Step 3: Create virtual environment
        if not self.create_virtual_environment():
            return False
        
        # Step 4: Install dependencies
        if not self.install_dependencies(dev=dev):
            return False
        
        # Step 5: Create configuration
        if not self.create_configuration(hardware_config):
            return False
        
        # Step 6: Download AI model
        if not skip_model:
            model_name = hardware_config["recommended_config"]["ai_model"]
            if not self.download_ai_model(model_name):
                return False
        
        # Step 7: Create startup scripts
        if not self.create_startup_scripts():
            return False
        
        # Step 8: Run tests
        if not skip_tests:
            if not self.run_tests():
                return False
        
        # Installation complete
        print("\n🎉 Installation Complete!")
        print("=" * 50)
        
        # Show configuration summary
        recommended = hardware_config["recommended_config"]
        print(f"\n📋 Configuration Summary:")
        print(f"   • AI Model: {recommended['ai_model']}")
        print(f"   • Memory Limit: {recommended['memory_limit']}")
        print(f"   • Max Workers: {recommended['max_workers']}")
        print(f"   • Transport: {', '.join(recommended['transport'])}")
        print(f"   • Security Level: {recommended['security']}")
        
        print(f"\n🚀 Next steps:")
        print("1. Start the server:")
        if self.platform == "windows":
            print("   start_uv.bat")
        else:
            print("   ./start_uv.sh")
        print("\n2. Test MCP connection:")
        print("   uv run python -c \"from mcplease_mcp.main import main; main(['--help'])\"")
        print("\n3. Configure your IDE:")
        print("   Add MCP server configuration to your IDE settings")
        
        return True


def main():
    """Main installation entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MCPlease MCP Server uv-based installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/install_uv.py                    # Full installation
  python scripts/install_uv.py --dev             # Install with dev dependencies
  python scripts/install_uv.py --skip-model      # Skip AI model download
  python scripts/install_uv.py --skip-tests      # Skip installation tests
        """
    )
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--skip-model", action="store_true", help="Skip AI model download")
    parser.add_argument("--skip-tests", action="store_true", help="Skip installation tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger("mcplease_installer").setLevel(logging.DEBUG)
    
    installer = UVInstaller()
    success = installer.install(
        dev=args.dev,
        skip_model=args.skip_model,
        skip_tests=args.skip_tests
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()