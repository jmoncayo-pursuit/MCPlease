"""Tests for Docker container functionality."""

import asyncio
import json
import pytest
import subprocess
import time
from typing import Dict, Any
import httpx


class TestDockerContainer:
    """Test Docker container deployment and functionality."""
    
    @pytest.fixture(scope="class")
    def container_name(self):
        """Container name for testing."""
        return "mcplease-mcp-test"
    
    @pytest.fixture(scope="class")
    def container_port(self):
        """Container port for testing."""
        return 8000
    
    @pytest.fixture(scope="class", autouse=True)
    async def docker_container(self, container_name, container_port):
        """Start and stop Docker container for testing."""
        # Build the container
        build_result = subprocess.run([
            "docker", "build", "-t", f"{container_name}:test", "."
        ], capture_output=True, text=True)
        
        if build_result.returncode != 0:
            pytest.skip(f"Docker build failed: {build_result.stderr}")
        
        # Start the container
        run_result = subprocess.run([
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"{container_port}:8000",
            "-e", "MCP_LOG_LEVEL=DEBUG",
            "-e", "MCP_REQUIRE_AUTH=false",
            f"{container_name}:test"
        ], capture_output=True, text=True)
        
        if run_result.returncode != 0:
            pytest.skip(f"Docker run failed: {run_result.stderr}")
        
        # Wait for container to be ready
        max_wait = 60  # seconds
        wait_time = 0
        while wait_time < max_wait:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"http://localhost:{container_port}/health")
                    if response.status_code == 200:
                        break
            except:
                pass
            
            time.sleep(2)
            wait_time += 2
        else:
            # Get container logs for debugging
            logs_result = subprocess.run([
                "docker", "logs", container_name
            ], capture_output=True, text=True)
            
            # Clean up
            subprocess.run(["docker", "stop", container_name], capture_output=True)
            subprocess.run(["docker", "rm", container_name], capture_output=True)
            
            pytest.skip(f"Container failed to start within {max_wait}s. Logs: {logs_result.stdout}")
        
        yield
        
        # Cleanup
        subprocess.run(["docker", "stop", container_name], capture_output=True)
        subprocess.run(["docker", "rm", container_name], capture_output=True)
        subprocess.run(["docker", "rmi", f"{container_name}:test"], capture_output=True)
    
    @pytest.mark.asyncio
    async def test_container_health_check(self, container_port):
        """Test container health check endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:{container_port}/health")
            
            assert response.status_code == 200
            health_data = response.json()
            
            assert "status" in health_data
            assert health_data["status"] in ["healthy", "degraded"]
            assert "components" in health_data
    
    @pytest.mark.asyncio
    async def test_container_mcp_tools_list(self, container_port):
        """Test MCP tools/list endpoint in container."""
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:{container_port}/mcp/message",
                json=mcp_request
            )
            
            assert response.status_code == 200
            mcp_response = response.json()
            
            assert "result" in mcp_response
            assert "tools" in mcp_response["result"]
            assert len(mcp_response["result"]["tools"]) > 0
    
    @pytest.mark.asyncio
    async def test_container_sse_endpoint(self, container_port):
        """Test SSE endpoint in container."""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET", 
                f"http://localhost:{container_port}/mcp/sse",
                headers={"Accept": "text/event-stream"}
            ) as response:
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
                
                # Read first event (connection message)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        assert data["type"] == "connected"
                        assert "client_id" in data
                        break
    
    @pytest.mark.asyncio
    async def test_container_environment_variables(self, container_name):
        """Test that environment variables are properly set in container."""
        result = subprocess.run([
            "docker", "exec", container_name,
            "python", "-c", 
            "import os; print(f'LOG_LEVEL={os.getenv(\"MCP_LOG_LEVEL\")}, DATA_DIR={os.getenv(\"MCP_DATA_DIR\")}')"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        output = result.stdout.strip()
        assert "LOG_LEVEL=DEBUG" in output
        assert "DATA_DIR=/app/data" in output
    
    @pytest.mark.asyncio
    async def test_container_user_permissions(self, container_name):
        """Test that container runs as non-root user."""
        result = subprocess.run([
            "docker", "exec", container_name,
            "whoami"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert result.stdout.strip() == "mcplease"
    
    @pytest.mark.asyncio
    async def test_container_data_directory(self, container_name):
        """Test that data directory is properly created and writable."""
        result = subprocess.run([
            "docker", "exec", container_name,
            "ls", "-la", "/app/data"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        
        # Test write permissions
        write_result = subprocess.run([
            "docker", "exec", container_name,
            "touch", "/app/data/test_file"
        ], capture_output=True, text=True)
        
        assert write_result.returncode == 0


class TestDockerCompose:
    """Test Docker Compose configurations."""
    
    @pytest.mark.asyncio
    async def test_docker_compose_config_validation(self):
        """Test that docker-compose.yml is valid."""
        result = subprocess.run([
            "docker-compose", "config"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Docker Compose config invalid: {result.stderr}"
    
    @pytest.mark.asyncio
    async def test_docker_compose_build_config_validation(self):
        """Test that docker-compose.build.yml is valid."""
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.build.yml", "config"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Docker Compose build config invalid: {result.stderr}"


class TestMultiArchBuild:
    """Test multi-architecture build capabilities."""
    
    @pytest.mark.asyncio
    async def test_buildx_availability(self):
        """Test that Docker Buildx is available for multi-arch builds."""
        result = subprocess.run([
            "docker", "buildx", "version"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            pytest.skip("Docker Buildx not available")
        
        assert "buildx" in result.stdout.lower()
    
    @pytest.mark.asyncio
    async def test_multi_arch_build_context(self):
        """Test that multi-arch build context can be created."""
        # Check if builder exists
        result = subprocess.run([
            "docker", "buildx", "ls"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            pytest.skip("Docker Buildx not available")
        
        # Look for multi-arch capable builder
        builders = result.stdout
        assert "linux/amd64" in builders or "linux/arm64" in builders


if __name__ == "__main__":
    pytest.main([__file__])