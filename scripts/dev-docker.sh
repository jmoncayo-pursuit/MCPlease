#!/bin/bash
# Development Docker script for MCPlease MCP Server

set -e

# Configuration
IMAGE_NAME="mcplease-mcp-dev"
CONTAINER_NAME="mcplease-mcp-dev"
PORT_SSE=${PORT_SSE:-8000}
PORT_WS=${PORT_WS:-8001}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Function to clean up existing container
cleanup() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo_info "Stopping and removing existing container: $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
        docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
    fi
}

# Function to build development image
build_dev_image() {
    echo_info "Building development image: $IMAGE_NAME"
    docker build \
        --target builder \
        --tag "$IMAGE_NAME" \
        --file Dockerfile \
        .
}

# Function to run development container
run_dev_container() {
    echo_info "Starting development container: $CONTAINER_NAME"
    echo_info "SSE endpoint: http://localhost:$PORT_SSE"
    echo_info "WebSocket endpoint: ws://localhost:$PORT_WS"
    
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "$PORT_SSE:8000" \
        -p "$PORT_WS:8001" \
        -v "$(pwd):/app" \
        -v "mcplease_dev_data:/app/data" \
        -e MCP_LOG_LEVEL=DEBUG \
        -e MCP_DATA_DIR=/app/data \
        -e MCP_ENABLE_TLS=false \
        -e MCP_REQUIRE_AUTH=false \
        -e PYTHONPATH=/app/src \
        --workdir /app \
        "$IMAGE_NAME" \
        uv run python -m mcplease_mcp.main --reload
}

# Function to show logs
show_logs() {
    echo_info "Showing container logs (Ctrl+C to exit):"
    docker logs -f "$CONTAINER_NAME"
}

# Function to run tests in container
run_tests() {
    echo_info "Running tests in development container"
    docker exec "$CONTAINER_NAME" uv run pytest tests/ -v
}

# Function to get container shell
get_shell() {
    echo_info "Opening shell in development container"
    docker exec -it "$CONTAINER_NAME" /bin/bash
}

# Function to check health
check_health() {
    echo_info "Checking container health"
    
    # Wait for container to be ready
    echo_info "Waiting for container to be ready..."
    sleep 5
    
    # Check health endpoint
    if curl -f "http://localhost:$PORT_SSE/health" >/dev/null 2>&1; then
        echo_info "✅ Health check passed"
        curl -s "http://localhost:$PORT_SSE/health" | python -m json.tool
    else
        echo_error "❌ Health check failed"
        echo_info "Container logs:"
        docker logs "$CONTAINER_NAME" --tail 20
        return 1
    fi
}

# Main script logic
case "${1:-start}" in
    "build")
        cleanup
        build_dev_image
        ;;
    "start")
        cleanup
        build_dev_image
        run_dev_container
        check_health
        ;;
    "stop")
        cleanup
        ;;
    "restart")
        cleanup
        build_dev_image
        run_dev_container
        check_health
        ;;
    "logs")
        show_logs
        ;;
    "test")
        run_tests
        ;;
    "shell")
        get_shell
        ;;
    "health")
        check_health
        ;;
    "clean")
        cleanup
        docker rmi "$IMAGE_NAME" >/dev/null 2>&1 || true
        docker volume rm mcplease_dev_data >/dev/null 2>&1 || true
        echo_info "Cleaned up development environment"
        ;;
    *)
        echo "Usage: $0 {build|start|stop|restart|logs|test|shell|health|clean}"
        echo ""
        echo "Commands:"
        echo "  build    - Build development image"
        echo "  start    - Build and start development container (default)"
        echo "  stop     - Stop and remove development container"
        echo "  restart  - Restart development container"
        echo "  logs     - Show container logs"
        echo "  test     - Run tests in container"
        echo "  shell    - Open shell in container"
        echo "  health   - Check container health"
        echo "  clean    - Clean up all development resources"
        exit 1
        ;;
esac