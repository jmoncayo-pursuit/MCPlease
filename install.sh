#!/bin/bash
set -e

# MCPlease One-Command Installer
# Usage: curl -sSL https://mcplease.dev/install.sh | bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     MCPlease Installer                      ║"
echo "║                Offline AI Coding Assistant                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    log_error "This installer is designed for macOS. Other platforms not yet supported."
    exit 1
fi

log_success "Running on macOS"

# Check system requirements
log_info "Checking system requirements..."

# Check memory
MEMORY_GB=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
if [ "$MEMORY_GB" -lt 12 ]; then
    log_warning "Only ${MEMORY_GB}GB RAM detected. 16GB+ recommended for optimal performance."
else
    log_success "Memory: ${MEMORY_GB}GB RAM detected"
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    log_success "Python $PYTHON_VERSION found"
else
    log_error "Python 3 not found. Please install Python 3.9+ first."
    log_info "Install Python via Homebrew: brew install python"
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    log_error "Git not found. Please install git first."
    log_info "Install git via Homebrew: brew install git"
    exit 1
fi

log_success "Git found"

# Set installation directory
INSTALL_DIR="$HOME/mcplease"
log_info "Installing to: $INSTALL_DIR"

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    log_info "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    log_info "Cloning MCPlease repository..."
    git clone https://github.com/your-org/mcplease-mvp.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

log_success "Repository ready"

# Make mcplease.py executable
chmod +x mcplease.py

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
    log_success "Virtual environment created"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip

# Install basic requirements first
log_info "Installing basic Python packages..."
pip install psutil requests tqdm

log_success "Basic packages installed"

# Run MCPlease setup
log_info "Running MCPlease setup..."
python mcplease.py --setup

# Create command line alias
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_RC="$HOME/.bash_profile"
fi

if [ -n "$SHELL_RC" ]; then
    # Remove existing mcplease alias
    sed -i '' '/alias mcplease=/d' "$SHELL_RC" 2>/dev/null || true
    
    # Add new alias
    echo "" >> "$SHELL_RC"
    echo "# MCPlease AI Coding Assistant" >> "$SHELL_RC"
    echo "alias mcplease='cd $INSTALL_DIR && source venv/bin/activate && python mcplease.py'" >> "$SHELL_RC"
    
    log_success "Command alias added to $SHELL_RC"
fi

# Create desktop shortcut (optional)
DESKTOP_DIR="$HOME/Desktop"
if [ -d "$DESKTOP_DIR" ]; then
    cat > "$DESKTOP_DIR/MCPlease.command" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
source venv/bin/activate
python mcplease.py --start
EOF
    chmod +x "$DESKTOP_DIR/MCPlease.command"
    log_success "Desktop shortcut created"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  🎉 Installation Complete! 🎉               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Quick Start:"
echo ""
echo "1. Restart your terminal or run:"
echo "   source $SHELL_RC"
echo ""
echo "2. Start MCPlease:"
echo "   mcplease --start"
echo ""
echo "3. Or check status:"
echo "   mcplease --status"
echo ""
echo "📖 Manual Usage:"
echo "   cd $INSTALL_DIR"
echo "   source venv/bin/activate"
echo "   python mcplease.py --start"
echo ""
echo "🔌 VSCode Integration:"
echo "   Install the Continue.dev extension and configure it to use:"
echo "   http://localhost:8000 (when server is running)"
echo ""
echo "💡 Need help? Run: mcplease --help"
echo ""
log_success "MCPlease is ready to use!"