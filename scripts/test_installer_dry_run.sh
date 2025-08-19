#!/bin/bash
# MCPlease Installer Dry-Run Test
# Shows what the installer would do without actually installing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                MCPlease Installer Dry-Run Test              ║"
    echo "║              Shows what would happen (no install)           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_status() {
    echo -e "${BLUE}[DRY-RUN]${NC} $1"
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

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS="$NAME"
            VER="$VERSION_ID"
        else
            OS="Linux"
            VER="Unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
        VER=$(sw_vers -productVersion)
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="Windows"
        VER="Unknown"
    else
        OS="Unknown"
        VER="Unknown"
    fi
    
    print_success "Would detect: $OS $VER"
}

# Detect package manager
detect_package_manager() {
    if command -v apt-get >/dev/null 2>&1; then
        PKG_MANAGER="apt"
        PKG_INSTALL="sudo apt-get install -y"
        PKG_UPDATE="sudo apt-get update"
    elif command -v yum >/dev/null 2>&1; then
        PKG_MANAGER="yum"
        PKG_INSTALL="sudo yum install -y"
        PKG_UPDATE="sudo yum update -y"
    elif command -v dnf >/dev/null 2>&1; then
        PKG_MANAGER="dnf"
        PKG_INSTALL="sudo dnf install -y"
        PKG_UPDATE="sudo dnf update -y"
    elif command -v pacman >/dev/null 2>&1; then
        PKG_MANAGER="pacman"
        PKG_INSTALL="sudo pacman -S --noconfirm"
        PKG_UPDATE="sudo pacman -Syu --noconfirm"
    elif command -v brew >/dev/null 2>&1; then
        PKG_MANAGER="brew"
        PKG_INSTALL="brew install"
        PKG_UPDATE="brew update"
    elif command -v choco >/dev/null 2>&1; then
        PKG_MANAGER="chocolatey"
        PKG_INSTALL="choco install -y"
        PKG_UPDATE="choco upgrade all -y"
    else
        PKG_MANAGER="unknown"
        PKG_INSTALL="echo 'Please install manually'"
        PKG_UPDATE="echo 'Please update manually'"
    fi
    
    if [ "$PKG_MANAGER" != "unknown" ]; then
        print_success "Would use package manager: $PKG_MANAGER"
        print_status "Update command: $PKG_UPDATE"
        print_status "Install command: $PKG_INSTALL"
    else
        print_warning "No package manager detected - manual installation required"
    fi
}

# Check Python installation
check_python() {
    print_step "Would check Python installation..."
    
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        PYTHON_CMD="python3"
        print_success "Would find Python $PYTHON_VERSION"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_VERSION=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        PYTHON_CMD="python"
        print_success "Would find Python $PYTHON_VERSION"
    else
        print_error "Would fail: Python not found"
        return 1
    fi
    
    # Check Python version
    if [ "$(printf '%s\n' "3.9" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.9" ]; then
        print_error "Would fail: Python 3.9+ required, found $PYTHON_VERSION"
        return 1
    fi
    
    print_success "Would use Python command: $PYTHON_CMD"
    return 0
}

# Check Docker installation
check_docker() {
    print_step "Would check Docker installation..."
    
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        DOCKER_VERSION=$(docker --version)
        print_success "Would find Docker: $DOCKER_VERSION"
        print_success "Would find Docker daemon: running"
        return 0
    else
        print_warning "Would find: Docker not available or not running"
        print_status "Would offer to install Docker"
        return 1
    fi
}

# Check system requirements
check_system_requirements() {
    print_step "Would check system requirements..."
    
    # Check available disk space
    DISK_SPACE=$(df . | awk 'NR==2 {print $4}')
    DISK_SPACE_GB=$((DISK_SPACE / 1024 / 1024))
    
    if [ $DISK_SPACE_GB -lt 15 ]; then
        print_error "Would fail: Insufficient disk space. Need 15GB+, have ${DISK_SPACE_GB}GB"
        return 1
    else
        print_success "Would find disk space: ${DISK_SPACE_GB}GB available"
    fi
    
    # Check available memory
    if command -v free >/dev/null 2>&1; then
        MEMORY_GB=$(free -g | awk 'NR==2{print $2}')
        if [ $MEMORY_GB -lt 4 ]; then
            print_warning "Would warn: Low memory: ${MEMORY_GB}GB available (4GB+ recommended)"
        else
            print_success "Would find memory: ${MEMORY_GB}GB available"
        fi
    fi
    
    return 0
}

# Show what would be installed
show_installation_plan() {
    print_step "Installation plan (what would happen):"
    echo
    echo "1. System Detection:"
    echo "   • OS: $OS $VER"
    echo "   • Package Manager: $PKG_MANAGER"
    echo "   • Python: $PYTHON_CMD $PYTHON_VERSION"
    echo
    echo "2. Dependencies to Install:"
    if [ "$PKG_MANAGER" != "unknown" ]; then
        case "$OS" in
            "Ubuntu"|"Debian"|"Linux Mint")
                echo "   • python3 python3-pip python3-venv"
                ;;
            "CentOS"|"Red Hat"|"Fedora")
                echo "   • python3 python3-pip python3-venv"
                ;;
            "Arch Linux")
                echo "   • python python-pip python-virtualenv"
                ;;
            "macOS")
                if [ "$PKG_MANAGER" = "brew" ]; then
                    echo "   • python@3.11 (via brew)"
                else
                    echo "   • Python from https://python.org"
                fi
                ;;
            *)
                echo "   • Python 3.9+ manually"
                ;;
        esac
    fi
    
    echo
    echo "3. Python Setup:"
    echo "   • Create virtual environment (.venv)"
    echo "   • Install requirements.txt"
    echo "   • Install MCP, FastAPI, uvicorn, etc."
    echo
    echo "4. Model Download:"
    echo "   • Offer to download OSS-20B (13GB)"
    echo "   • Skip if user declines"
    echo
    echo "5. IDE Configuration:"
    echo "   • Create ~/.cursor/mcp.json"
    echo "   • Create ~/.vscode/mcp.json"
    echo "   • Create .continue/config.json"
    echo
    echo "6. Testing:"
    echo "   • Test MCP library import"
    echo "   • Test server startup"
    echo "   • Verify installation"
}

# Main dry-run function
main() {
    print_header
    
    print_status "Starting MCPlease installer dry-run test..."
    echo
    
    # Detect system
    detect_os
    detect_package_manager
    echo
    
    # Check requirements
    if ! check_system_requirements; then
        print_error "System requirements not met. Installation would fail."
        exit 1
    fi
    
    # Check Python
    if ! check_python; then
        print_error "Python check failed. Installation would fail."
        exit 1
    fi
    
    # Check Docker
    check_docker
    echo
    
    # Show installation plan
    show_installation_plan
    
    echo
    print_success "Dry-run test complete!"
    echo
    echo "💡 To actually install:"
    echo "   • Run: ./install.sh"
    echo "   • Or test in a clean directory first"
    echo
    echo "🧪 To test individual functions:"
    echo "   • Run: make test-installer"
    echo "   • Or: python3 scripts/test_installer.py"
}

# Run dry-run
main "$@"
