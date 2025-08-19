"""Tests for configuration management."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from src.mcplease_mcp.config.manager import ConfigManager, MCPConfig, HardwareInfo
from src.mcplease_mcp.config.installer import InstallerConfig, InstallerConfigManager


class TestConfigManager:
    """Test cases for ConfigManager."""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create temporary project root for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create pyproject.toml to mark as project root
            (project_root / "pyproject.toml").touch()
            
            yield project_root
    
    @pytest.fixture
    def config_manager(self, temp_project_root):
        """Create config manager with temporary project root."""
        return ConfigManager(project_root=temp_project_root)
    
    def test_config_manager_initialization(self, config_manager, temp_project_root):
        """Test config manager initializes correctly."""
        assert config_manager.project_root == temp_project_root
        assert config_manager.config_dir == temp_project_root / ".mcplease"
        assert config_manager.config_file == temp_project_root / ".mcplease" / "config.json"
        assert config_manager.env_file == temp_project_root / ".env"
    
    def test_load_config_defaults(self, config_manager):
        """Test loading default configuration."""
        config = config_manager.load_config()
        
        assert isinstance(config, MCPConfig)
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.transport == ["stdio"]
        assert config.ai_model == "disabled"
        assert config.security_level == "basic"
    
    def test_load_config_from_file(self, config_manager):
        """Test loading configuration from JSON file."""
        # Create config file
        config_manager.config_dir.mkdir(exist_ok=True)
        config_data = {
            "server": {
                "host": "0.0.0.0",
                "port": 9000,
                "transport": ["sse", "websocket"],
                "max_workers": 8
            },
            "ai": {
                "model": "openai/gpt-oss-20b",
                "memory_limit": "12GB",
                "quantization": "fp16"
            },
            "security": {
                "level": "full",
                "require_auth": True,
                "enable_tls": True
            }
        }
        
        with open(config_manager.config_file, "w") as f:
            json.dump(config_data, f)
        
        config = config_manager.load_config()
        
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.transport == ["sse", "websocket"]
        assert config.max_workers == 8
        assert config.ai_model == "openai/gpt-oss-20b"
        assert config.memory_limit == "12GB"
        assert config.quantization == "fp16"
        assert config.security_level == "full"
        assert config.require_auth is True
        assert config.enable_tls is True
    
    def test_load_config_from_env(self, config_manager):
        """Test loading configuration from environment variables."""
        env_vars = {
            "MCPLEASE_HOST": "192.168.1.100",
            "MCPLEASE_PORT": "8080",
            "MCPLEASE_TRANSPORT": "stdio,sse",
            "MCPLEASE_MAX_WORKERS": "6",
            "MCPLEASE_AI_MODEL": "test-model",
            "MCPLEASE_MEMORY_LIMIT": "8GB",
            "MCPLEASE_SECURITY_LEVEL": "standard",
            "MCPLEASE_REQUIRE_AUTH": "true",
            "MCPLEASE_ENABLE_TLS": "false",
            "MCPLEASE_LOG_LEVEL": "DEBUG"
        }
        
        with patch.dict(os.environ, env_vars):
            config = config_manager.load_config()
        
        assert config.host == "192.168.1.100"
        assert config.port == 8080
        assert config.transport == ["stdio", "sse"]
        assert config.max_workers == 6
        assert config.ai_model == "test-model"
        assert config.memory_limit == "8GB"
        assert config.security_level == "standard"
        assert config.require_auth is True
        assert config.enable_tls is False
        assert config.log_level == "DEBUG"
    
    def test_env_overrides_file(self, config_manager):
        """Test that environment variables override file configuration."""
        # Create config file
        config_manager.config_dir.mkdir(exist_ok=True)
        config_data = {
            "server": {"host": "127.0.0.1", "port": 8000},
            "ai": {"model": "file-model"}
        }
        
        with open(config_manager.config_file, "w") as f:
            json.dump(config_data, f)
        
        # Set environment variables
        env_vars = {
            "MCPLEASE_HOST": "0.0.0.0",
            "MCPLEASE_AI_MODEL": "env-model"
        }
        
        with patch.dict(os.environ, env_vars):
            config = config_manager.load_config()
        
        assert config.host == "0.0.0.0"  # From env
        assert config.port == 8000  # From file
        assert config.ai_model == "env-model"  # From env
    
    def test_save_config(self, config_manager):
        """Test saving configuration to file."""
        config = MCPConfig(
            host="0.0.0.0",
            port=9000,
            transport=["sse", "websocket"],
            max_workers=8,
            ai_model="openai/gpt-oss-20b",
            memory_limit="12GB",
            security_level="full",
            require_auth=True,
            enable_tls=True
        )
        
        config_manager.save_config(config)
        
        # Check file was created
        assert config_manager.config_file.exists()
        
        # Check file content
        with open(config_manager.config_file) as f:
            saved_data = json.load(f)
        
        assert saved_data["server"]["host"] == "0.0.0.0"
        assert saved_data["server"]["port"] == 9000
        assert saved_data["server"]["transport"] == ["sse", "websocket"]
        assert saved_data["ai"]["model"] == "openai/gpt-oss-20b"
        assert saved_data["security"]["level"] == "full"
    
    def test_load_hardware_info(self, config_manager):
        """Test loading hardware information from config file."""
        # Create config file with hardware info
        config_manager.config_dir.mkdir(exist_ok=True)
        config_data = {
            "hardware": {
                "memory_gb": 16.0,
                "cpu_count": 8,
                "architecture": "x86_64",
                "platform": "linux",
                "is_raspberry_pi": False,
                "gpu": {
                    "available": True,
                    "type": "nvidia",
                    "memory_gb": 8.0
                }
            }
        }
        
        with open(config_manager.config_file, "w") as f:
            json.dump(config_data, f)
        
        hardware_info = config_manager.load_hardware_info()
        
        assert hardware_info is not None
        assert hardware_info.memory_gb == 16.0
        assert hardware_info.cpu_count == 8
        assert hardware_info.architecture == "x86_64"
        assert hardware_info.platform == "linux"
        assert hardware_info.is_raspberry_pi is False
        assert hardware_info.gpu_available is True
        assert hardware_info.gpu_type == "nvidia"
        assert hardware_info.gpu_memory_gb == 8.0
    
    def test_get_config_summary(self, config_manager):
        """Test getting configuration summary."""
        # Create config with hardware info
        config_manager.config_dir.mkdir(exist_ok=True)
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8000, "max_workers": 4},
            "ai": {"model": "test-model", "memory_limit": "8GB"},
            "security": {"level": "standard", "require_auth": False, "enable_tls": False},
            "hardware": {
                "memory_gb": 16.0,
                "cpu_count": 8,
                "architecture": "x86_64",
                "platform": "linux",
                "is_raspberry_pi": False,
                "gpu": {"available": False}
            }
        }
        
        with open(config_manager.config_file, "w") as f:
            json.dump(config_data, f)
        
        summary = config_manager.get_config_summary()
        
        assert "server" in summary
        assert "ai" in summary
        assert "security" in summary
        assert "hardware" in summary
        
        assert summary["server"]["host"] == "0.0.0.0"
        assert summary["ai"]["model"] == "test-model"
        assert summary["hardware"]["memory_gb"] == 16.0
    
    def test_validate_config(self, config_manager):
        """Test configuration validation."""
        # Test config with potential issues
        config = MCPConfig(
            ai_model="openai/gpt-oss-20b",
            memory_limit="2GB",  # Too low for AI model
            require_auth=True,
            enable_tls=False,  # Auth without TLS
            transport=["websocket"],  # WebSocket without TLS
            is_raspberry_pi=True,
            max_workers=8  # Too many workers for Pi
        )
        
        config_manager._config = config
        warnings = config_manager.validate_config()
        
        assert len(warnings) > 0
        assert any("memory limit is only 2GB" in w for w in warnings)
        assert any("Authentication enabled but TLS disabled" in w for w in warnings)
        assert any("WebSocket transport without TLS" in w for w in warnings)
        assert any("AI model enabled on Raspberry Pi" in w for w in warnings)
        assert any("High worker count on Raspberry Pi" in w for w in warnings)


class TestHardwareConfig:
    """Test cases for HardwareConfig."""
    
    @patch('src.mcplease_mcp.config.hardware.get_hardware_info')
    @patch('src.mcplease_mcp.config.hardware.get_optimization_config')
    def test_get_hardware_config(self, mock_optimization, mock_hardware):
        """Test getting hardware configuration."""
        # Mock hardware info
        mock_hardware_info = Mock()
        mock_hardware_info.memory_gb = 16.0
        mock_hardware_info.cpu_count = 8
        mock_hardware_info.architecture = "x86_64"
        mock_hardware_info.is_raspberry_pi = False
        mock_hardware_info.is_arm64 = False
        mock_hardware_info.gpu_available = True
        mock_hardware_info.gpu_type = "nvidia"
        mock_hardware_info.optimization_profile = "x86_standard"
        mock_hardware_info.recommended_workers = 6
        mock_hardware_info.recommended_memory_limit = "12GB"
        
        mock_hardware.return_value = mock_hardware_info
        
        # Mock optimization config
        mock_optimization.return_value = {
            "model_quantization": "fp16",
            "context_length": 4096,
            "batch_size": 2,
            "enable_gpu": True,
            "temperature_monitoring": False,
            "cpu_governor": "performance"
        }
        
        config = get_hardware_config()
        
        assert config.memory_gb == 16.0
        assert config.cpu_count == 8
        assert config.architecture == "x86_64"
        assert config.is_raspberry_pi is False
        assert config.gpu_available is True
        assert config.quantization == "fp16"
        assert config.context_length == 4096
        assert config.enable_gpu is True
    
    @patch('src.mcplease_mcp.config.hardware.get_hardware_info')
    def test_get_hardware_config_fallback(self, mock_hardware):
        """Test hardware config fallback when detection fails."""
        mock_hardware.side_effect = Exception("Hardware detection failed")
        
        config = get_hardware_config()
        
        # Should return default values
        assert config.memory_gb == 4.0
        assert config.cpu_count == 2
        assert config.architecture == "unknown"
        assert config.is_raspberry_pi is False
        assert config.gpu_available is False


class TestInstallerConfig:
    """Test cases for InstallerConfig and InstallerConfigManager."""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create temporary project root for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / "pyproject.toml").touch()
            yield project_root
    
    @pytest.fixture
    def installer_manager(self, temp_project_root):
        """Create installer config manager with temporary project root."""
        return InstallerConfigManager(project_root=temp_project_root)
    
    def test_installer_config_creation(self):
        """Test installer config creation."""
        config = InstallerConfig(
            python_version="3.11.0",
            detected_memory_gb=16.0,
            detected_cpu_count=8,
            selected_ai_model="openai/gpt-oss-20b",
            installation_successful=True
        )
        
        assert config.python_version == "3.11.0"
        assert config.detected_memory_gb == 16.0
        assert config.installation_successful is True
        assert config.installation_date != ""  # Should be auto-set
        assert config.failed_components == []  # Should be initialized
    
    def test_save_and_load_installer_config(self, installer_manager):
        """Test saving and loading installer configuration."""
        config = InstallerConfig(
            python_version="3.11.0",
            detected_memory_gb=16.0,
            detected_cpu_count=8,
            selected_ai_model="openai/gpt-oss-20b",
            installation_successful=True,
            dev_dependencies=True,
            warnings=["Test warning"]
        )
        
        installer_manager.save_installer_config(config)
        
        # Check file was created
        assert installer_manager.installer_config_file.exists()
        
        # Load and verify
        loaded_config = installer_manager.load_installer_config()
        
        assert loaded_config is not None
        assert loaded_config.python_version == "3.11.0"
        assert loaded_config.detected_memory_gb == 16.0
        assert loaded_config.installation_successful is True
        assert loaded_config.dev_dependencies is True
        assert loaded_config.warnings == ["Test warning"]
    
    def test_get_installation_summary(self, installer_manager):
        """Test getting installation summary."""
        config = InstallerConfig(
            python_version="3.11.0",
            detected_memory_gb=16.0,
            detected_cpu_count=8,
            detected_architecture="x86_64",
            detected_platform="linux",
            selected_ai_model="openai/gpt-oss-20b",
            selected_transport=["stdio", "sse"],
            installation_successful=True
        )
        
        installer_manager.save_installer_config(config)
        summary = installer_manager.get_installation_summary()
        
        assert summary["status"] == "installed"
        assert summary["python_version"] == "3.11.0"
        assert summary["hardware"]["memory_gb"] == 16.0
        assert summary["configuration"]["ai_model"] == "openai/gpt-oss-20b"
    
    def test_check_installation_health_healthy(self, installer_manager):
        """Test installation health check for healthy installation."""
        # Create successful installation config
        config = InstallerConfig(
            installation_successful=True,
            selected_ai_model="disabled",  # No model to download
            ai_model_downloaded=False
        )
        installer_manager.save_installer_config(config)
        
        # Create required files
        installer_manager.config_dir.mkdir(exist_ok=True)
        (installer_manager.config_dir / "config.json").touch()
        (installer_manager.project_root / ".env").touch()
        (installer_manager.project_root / ".venv").mkdir()
        
        health = installer_manager.check_installation_health()
        
        assert health["healthy"] is True
        assert len(health["issues"]) == 0
    
    def test_check_installation_health_unhealthy(self, installer_manager):
        """Test installation health check for unhealthy installation."""
        # Create failed installation config
        config = InstallerConfig(
            installation_successful=False,
            failed_components=["ai_model"],
            selected_ai_model="openai/gpt-oss-20b",
            ai_model_downloaded=False
        )
        installer_manager.save_installer_config(config)
        
        health = installer_manager.check_installation_health()
        
        assert health["healthy"] is False
        assert len(health["issues"]) > 0
        assert any("not completed successfully" in issue for issue in health["issues"])
        assert any("Component failed: ai_model" in issue for issue in health["issues"])
        assert len(health["recommendations"]) > 0
    
    def test_update_installation_status(self, installer_manager):
        """Test updating installation status."""
        # Create initial config
        config = InstallerConfig(installation_successful=False)
        installer_manager.save_installer_config(config)
        
        # Update status
        installer_manager.update_installation_status(
            successful=True,
            failed_components=["test_component"],
            warnings=["test_warning"]
        )
        
        # Verify update
        updated_config = installer_manager.load_installer_config()
        assert updated_config.installation_successful is True
        assert "test_component" in updated_config.failed_components
        assert "test_warning" in updated_config.warnings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])