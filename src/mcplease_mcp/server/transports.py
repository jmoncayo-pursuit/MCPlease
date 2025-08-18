"""Transport implementations for MCP server."""

import asyncio
import json
import logging
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    FastMCP = None

logger = logging.getLogger(__name__)


class MCPTransport(ABC):
    """Abstract base class for MCP transports."""
    
    def __init__(self, name: str):
        """Initialize transport.
        
        Args:
            name: Transport name
        """
        self.name = name
        self.is_running = False
        self.message_handler: Optional[Callable[[Dict[str, Any], str], Awaitable[Dict[str, Any]]]] = None
    
    def set_message_handler(self, handler: Callable[[Dict[str, Any], str], Awaitable[Dict[str, Any]]]) -> None:
        """Set the message handler for incoming requests.
        
        Args:
            handler: Async function to handle MCP messages
        """
        self.message_handler = handler
    
    @abstractmethod
    async def start(self) -> None:
        """Start the transport."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the transport."""
        pass
    
    @abstractmethod
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message through the transport.
        
        Args:
            message: Message to send
        """
        pass


class StdioTransport(MCPTransport):
    """Standard input/output transport for local IDE integration."""
    
    def __init__(self):
        """Initialize stdio transport."""
        super().__init__("stdio")
        self._read_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
    
    async def start(self) -> None:
        """Start stdio transport."""
        if self.is_running:
            return
        
        self.is_running = True
        self._read_task = asyncio.create_task(self._read_loop())
        
        logger.info("Started stdio transport")
    
    async def stop(self) -> None:
        """Stop stdio transport."""
        if not self.is_running:
            return
        
        self.is_running = False
        self._shutdown_event.set()
        
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
            self._read_task = None
        
        logger.info("Stopped stdio transport")
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send message to stdout.
        
        Args:
            message: Message to send
        """
        try:
            json_str = json.dumps(message)
            print(json_str, flush=True)
            logger.debug(f"Sent message via stdio: {message.get('method', message.get('id', 'unknown'))}")
        except Exception as e:
            logger.error(f"Failed to send message via stdio: {e}")
    
    async def _read_loop(self) -> None:
        """Read messages from stdin."""
        logger.debug("Started stdio read loop")
        
        while self.is_running and not self._shutdown_event.is_set():
            try:
                # Read line from stdin with timeout
                line = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline),
                    timeout=1.0
                )
                
                if not line:
                    # EOF reached
                    logger.info("EOF reached on stdin, stopping transport")
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse JSON message
                try:
                    message = json.loads(line)
                    logger.debug(f"Received message via stdio: {message.get('method', message.get('id', 'unknown'))}")
                    
                    # Handle message if handler is set
                    if self.message_handler:
                        response = await self.message_handler(message, "127.0.0.1")  # Stdio is always local
                        if response:
                            await self.send_message(response)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON received via stdio: {e}")
                    continue
                
            except asyncio.TimeoutError:
                # Timeout is normal, continue loop
                continue
            except Exception as e:
                logger.error(f"Error in stdio read loop: {e}")
                break
        
        logger.debug("Stdio read loop ended")


