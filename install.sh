#!/bin/bash
# MCPlease Universal Installer
# Auto-detects system and provides easiest installation path

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
    echo "║                    MCPlease Universal Installer              ║"
    echo "║              AI Coding Assistant for Any System             ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

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
    
    print_success "Detected: $OS $VER"
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
        print_success "Package manager: $PKG_MANAGER"
    else
        print_warning "No package manager detected - manual installation required"
    fi
}

# Check Python installation
check_python() {
    print_step "Checking Python installation..."
    
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        PYTHON_CMD="python3"
        print_success "Python $PYTHON_VERSION found"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_VERSION=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        PYTHON_CMD="python"
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python not found"
        return 1
    fi
    
    # Check Python version
    if [ "$(printf '%s\n' "3.9" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.9" ]; then
        print_error "Python 3.9+ required, found $PYTHON_VERSION"
        return 1
    fi
    
    print_success "Python version $PYTHON_VERSION is compatible"
    return 0
}

# Install Python if needed
install_python() {
    print_step "Installing Python..."
    
    case "$OS" in
        "Ubuntu"|"Debian"|"Linux Mint")
            $PKG_UPDATE
            $PKG_INSTALL python3 python3-pip python3-venv
            ;;
        "CentOS"|"Red Hat"|"Fedora")
            $PKG_UPDATE
            $PKG_INSTALL python3 python3-pip python3-venv
            ;;
        "Arch Linux")
            $PKG_UPDATE
            $PKG_INSTALL python python-pip python-virtualenv
            ;;
        "macOS")
            if [ "$PKG_MANAGER" = "brew" ]; then
                $PKG_INSTALL python@3.11
            else
                print_warning "Please install Python from https://python.org"
            fi
            ;;
        "Windows")
            print_warning "Please install Python from https://python.org"
            ;;
        *)
            print_warning "Please install Python 3.9+ manually"
            ;;
    esac
}

# Check Docker installation
check_docker() {
    print_step "Checking Docker installation..."
    
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        DOCKER_VERSION=$(docker --version)
        print_success "Docker found: $DOCKER_VERSION"
        return 0
    else
        print_warning "Docker not found or not running"
        return 1
    fi
}

# Install Docker if needed
install_docker() {
    print_step "Installing Docker..."
    
    case "$OS" in
        "Ubuntu"|"Debian"|"Linux Mint")
            $PKG_UPDATE
            $PKG_INSTALL docker.io docker-compose
            sudo usermod -aG docker $USER
            print_warning "Please log out and back in for Docker group changes to take effect"
            ;;
        "CentOS"|"Red Hat"|"Fedora")
            $PKG_UPDATE
            $PKG_INSTALL docker docker-compose
            sudo systemctl enable docker
            sudo systemctl start docker
            sudo usermod -aG docker $USER
            ;;
        "Arch Linux")
            $PKG_UPDATE
            $PKG_INSTALL docker docker-compose
            sudo systemctl enable docker
            sudo systemctl start docker
            sudo usermod -aG docker $USER
            ;;
        "macOS")
            if [ "$PKG_MANAGER" = "brew" ]; then
                $PKG_INSTALL docker docker-compose
                print_warning "Please start Docker Desktop manually"
            else
                print_warning "Please install Docker Desktop from https://docker.com"
            fi
            ;;
        "Windows")
            print_warning "Please install Docker Desktop from https://docker.com"
            ;;
        *)
            print_warning "Please install Docker manually"
            ;;
    esac
}

# Check system requirements
check_system_requirements() {
    print_step "Checking system requirements..."
    
    # Check available disk space
    DISK_SPACE=$(df . | awk 'NR==2 {print $4}')
    DISK_SPACE_GB=$((DISK_SPACE / 1024 / 1024))
    
    if [ $DISK_SPACE_GB -lt 15 ]; then
        print_error "Insufficient disk space. Need 15GB+, have ${DISK_SPACE_GB}GB"
        return 1
    else
        print_success "Disk space: ${DISK_SPACE_GB}GB available"
    fi
    
    # Check available memory
    if command -v free >/dev/null 2>&1; then
        MEMORY_GB=$(free -g | awk 'NR==2{print $2}')
        if [ $MEMORY_GB -lt 4 ]; then
            print_warning "Low memory: ${MEMORY_GB}GB available (4GB+ recommended)"
        else
            print_success "Memory: ${MEMORY_GB}GB available"
        fi
    fi
    
    return 0
}

