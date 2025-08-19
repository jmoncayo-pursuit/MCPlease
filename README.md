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

<details>
<summary><b>🧪 Test the Installer First (Recommended)</b></summary>

Test what the installer would do without installing anything:

```bash
# Test individual functions
make test-installer

# Show complete installation plan
make test-installer-dry-run
```

</details>

## 🚀 **Getting Started**

<details>
<summary><b>📋 Choose Your Setup Method</b></summary>

<details>
<summary><b>🎯 Option 1: Universal Installer (Recommended)</b></summary>

**One command works on any system:**

```bash
# macOS/Linux
./install.sh

# Windows
install.bat
```

The installer automatically detects your system and sets up everything.

</details>

<details>
<summary><b>🐳 Option 2: Docker Setup</b></summary>

**One command starts everything:**

```bash
# Simple Docker (default)
./start-docker.sh

# Production Docker Stack
./start-docker.sh prod

# Development Docker Stack
./start-docker.sh dev
```

</details>

<details>
<summary><b>🛠️ Option 3: Manual Setup</b></summary>

For advanced users who prefer manual configuration:

```bash
# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server manually
python mcplease_mcp_server.py --transport stdio  # For IDE
python mcplease_http_server.py --port 8000      # For HTTP
```

</details>

</details>

## 🐳 **Docker Options**

<details>
<summary><b>🐳 Choose Your Docker Setup</b></summary>

<details>
<summary><b>🚀 Simple Docker (Default)</b></summary>

**Perfect for development and testing:**

```bash
./start-docker.sh
# or
make docker-start
```

**Features:**
- **Single container** with MCP server
- **HTTP transport** on port 8000
- **Health checks** enabled
- **Auto-restart** on failure

</details>

<details>
<summary><b>🏭 Production Docker Stack</b></summary>

**Enterprise-grade with monitoring:**

```bash
./start-docker.sh prod
# or
make docker-prod
```

**Features:**
- **Load balanced** MCP servers (2x instances)
- **HAProxy** load balancer
- **Monitoring stack** (Prometheus, Grafana, Loki)
- **High availability** with health checks
- **Alerting** via Alertmanager

</details>

<details>
<summary><b>🔧 Development Docker Stack</b></summary>

**Team development with hot reload:**

```bash
./start-docker.sh dev
# or
make docker-dev
```

**Features:**
- **Hot reload** for development
- **Nginx** reverse proxy
- **Redis** caching
- **Volume mounting** for live code changes

</details>

</details>

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

## 🔌 **Transport Options**

<details>
<summary><b>🔌 Choose Your Transport</b></summary>

<details>
<summary><b>💻 IDE Integration (stdio) - Default</b></summary>

**Works in Cursor, VS Code:**

```bash
./start.sh
```

**Features:**
- **Protocol**: MCP via stdio
- **Setup**: Automatic IDE detection and configuration
- **Use**: Workspace Tools → MCP → MCPlease
- **Performance**: Direct communication, no network overhead

</details>

<details>
<summary><b>🌐 Continue.dev Integration (HTTP)</b></summary>

**Works with Continue.dev, web clients:**

```bash
./start.sh --http
```

**Features:**
- **Protocol**: HTTP REST API
- **Port**: Auto-detects available port (8000+)
- **Use**: Continue.dev extension or direct HTTP calls
- **Access**: From any device on your network

</details>

<details>
<summary><b>⌨️ CLI Direct (stdio)</b></summary>

**Terminal automation and scripts:**

```bash
python mcplease_mcp_server.py --transport stdio
```

**Features:**
- **Protocol**: MCP via stdio
- **Use**: Direct command-line interaction
- **Automation**: Perfect for CI/CD and scripts
- **Integration**: Easy to pipe into other tools

</details>

</details>

## 🔧 **IDE Configuration**

<details>
<summary><b>🔧 Setup Your IDE</b></summary>

<details>
<summary><b>🤖 Automatic Setup (Recommended)</b></summary>

**One command configures everything:**

```bash
python scripts/setup_ide.py
```

This creates MCP configurations for:
- **Cursor**: `~/.cursor/mcp.json`
- **VS Code**: `~/.vscode/mcp.json`  
- **Continue.dev**: `.continue/config.json`

