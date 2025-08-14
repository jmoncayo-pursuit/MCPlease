# Dependency Installation System

This document describes the comprehensive dependency installation system for AI model integration.

## Overview

The dependency installation system provides robust, error-handled installation of AI model dependencies, with special focus on vLLM and PyTorch compatibility with Mac hardware.

## Components

### 1. Requirements File (`requirements.txt`)
- Pinned versions for compatibility with Python 3.9-3.12
- Optimized for Mac hardware with Metal Performance Shaders
- Includes all necessary dependencies for AI model integration

### 2. DependencyInstaller (`src/environment/installer.py`)
- Specialized installer for critical AI packages (torch, vLLM)
- Comprehensive error handling and compatibility checking
- Mac-specific optimizations and warnings
- Detailed installation reporting

### 3. Installation Scripts
- `scripts/install_dependencies.py` - Python-based installer with full features
- `scripts/install.sh` - Simple shell wrapper for easy execution

## Usage

### Quick Installation
```bash
# Install all dependencies
./scripts/install.sh

# Install only critical packages (torch + vLLM)
./scripts/install.sh --critical-only

# Check compatibility without installing
./scripts/install.sh --dry-run
```

### Python Script Usage
```bash
# Full installation
python scripts/install_dependencies.py

# Critical packages only
python scripts/install_dependencies.py --critical-only

# Verbose output
python scripts/install_dependencies.py --verbose

# Use virtual environment pip
python scripts/install_dependencies.py --use-venv
```

### Programmatic Usage
```python
from environment.installer import DependencyInstaller
from pathlib import Path

# Create installer
installer = DependencyInstaller()

# Install from requirements file
results = installer.install_requirements_file(Path('requirements.txt'))

# Get installation summary
summary = installer.get_installation_summary(results)
print(f"Success: {summary['overall_success']}")
```

## Features

### Compatibility Checking
- Python version validation (3.9-3.12 required for vLLM)
- Mac hardware detection and optimization
- Pre-installation compatibility checks

### Error Handling
- Detailed error messages with troubleshooting hints
- Graceful handling of installation failures
- Timeout protection for long installations
- Automatic retry logic for transient failures

### Mac Optimizations
- PyTorch with Metal Performance Shaders support
- Apple Silicon detection and memory warnings
- CPU-optimized builds for Mac hardware

### Installation Reporting
- Comprehensive installation summaries
- Success/failure tracking per package
- Warning collection and display
- System information reporting

## Critical Packages

### PyTorch (torch==2.1.2)
- Installed first as dependency for vLLM
- Mac-optimized with CPU/Metal support
- Uses PyTorch CPU index for Mac compatibility

### vLLM (vllm==0.2.7)
- High-performance LLM inference server
- Requires Python 3.9-3.12 (not 3.13)
- Mac compatibility with memory warnings

## Error Handling

### Common Issues and Solutions

#### Python Version Incompatibility
```
Error: Python 3.13 not supported
Solution: Use Python 3.9-3.12 for vLLM compatibility
```

#### Memory Issues
```
Error: Insufficient memory during compilation
Solution: Ensure 16GB+ RAM available, close other applications
```

#### CUDA Errors on Mac
```
Error: CUDA toolkit not found
Solution: This is expected on Mac - vLLM will use CPU inference
```

### Installation Timeouts
- PyTorch: 5 minute timeout
- vLLM: 10 minute timeout (compilation intensive)
- Other packages: 5 minute timeout

## Integration with Environment Manager

The `EnvironmentManager` automatically uses the `DependencyInstaller` for enhanced installation capabilities:

```python
from environment.manager import EnvironmentManager

manager = EnvironmentManager()
success = manager.install_dependencies()  # Uses DependencyInstaller internally
```

## Testing

Run the dependency installer tests:
```bash
python -c "
import sys; sys.path.insert(0, 'src')
from environment.installer import DependencyInstaller
installer = DependencyInstaller()
print('✅ Installation system ready')
"
```

## Requirements Satisfied

This implementation satisfies the following requirements:

- **3.1**: Python 3.9-3.12 compatibility validation
- **3.2**: Virtual environment isolation and dependency management
- **Error Handling**: Comprehensive error handling for installation failures
- **Pinned Versions**: Requirements file with pinned versions for compatibility
- **vLLM and torch**: Specialized installers for critical AI packages