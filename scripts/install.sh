#!/bin/bash
# Simple shell wrapper for dependency installation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 MCPlease Dependency Installer"
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

# Run the Python installer
cd "$PROJECT_ROOT"
python3 scripts/install_dependencies.py "$@"