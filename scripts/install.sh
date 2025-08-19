#!/bin/bash
# MCPlease MCP Server - uv-based Installation Wrapper

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 MCPlease MCP Server - uv-based Installation"
echo "=============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    echo "   Please install Python 3.9+ and try again"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.9"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    echo "❌ Python $PYTHON_VERSION found, but Python 3.9+ is required"
    echo "   Please upgrade Python and try again"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION found"

# Run the uv-based installer
cd "$PROJECT_ROOT"
echo "Starting uv-based installation..."
python3 scripts/install_uv.py "$@"