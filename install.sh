#!/bin/bash

# MCPlease MCP Server Installation Script
# This script sets up the MCPlease environment using uv package manager

set -e

echo "🚀 MCPlease MCP Server Installation Starting..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.11+ and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ Python $REQUIRED_VERSION+ is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Check if uv is available, if not use the Python installer
if command -v uv &> /dev/null; then
    echo "✅ uv package manager detected"
    echo "🚀 Running uv-based installation..."
    uv run python scripts/install_uv.py "$@"
else
    echo "📦 uv not found, using Python installer..."
    python3 scripts/install_uv.py "$@"
fi

echo ""
echo "🎉 MCPlease installation completed!"
echo ""
echo "To start the server:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  start_uv.bat"
else
    echo "  ./start_uv.sh"
fi