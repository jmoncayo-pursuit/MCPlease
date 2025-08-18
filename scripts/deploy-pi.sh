#!/bin/bash
# Raspberry Pi deployment script for MCPlease MCP Server

set -e

# Configuration
PI_USER=${PI_USER:-"pi"}
PI_HOST=${PI_HOST:-"raspberrypi.local"}
DEPLOY_DIR="/home/$PI_USER/mcplease-mcp"
SERVICE_NAME="mcplease-mcp"
NGROK_AUTH_TOKEN=${NGROK_AUTH_TOKEN:-""}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to check if Pi is accessible
check_pi_connection() {
    echo_step "Checking connection to Raspberry Pi"
    
    if ! ping -c 1 "$PI_HOST" >/dev/null 2>&1; then
        echo_error "Cannot reach Raspberry Pi at $PI_HOST"
        echo_info "Please ensure:"
        echo_info "  - Pi is powered on and connected to network"
        echo_info "  - SSH is enabled on the Pi"
        echo_info "  - Hostname/IP is correct: $PI_HOST"
        exit 1
    fi
    
    if ! ssh -o ConnectTimeout=10 "$PI_USER@$PI_HOST" "echo 'Connection test'" >/dev/null 2>&1; then
        echo_error "Cannot SSH to Raspberry Pi"
        echo_info "Please ensure SSH key is set up or password authentication is enabled"
        exit 1
    fi
    
    echo_info "✅ Connection to Pi established"
}

# Function to detect Pi hardware
detect_pi_hardware() {
    echo_step "Detecting Raspberry Pi hardware"
    
    PI_MODEL=$(ssh "$PI_USER@$PI_HOST" "cat /proc/device-tree/model 2>/dev/null || echo 'Unknown'")
    PI_MEMORY=$(ssh "$PI_USER@$PI_HOST" "free -h | grep '^Mem:' | awk '{print \$2}'")
    PI_ARCH=$(ssh "$PI_USER@$PI_HOST" "uname -m")
    
    echo_info "Pi Model: $PI_MODEL"
    echo_info "Memory: $PI_MEMORY"
    echo_info "Architecture: $PI_ARCH"
    
    # Check if it's a supported Pi
    if [[ "$PI_MODEL" == *"Raspberry Pi 4"* ]] || [[ "$PI_MODEL" == *"Raspberry Pi 5"* ]]; then
        echo_info "✅ Supported Raspberry Pi model detected"
    else
        echo_warn "⚠️  Unsupported or unknown Pi model. Deployment may not work optimally."
    fi
}

# Function to install system dependencies
install_system_dependencies() {
    echo_step "Installing system dependencies on Pi"
    
    ssh "$PI_USER@$PI_HOST" << 'EOF'
        # Update system
        sudo apt-get update
        
        # Install required packages
        sudo apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            curl \
            git \
            build-essential \
            libffi-dev \
            libssl-dev \
            pkg-config
        
        # Install Docker if not present
        if ! command -v docker &> /dev/null; then
            echo "Installing Docker..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
        fi
        
        # Install Docker Compose
        if ! command -v docker-compose &> /dev/null; then
            echo "Installing Docker Compose..."
            sudo pip3 install docker-compose
        fi
EOF
    
    echo_info "✅ System dependencies installed"
}

