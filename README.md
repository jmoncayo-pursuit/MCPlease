# MCPlease - Universal MCP Server

🤖 **Powered by OSS-20B** | 🔒 **100% Offline & Private** | 💻 **Universal Transport** | ⚡ **One-Command Setup**

MCPlease is a universal MCP (Model Context Protocol) server that works everywhere - in your IDE, with Continue.dev, or directly via CLI. It provides intelligent code completion, explanations, and debugging help using a locally-hosted language model, ensuring your code never leaves your machine.

## 🎯 **The Promise: Universal MCP Server, One Command**

**Before MCPlease**: Multiple setup steps, manual configuration, transport-specific setup
**With MCPlease**: Run `./start.sh` and it works everywhere - IDE, Continue.dev, CLI, Docker

Built for developers who want AI coding assistance that works in any environment without cloud dependencies.

## ✨ Features

- **🔒 Complete Privacy**: All AI processing happens locally - your code never leaves your machine
- **🚇 Universal Transport**: Works via stdio (IDE) or HTTP (Continue.dev, web clients)
- **⚡ One-Command Setup**: `./start.sh` auto-detects environment and configures everything
- **🧠 Professional AI**: Full OSS-20B model for production-quality coding assistance
- **💻 Cross-Platform**: Works on macOS, Linux, and Windows
- **🔌 IDE Ready**: Seamless integration with Cursor, VS Code, and Continue.dev
- **🚀 AI-Native**: Built for developers who code with AI

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+**
- **15GB+ free disk space** (for OSS-20B model)

### 🎯 **Universal Installer (Recommended)**

**One command works on any system:**

```bash
# macOS/Linux
./install.sh

# Windows
install.bat
```

The installer automatically:
- ✅ **Detects your OS** (macOS, Ubuntu, CentOS, Arch, Windows)
- ✅ **Finds package manager** (apt, yum, dnf, pacman, brew, chocolatey)
- ✅ **Installs Python** if needed
- ✅ **Installs Docker** (optional)
- ✅ **Creates virtual environment**
- ✅ **Installs dependencies**
- ✅ **Downloads OSS-20B model** (optional)
- ✅ **Sets up IDE configurations**
- ✅ **Tests everything**

### Option 1: Local Setup (After Installer)
```bash
# Download model first (if not done by installer)
python download_model.py

# One command gets everything working
./start.sh
```

### Option 2: Docker Setup (After Installer)
```bash
# One command starts Docker containers
./start-docker.sh

# Or use Makefile
make docker-start
```

**That's it!** Both scripts auto-detect your environment and start the appropriate setup.

## 🐳 Docker Options

### **Simple Docker (Default)**
```bash
./start-docker.sh
# or
make docker-start
```
- **Single container** with MCP server
- **HTTP transport** on port 8000
- **Health checks** enabled
- **Perfect for** development and testing

### **Production Docker Stack**
```bash
./start-docker.sh prod
# or
make docker-prod
```
- **Load balanced** MCP servers (2x instances)
- **HAProxy** load balancer
- **Monitoring stack** (Prometheus, Grafana, Loki)
- **High availability** with health checks
- **Perfect for** production deployments

### **Development Docker Stack**
```bash
./start-docker.sh dev
# or
make docker-dev
```
- **Hot reload** for development
- **Nginx** reverse proxy
- **Redis** caching
- **Perfect for** team development

### **Docker Management**
```bash
# Stop containers
make docker-stop

# View logs
make docker-logs

# Or direct commands
docker-compose down
docker-compose logs -f
```

## 🔌 Transport Options

### 1. **IDE Integration (stdio) - Default**
```bash
./start.sh
```
- **Works in**: Cursor, VS Code
- **Protocol**: MCP via stdio
- **Setup**: Automatic IDE detection and configuration
- **Use**: Workspace Tools → MCP → MCPlease

### 2. **Continue.dev Integration (HTTP)**
```bash
./start.sh --http
```
- **Works with**: Continue.dev, web clients, API calls
- **Protocol**: HTTP REST API
- **Port**: Auto-detects available port (8000+)
- **Use**: Continue.dev extension or direct HTTP calls

### 3. **CLI Direct (stdio)**
```bash
python mcplease_mcp_server.py --transport stdio
```
- **Works in**: Terminal, scripts, automation
- **Protocol**: MCP via stdio
- **Use**: Direct command-line interaction

