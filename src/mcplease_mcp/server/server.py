"""Main MCP server implementation."""

import asyncio
import logging
import signal
from typing import Dict, Any, Optional, List
from pathlib import Path

from .transports import MCPTransport, create_transport
from ..protocol.handler import MCPProtocolHandler
from ..tools.registry import MCPToolRegistry
from ..context.manager import MCPContextManager
from ..adapters.ai_adapter import MCPAIAdapter
from ..protocol.models import MCPRequest, MCPResponse, MCPError
from ..security.manager import MCPSecurityManager
from ..security.network import NetworkSecurityManager

logger = logging.getLogger(__name__)


class MCPServer:
    """Main MCP server with multiple transport support."""
    
    def __init__(
        self,
        server_name: str = "MCPlease MCP Server",
        transport_configs: Optional[List[Dict[str, Any]]] = None,
        ai_adapter: Optional[MCPAIAdapter] = None,
        context_manager: Optional[MCPContextManager] = None,
        security_manager: Optional[MCPSecurityManager] = None,
        network_security_manager: Optional[NetworkSecurityManager] = None,
        data_dir: Optional[Path] = None
    ):
        """Initialize MCP server.
        
        Args:
            server_name: Name of the MCP server
            transport_configs: List of transport configurations
            ai_adapter: Optional AI adapter for intelligent responses
            context_manager: Optional context manager for session handling
            security_manager: Optional security manager for authentication
            network_security_manager: Optional network security manager
            data_dir: Optional data directory for storage
        """
        self.server_name = server_name
        self.data_dir = data_dir or Path.cwd() / ".mcp_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.ai_adapter = ai_adapter
        self.context_manager = context_manager or MCPContextManager()
        self.security_manager = security_manager or MCPSecurityManager()
        self.network_security_manager = network_security_manager or NetworkSecurityManager()
        self.tool_registry = MCPToolRegistry(ai_adapter=self.ai_adapter)
        self.protocol_handler = MCPProtocolHandler(server_name, self.tool_registry)
        
        # Initialize transports
        self.transports: List[MCPTransport] = []
        self._setup_transports(transport_configs or [{"type": "stdio"}])
        
        # Server state
        self.is_running = False
        self._shutdown_event = asyncio.Event()
        
        logger.info(f"Initialized MCP server: {server_name}")
    
    def _setup_transports(self, transport_configs: List[Dict[str, Any]]) -> None:
        """Set up transports from configuration.
        
        Args:
            transport_configs: List of transport configurations
        """
        for config in transport_configs:
            transport_type = config.pop("type")
            try:
                transport = create_transport(transport_type, **config)
                transport.set_message_handler(self._handle_message)
                self.transports.append(transport)
                logger.info(f"Configured {transport_type} transport")
            except Exception as e:
                logger.error(f"Failed to create {transport_type} transport: {e}")
    
    async def start(self) -> None:
        """Start the MCP server and all transports."""
        if self.is_running:
            logger.warning("Server is already running")
            return
        
        try:
            logger.info("Starting MCP server...")
            
            # Start context manager
            await self.context_manager.start()
            
            # Start security manager
            await self.security_manager.start()
            
            # Start network security manager
            await self.network_security_manager.start()
            
            # Initialize AI adapter if available
            if self.ai_adapter:
                logger.info("Initializing AI adapter...")
                await self.ai_adapter.initialize()
            
            # Start all transports
            for transport in self.transports:
                try:
                    await transport.start()
                    logger.info(f"Started {transport.name} transport")
                except Exception as e:
                    logger.error(f"Failed to start {transport.name} transport: {e}")
            
            self.is_running = True
            
            # Set up signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            logger.info(f"MCP server '{self.server_name}' started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the MCP server and all transports."""
        if not self.is_running:
            return
        
        logger.info("Stopping MCP server...")
        
        self.is_running = False
        self._shutdown_event.set()
        
        # Stop all transports
        for transport in self.transports:
            try:
                await transport.stop()
                logger.info(f"Stopped {transport.name} transport")
            except Exception as e:
                logger.error(f"Error stopping {transport.name} transport: {e}")
        
        # Stop context manager
        try:
            await self.context_manager.stop()
        except Exception as e:
            logger.error(f"Error stopping context manager: {e}")
        
        # Stop security manager
        try:
            await self.security_manager.stop()
        except Exception as e:
            logger.error(f"Error stopping security manager: {e}")
        
        # Stop network security manager
        try:
            await self.network_security_manager.stop()
        except Exception as e:
            logger.error(f"Error stopping network security manager: {e}")
        
        logger.info("MCP server stopped")
    
    async def run(self) -> None:
        """Run the server until shutdown."""
        await self.start()
        
        try:
            # Wait for shutdown signal
            await self._shutdown_event.wait()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            await self.stop()
    
    async def _handle_message(self, message: Dict[str, Any], client_ip: str = "127.0.0.1") -> Optional[Dict[str, Any]]:
        """Handle incoming MCP message.
        
        Args:
            message: Incoming MCP message
            
        Returns:
            Response message or None
        """
        try:
            # Validate network access
            network_allowed, network_reason = await self.network_security_manager.validate_network_access(
                client_ip, 8000, "http"  # Default to HTTP on port 8000
            )
            
            if not network_allowed:
                error_response = MCPResponse(
                    id=message.get("id"),
                    error=MCPError(
                        code=-32003,
                        message="Network access denied",
                        data={"error": network_reason, "client_ip": client_ip}
                    )
                )
                return error_response.to_dict()
            
            # Check rate limiting
            rate_allowed, rate_reason = await self.network_security_manager.check_rate_limit(client_ip)
            if not rate_allowed:
                error_response = MCPResponse(
                    id=message.get("id"),
                    error=MCPError(
                        code=-32004,
                        message="Rate limit exceeded",
                        data={"error": rate_reason, "client_ip": client_ip}
                    )
                )
                return error_response.to_dict()
            
            # Parse message into MCP request
            request = MCPRequest.from_dict(message)
            
            # Extract authentication and session information
            session_id = self._extract_session_id(message)
            credentials = self._extract_credentials(message)
            client_info = self._extract_client_info(message)
            
            # Authenticate request and get/create session
            security_session = None
            if session_id:
                # Try to validate existing session first
                security_session = await self.security_manager.validate_session(session_id)
            
            if not security_session:
                # Create new session through authentication
                security_session = await self.security_manager.authenticate_request(
                    credentials=credentials,
                    client_info=client_info
                )
                
                if not security_session:
                    # Authentication failed
                    error_response = MCPResponse(
                        id=message.get("id"),
                        error=MCPError(
                            code=-32001,
                            message="Authentication required",
                            data={"error": "Invalid or missing credentials"}
                        )
                    )
                    return error_response.to_dict()
            
            # Create or update network user session
            user_agent = client_info.get("user_agent", "")
            network_session = await self.network_security_manager.get_user_session(security_session.session_id)
            
            if not network_session:
                # Create new network session
                network_session = await self.network_security_manager.create_user_session(
                    user_id=security_session.user_info.get("user_id", "unknown"),
                    session_id=security_session.session_id,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    permissions=security_session.permissions
                )
            else:
                # Update existing session activity
                await self.network_security_manager.update_session_activity(security_session.session_id)
            
            # Check permissions for the requested method
            if not await self._check_method_permission(security_session, request.method):
                error_response = MCPResponse(
                    id=message.get("id"),
                    error=MCPError(
                        code=-32002,
                        message="Permission denied",
                        data={"error": f"Insufficient permissions for {request.method}"}
                    )
                )
                return error_response.to_dict()
            
            # Add context handling for requests
            if security_session.session_id:
                # Update context with request information
                await self._update_request_context(security_session.session_id, request)
            
            # Handle request through protocol handler
            response = await self.protocol_handler.handle_request(request)
            
            # Add session information to response
            if response and security_session:
                # Add session info to result metadata
                if response.result and isinstance(response.result, dict):
                    if 'meta' not in response.result:
                        response.result['meta'] = {}
                    response.result['meta']['session_id'] = security_session.session_id
                else:
                    # Create result with meta if no result exists
                    if not response.result:
                        response.result = {}
                    if isinstance(response.result, dict):
                        response.result['meta'] = {'session_id': security_session.session_id}
            
            # Update context with response if applicable
            if security_session.session_id and response:
                await self._update_response_context(security_session.session_id, response)
            
            return response.to_dict() if response else None
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            
            # Return error response
            error_response = MCPResponse(
                id=message.get("id"),
                error=MCPError(
                    code=-32603,
                    message="Internal error",
                    data={"error": str(e)}
                )
            )
            return error_response.to_dict()
    
    def _extract_session_id(self, message: Dict[str, Any]) -> Optional[str]:
        """Extract session ID from message.
        
        Args:
            message: MCP message
            
        Returns:
            Session ID if found
        """
        # Try to extract session ID from various places
        params = message.get("params", {})
        
        # Check for explicit session ID
        if "session_id" in params:
            return params["session_id"]
        
        # Check for client info
        client_info = params.get("clientInfo", {})
        if "session_id" in client_info:
            return client_info["session_id"]
        
        # Use request ID as session ID for now
        request_id = message.get("id")
        if request_id:
            return f"session_{request_id}"
        
        return None
    
    def _extract_credentials(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract authentication credentials from message.
        
        Args:
            message: MCP message
            
        Returns:
            Credentials if found
        """
        # Check for credentials in params
        params = message.get("params", {})
        if "credentials" in params:
            return params["credentials"]
        
        # Check for authorization header style
        if "authorization" in params:
            auth_header = params["authorization"]
            if auth_header.startswith("Bearer "):
                return {"token": auth_header[7:]}
        
        # Check for token directly in params
        if "token" in params:
            return {"token": params["token"]}
        
        return None
    
    def _extract_client_info(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Extract client information from message.
        
        Args:
            message: MCP message
            
        Returns:
            Client information
        """
        params = message.get("params", {})
        client_info = params.get("clientInfo", {})
        
        # Add any additional client metadata
        if "user_agent" in params:
            client_info["user_agent"] = params["user_agent"]
        
        return client_info
    
    async def _check_method_permission(self, security_session, method: str) -> bool:
        """Check if session has permission for the requested method.
        
        Args:
            security_session: Security session
            method: MCP method name
            
        Returns:
            True if permission granted
        """
        # Map MCP methods to permissions
        method_permissions = {
            "initialize": "read",
            "tools/list": "tools/list", 
            "tools/call": "tools/call",
            "resources/list": "read",
            "resources/read": "read",
            "prompts/list": "read",
            "prompts/get": "read"
        }
        
        required_permission = method_permissions.get(method, "read")
        return await self.security_manager.check_permission(
            security_session.session_id, 
            required_permission
        )
    
    async def _update_request_context(self, session_id: str, request: MCPRequest) -> None:
        """Update context with request information.
        
        Args:
            session_id: Session ID
            request: MCP request
        """
        try:
            # Get or create context
            context = await self.context_manager.get_context(session_id)
            if not context:
                context = await self.context_manager.create_context(session_id=session_id)
            
            # Add request to conversation history
            if request.method == "tools/call":
                params = request.params or {}
                tool_name = params.get("name", "unknown")
                await self.context_manager.add_conversation_entry(
                    session_id,
                    "user",
                    f"Called tool: {tool_name}",
                    metadata={"tool": tool_name, "method": request.method}
                )
            
        except Exception as e:
            logger.warning(f"Failed to update request context: {e}")
    
    async def _update_response_context(self, session_id: str, response: MCPResponse) -> None:
        """Update context with response information.
        
        Args:
            session_id: Session ID
            response: MCP response
        """
        try:
            if response.result and not response.error:
                # Add successful response to conversation history
                content = "Tool executed successfully"
                if isinstance(response.result, dict) and "content" in response.result:
                    content_items = response.result["content"]
                    if content_items and len(content_items) > 0:
                        first_item = content_items[0]
                        if first_item.get("type") == "text":
                            content = first_item.get("text", content)[:200] + "..."
                
                await self.context_manager.add_conversation_entry(
                    session_id,
                    "assistant",
                    content,
                    metadata={"response_type": "success"}
                )
            
        except Exception as e:
            logger.warning(f"Failed to update response context: {e}")
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self._shutdown_event.set()
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except ValueError:
            # Signal handling not available (e.g., in threads)
            pass
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get server status information.
        
        Returns:
            Dictionary with server status
        """
        transport_status = {}
        for transport in self.transports:
            transport_status[transport.name] = {
                "running": transport.is_running,
                "clients": len(getattr(transport, "clients", {}))
            }
        
        return {
            "server_name": self.server_name,
            "is_running": self.is_running,
            "data_dir": str(self.data_dir),
            "transports": transport_status,
            "ai_adapter_available": self.ai_adapter is not None,
            "ai_adapter_ready": (
                self.ai_adapter.is_model_ready() 
                if self.ai_adapter else False
            ),
            "tool_count": len(self.tool_registry.get_tool_names()),
            "context_stats": {}  # Will be populated in health_check method
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check.
        
        Returns:
            Health check results
        """
        health = {
            "overall_status": "healthy",
            "server_running": self.is_running,
            "transports": {},
            "components": {},
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Check transport health
        for transport in self.transports:
            health["transports"][transport.name] = {
                "status": "healthy" if transport.is_running else "stopped",
                "clients": len(getattr(transport, "clients", {}))
            }
        
        # Check component health
        try:
            # AI adapter health
            if self.ai_adapter:
                ai_health = await self.ai_adapter.health_check()
                health["components"]["ai_adapter"] = ai_health
            else:
                health["components"]["ai_adapter"] = {"status": "not_configured"}
            
            # Context manager health
            if self.context_manager:
                context_stats = await self.context_manager.get_context_stats()
                health["components"]["context_manager"] = {
                    "status": "healthy",
                    "stats": context_stats
                }
            
            # Tool registry health
            registry_stats = self.tool_registry.get_registry_stats()
            health["components"]["tool_registry"] = {
                "status": "healthy",
                "stats": registry_stats
            }
            
            # Security manager health
            if self.security_manager:
                security_stats = await self.security_manager.get_session_stats()
                health["components"]["security_manager"] = {
                    "status": "healthy",
                    "stats": security_stats
                }
            
            # Network security manager health
            if self.network_security_manager:
                network_stats = await self.network_security_manager.get_security_stats()
                health["components"]["network_security_manager"] = {
                    "status": "healthy",
                    "stats": network_stats
                }
            
        except Exception as e:
            health["overall_status"] = "degraded"
            health["error"] = str(e)
        
        # Determine overall status
        if not self.is_running:
            health["overall_status"] = "stopped"
        elif any(
            comp.get("status") in ["unhealthy", "error"] 
            for comp in health["components"].values()
        ):
            health["overall_status"] = "unhealthy"
        elif any(
            comp.get("status") == "degraded" 
            for comp in health["components"].values()
        ):
            health["overall_status"] = "degraded"
        
        return health