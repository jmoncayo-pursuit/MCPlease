"""Tests for dependency installation system."""

import pytest
import sys
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from environment.installer import DependencyInstaller, InstallationResult


class TestDependencyInstaller:
    """Test cases for DependencyInstaller."""
    
    def test_installer_initialization(self):
        """Test installer initializes correctly."""
        installer = DependencyInstaller()
        assert installer.pip_executable is not None
        assert installer.system_info is not None
        assert 'platform' in installer.system_info
        assert 'python_version' in installer.system_info
    
    def test_python_compatibility_check(self):
        """Test Python version compatibility checking."""
        installer = DependencyInstaller()
        
        # Test vLLM compatibility
        is_compatible, message = installer.check_python_compatibility('vllm')
        
        # Should be compatible with current Python version (assuming 3.9-3.12)
        current_version = (sys.version_info.major, sys.version_info.minor)
        expected_compatible = current_version in [(3, 9), (3, 10), (3, 11), (3, 12)]
        
        assert is_compatible == expected_compatible
        assert 'Python' in message
    
    def test_system_info_collection(self):
        """Test system information collection."""
        installer = DependencyInstaller()
        system_info = installer.system_info
        
        required_keys = ['platform', 'machine', 'python_version', 'is_mac', 'is_apple_silicon']
        for key in required_keys:
            assert key in system_info
        
        # Verify boolean values
        assert isinstance(system_info['is_mac'], bool)
        assert isinstance(system_info['is_apple_silicon'], bool)
    
    @patch('subprocess.run')
    def test_torch_installation_success(self, mock_run):
        """Test successful PyTorch installation."""
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully installed torch"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Mock package import verification
        with patch.object(DependencyInstaller, '_verify_package_import', return_value=True):
            installer = DependencyInstaller()
            result = installer.install_torch()
        
        assert result.success is True
        assert result.package == 'torch'
        assert result.version == '2.1.2'
        assert result.error_message is None
    
    @patch('subprocess.run')
    def test_torch_installation_failure(self, mock_run):
        """Test PyTorch installation failure."""
        # Mock failed subprocess call
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'pip install', stderr="Installation failed"
        )
        
        installer = DependencyInstaller()
        result = installer.install_torch()
        
        assert result.success is False
        assert result.package == 'torch'
        assert result.error_message is not None
        assert "Installation command failed" in result.error_message
    
    @patch('subprocess.run')
    def test_vllm_installation_success(self, mock_run):
        """Test successful vLLM installation."""
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully installed vllm"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Mock package import verification
        with patch.object(DependencyInstaller, '_verify_package_import', return_value=True):
            installer = DependencyInstaller()
            result = installer.install_vllm()
        
        assert result.success is True
        assert result.package == 'vllm'
        assert result.version == '0.2.7'
    
    @patch('subprocess.run')
    def test_vllm_python_incompatibility(self, mock_run):
        """Test vLLM installation with incompatible Python version."""
        installer = DependencyInstaller()
        
        # Mock incompatible Python version
        with patch.object(installer, 'check_python_compatibility', return_value=(False, "Python 3.13 not supported")):
            result = installer.install_vllm()
        
        assert result.success is False
        assert result.package == 'vllm'
        assert "Python compatibility check failed" in result.error_message
    
    def test_package_import_verification(self):
        """Test package import verification."""
        installer = DependencyInstaller()
        
        # Test with a package that should exist (sys)
        assert installer._verify_package_import('sys') is True
        
        # Test with a package that shouldn't exist
        assert installer._verify_package_import('nonexistent_package_12345') is False
    
    def test_vllm_error_parsing(self):
        """Test vLLM error message parsing."""
        installer = DependencyInstaller()
        
        # Test CUDA error on Mac
        cuda_error = "CUDA toolkit not found"
        parsed = installer._parse_vllm_error(cuda_error)
        assert "CUDA not available on Mac" in parsed
        
        # Test memory error
        memory_error = "Not enough memory to compile"
        parsed = installer._parse_vllm_error(memory_error)
        assert "Insufficient memory" in parsed
        
        # Test generic error
        generic_error = "Some random error occurred"
        parsed = installer._parse_vllm_error(generic_error)
        assert "Some random error occurred" in parsed
    
    def test_installation_summary(self):
        """Test installation summary generation."""
        installer = DependencyInstaller()
        
        # Create mock results
        results = [
            InstallationResult(success=True, package='torch', version='2.1.2'),
            InstallationResult(success=False, package='vllm', error_message='Installation failed'),
            InstallationResult(success=True, package='transformers', warnings=['Some warning'])
        ]
        
        summary = installer.get_installation_summary(results)
        
        assert summary['overall_success'] is False  # One package failed
        assert summary['successful_packages'] == 2
        assert summary['failed_packages'] == 1
        assert 'torch' in summary['successful']
        assert 'transformers' in summary['successful']
        assert len(summary['failed']) == 1
        assert summary['failed'][0]['package'] == 'vllm'
        assert 'Some warning' in summary['warnings']
    
    @patch('pathlib.Path.exists')
    def test_requirements_file_not_found(self, mock_exists):
        """Test handling of missing requirements file."""
        mock_exists.return_value = False
        
        installer = DependencyInstaller()
        results = installer.install_requirements_file(Path('nonexistent.txt'))
        
        assert len(results) == 1
        assert results[0].success is False
        assert 'not found' in results[0].error_message


class TestInstallationResult:
    """Test cases for InstallationResult dataclass."""
    
    def test_installation_result_creation(self):
        """Test InstallationResult creation."""
        result = InstallationResult(
            success=True,
            package='test_package',
            version='1.0.0'
        )
        
        assert result.success is True
        assert result.package == 'test_package'
        assert result.version == '1.0.0'
        assert result.error_message is None
        assert result.warnings == []  # Should be initialized as empty list
    
    def test_installation_result_with_warnings(self):
        """Test InstallationResult with warnings."""
        warnings = ['Warning 1', 'Warning 2']
        result = InstallationResult(
            success=True,
            package='test_package',
            warnings=warnings
        )
        
        assert result.warnings == warnings
    
    def test_installation_result_failure(self):
        """Test InstallationResult for failed installation."""
        result = InstallationResult(
            success=False,
            package='failed_package',
            error_message='Installation failed'
        )
        
        assert result.success is False
        assert result.error_message == 'Installation failed'
        assert result.version is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])