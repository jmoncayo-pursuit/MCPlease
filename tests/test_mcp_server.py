"""Tests for MCP server."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from mcplease_mcp.server.server import MCPServer
from mcplease_mcp.adapters.ai_adapter import MCPAIAdapter
from mcplease_mcp.context.manager import MCPContextManager
from mcplease_mcp.protocol.models import MCPRequest


class TestMCPServer:
    """Test MCP server functionality."""

    @pytest.fixture
    def mock_ai_adapter(self):
        """Create mock AI adapter."""
        adapter = MagicMock(spec=MCPAIAdapter)
        adapter.initialize = AsyncMock(return_value=True)
        adapter.is_model_ready = MagicMock(return_value=True)
        adapter.health_check = AsyncMock(return_value={"status": "healthy"})
        return adapter

    @pytest.fixture
    def mock_context_manager(self):
        """Create mock context manager."""
        manager = MagicMock(spec=MCPContextManager)
        manager.start = AsyncMock()
        manager.stop = AsyncMock()
        manager.get_context = AsyncMock(return_value=None)
        manager.create_context = AsyncMock()
        manager.add_conversation_entry = AsyncMock()
        manager.get_context_stats = AsyncMock(return_value={"total_contexts": 0})
        return manager

    @pytest.fixture
    def server(self, mock_ai_adapter, mock_context_manager):
        """Create MCP server for testing."""
        return MCPServer(
            server_name="Test MCP Server",
            transport_configs=[{"type": "stdio"}],
            ai_adapter=mock_ai_adapter,
            context_manager=mock_context_manager
        )

    def test_server_initialization(self, server):
        """Test server initialization."""
        assert server.server_name == "Test MCP Server"
        assert len(server.transports) == 1
        assert server.transports[0].name == "stdio"
        assert not server.is_running
        assert server.ai_adapter is not None
        assert server.context_manager is not None
        assert server.tool_registry is not None
        assert server.protocol_handler is not None

    def test_server_initialization_defaults(self):
        """Test server initialization with defaults."""
        server = MCPServer()
        
        assert server.server_name == "MCPlease MCP Server"
        assert len(server.transports) == 1
        assert server.transports[0].name == "stdio"
        assert server.ai_adapter is None
        assert server.context_manager is not None

    def test_server_initialization_multiple_transports(self):
        """Test server initialization with multiple transports."""
        transport_configs = [
            {"type": "stdio"},
            {"type": "sse", "host": "localhost", "port": 8000}
        ]
        
        server = MCPServer(transport_configs=transport_configs)
        
        assert len(server.transports) == 2
        assert server.transports[0].name == "stdio"
        assert server.transports[1].name == "sse"

    def test_server_initialization_invalid_transport(self):
        """Test server initialization with invalid transport."""
        transport_configs = [
            {"type": "invalid_transport"}
        ]
        
        # Should not raise exception, just log error
        server = MCPServer(transport_configs=transport_configs)
        assert len(server.transports) == 0

    @pytest.mark.asyncio
    async def test_server_start_stop(self, server, mock_ai_adapter, mock_context_manager):
        """Test server start and stop."""
        # Mock transport start/stop
        for transport in server.transports:
            transport.start = AsyncMock()
            transport.stop = AsyncMock()
        
        # Start server
        await server.start()
        
        assert server.is_running
        mock_context_manager.start.assert_called_once()
        mock_ai_adapter.initialize.assert_called_once()
        
        for transport in server.transports:
            transport.start.assert_called_once()
        
        # Stop server
        await server.stop()
        
        assert not server.is_running
        mock_context_manager.stop.assert_called_once()
        
        for transport in server.transports:
            transport.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_start_already_running(self, server):
        """Test starting server when already running."""
        server.is_running = True
        
        with patch('mcplease_mcp.server.server.logger') as mock_logger:
            await server.start()
            mock_logger.warning.assert_called_with("Server is already running")

    @pytest.mark.asyncio
    async def test_server_start_transport_failure(self, server):
        """Test server start with transport failure."""
        # Mock transport to fail on start
        server.transports[0].start = AsyncMock(side_effect=Exception("Transport failed"))
        server.transports[0].stop = AsyncMock()
        
        # Should not raise exception
        await server.start()
        assert server.is_running

    @pytest.mark.asyncio
    async def test_handle_message_success(self, server):
        """Test successful message handling."""
        message = {
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"}
        }
        
        response = await server._handle_message(message)
        
        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "test-1"
        assert "result" in response

    @pytest.mark.asyncio
    async def test_handle_message_error(self, server):
        """Test message handling with error."""
        # Invalid message format
        message = {"invalid": "message"}
        
        response = await server._handle_message(message)
        
        assert response is not None
        assert "error" in response
        assert response["error"]["code"] == -32603

    @pytest.mark.asyncio
    async def test_handle_message_with_context(self, server, mock_context_manager):
        """Test message handling with context updates."""
        message = {
            "jsonrpc": "2.0",
            "id": "test-2",
            "method": "tools/call",
            "params": {
                "name": "code_completion",
                "arguments": {"code": "def hello():"}
            }
        }
        
        # Mock context creation
        mock_context = MagicMock()
        mock_context_manager.get_context.return_value = None
        mock_context_manager.create_context.return_value = mock_context
        
        response = await server._handle_message(message)
        
        assert response is not None
        # Should have attempted to update context
        mock_context_manager.add_conversation_entry.assert_called()

    def test_extract_session_id(self, server):
        """Test session ID extraction from messages."""
        # Test explicit session ID
        message1 = {
            "params": {"session_id": "explicit_session"}
        }
        session_id = server._extract_session_id(message1)
        assert session_id == "explicit_session"
        
        # Test client info session ID
        message2 = {
            "params": {"clientInfo": {"session_id": "client_session"}}
        }
        session_id = server._extract_session_id(message2)
        assert session_id == "client_session"
        
        # Test request ID fallback
        message3 = {
            "id": "request_123"
        }
        session_id = server._extract_session_id(message3)
        assert session_id == "session_request_123"
        
        # Test no session ID
        message4 = {}
        session_id = server._extract_session_id(message4)
        assert session_id is None

    @pytest.mark.asyncio
    async def test_update_request_context(self, server, mock_context_manager):
        """Test updating context with request information."""
        request = MCPRequest(
            id="test",
            method="tools/call",
            params={"name": "code_completion"}
        )
        
        # Mock context
        mock_context = MagicMock()
        mock_context_manager.get_context.return_value = mock_context
        
        await server._update_request_context("test_session", request)
        
        mock_context_manager.add_conversation_entry.assert_called_once()
        call_args = mock_context_manager.add_conversation_entry.call_args
        assert call_args[0][0] == "test_session"  # session_id
        assert call_args[0][1] == "user"  # role
        assert "code_completion" in call_args[0][2]  # content

    @pytest.mark.asyncio
    async def test_update_request_context_no_context(self, server, mock_context_manager):
        """Test updating context when context doesn't exist."""
        request = MCPRequest(
            id="test",
            method="tools/call",
            params={"name": "code_completion"}
        )
        
        # Mock no existing context
        mock_context_manager.get_context.return_value = None
        mock_new_context = MagicMock()
        mock_context_manager.create_context.return_value = mock_new_context
        
        await server._update_request_context("test_session", request)
        
        mock_context_manager.create_context.assert_called_once_with(session_id="test_session")
        mock_context_manager.add_conversation_entry.assert_called_once()

    def test_get_server_status(self, server):
        """Test getting server status."""
        # Mock transport clients
        server.transports[0].clients = {"client1": MagicMock()}
        
        status = server.get_server_status()
        
        assert status["server_name"] == "Test MCP Server"
        assert status["is_running"] == False
        assert "transports" in status
        assert "stdio" in status["transports"]
        assert status["transports"]["stdio"]["clients"] == 1
        assert status["ai_adapter_available"] is True
        assert "tool_count" in status

    @pytest.mark.asyncio
    async def test_health_check(self, server, mock_ai_adapter, mock_context_manager):
        """Test server health check."""
        # Mock component health checks
        mock_ai_adapter.health_check.return_value = {"status": "healthy"}
        mock_context_manager.get_context_stats.return_value = {"total_contexts": 5}
        
        health = await server.health_check()
        
        assert "overall_status" in health
        assert "server_running" in health
        assert "transports" in health
        assert "components" in health
        assert "timestamp" in health
        
        assert "ai_adapter" in health["components"]
        assert "context_manager" in health["components"]
        assert "tool_registry" in health["components"]

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_component(self, server, mock_ai_adapter):
        """Test health check with unhealthy component."""
        # Mock unhealthy AI adapter
        mock_ai_adapter.health_check.return_value = {"status": "unhealthy"}
        
        health = await server.health_check()
        
        assert health["overall_status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_error(self, server, mock_ai_adapter):
        """Test health check with component error."""
        # Mock AI adapter error
        mock_ai_adapter.health_check.side_effect = Exception("Health check failed")
        
        health = await server.health_check()
        
        assert health["overall_status"] == "degraded"
        assert "error" in health

    @pytest.mark.asyncio
    async def test_run_server(self, server):
        """Test running server until shutdown."""
        # Mock start and stop
        server.start = AsyncMock()
        server.stop = AsyncMock()
        
        # Set shutdown event immediately to avoid hanging
        server._shutdown_event.set()
        
        await server.run()
        
        server.start.assert_called_once()
        server.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_server_keyboard_interrupt(self, server):
        """Test running server with keyboard interrupt."""
        server.start = AsyncMock()
        server.stop = AsyncMock()
        
        # Mock keyboard interrupt
        async def mock_wait():
            raise KeyboardInterrupt()
        
        server._shutdown_event.wait = mock_wait
        
        await server.run()
        
        server.start.assert_called_once()
        server.stop.assert_called_once()

    def test_setup_signal_handlers(self, server):
        """Test signal handler setup."""
        # Should not raise exception
        server._setup_signal_handlers()
        
        # Test signal handler function
        import signal
        handler = signal.signal(signal.SIGINT, signal.SIG_DFL)  # Reset to default
        
        # Call setup again
        server._setup_signal_handlers()
        
        # Should have set up handlers (if available)
        # Note: This test may not work in all environments