# MCPlease MCP Server - uv-based Installation System

## Overview

This document describes the comprehensive uv-based installation and configuration management system implemented for MCPlease MCP Server. The system provides one-command installation with automatic hardware detection and optimal configuration selection.

## Key Features

### 🚀 One-Command Installation
- **Simple entry point**: `python install.py` or `python scripts/install_uv.py`
- **Automatic uv installation**: Downloads and installs uv package manager if not present
- **Cross-platform support**: Works on macOS, Linux, Windows, and Raspberry Pi
- **Hardware-optimized configuration**: Automatically detects and configures for optimal performance

### 🔍 Automatic Hardware Detection
- **Memory and CPU detection**: Uses psutil for accurate system resource detection
- **GPU detection**: Supports NVIDIA GPUs, Apple Metal, and integrated graphics
- **Raspberry Pi detection**: Special optimizations for Pi 4/5 deployments
- **Architecture detection**: Handles x86_64, ARM64, and other architectures

### ⚙️ Intelligent Configuration Management
- **Hardware-based recommendations**: AI model, memory limits, worker counts
- **Security level selection**: Basic, standard, or full security configurations
- **Transport protocol selection**: stdio, SSE, WebSocket based on use case
- **Platform-specific optimizations**: Pi-specific settings, macOS Metal support

## Implementation Details

### Core Components

#### 1. UVInstaller (`scripts/install_uv.py`)
The main installer class that orchestrates the entire installation process:

```python
class UVInstaller:
    def __init__(self, project_root: Optional[Path] = None)
    def detect_hardware(self) -> Dict[str, Any]
    def check_uv_installation(self) -> bool
    def create_virtual_environment(self) -> bool
    def install_dependencies(self, dev: bool = False) -> bool
    def create_configuration(self, hardware_config: Dict[str, Any]) -> bool
    def download_ai_model(self, model_name: str) -> bool
    def create_startup_scripts(self) -> bool
    def run_tests(self) -> bool
    def install(self, dev: bool = False, skip_model: bool = False, skip_tests: bool = False) -> bool
```

#### 2. Configuration Management (`src/mcplease_mcp/config/`)
Comprehensive configuration system with multiple layers:

- **ConfigManager**: Main configuration loading and saving
- **HardwareConfig**: Hardware-specific optimizations
- **InstallerConfig**: Installation metadata and tracking

#### 3. Hardware Detection (`src/mcplease_mcp/utils/hardware.py`)
Advanced hardware detection with optimization profiles:

- **Memory and CPU detection**: Accurate resource measurement
- **GPU detection**: NVIDIA, AMD, Apple Metal support
- **Raspberry Pi detection**: Multiple detection methods
- **Optimization profiles**: Performance tuning based on hardware

### Installation Process

The installation follows these steps:

1. **uv Installation Check**: Automatically installs uv if not present
2. **Hardware Detection**: Comprehensive system analysis
3. **Virtual Environment**: Creates isolated Python environment
4. **Dependency Installation**: Installs all required packages
5. **Configuration Creation**: Generates optimized config files
6. **AI Model Download**: Downloads appropriate model (optional)
7. **Startup Scripts**: Creates platform-specific launch scripts
8. **Installation Tests**: Verifies installation integrity

### Configuration Files Generated

#### `.mcplease/config.json`
Main configuration file with nested structure:
```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8000,
    "transport": ["stdio", "sse"],
    "max_workers": 8
  },
  "ai": {
    "model": "openai/gpt-oss-20b",
    "memory_limit": "12GB",
    "quantization": "fp16",
    "device": "auto"
  },
  "security": {
    "level": "full",
    "require_auth": true,
    "enable_tls": true
  },
  "hardware": { /* hardware detection results */ },
  "installation": { /* installation metadata */ }
}
```

#### `.env`
Environment variables for easy configuration:
```bash
MCPLEASE_CONFIG_FILE=.mcplease/config.json
MCPLEASE_LOG_LEVEL=INFO
MCPLEASE_HOST=127.0.0.1
MCPLEASE_PORT=8000
MCPLEASE_AI_MODEL=openai/gpt-oss-20b
MCPLEASE_MEMORY_LIMIT=12GB
MCPLEASE_SECURITY_LEVEL=full
```

#### `start_uv.sh` / `start_uv.bat`
Platform-specific startup scripts:
```bash
#!/bin/bash
# Load configuration
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start server
uv run python -m mcplease_mcp.main "$@"
```

### Hardware-Specific Optimizations

#### High-Memory Systems (16GB+)
- **AI Model**: Full OSS-20B model
- **Memory Limit**: 12GB
- **Workers**: Up to 8
- **Transport**: All protocols (stdio, SSE, WebSocket)
- **Security**: Full TLS/SSL support
- **Quantization**: FP16 for quality