## 🛠️ Manual Setup (Optional)

If you prefer manual configuration:

```bash
# Clone repository
git clone https://github.com/your-org/mcplease.git
cd mcplease

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server manually
python mcplease_mcp_server.py --transport stdio  # For IDE
python mcplease_http_server.py --port 8000      # For HTTP
```

## 🔧 IDE Configuration

### Automatic Setup (Recommended)
```bash
python scripts/setup_ide.py
```
This creates MCP configurations for:
- **Cursor**: `~/.cursor/mcp.json`
- **VS Code**: `~/.vscode/mcp.json`  
- **Continue.dev**: `.continue/config.json`

### Manual Configuration
For Cursor/VS Code, create `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "MCPlease": {
      "command": "/path/to/mcplease/.venv/bin/python",
      "args": ["-u", "mcplease_mcp_server.py"],
      "cwd": "/path/to/mcplease",
      "env": {"PYTHONUNBUFFERED": "1"},
      "enabled": true
    }
  }
}
```

## 💡 Available Tools

MCPlease provides these MCP tools:

- **`file/read`** - Read file contents for analysis
- **`file/write`** - Write or modify file content
- **`file/list`** - List files in directory
- **`terminal/run`** - Execute terminal commands
- **`codebase/search`** - Search codebase for patterns
- **`ai/analyze`** - Analyze code using OSS-20B AI
- **`ai/build`** - Generate code using OSS-20B AI
- **`health/check`** - Server health and status

## 📊 Performance

- **Response Time**: Instant with fallback responses, AI-powered with OSS-20B
- **Memory Usage**: Minimal (fallback mode), optimized (AI mode)
- **Setup Time**: ~10 seconds total
- **Context Length**: Unlimited (fallback mode), model-dependent (AI mode)

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   IDE/Client    │◄──►│  MCP Server      │◄──►│  OSS-20B AI    │
│  (Cursor/VS)    │    │  (Universal)     │    │  (Local)        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────────────────┐
                       │  Transport Layer │
                       │  stdio | HTTP    │
                       └──────────────────┘
```

## 🧪 Development

### Project Structure
```
mcplease/
├── start.sh                    # Universal startup script
├── mcplease_mcp_server.py      # MCP server with stdio transport
├── mcplease_http_server.py     # HTTP server for Continue.dev
├── scripts/                    # Setup and utility scripts
├── tests/                      # Comprehensive test suite
└── docs/                       # Documentation
```

### Running Tests
```bash
# Test all transports
python scripts/test_transports.py

# Run comprehensive test suite
python scripts/run_comprehensive_tests.py

# Run specific test categories
python -m pytest tests/ -v
```

### Testing Transports
```bash
# Test stdio transport
python mcplease_mcp_server.py --transport stdio

# Test HTTP transport
python mcplease_http_server.py --port 8000

# Test both transports
python scripts/test_transports.py
```

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.production.yml up -d

# Includes HAProxy, monitoring, and health checks
```

### Monitoring
- **Prometheus** metrics collection
- **Grafana** dashboards
- **Loki** log aggregation
- **Alertmanager** notifications

## 🤝 Contributing

We welcome contributions! 

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

### Common Issues

#### Transport Issues
- **stdio not working**: Run `python scripts/setup_ide.py` and restart IDE
- **HTTP not working**: Check if port is available, try `./start.sh --http`
- **IDE not detecting**: Verify MCP configuration in `~/.cursor/mcp.json`

#### Model Issues
- **Model not found**: Run `python download_model.py` first
- **Slow responses**: OSS-20B model loads on first use, subsequent calls are fast
- **Memory issues**: Model uses ~13GB RAM, ensure sufficient memory

### Getting Help
- **Documentation**: Check our documentation files
- **Issues**: Report bugs on GitHub Issues
- **Questions**: Open a GitHub Discussion

## 🙏 Acknowledgments

- **MCP Protocol** for the universal server-client communication
- **FastAPI** for the high-performance HTTP server
- **OSS-20B** for the powerful local AI model

---
<div align="center">
**MCPlease** - Made with ❤️ for developers who want universal AI coding assistance
#ForTheLoveOfCode
</div>