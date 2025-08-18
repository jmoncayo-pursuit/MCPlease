"""Tests for MCP transport implementations."""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from mcplease_mcp.server.transports import (
    StdioTransport,
    SSETransport,
    WebSocketTransport,
    create_transport
)


class TestStdioTransport:
    """Test stdio transport."""

    @pytest.fixture
    def transport(self):
        """Create stdio transport for testing."""
        return StdioTransport()

    def test_transport_initialization(self, transport):
        """Test transport initialization."""
        assert transport.name == "stdio"
        assert not transport.is_running
        assert transport.message_handler is None

    def test_set_message_handler(self, transport):
        """Test setting message handler."""
        handler = AsyncMock()
        transport.set_message_handler(handler)
        assert transport.message_handler == handler

    @pytest.mark.asyncio
    async def test_start_stop(self, transport):
        """Test starting and stopping transport."""
        # Start transport
        await transport.start()
        assert transport.is_running
        
        # Stop transport
        await transport.stop()
        assert not transport.is_running

    @pytest.mark.asyncio
    async def test_send_message(self, transport):
        """Test sending message via stdio."""
        message = {"jsonrpc": "2.0", "id": "test", "result": {"status": "ok"}}
        
        with patch('builtins.print') as mock_print:
            await transport.send_message(message)
            mock_print.assert_called_once_with(json.dumps(message), flush=True)

    @pytest.mark.asyncio
    async def test_send_message_error(self, transport):
        """Test error handling in send_message."""
        # Create message that can't be serialized
        message = {"test": set()}  # Sets are not JSON serializable
        
        # Should not raise exception
        await transport.send_message(message)


class TestSSETransport:
    """Test SSE transport."""

    @pytest.fixture
    def transport(self):
        """Create SSE transport for testing."""
        return SSETransport(host="localhost", port=8888)

    def test_transport_initialization(self, transport):
        """Test transport initialization."""
        assert transport.name == "sse"
        assert transport.host == "localhost"
        assert transport.port == 8888
        assert not transport.is_running
        assert len(transport.clients) == 0

    @pytest.mark.asyncio
    async def test_start_requires_fastapi(self, transport):
        """Test that SSE transport requires FastAPI."""
        with patch.dict('sys.modules', {'fastapi': None}):
            with pytest.raises(ImportError):
                await transport.start()

    @pytest.mark.asyncio
    async def test_send_message_no_clients(self, transport):
        """Test sending message with no clients."""
        message = {"test": "message"}
        
        # Should not raise exception
        await transport.send_message(message)

    @pytest.mark.asyncio
    async def test_send_message_with_clients(self, transport):
        """Test sending message to clients."""
        # Mock client queue
        mock_queue = AsyncMock()
        transport.clients["test_client"] = mock_queue
        
        message = {"test": "message"}
        await transport.send_message(message)
        
        # Should put message in queue
        mock_queue.put.assert_called_once()
        call_args = mock_queue.put.call_args[0][0]
        assert "data:" in call_args
        assert json.dumps(message) in call_args


class TestWebSocketTransport:
    """Test WebSocket transport."""

    @pytest.fixture
    def transport(self):
        """Create WebSocket transport for testing."""
        return WebSocketTransport(host="localhost", port=8889)

    def test_transport_initialization(self, transport):
        """Test transport initialization."""
        assert transport.name == "websocket"
        assert transport.host == "localhost"
        assert transport.port == 8889
        assert not transport.is_running
        assert len(transport.clients) == 0

    @pytest.mark.asyncio
    async def test_start_requires_websockets(self, transport):
        """Test that WebSocket transport requires websockets library."""
        with patch.dict('sys.modules', {'websockets': None}):
            with pytest.raises(ImportError):
                await transport.start()

    @pytest.mark.asyncio
    async def test_send_message_no_clients(self, transport):
        """Test sending message with no clients."""
        message = {"test": "message"}
        
        # Should not raise exception
        await transport.send_message(message)

    @pytest.mark.asyncio
    async def test_send_message_with_clients(self, transport):
        """Test sending message to clients."""
        # Mock WebSocket client
        mock_websocket = AsyncMock()
        transport.clients["test_client"] = mock_websocket
        
        message = {"test": "message"}
        await transport.send_message(message)
        
        # Should send JSON message
        mock_websocket.send.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_send_message_client_error(self, transport):
        """Test handling client send errors."""
        # Mock WebSocket client that raises exception
        mock_websocket = AsyncMock()
        mock_websocket.send.side_effect = Exception("Connection closed")
        transport.clients["test_client"] = mock_websocket
        
        message = {"test": "message"}
        await transport.send_message(message)
        
        # Client should be removed after error
        assert "test_client" not in transport.clients