# Function to install ngrok
install_ngrok() {
    echo_step "Installing ngrok on Pi"
    
    ssh "$PI_USER@$PI_HOST" << 'EOF'
        # Check if ngrok is already installed
        if command -v ngrok &> /dev/null; then
            echo "ngrok already installed"
            exit 0
        fi
        
        # Detect architecture
        ARCH=$(uname -m)
        if [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
            NGROK_ARCH="arm64"
        elif [[ "$ARCH" == "armv7l" ]]; then
            NGROK_ARCH="arm"
        else
            echo "Unsupported architecture: $ARCH"
            exit 1
        fi
        
        # Download and install ngrok
        cd /tmp
        wget "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-${NGROK_ARCH}.tgz"
        tar -xzf "ngrok-v3-stable-linux-${NGROK_ARCH}.tgz"
        sudo mv ngrok /usr/local/bin/
        rm "ngrok-v3-stable-linux-${NGROK_ARCH}.tgz"
        
        # Verify installation
        ngrok version
EOF
    
    echo_info "✅ ngrok installed"
}

# Function to deploy application
deploy_application() {
    echo_step "Deploying MCPlease MCP Server to Pi"
    
    # Create deployment directory
    ssh "$PI_USER@$PI_HOST" "mkdir -p $DEPLOY_DIR"
    
    # Copy application files
    echo_info "Copying application files..."
    rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='.pytest_cache' \
        ./ "$PI_USER@$PI_HOST:$DEPLOY_DIR/"
    
    # Set up Python environment and install dependencies
    ssh "$PI_USER@$PI_HOST" << EOF
        cd $DEPLOY_DIR
        
        # Install uv if not present
        if ! command -v uv &> /dev/null; then
            echo "Installing uv package manager..."
            curl -LsSf https://astral.sh/uv/install.sh | sh
            source ~/.bashrc
        fi
        
        # Create virtual environment and install dependencies
        uv sync --frozen
        
        # Make scripts executable
        chmod +x scripts/*.sh
EOF
    
    echo_info "✅ Application deployed"
}

# Function to configure ngrok
configure_ngrok() {
    if [[ -z "$NGROK_AUTH_TOKEN" ]]; then
        echo_warn "No ngrok auth token provided. Skipping ngrok configuration."
        echo_info "To enable remote access, set NGROK_AUTH_TOKEN environment variable"
        return
    fi
    
    echo_step "Configuring ngrok"
    
    ssh "$PI_USER@$PI_HOST" << EOF
        # Configure ngrok auth token
        ngrok config add-authtoken "$NGROK_AUTH_TOKEN"
        
        # Create ngrok config
        mkdir -p ~/.config/ngrok
        cat > ~/.config/ngrok/ngrok.yml << 'NGROK_CONFIG'
version: "2"
authtoken: "$NGROK_AUTH_TOKEN"
region: us
tunnels:
  mcp-sse:
    proto: http
    addr: 8000
    bind_tls: true
  mcp-websocket:
    proto: http
    addr: 8001
    bind_tls: true
NGROK_CONFIG
EOF
    
    echo_info "✅ ngrok configured"
}

# Function to create systemd service
create_systemd_service() {
    echo_step "Creating systemd service"
    
    ssh "$PI_USER@$PI_HOST" << EOF
        # Create service file
        sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << 'SERVICE_FILE'
[Unit]
Description=MCPlease MCP Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=$PI_USER
Group=$PI_USER
WorkingDirectory=$DEPLOY_DIR
Environment=PATH=$DEPLOY_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$DEPLOY_DIR/src
Environment=MCP_DATA_DIR=$DEPLOY_DIR/data
Environment=MCP_LOG_LEVEL=INFO
Environment=MCP_ARM64_OPTIMIZED=true
ExecStart=$DEPLOY_DIR/.venv/bin/python -m mcplease_mcp.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_FILE
        
        # Reload systemd and enable service
        sudo systemctl daemon-reload
        sudo systemctl enable $SERVICE_NAME
EOF
    
    echo_info "✅ Systemd service created"
}

# Function to start services
start_services() {
    echo_step "Starting services"
    
    ssh "$PI_USER@$PI_HOST" << EOF
        # Start MCP server
        sudo systemctl start $SERVICE_NAME
        
        # Check service status
        sleep 5
        if sudo systemctl is-active --quiet $SERVICE_NAME; then
            echo "✅ MCP server started successfully"
        else
            echo "❌ MCP server failed to start"
            sudo systemctl status $SERVICE_NAME
            exit 1
        fi
EOF
    
    echo_info "✅ Services started"
}

# Function to setup ngrok tunnels
setup_tunnels() {
    if [[ -z "$NGROK_AUTH_TOKEN" ]]; then
        echo_info "Skipping tunnel setup (no auth token)"
        return
    fi
    
    echo_step "Setting up ngrok tunnels"
    
    ssh "$PI_USER@$PI_HOST" << 'EOF'
        # Start ngrok tunnels in background
        nohup ngrok start mcp-sse mcp-websocket > /tmp/ngrok.log 2>&1 &
        
        # Wait for tunnels to be ready
        sleep 10
        
        # Get tunnel URLs
        if curl -s http://localhost:4040/api/tunnels | grep -q "public_url"; then
            echo "✅ Ngrok tunnels created successfully"
            echo "Tunnel URLs:"
            curl -s http://localhost:4040/api/tunnels | python3 -c "
import json, sys
data = json.load(sys.stdin)
for tunnel in data.get('tunnels', []):
    print(f\"  {tunnel['name']}: {tunnel['public_url']}\")
"
        else
            echo "❌ Failed to create ngrok tunnels"
            cat /tmp/ngrok.log
        fi
EOF
    
    echo_info "✅ Tunnels configured"
}

# Function to show deployment status
show_status() {
    echo_step "Deployment Status"
    
    ssh "$PI_USER@$PI_HOST" << EOF
        echo "=== System Info ==="
        uname -a
        free -h
        
        echo -e "\n=== Service Status ==="
        sudo systemctl status $SERVICE_NAME --no-pager -l
        
        echo -e "\n=== Service Logs (last 10 lines) ==="
        sudo journalctl -u $SERVICE_NAME -n 10 --no-pager
        
        echo -e "\n=== Network Ports ==="
        ss -tlnp | grep -E ':(8000|8001|4040)'
        
        if command -v ngrok &> /dev/null && [[ -n "$NGROK_AUTH_TOKEN" ]]; then
            echo -e "\n=== Ngrok Tunnels ==="
            curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        print(f\"{tunnel['name']}: {tunnel['public_url']}\")
except:
    print('No active tunnels')
" || echo "Ngrok not running"
        fi
EOF
}

# Main deployment process
main() {
    echo_info "🚀 Starting Raspberry Pi deployment for MCPlease MCP Server"
    echo_info "Target: $PI_USER@$PI_HOST"
    
    check_pi_connection
    detect_pi_hardware
    install_system_dependencies
    install_ngrok
    deploy_application
    configure_ngrok
    create_systemd_service
    start_services
    setup_tunnels
    show_status
    
    echo_info "🎉 Deployment completed successfully!"
    echo_info ""
    echo_info "Next steps:"
    echo_info "  1. Test local access: http://$PI_HOST:8000/health"
    echo_info "  2. Check service logs: ssh $PI_USER@$PI_HOST 'sudo journalctl -u $SERVICE_NAME -f'"
    if [[ -n "$NGROK_AUTH_TOKEN" ]]; then
        echo_info "  3. Use ngrok URLs for remote access (shown above)"
    else
        echo_info "  3. Set NGROK_AUTH_TOKEN to enable remote access"
    fi
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        check_pi_connection
        show_status
        ;;
    "logs")
        check_pi_connection
        ssh "$PI_USER@$PI_HOST" "sudo journalctl -u $SERVICE_NAME -f"
        ;;
    "restart")
        check_pi_connection
        ssh "$PI_USER@$PI_HOST" "sudo systemctl restart $SERVICE_NAME"
        echo_info "Service restarted"
        ;;
    "stop")
        check_pi_connection
        ssh "$PI_USER@$PI_HOST" "sudo systemctl stop $SERVICE_NAME"
        echo_info "Service stopped"
        ;;
    "start")
        check_pi_connection
        ssh "$PI_USER@$PI_HOST" "sudo systemctl start $SERVICE_NAME"
        echo_info "Service started"
        ;;
    *)
        echo "Usage: $0 {deploy|status|logs|restart|stop|start}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment to Raspberry Pi (default)"
        echo "  status   - Show deployment status"
        echo "  logs     - Show service logs"
        echo "  restart  - Restart the service"
        echo "  stop     - Stop the service"
        echo "  start    - Start the service"
        echo ""
        echo "Environment variables:"
        echo "  PI_USER          - Pi username (default: pi)"
        echo "  PI_HOST          - Pi hostname/IP (default: raspberrypi.local)"
        echo "  NGROK_AUTH_TOKEN - Ngrok auth token for remote access"
        exit 1
        ;;
esac