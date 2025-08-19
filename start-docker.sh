#!/bin/bash
# MCPlease One-Command Docker Startup
# Auto-detects environment and starts appropriate Docker setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

print_success "Docker is running"

# Check if Docker Compose is available
if ! docker-compose --version > /dev/null 2>&1; then
    print_error "Docker Compose not found. Please install Docker Compose."
    exit 1
fi

print_success "Docker Compose available"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the MCPlease repository root"
    exit 1
fi

# Auto-detect environment and start appropriate Docker setup
print_status "Detecting environment..."

# Check if we want production mode
if [ "$1" = "prod" ] || [ "$1" = "--production" ]; then
    print_status "Starting PRODUCTION Docker stack..."
    
    if [ ! -f "docker-compose.production.yml" ]; then
        print_error "Production compose file not found"
        exit 1
    fi
    
    # Check if models directory exists
    if [ ! -d "models/gpt-oss-20b" ]; then
        print_warning "OSS-20B model not found. Starting without AI model..."
        print_status "To add AI capabilities, run: python download_model.py"
    fi
    
    print_success "Starting production stack with monitoring, load balancing, and HAProxy..."
    print_status "This will start:"
    print_status "  • 2x MCP servers (load balanced)"
    print_status "  • HAProxy load balancer"
    print_status "  • Prometheus monitoring"
    print_status "  • Grafana dashboards"
    print_status "  • Loki log aggregation"
    
    docker-compose -f docker-compose.production.yml up -d
    
    print_success "Production stack started!"
    print_status "Access points:"
    print_status "  • MCP Server: http://localhost:8000"
    print_status "  • HAProxy Stats: http://localhost:8404"
    print_status "  • Grafana: http://localhost:3000"
    print_status "  • Prometheus: http://localhost:9090"
    
elif [ "$1" = "dev" ] || [ "$1" = "--development" ]; then
    print_status "Starting DEVELOPMENT Docker stack..."
    
    print_success "Starting development environment with hot reload..."
    print_status "This will start:"
    print_status "  • MCP server with hot reload"
    print_status "  • Nginx reverse proxy (optional)"
    print_status "  • Redis caching (optional)"
    
    docker-compose --profile dev up -d
    
    print_success "Development stack started!"
    print_status "Access points:"
    print_status "  • MCP Server: http://localhost:8000"
    print_status "  • Nginx: http://localhost:80"
    
else
    # Default: simple single-container setup
    print_status "Starting SIMPLE Docker setup..."
    
    print_success "Starting single MCP server container..."
    print_status "This will start:"
    print_status "  • Single MCP server"
    print_status "  • HTTP transport on port 8000"
    print_status "  • Health checks enabled"
    
    docker-compose up -d mcplease-mcp
    
    print_success "Simple Docker setup started!"
    print_status "Access points:"
    print_status "  • MCP Server: http://localhost:8000"
    print_status "  • Health Check: http://localhost:8000/health"
    print_status "  • Tools: http://localhost:8000/tools"
fi

print_status "Docker containers starting..."
sleep 5

# Show running containers
print_status "Running containers:"
docker-compose ps

print_status ""
print_success "MCPlease Docker setup complete!"
print_status ""
print_status "Next steps:"
print_status "1. Test the server: curl http://localhost:8000/health"
print_status "2. Use in IDE: Configure MCP to connect to localhost:8000"
print_status "3. Use with Continue.dev: Point to http://localhost:8000"
print_status ""
print_status "To stop: docker-compose down"
print_status "To view logs: docker-compose logs -f"