# Install dependencies
install_dependencies() {
    print_step "Installing Python dependencies..."
    
    # Create virtual environment
    if [ ! -d ".venv" ]; then
        $PYTHON_CMD -m venv .venv
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_warning "requirements.txt not found"
    fi
}

# Download model
download_model() {
    print_step "Checking OSS-20B model..."
    
    if [ ! -d "models/gpt-oss-20b" ]; then
        print_warning "OSS-20B model not found"
        read -p "Download OSS-20B model now? (13GB, y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Downloading OSS-20B model (this may take 10-30 minutes)..."
            $PYTHON_CMD download_model.py
        else
            print_warning "Model download skipped. AI features will use fallback responses."
        fi
    else
        print_success "OSS-20B model found"
    fi
}

# Setup IDE configurations
setup_ide() {
    print_step "Setting up IDE configurations..."
    
    if [ -f "scripts/setup_ide.py" ]; then
        $PYTHON_CMD scripts/setup_ide.py
        print_success "IDE configurations created"
    else
        print_warning "IDE setup script not found"
    fi
}

# Test installation
test_installation() {
    print_step "Testing installation..."
    
    # Test Python imports
    if $PYTHON_CMD -c "import mcp" 2>/dev/null; then
        print_success "MCP library import successful"
    else
        print_error "MCP library import failed"
        return 1
    fi
    
    # Test server startup
    if timeout 10s $PYTHON_CMD mcplease_mcp_server.py --help >/dev/null 2>&1; then
        print_success "MCP server startup test successful"
    else
        print_error "MCP server startup test failed"
        return 1
    fi
    
    return 0
}

# Show next steps
show_next_steps() {
    print_success "Installation complete!"
    echo
    echo -e "${CYAN}🎯 Next Steps:${NC}"
    echo
    echo "1. Start MCPlease:"
    echo "   • Local: ./start.sh"
    echo "   • Docker: ./start-docker.sh"
    echo
    echo "2. Use in your IDE:"
    echo "   • Cursor/VS Code: Look for MCPlease in Workspace Tools → MCP"
    echo "   • Continue.dev: Use ./start-docker.sh --http"
    echo
    echo "3. Test everything:"
    echo "   • python scripts/test_transports.py"
    echo
    echo "4. Get help:"
    echo "   • README.md for detailed instructions"
    echo "   • GitHub Issues for support"
    echo
}

# Main installation flow
main() {
    print_header
    
    print_status "Starting MCPlease installation..."
    echo
    
    # Detect system
    detect_os
    detect_package_manager
    echo
    
    # Check requirements
    if ! check_system_requirements; then
        print_error "System requirements not met. Installation cannot continue."
        exit 1
    fi
    
    # Check/install Python
    if ! check_python; then
        if [ "$PKG_MANAGER" != "unknown" ]; then
            install_python
            if ! check_python; then
                print_error "Python installation failed"
                exit 1
            fi
        else
            print_error "Please install Python 3.9+ manually and run installer again"
            exit 1
        fi
    fi
    
    # Check/install Docker (optional)
    if ! check_docker; then
        if [ "$PKG_MANAGER" != "unknown" ]; then
            read -p "Install Docker? (optional, y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                install_docker
            fi
        fi
    fi
    
    echo
    
    # Install dependencies
    install_dependencies
    
    # Download model
    download_model
    
    # Setup IDE
    setup_ide
    
    echo
    
    # Test installation
    if test_installation; then
        show_next_steps
    else
        print_error "Installation test failed. Please check the errors above."
        exit 1
    fi
}

# Run installer
main "$@"