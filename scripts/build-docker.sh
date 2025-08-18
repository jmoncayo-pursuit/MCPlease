#!/bin/bash
# Multi-architecture Docker build script for MCPlease MCP Server

set -e

# Configuration
IMAGE_NAME="mcplease/mcp-server"
VERSION=${VERSION:-"latest"}
PLATFORMS="linux/amd64,linux/arm64"

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

# Check if Docker Buildx is available
if ! docker buildx version >/dev/null 2>&1; then
    echo_error "Docker Buildx is required for multi-architecture builds"
    exit 1
fi

# Create builder if it doesn't exist
BUILDER_NAME="mcplease-builder"
if ! docker buildx ls | grep -q "$BUILDER_NAME"; then
    echo_info "Creating multi-architecture builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --bootstrap
fi

# Use the builder
docker buildx use "$BUILDER_NAME"

# Build and push multi-architecture image
echo_info "Building multi-architecture image: $IMAGE_NAME:$VERSION"
echo_info "Platforms: $PLATFORMS"

docker buildx build \
    --platform "$PLATFORMS" \
    --tag "$IMAGE_NAME:$VERSION" \
    --tag "$IMAGE_NAME:latest" \
    --push \
    --file Dockerfile \
    --target production \
    .

echo_info "Multi-architecture build completed successfully!"

# Build ARM64 specific image for Raspberry Pi
echo_info "Building ARM64-specific image for Raspberry Pi"
docker buildx build \
    --platform linux/arm64 \
    --tag "$IMAGE_NAME:arm64" \
    --tag "$IMAGE_NAME:pi" \
    --push \
    --file Dockerfile.arm64 \
    --target production \
    .

echo_info "ARM64 build completed successfully!"

# Verify images
echo_info "Verifying built images:"
docker buildx imagetools inspect "$IMAGE_NAME:$VERSION"
docker buildx imagetools inspect "$IMAGE_NAME:arm64"

echo_info "Build process completed successfully!"
echo_info "Images available:"
echo_info "  - $IMAGE_NAME:$VERSION (multi-arch)"
echo_info "  - $IMAGE_NAME:latest (multi-arch)"
echo_info "  - $IMAGE_NAME:arm64 (ARM64 only)"
echo_info "  - $IMAGE_NAME:pi (ARM64 only)"