#### Medium-Memory Systems (8-16GB)
- **AI Model**: OSS-20B with quantization
- **Memory Limit**: 6GB
- **Workers**: Up to 6
- **Transport**: stdio + SSE
- **Security**: Standard authentication
- **Quantization**: INT8 for efficiency

#### Low-Memory Systems (<8GB)
- **AI Model**: Disabled by default
- **Memory Limit**: 2-3GB
- **Workers**: 2-4
- **Transport**: stdio only
- **Security**: Basic
- **Quantization**: INT8

#### Raspberry Pi Optimizations
- **AI Model**: Disabled (too resource intensive)
- **Memory Limit**: 1GB
- **Workers**: 2 (prevent overheating)
- **Transport**: SSE (better for remote access)
- **Security**: Standard with ngrok support
- **Special Features**: Temperature monitoring, CPU governor tuning

## Testing

### Comprehensive Test Suite

#### Unit Tests (`tests/test_uv_installation.py`)
- **Hardware detection**: All platforms and edge cases
- **Configuration creation**: Various hardware scenarios
- **Installation steps**: Each phase individually tested
- **Error handling**: Graceful failure scenarios
- **Integration tests**: End-to-end workflows

#### Configuration Tests (`tests/test_config_management.py`)
- **Config loading**: File and environment sources
- **Config validation**: Security and performance warnings
- **Hardware integration**: Optimization recommendations
- **Installer tracking**: Installation metadata

#### Integration Test (`test_installation.py`)
- **Dry-run installation**: Full process without actual installation
- **Hardware detection**: Real system testing
- **Configuration generation**: Actual file creation
- **Startup script creation**: Platform-specific scripts

### Test Results
```bash
$ python -m pytest tests/test_uv_installation.py -v
================ 33 passed, 1 skipped in 0.16s =================

$ python -m pytest tests/test_config_management.py -v  
================ 17 passed, 1 warning in 0.13s =================

$ python test_installation.py
🎉 All tests passed! Installation system is ready.
```

## Usage Examples

### Basic Installation
```bash
# One-command installation
python install.py

# Or directly
python scripts/install_uv.py
```

### Development Installation
```bash
# Install with development dependencies
python install.py --dev

# Skip AI model download
python install.py --skip-model

# Skip installation tests
python install.py --skip-tests
```

### Starting the Server
```bash
# Unix/Linux/macOS
./start_uv.sh

# Windows
start_uv.bat

# Direct uv command
uv run python -m mcplease_mcp.main
```

### Configuration Management
```python
from mcplease_mcp.config import get_config, get_hardware_info

# Load current configuration
config = get_config()
print(f"Server: {config.host}:{config.port}")
print(f"AI Model: {config.ai_model}")

# Get hardware information
hardware = get_hardware_info()
if hardware:
    print(f"Memory: {hardware.memory_gb}GB")
    print(f"CPUs: {hardware.cpu_count}")
```

## Requirements Satisfied

This implementation satisfies all requirements from task 11:

✅ **Create one-command installation script using uv for dependency management**
- `python install.py` provides single-command installation
- Automatic uv installation and management
- Complete dependency resolution with uv

✅ **Implement pyproject.toml configuration with FastMCP and AI model dependencies**
- Updated pyproject.toml with all required dependencies
- FastMCP integration for MCP protocol
- AI model dependencies (vLLM, transformers, torch)
- Development and testing dependencies

✅ **Add automatic hardware detection and optimal configuration selection**
- Comprehensive hardware detection (CPU, memory, GPU, architecture)
- Raspberry Pi specific detection and optimizations
- Automatic configuration based on detected hardware
- Performance tuning recommendations

✅ **Write tests for uv-based installation and configuration management**
- 33 unit tests for installation system
- 17 tests for configuration management
- Integration tests with real hardware detection
- Error handling and edge case coverage

## Future Enhancements

### Planned Improvements
1. **Docker Integration**: Automatic container builds during installation
2. **IDE Configuration**: Automatic VSCode/Cursor MCP client setup
3. **Update Management**: In-place updates using uv
4. **Health Monitoring**: Post-installation health checks
5. **Backup/Restore**: Configuration backup and restoration

### Platform Extensions
1. **ARM64 Optimizations**: Better Apple Silicon support
2. **Windows WSL**: Enhanced Windows Subsystem for Linux support
3. **Cloud Deployment**: AWS/GCP/Azure deployment templates
4. **Kubernetes**: Helm charts and operators

## Conclusion

The uv-based installation and configuration management system provides a robust, user-friendly way to install and configure MCPlease MCP Server across all supported platforms. With automatic hardware detection, intelligent configuration, and comprehensive testing, it ensures optimal performance and reliability for all users.

The system is production-ready and provides a solid foundation for the MCPlease MCP Server ecosystem.