"""Tests for uv-based installation and configuration management."""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest

# Import the installer
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from install_uv import UVInstaller


class TestUVInstaller:
    """Test cases for UVInstaller."""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project root for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create basic project structure
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

[project.optional-dependencies]
dev = ["pytest>=7.4.0"]
"""
            (project_root / "pyproject.toml").write_text(pyproject_content)
            
            yield project_root
    
    @pytest.fixture
    def installer(self, temp_project_root):
        """Create installer instance with temporary project root."""
        return UVInstaller(project_root=temp_project_root)
    
    def test_installer_initialization(self, installer, temp_project_root):
        """Test installer initializes correctly."""
        assert installer.project_root == temp_project_root
        assert installer.config_dir == temp_project_root / ".mcplease"
        assert installer.platform == platform.system().lower()
        assert installer.arch == platform.machine().lower()
        assert installer.python_version == f"{sys.version_info.major}.{sys.version_info.minor}"
    
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_count')
    def test_hardware_detection_with_psutil(self, mock_cpu_count, mock_memory, installer):
        """Test hardware detection with psutil available."""
        # Mock psutil responses
        mock_memory.return_value.total = 16 * 1024**3  # 16GB
        mock_cpu_count.return_value = 8
        
        with patch.object(installer, '_detect_gpu', return_value={"available": False, "type": None, "memory_gb": 0}):
            with patch.object(installer, '_is_raspberry_pi', return_value=False):
                config = installer.detect_hardware()
        
        assert config["memory_gb"] == 16.0
        assert config["cpu_count"] == 8
        assert config["platform"] == installer.platform
        assert config["architecture"] == installer.arch
        assert "recommended_config" in config
    
    def test_hardware_detection_without_psutil(self, installer):
        """Test hardware detection fallback without psutil."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'psutil'")):
            with patch.object(installer, '_is_raspberry_pi', return_value=False):
                config = installer.detect_hardware()
        
        assert "memory_gb" in config
        assert "cpu_count" in config
        assert config["memory_gb"] > 0
        assert config["cpu_count"] > 0
    
    def test_raspberry_pi_detection_true(self, installer):
        """Test Raspberry Pi detection when running on Pi."""
        mock_cpuinfo = "processor\t: 0\nmodel name\t: ARMv7 Processor rev 4 (v7l)\nHardware\t: BCM2835\nRevision\t: a020d3\nSerial\t\t: 00000000abcdefgh\n"
        
        with patch('builtins.open', mock_open_multiple_files({"/proc/cpuinfo": mock_cpuinfo})):
            assert installer._is_raspberry_pi() is True
    
    def test_raspberry_pi_detection_false(self, installer):
        """Test Raspberry Pi detection when not on Pi."""
        mock_cpuinfo = "processor\t: 0\nvendor_id\t: GenuineIntel\nmodel name\t: Intel(R) Core(TM) i7-8700K CPU @ 3.70GHz\n"
        
        with patch('builtins.open', mock_open_multiple_files({"/proc/cpuinfo": mock_cpuinfo})):
            assert installer._is_raspberry_pi() is False
    
    def test_raspberry_pi_detection_file_not_found(self, installer):
        """Test Raspberry Pi detection when /proc/cpuinfo doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            assert installer._is_raspberry_pi() is False
    
    @patch('subprocess.run')
    def test_gpu_detection_nvidia(self, mock_run, installer):
        """Test NVIDIA GPU detection."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "8192"  # 8GB GPU
        
        gpu_info = installer._detect_gpu()
        
        assert gpu_info["available"] is True
        assert gpu_info["type"] == "nvidia"
        assert gpu_info["memory_gb"] == 8.0
    
    @patch('subprocess.run')
    def test_gpu_detection_none(self, mock_run, installer):
        """Test GPU detection when no GPU available."""
        mock_run.side_effect = FileNotFoundError("nvidia-smi not found")
        
        # Mock platform to not be darwin to avoid Apple Metal detection
        with patch.object(installer, 'platform', 'linux'):
            gpu_info = installer._detect_gpu()
        
        assert gpu_info["available"] is False
        assert gpu_info["type"] is None
        assert gpu_info["memory_gb"] == 0
    
    def test_gpu_detection_apple_metal(self, installer):
        """Test Apple Metal GPU detection on macOS ARM."""
        if installer.platform == "darwin" and installer.arch in ['arm64', 'aarch64']:
            gpu_info = installer._detect_gpu()
            assert gpu_info["available"] is True
            assert gpu_info["type"] == "metal"
            assert gpu_info["memory_gb"] > 0
    
    def test_recommended_config_high_memory(self, installer):
        """Test recommended configuration for high-memory system."""
        config = installer._get_recommended_config(
            memory_gb=32.0, 
            cpu_count=16, 
            gpu_info={"available": True, "type": "nvidia"}, 
            is_raspberry_pi=False
        )
        
        assert config["ai_model"] == "openai/gpt-oss-20b"
        assert config["memory_limit"] == "12GB"
        assert config["max_workers"] <= 16
        assert "websocket" in config["transport"]
        assert config["security"] == "full"
    
    def test_recommended_config_raspberry_pi(self, installer):
        """Test recommended configuration for Raspberry Pi."""
        config = installer._get_recommended_config(
            memory_gb=4.0, 
            cpu_count=4, 
            gpu_info={"available": False}, 
            is_raspberry_pi=True
        )
        
        assert config["ai_model"] == "disabled"
        assert config["memory_limit"] == "1GB"
        assert config["max_workers"] == 2
        assert config["transport"] == ["sse"]
        assert config["enable_ngrok"] is True
    
    def test_recommended_config_low_memory(self, installer):
        """Test recommended configuration for low-memory system."""
        config = installer._get_recommended_config(
            memory_gb=2.0, 
            cpu_count=2, 
            gpu_info={"available": False}, 
            is_raspberry_pi=False
        )
        
        assert config["ai_model"] == "disabled"
        assert config["memory_limit"] == "2GB"
        assert config["max_workers"] <= 4
        assert config["transport"] == ["stdio"]
    
    @patch('shutil.which')
    def test_check_uv_installation_found(self, mock_which, installer):
        """Test uv installation check when uv is found."""
        mock_which.return_value = "/usr/local/bin/uv"
        
        assert installer.check_uv_installation() is True
        mock_which.assert_called_once_with("uv")
    
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_check_uv_installation_install_success(self, mock_run, mock_which, installer):
        """Test uv installation when not found but installation succeeds."""
        mock_which.return_value = None
        mock_run.return_value.returncode = 0
        
        result = installer.check_uv_installation()
        
        assert result is True
        mock_run.assert_called_once()
    
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_check_uv_installation_install_failure(self, mock_run, mock_which, installer):
        """Test uv installation when installation fails."""
        mock_which.return_value = None
        mock_run.side_effect = subprocess.CalledProcessError(1, "curl")
        
        result = installer.check_uv_installation()
        
        assert result is False
    
    @patch('subprocess.run')
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_create_virtual_environment_success(self, mock_exists, mock_rmtree, mock_run, installer):
        """Test virtual environment creation success."""
        mock_run.return_value.returncode = 0
        mock_exists.return_value = True
        
        result = installer.create_virtual_environment()
        
        assert result is True
        mock_rmtree.assert_called_once()
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_create_virtual_environment_failure(self, mock_run, installer):
        """Test virtual environment creation failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "uv venv")
        
        result = installer.create_virtual_environment()
        
        assert result is False
    
    @patch('subprocess.run')
    def test_install_dependencies_success(self, mock_run, installer):
        """Test dependency installation success."""
        mock_run.return_value.returncode = 0
        
        result = installer.install_dependencies(dev=False)
        
        assert result is True
        mock_run.assert_called_once()
        
        # Check command arguments
        args = mock_run.call_args[0][0]
        assert "uv" in args
        assert "pip" in args
        assert "install" in args
        assert "-e" in args
        assert "." in args
    
    @patch('subprocess.run')
    def test_install_dependencies_with_dev(self, mock_run, installer):
        """Test dependency installation with dev dependencies."""
        mock_run.return_value.returncode = 0
        
        result = installer.install_dependencies(dev=True)
        
        assert result is True
        
        # Check that dev extras are included
        args = mock_run.call_args[0][0]
        assert "--extra" in args
        assert "dev,test,docs" in args
    
    @patch('subprocess.run')
    def test_install_dependencies_failure(self, mock_run, installer):
        """Test dependency installation failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "uv pip install")
        
        result = installer.install_dependencies()
        
        assert result is False
    
    def test_create_configuration_success(self, installer):
        """Test configuration file creation."""
        hardware_config = {
            "memory_gb": 16.0,
            "cpu_count": 8,
            "is_raspberry_pi": False,
            "recommended_config": {
                "ai_model": "openai/gpt-oss-20b",
                "memory_limit": "12GB",
                "max_workers": 8,
                "transport": ["stdio", "sse"],
                "security": "full",
                "quantization": "fp16"
            }
        }
        
        result = installer.create_configuration(hardware_config)
        
        assert result is True
        
        # Check config file was created
        config_file = installer.config_dir / "config.json"
        assert config_file.exists()
        
        # Check config content
        with open(config_file) as f:
            config = json.load(f)
        
        assert config["server"]["max_workers"] == 8
        assert config["ai"]["model"] == "openai/gpt-oss-20b"
        assert config["ai"]["memory_limit"] == "12GB"
        assert config["security"]["level"] == "full"
        
        # Check .env file was created
        env_file = installer.project_root / ".env"
        assert env_file.exists()
        
        env_content = env_file.read_text()
        assert "MCPLEASE_AI_MODEL=openai/gpt-oss-20b" in env_content
        assert "MCPLEASE_MEMORY_LIMIT=12GB" in env_content
    
    def test_create_configuration_raspberry_pi(self, installer):
        """Test configuration file creation for Raspberry Pi."""
        hardware_config = {
            "memory_gb": 4.0,
            "cpu_count": 4,
            "is_raspberry_pi": True,
            "recommended_config": {
                "ai_model": "disabled",
                "memory_limit": "1GB",
                "max_workers": 2,
                "transport": ["sse"],
                "security": "standard",
                "quantization": "int8",
                "enable_ngrok": True
            }
        }
        
        result = installer.create_configuration(hardware_config)
        
        assert result is True
        
        # Check Raspberry Pi specific config
        config_file = installer.config_dir / "config.json"
        with open(config_file) as f:
            config = json.load(f)
        
        assert "raspberry_pi" in config
        assert config["raspberry_pi"]["enable_ngrok"] is True
        assert config["raspberry_pi"]["temperature_monitoring"] is True
    
    def test_download_ai_model_disabled(self, installer):
        """Test AI model download when disabled."""
        result = installer.download_ai_model("disabled")
        
        assert result is True
    
    @patch('subprocess.run')
    def test_download_ai_model_success(self, mock_run, installer):
        """Test AI model download success."""
        mock_run.return_value.returncode = 0
        
        # Create mock download script
        download_script = installer.project_root / "download_model.py"
        download_script.touch()
        
        result = installer.download_ai_model("openai/gpt-oss-20b")
        
        assert result is True
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_download_ai_model_failure(self, mock_run, installer):
        """Test AI model download failure (should not fail installation)."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "download")
        
        # Create mock download script
        download_script = installer.project_root / "download_model.py"
        download_script.touch()
        
        result = installer.download_ai_model("openai/gpt-oss-20b")
        
        # Should return True even on failure (non-critical)
        assert result is True
    
    def test_create_startup_scripts_unix(self, installer):
        """Test startup script creation on Unix systems."""
        if installer.platform == "windows":
            pytest.skip("Test for Unix systems only")
        
        result = installer.create_startup_scripts()
        
        assert result is True
        
        # Check startup script was created
        startup_script = installer.project_root / "start_uv.sh"
        assert startup_script.exists()
        
        # Check script is executable
        assert startup_script.stat().st_mode & 0o111  # Check execute bits
        
        # Check script content
        content = startup_script.read_text()
        assert "uv run python -m mcplease_mcp.main" in content
        assert "#!/bin/bash" in content
    
    def test_create_startup_scripts_windows(self, installer):
        """Test startup script creation on Windows."""
        if installer.platform != "windows":
            # Mock Windows platform for this test
            installer.platform = "windows"
        
        result = installer.create_startup_scripts()
        
        assert result is True
        
        # Check startup script was created
        startup_script = installer.project_root / "start_uv.bat"
        assert startup_script.exists()
        
        # Check script content
        content = startup_script.read_text()
        assert "uv run python -m mcplease_mcp.main" in content
        assert "@echo off" in content
    
    @patch('subprocess.run')
    def test_run_tests_success(self, mock_run, installer):
        """Test installation tests success."""
        # Mock successful import test
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "✓ Import successful"
        
        result = installer.run_tests()
        
        assert result is True
        assert mock_run.call_count >= 1  # At least the import test
    
    @patch('subprocess.run')
    def test_run_tests_failure(self, mock_run, installer):
        """Test installation tests failure (should not fail installation)."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "pytest")
        
        result = installer.run_tests()
        
        # Should return True even on test failure (non-critical)
        assert result is True
    
    @patch.object(UVInstaller, 'check_uv_installation')
    @patch.object(UVInstaller, 'detect_hardware')
    @patch.object(UVInstaller, 'create_virtual_environment')
    @patch.object(UVInstaller, 'install_dependencies')
    @patch.object(UVInstaller, 'create_configuration')
    @patch.object(UVInstaller, 'download_ai_model')
    @patch.object(UVInstaller, 'create_startup_scripts')
    @patch.object(UVInstaller, 'run_tests')
    def test_full_installation_success(self, mock_run_tests, mock_create_scripts, 
                                     mock_download_model, mock_create_config,
                                     mock_install_deps, mock_create_venv,
                                     mock_detect_hardware, mock_check_uv, installer):
        """Test full installation process success."""
        # Mock all steps to succeed
        mock_check_uv.return_value = True
        mock_detect_hardware.return_value = {
            "memory_gb": 16.0,
            "cpu_count": 8,
            "recommended_config": {
                "ai_model": "openai/gpt-oss-20b",
                "memory_limit": "12GB",
                "max_workers": 8,
                "transport": ["stdio", "sse"],
                "security": "full",
                "quantization": "fp16"
            }
        }
        mock_create_venv.return_value = True
        mock_install_deps.return_value = True
        mock_create_config.return_value = True
        mock_download_model.return_value = True
        mock_create_scripts.return_value = True
        mock_run_tests.return_value = True
        
        result = installer.install()
        
        assert result is True
        
        # Verify all steps were called
        mock_check_uv.assert_called_once()
        mock_detect_hardware.assert_called_once()
        mock_create_venv.assert_called_once()
        mock_install_deps.assert_called_once_with(dev=False)
        mock_create_config.assert_called_once()
        mock_download_model.assert_called_once()
        mock_create_scripts.assert_called_once()
        mock_run_tests.assert_called_once()
    
    @patch.object(UVInstaller, 'check_uv_installation')
    def test_full_installation_uv_failure(self, mock_check_uv, installer):
        """Test full installation process with uv installation failure."""
        mock_check_uv.return_value = False
        
        result = installer.install()
        
        assert result is False
    
    @patch.object(UVInstaller, 'check_uv_installation')
    @patch.object(UVInstaller, 'detect_hardware')
    @patch.object(UVInstaller, 'create_virtual_environment')
    def test_full_installation_venv_failure(self, mock_create_venv, mock_detect_hardware, 
                                          mock_check_uv, installer):
        """Test full installation process with virtual environment creation failure."""
        mock_check_uv.return_value = True
        mock_detect_hardware.return_value = {"recommended_config": {"ai_model": "disabled"}}
        mock_create_venv.return_value = False
        
        result = installer.install()
        
        assert result is False


def mock_open_multiple_files(files_dict):
    """Helper to mock opening multiple files with different content."""
    def mock_open_func(filename, mode='r', **kwargs):
        if str(filename) in files_dict:
            return mock_open(read_data=files_dict[str(filename)]).return_value
        else:
            raise FileNotFoundError(f"No such file: {filename}")
    
    return mock_open_func


class TestUVInstallerIntegration:
    """Integration tests for UVInstaller."""
    
    @pytest.mark.integration
    def test_hardware_detection_real(self):
        """Test hardware detection with real system (integration test)."""
        installer = UVInstaller()
        config = installer.detect_hardware()
        
        # Basic sanity checks
        assert config["memory_gb"] > 0
        assert config["cpu_count"] > 0
        assert config["platform"] in ["linux", "darwin", "windows"]
        assert "recommended_config" in config
        assert isinstance(config["recommended_config"], dict)
    
    @pytest.mark.integration
    @pytest.mark.skipif(not shutil.which("uv"), reason="uv not available")
    def test_uv_available(self):
        """Test that uv is available for integration tests."""
        installer = UVInstaller()
        assert installer.check_uv_installation() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])