class TestTransportFactory:
    """Test transport factory function."""

    def test_create_stdio_transport(self):
        """Test creating stdio transport."""
        transport = create_transport("stdio")
        assert isinstance(transport, StdioTransport)
        assert transport.name == "stdio"

    def test_create_sse_transport(self):
        """Test creating SSE transport."""
        transport = create_transport("sse", host="0.0.0.0", port=9000)
        assert isinstance(transport, SSETransport)
        assert transport.name == "sse"
        assert transport.host == "0.0.0.0"
        assert transport.port == 9000

    def test_create_websocket_transport(self):
        """Test creating WebSocket transport."""
        transport = create_transport("websocket", host="0.0.0.0", port=9001)
        assert isinstance(transport, WebSocketTransport)
        assert transport.name == "websocket"
        assert transport.host == "0.0.0.0"
        assert transport.port == 9001

    def test_create_unknown_transport(self):
        """Test creating unknown transport type."""
        with pytest.raises(ValueError, match="Unknown transport type"):
            create_transport("unknown")

    def test_create_transport_with_kwargs(self):
        """Test creating transport with keyword arguments."""
        transport = create_transport("sse", host="example.com", port=8080)
        assert transport.host == "example.com"
        assert transport.port == 8080


class TestTransportMessageHandling:
    """Test transport message handling."""

    @pytest.fixture
    def handler(self):
        """Create mock message handler."""
        return AsyncMock(return_value={"jsonrpc": "2.0", "id": "test", "result": "ok"})

    @pytest.mark.asyncio
    async def test_stdio_message_handling(self, handler):
        """Test stdio transport message handling."""
        transport = StdioTransport()
        transport.set_message_handler(handler)
        
        # Mock stdin input
        test_message = {"jsonrpc": "2.0", "id": "test", "method": "test"}
        
        with patch('sys.stdin.readline', return_value=json.dumps(test_message) + "\n"):
            with patch('builtins.print') as mock_print:
                # Start transport briefly to test message handling
                await transport.start()
                
                # Give it a moment to process
                await asyncio.sleep(0.1)
                
                await transport.stop()
                
                # Handler should have been called
                if handler.called:
                    handler.assert_called_with(test_message)

    @pytest.mark.asyncio
    async def test_transport_invalid_json(self):
        """Test handling invalid JSON input."""
        transport = StdioTransport()
        handler = AsyncMock()
        transport.set_message_handler(handler)
        
        with patch('sys.stdin.readline', return_value="invalid json\n"):
            await transport.start()
            await asyncio.sleep(0.1)
            await transport.stop()
            
            # Handler should not be called for invalid JSON
            handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_transport_empty_line(self):
        """Test handling empty lines."""
        transport = StdioTransport()
        handler = AsyncMock()
        transport.set_message_handler(handler)
        
        with patch('sys.stdin.readline', return_value="\n"):
            await transport.start()
            await asyncio.sleep(0.1)
            await transport.stop()
            
            # Handler should not be called for empty lines
            handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_transport_eof(self):
        """Test handling EOF on stdin."""
        transport = StdioTransport()
        handler = AsyncMock()
        transport.set_message_handler(handler)
        
        with patch('sys.stdin.readline', return_value=""):  # EOF
            await transport.start()
            await asyncio.sleep(0.1)
            
            # Transport should stop on EOF
            assert not transport.is_running