class SSETransport(MCPTransport):
    """Server-Sent Events transport for HTTP-based connections."""
    
    def __init__(self, host: str = "localhost", port: int = 8000, ssl_context=None):
        """Initialize SSE transport.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            ssl_context: Optional SSL context for HTTPS
        """
        super().__init__("sse")
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.app = None
        self.server = None
        
        # Client connections
        self.clients: Dict[str, Any] = {}
    
    async def start(self) -> None:
        """Start SSE transport server."""
        if self.is_running:
            return
        
        try:
            # Import FastAPI and related modules
            from fastapi import FastAPI, Request
            from fastapi.responses import StreamingResponse
            from fastapi.middleware.cors import CORSMiddleware
            import uvicorn
            
            self.app = FastAPI(title="MCP Server SSE Transport")
            
            # Add CORS middleware
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            @self.app.get("/mcp/sse")
            async def sse_endpoint(request: Request):
                """SSE endpoint for MCP communication."""
                return StreamingResponse(
                    self._sse_stream(request),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                    }
                )
            
            @self.app.post("/mcp/message")
            async def message_endpoint(request: Request):
                """HTTP endpoint for sending MCP messages."""
                try:
                    message = await request.json()
                    
                    # Extract client IP
                    client_ip = request.client.host if request.client else "127.0.0.1"
                    
                    if self.message_handler:
                        response = await self.message_handler(message, client_ip)
                        return response
                    
                    return {"error": "No message handler configured"}
                    
                except Exception as e:
                    logger.error(f"Error handling HTTP message: {e}")
                    return {"error": str(e)}
            
            # Start server
            config = uvicorn.Config(
                self.app,
                host=self.host,
                port=self.port,
                ssl_keyfile=None,
                ssl_certfile=None,
                ssl_context=self.ssl_context,
                log_level="error"  # Reduce uvicorn logging
            )
            self.server = uvicorn.Server(config)
            
            # Start server in background
            asyncio.create_task(self.server.serve())
            
            self.is_running = True
            protocol = "https" if self.ssl_context else "http"
            logger.info(f"Started SSE transport on {protocol}://{self.host}:{self.port}")
            
        except ImportError:
            logger.error("FastAPI and uvicorn are required for SSE transport")
            raise
        except Exception as e:
            logger.error(f"Failed to start SSE transport: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop SSE transport server."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.server:
            self.server.should_exit = True
            await self.server.shutdown()
            self.server = None
        
        self.clients.clear()
        logger.info("Stopped SSE transport")
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send message to all connected SSE clients.
        
        Args:
            message: Message to send
        """
        if not self.clients:
            return
        
        try:
            json_str = json.dumps(message)
            
            # Send to all connected clients
            for client_id, client_queue in list(self.clients.items()):
                try:
                    await client_queue.put(f"data: {json_str}\n\n")
                except Exception as e:
                    logger.warning(f"Failed to send to SSE client {client_id}: {e}")
                    # Remove disconnected client
                    self.clients.pop(client_id, None)
            
            logger.debug(f"Sent message to {len(self.clients)} SSE clients")
            
        except Exception as e:
            logger.error(f"Failed to send message via SSE: {e}")
    
    async def _sse_stream(self, request):
        """Generate SSE stream for a client."""
        client_id = f"client_{id(request)}"
        client_queue = asyncio.Queue()
        self.clients[client_id] = client_queue
        
        logger.info(f"SSE client connected: {client_id}")
        
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'client_id': client_id})}\n\n"
            
            while self.is_running:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                    yield message
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                
        except Exception as e:
            logger.warning(f"SSE client {client_id} disconnected: {e}")
        finally:
            self.clients.pop(client_id, None)
            logger.info(f"SSE client disconnected: {client_id}")


class WebSocketTransport(MCPTransport):
    """WebSocket transport for real-time remote connections."""
    
    def __init__(self, host: str = "localhost", port: int = 8001, ssl_context=None):
        """Initialize WebSocket transport.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            ssl_context: Optional SSL context for WSS
        """
        super().__init__("websocket")
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.server = None
        
        # Client connections
        self.clients: Dict[str, Any] = {}
    
    async def start(self) -> None:
        """Start WebSocket transport server."""
        if self.is_running:
            return
        
        try:
            import websockets
            
            async def handle_client(websocket, path):
                """Handle WebSocket client connection."""
                client_id = f"ws_client_{id(websocket)}"
                self.clients[client_id] = websocket
                
                # Extract client IP
                client_ip = websocket.remote_address[0] if websocket.remote_address else "127.0.0.1"
                
                logger.info(f"WebSocket client connected: {client_id} from {client_ip}")
                
                try:
                    # Send welcome message
                    await websocket.send(json.dumps({
                        "type": "connected",
                        "client_id": client_id
                    }))
                    
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            logger.debug(f"Received WebSocket message from {client_id}: {data.get('method', data.get('id', 'unknown'))}")
                            
                            if self.message_handler:
                                response = await self.message_handler(data, client_ip)
                                if response:
                                    await websocket.send(json.dumps(response))
                            
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON from WebSocket client {client_id}: {e}")
                        except Exception as e:
                            logger.error(f"Error handling WebSocket message from {client_id}: {e}")
                
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"WebSocket client {client_id} disconnected normally")
                except Exception as e:
                    logger.warning(f"WebSocket client {client_id} disconnected with error: {e}")
                finally:
                    self.clients.pop(client_id, None)
                    logger.info(f"WebSocket client removed: {client_id}")
            
            # Start WebSocket server
            self.server = await websockets.serve(
                handle_client,
                self.host,
                self.port,
                ssl=self.ssl_context
            )
            
            self.is_running = True
            protocol = "wss" if self.ssl_context else "ws"
            logger.info(f"Started WebSocket transport on {protocol}://{self.host}:{self.port}")
            
        except ImportError:
            logger.error("websockets library is required for WebSocket transport")
            raise
        except Exception as e:
            logger.error(f"Failed to start WebSocket transport: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop WebSocket transport server."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        
        # Close all client connections
        for client_id, websocket in list(self.clients.items()):
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket client {client_id}: {e}")
        
        self.clients.clear()
        logger.info("Stopped WebSocket transport")
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send message to all connected WebSocket clients.
        
        Args:
            message: Message to send
        """
        if not self.clients:
            return
        
        try:
            json_str = json.dumps(message)
            
            # Send to all connected clients
            for client_id, websocket in list(self.clients.items()):
                try:
                    await websocket.send(json_str)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket client {client_id}: {e}")
                    # Remove disconnected client
                    self.clients.pop(client_id, None)
            
            logger.debug(f"Sent message to {len(self.clients)} WebSocket clients")
            
        except Exception as e:
            logger.error(f"Failed to send message via WebSocket: {e}")


def create_transport(transport_type: str, **kwargs) -> MCPTransport:
    """Create a transport instance.
    
    Args:
        transport_type: Type of transport ("stdio", "sse", "websocket")
        **kwargs: Transport-specific arguments
        
    Returns:
        Transport instance
        
    Raises:
        ValueError: If transport type is unknown
    """
    if transport_type == "stdio":
        return StdioTransport()
    elif transport_type == "sse":
        return SSETransport(**kwargs)
    elif transport_type == "websocket":
        return WebSocketTransport(**kwargs)
    else:
        raise ValueError(f"Unknown transport type: {transport_type}")