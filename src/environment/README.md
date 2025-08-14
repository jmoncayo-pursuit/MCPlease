# Environment Management

This module provides Python environment validation and virtual environment setup for the AI model integration project.

## Features

- **Python Version Validation**: Ensures Python 3.9-3.12 compatibility (required for vLLM)
- **Virtual Environment Management**: Automated creation and management of project virtual environments
- **Dependency Installation**: Automated installation of project dependencies
- **Environment Validation**: Comprehensive validation reporting

## Usage

### Command Line Interface

From the project root directory:

```bash
# Run environment validation
python -m src.environment.validator

# Setup environment (create venv and install dependencies)
python -m src.environment.setup

# Show setup information
python -m src.environment.setup --info

# Force recreate virtual environment
python -m src.environment.setup --force

# Alternative: use the convenience script
python scripts/setup_environment.py
```

### Programmatic Usage

```python
from src.environment.manager import EnvironmentManager
from src.environment.validator import EnvironmentValidator

# Create environment manager
env_manager = EnvironmentManager()

# Validate Python version
is_valid, message = env_manager.check_python_version()

# Setup complete environment
success = env_manager.setup_dependencies()

# Validate environment
validator = EnvironmentValidator()
is_valid, issues, warnings = validator.validate_all()
```

## Components

### EnvironmentManager

Main class for environment management operations:

- `check_python_version()`: Validates Python version compatibility
- `validate_environment()`: Runs environment validation
- `setup_virtual_env()`: Creates virtual environment
- `install_dependencies()`: Installs project dependencies
- `setup_dependencies()`: Complete setup process

### EnvironmentValidator

Provides comprehensive environment validation:

- `validate_all()`: Runs all validation checks
- `print_validation_report()`: Prints detailed validation report

### Setup Script

Automated setup with command-line interface:

- Environment validation
- Virtual environment creation
- Dependency installation
- Final validation

## Requirements

- Python 3.9, 3.10, 3.11, or 3.12 (vLLM compatibility requirement)
- `requirements.txt` file in project root
- Write permissions in project directory

## Error Handling

The module provides comprehensive error handling:

- **Python Version Issues**: Clear error messages for unsupported versions
- **Virtual Environment Failures**: Detailed error reporting for venv creation issues
- **Dependency Installation Failures**: pip error output capture and reporting
- **Permission Issues**: Clear error messages for file system permission problems

## Testing

Run the test suite:

```bash
python tests/test_environment.py
```

The test suite covers:
- Python version validation
- Virtual environment management
- Environment validation logic
- Cross-platform compatibility