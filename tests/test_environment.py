"""Tests for environment management functionality."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from environment.manager import EnvironmentManager
from environment.validator import EnvironmentValidator


class TestEnvironmentManager(unittest.TestCase):
    """Test cases for EnvironmentManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.env_manager = EnvironmentManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_check_python_version_supported(self):
        """Test Python version checking with supported versions."""
        with patch('sys.version_info', (3, 11, 0)):
            is_valid, message = self.env_manager.check_python_version()
            self.assertTrue(is_valid)
            self.assertIn("3.11", message)
            self.assertIn("supported", message)
    
    def test_check_python_version_unsupported(self):
        """Test Python version checking with unsupported versions."""
        with patch('sys.version_info', (3, 8, 0)):
            is_valid, message = self.env_manager.check_python_version()
            self.assertFalse(is_valid)
            self.assertIn("3.8", message)
            self.assertIn("not supported", message)
    
    def test_validate_environment_valid(self):
        """Test environment validation with valid Python version."""
        with patch('sys.version_info', (3, 11, 0)):
            result = self.env_manager.validate_environment()
            self.assertTrue(result)
    
    def test_validate_environment_invalid(self):
        """Test environment validation with invalid Python version."""
        with patch('sys.version_info', (3, 8, 0)):
            result = self.env_manager.validate_environment()
            self.assertFalse(result)
    
    def test_get_python_executable_no_venv(self):
        """Test getting Python executable when no venv exists."""
        python_exe = self.env_manager.get_python_executable()
        # Should fallback to system Python
        self.assertEqual(python_exe, sys.executable)
    
    def test_get_pip_executable_no_venv(self):
        """Test getting pip executable when no venv exists."""
        pip_exe = self.env_manager.get_pip_executable()
        # Should fallback to system pip
        self.assertEqual(pip_exe, "pip")
    
    def test_is_venv_active_no_venv(self):
        """Test checking if venv is active when no venv exists."""
        result = self.env_manager.is_venv_active()
        # Should be False since no venv exists
        self.assertFalse(result)
    
    def test_activate_venv_command_unix(self):
        """Test getting venv activation command on Unix systems."""
        with patch('sys.platform', 'linux'):
            command = self.env_manager.activate_venv_command()
            self.assertTrue(command.startswith("source"))
            self.assertIn("bin/activate", command)
    
    def test_activate_venv_command_windows(self):
        """Test getting venv activation command on Windows."""
        with patch('sys.platform', 'win32'):
            command = self.env_manager.activate_venv_command()
            self.assertIn("Scripts", command)
            self.assertIn("activate.bat", command)


class TestEnvironmentValidator(unittest.TestCase):
    """Test cases for EnvironmentValidator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.validator = EnvironmentValidator(self.temp_dir)
        
        # Create a mock requirements.txt file
        (self.temp_dir / "requirements.txt").write_text("# Test requirements\n")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_validate_all_with_supported_python(self):
        """Test validation with supported Python version."""
        with patch('sys.version_info', (3, 11, 0)):
            is_valid, issues, warnings = self.validator.validate_all()
            
            # Should be valid (no critical issues)
            self.assertTrue(is_valid)
            self.assertEqual(len(issues), 0)
            
            # Should have warnings about missing venv
            self.assertGreater(len(warnings), 0)
            self.assertTrue(any("Virtual environment not found" in w for w in warnings))
    
    def test_validate_all_with_unsupported_python(self):
        """Test validation with unsupported Python version."""
        with patch('sys.version_info', (3, 8, 0)):
            is_valid, issues, warnings = self.validator.validate_all()
            
            # Should be invalid due to Python version
            self.assertFalse(is_valid)
            self.assertGreater(len(issues), 0)
            self.assertTrue(any("Python version issue" in i for i in issues))
    
    def test_validate_all_missing_requirements(self):
        """Test validation when requirements.txt is missing."""
        # Remove the requirements file
        (self.temp_dir / "requirements.txt").unlink()
        
        with patch('sys.version_info', (3, 11, 0)):
            is_valid, issues, warnings = self.validator.validate_all()
            
            # Should be invalid due to missing requirements
            self.assertFalse(is_valid)
            self.assertTrue(any("requirements.txt not found" in i for i in issues))


if __name__ == '__main__':
    unittest.main()