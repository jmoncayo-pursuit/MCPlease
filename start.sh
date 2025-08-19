#!/bin/bash
# MCPlease Universal Startup Script
# Auto-detects environment and starts appropriate transport

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "mcplease_mcp_server.py" ]; then
    print_error "Please run this script from the MCPlease repository root"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.9+ required, found $python_version"
    exit 1
fi

print_success "Python version: $python_version"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv .venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
print_status "Checking dependencies..."
pip install --upgrade pip > /dev/null 2>&1

# Check if required packages are installed
if ! python3 -c "import mcp" 2>/dev/null; then
    print_status "Installing MCP library..."
    pip install mcp
fi

if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    print_status "Installing HTTP transport dependencies..."
    pip install fastapi uvicorn
fi

if ! python3 -c "import transformers, torch" 2>/dev/null; then
    print_warning "AI dependencies not installed. Install with: pip install transformers torch"
fi

print_success "Dependencies ready"

# Auto-detect environment and start appropriate transport
print_status "Detecting environment..."

# Check if we're in Cursor/VS Code (look for MCP config)
if [ -f "$HOME/.cursor/mcp.json" ] || [ -f "$HOME/.vscode/settings.json" ]; then
    print_status "IDE detected - starting stdio transport for MCP"
    print_success "Server starting in stdio mode..."
    print_status "Use Workspace Tools → MCP → MCPlease in your IDE"
    python3 mcplease_mcp_server.py --transport stdio

# Check if we're in Continue.dev or want HTTP
elif [ "$1" = "http" ] || [ "$1" = "--http" ]; then
    print_status "Starting HTTP transport for Continue.dev/web clients"
    
    # Find available port
    port=8000
    while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; do
        port=$((port + 1))
    done
    
    print_success "HTTP server starting on port $port"
    print_status "Continue.dev endpoint: http://127.0.0.1:$port"
    print_status "Press Ctrl+C to stop"
    
    python3 mcplease_http_server.py --port $port

# Default: stdio transport
else
    print_status "Starting stdio transport (default)"
    print_status "Use --http flag for HTTP transport"
    print_status "Press Ctrl+C to stop"
    
    python3 mcplease_mcp_server.py --transport stdio
fi