</details>

<details>
<summary><b>✏️ Manual Configuration</b></summary>

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

</details>

</details>

## 💡 **Available Tools**

<details>
<summary><b>🛠️ MCP Tools Overview</b></summary>

MCPlease provides these MCP tools:

**File Operations:**
- **`file/read`** - Read file contents for analysis
- **`file/write`** - Write or modify file content
- **`file/list`** - List files in directory

**Terminal & Code:**
- **`terminal/run`** - Execute terminal commands
- **`codebase/search`** - Search codebase for patterns

**AI-Powered Tools:**
- **`ai/analyze`** - Analyze code using OSS-20B AI
- **`ai/build`** - Generate code using OSS-20B AI

**System Tools:**
- **`health/check`** - Server health and status

</details>

## 📊 **Performance**

<details>
<summary><b>📊 Performance Metrics</b></summary>

**Response Times:**
- **Fallback Mode**: Instant responses
- **AI Mode**: Model-dependent (first call loads model, subsequent calls are fast)

**Resource Usage:**
- **Memory**: Minimal (fallback mode), optimized (AI mode)
- **Setup Time**: ~10 seconds total
- **Context Length**: Unlimited (fallback mode), model-dependent (AI mode)

</details>

## 🏗️ **Architecture**

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

## 🧪 **Development**

<details>
<summary><b>🧪 Development & Testing</b></summary>

<details>
<summary><b>📁 Project Structure</b></summary>

```
mcplease/
├── start.sh                    # Universal startup script
├── mcplease_mcp_server.py      # MCP server with stdio transport
├── mcplease_http_server.py     # HTTP server for Continue.dev
├── scripts/                    # Setup and utility scripts
├── tests/                      # Comprehensive test suite
└── docs/                       # Documentation
```

</details>

<details>
<summary><b>🧪 Running Tests</b></summary>

```bash
# Test all transports
python scripts/test_transports.py

# Run comprehensive test suite
python scripts/run_comprehensive_tests.py

# Run specific test categories
python -m pytest tests/ -v
```

</details>

<details>
<summary><b>🔌 Testing Transports</b></summary>

```bash
# Test stdio transport
python mcplease_mcp_server.py --transport stdio

# Test HTTP transport
python mcplease_http_server.py --port 8000

# Test both transports
python scripts/test_transports.py
```

</details>

</details>

## 🚀 **Production Deployment**

<details>
<summary><b>🚀 Production Setup</b></summary>

<details>
<summary><b>🐳 Docker Deployment</b></summary>

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.production.yml up -d

# Includes HAProxy, monitoring, and health checks
```

</details>

<details>
<summary><b>📊 Monitoring Stack</b></summary>

- **Prometheus** metrics collection
- **Grafana** dashboards
- **Loki** log aggregation
- **Alertmanager** notifications

</details>

</details>

## 🤝 **Contributing**

We welcome contributions! 

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Submit a pull request

## 📝 **License**

This project is licensed under the MIT License.

## 🆘 **Support**

<details>
<summary><b>🆘 Common Issues & Solutions</b></summary>

<details>
<summary><b>🔌 Transport Issues</b></summary>

- **stdio not working**: Run `python scripts/setup_ide.py` and restart IDE
- **HTTP not working**: Check if port is available, try `./start.sh --http`
- **IDE not detecting**: Verify MCP configuration in `~/.cursor/mcp.json`

</details>

<details>
<summary><b>🧠 Model Issues</b></summary>

- **Model not found**: Run `python download_model.py` first
- **Slow responses**: OSS-20B model loads on first use, subsequent calls are fast
- **Memory issues**: Model uses ~13GB RAM, ensure sufficient memory

</details>

</details>

### **Getting Help**
- **Documentation**: Check our documentation files
- **Issues**: Report bugs on GitHub Issues
- **Questions**: Open a GitHub Discussion

## 🙏 **Acknowledgments**

- **MCP Protocol** for the universal server-client communication
- **FastAPI** for the high-performance HTTP server
- **OSS-20B** for the powerful local AI model

---
<div align="center">
**MCPlease** - Made with ❤️ for developers who want universal AI coding assistance
#ForTheLoveOfCode
</div>