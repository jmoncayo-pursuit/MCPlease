"""MCP protocol handler using FastMCP framework."""

import asyncio
import logging
import structlog
from typing import Any, Dict, List, Optional

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    FastMCP = None

from .models import (
    MCPRequest,
    MCPResponse,
    MCPError,
    MCPTool,
    MCPMethods,
    MCPErrorCodes,
)
from ..utils.error_handler import get_error_handler, error_context
from ..utils.exceptions import MCPProtocolError, ValidationError
from ..utils.logging import get_structured_logger, get_security_logger, get_performance_logger

logger = logging.getLogger(__name__)
structured_logger = get_structured_logger(__name__)
security_logger = get_security_logger()
performance_logger = get_performance_logger()


class MCPProtocolHandler:
    """Handles MCP protocol communication using FastMCP framework."""

    def __init__(self, server_name: str = "MCPlease MCP Server", tool_registry=None):
        """Initialize the MCP protocol handler.
        
        Args:
            server_name: Name of the MCP server
            tool_registry: Optional MCPToolRegistry instance
        """
        self.server_name = server_name
        self.mcp = None
        if FASTMCP_AVAILABLE:
            self.mcp = FastMCP(server_name)
        self.tools: Dict[str, MCPTool] = {}
        self.tool_registry = tool_registry
        self.capabilities = {
            "tools": {},
            "resources": {},
            "prompts": {},
        }
        
        # Initialize FastMCP server if available
        if FASTMCP_AVAILABLE:
            self._setup_fastmcp()
        
        # Set up tool registry if provided
        if tool_registry:
            self.set_tool_registry(tool_registry)
        
        logger.info(f"Initialized MCP protocol handler: {server_name}")

    def _setup_fastmcp(self) -> None:
        """Set up FastMCP server with basic configuration."""
        # FastMCP automatically handles protocol negotiation and basic methods
        # We'll add custom tools and handlers as needed
        pass

    async def handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP initialize request.
        
        Args:
            request: MCP initialize request
            
        Returns:
            MCP response with server capabilities
        """
        start_time = asyncio.get_event_loop().time()
        
        with error_context(
            context={"method": "initialize", "request_id": request.id},
            request_id=str(request.id) if request.id else None
        ):
            try:
                params = request.params or {}
                client_info = params.get("clientInfo", {})
                protocol_version = params.get("protocolVersion", "2024-11-05")
                
                # Log security event for client connection
                security_logger.authentication_attempt(
                    user_id=None,
                    method="mcp_initialize",
                    success=True,
                    details={"client_info": client_info, "protocol_version": protocol_version}
                )
                
                structured_logger.info("MCP initialize request received")
                
                # Validate protocol version
                if not self._is_protocol_version_supported(protocol_version):
                    error = ValidationError(f"Unsupported protocol version: {protocol_version}")
                    handler = get_error_handler()
                    await handler.handle_error(
                        error,
                        context={"protocol_version": protocol_version, "supported": ["2024-11-05"]},
                        request_id=str(request.id) if request.id else None
                    )
                    
                    return MCPResponse(
                        id=request.id,
                        error=MCPError(
                            code=MCPErrorCodes.INVALID_PARAMS,
                            message=f"Unsupported protocol version: {protocol_version}",
                            data={"supported_versions": ["2024-11-05"]}
                        )
                    )
                
                # Return server capabilities
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": self.capabilities,
                    "serverInfo": {
                        "name": self.server_name,
                        "version": "1.0.0",
                        "description": "True MCP Server with local AI model integration"
                    }
                }
                
                # Log performance metrics
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                performance_logger.request_timing(
                    endpoint="initialize",
                    method="MCP",
                    duration_ms=duration_ms,
                    status_code=200
                )
                
                return MCPResponse(id=request.id, result=result)
                
            except Exception as e:
                # Handle error with comprehensive error handler
                handler = get_error_handler()
                handled_error = await handler.handle_error(
                    e,
                    context={"method": "initialize", "params": request.params},
                    request_id=str(request.id) if request.id else None
                )
                
                # Log performance metrics for failed request
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                performance_logger.request_timing(
                    endpoint="initialize",
                    method="MCP",
                    duration_ms=duration_ms,
                    status_code=500
                )
                
                return MCPResponse(
                    id=request.id,
                    error=MCPError(
                        code=MCPErrorCodes.INTERNAL_ERROR,
                        message="Failed to initialize server",
                        data={
                            "error_code": handled_error.error_code,
                            "category": handled_error.category.value,
                            "severity": handled_error.severity.value
                        }
                    )
                )

    async def handle_tools_list(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP tools/list request.
        
        Args:
            request: MCP tools/list request
            
        Returns:
            MCP response with available tools
        """
        start_time = asyncio.get_event_loop().time()
        
        with error_context(
            context={"method": "tools_list", "request_id": request.id},
            request_id=str(request.id) if request.id else None
        ):
            try:
                tools_list = [tool.to_dict() for tool in self.tools.values()]
                
                result = {
                    "tools": tools_list
                }
                
                structured_logger.debug("Tools list request completed")
                
                # Log performance metrics
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                performance_logger.request_timing(
                    endpoint="tools/list",
                    method="MCP",
                    duration_ms=duration_ms,
                    status_code=200
                )
                
                return MCPResponse(id=request.id, result=result)
                
            except Exception as e:
                # Handle error with comprehensive error handler
                handler = get_error_handler()
                handled_error = await handler.handle_error(
                    e,
                    context={"method": "tools_list", "tool_count": len(self.tools)},
                    request_id=str(request.id) if request.id else None
                )
                
                # Log performance metrics for failed request
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                performance_logger.request_timing(
                    endpoint="tools/list",
                    method="MCP",
                    duration_ms=duration_ms,
                    status_code=500
                )
                
                return MCPResponse(
                    id=request.id,
                    error=MCPError(
                        code=MCPErrorCodes.INTERNAL_ERROR,
                        message="Failed to list tools",
                        data={
                            "error_code": handled_error.error_code,
                            "category": handled_error.category.value,
                            "severity": handled_error.severity.value
                        }
                    )
                )

    async def handle_tools_call(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP tools/call request.
        
        Args:
            request: MCP tools/call request
            
        Returns:
            MCP response with tool execution result
        """
        start_time = asyncio.get_event_loop().time()
        
        with error_context(
            context={"method": "tools_call", "request_id": request.id},
            request_id=str(request.id) if request.id else None
        ):
            try:
                params = request.params or {}
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if not tool_name:
                    error = ValidationError("Tool name is required")
                    handler = get_error_handler()
                    await handler.handle_error(
                        error,
                        context={"method": "tools_call", "params": params},
                        request_id=str(request.id) if request.id else None
                    )
                    
                    return MCPResponse(
                        id=request.id,
                        error=MCPError(
                            code=MCPErrorCodes.INVALID_PARAMS,
                            message="Tool name is required",
                        )
                    )
                
                if tool_name not in self.tools:
                    error = ValidationError(f"Tool '{tool_name}' not found")
                    handler = get_error_handler()
                    await handler.handle_error(
                        error,
                        context={"tool_name": tool_name, "available_tools": list(self.tools.keys())},
                        request_id=str(request.id) if request.id else None
                    )
                    
                    return MCPResponse(
                        id=request.id,
                        error=MCPError(
                            code=MCPErrorCodes.METHOD_NOT_FOUND,
                            message=f"Tool '{tool_name}' not found",
                            data={"available_tools": list(self.tools.keys())}
                        )
                    )
                
                structured_logger.info(
                    f"Tool execution started: {tool_name}")
                
                # Execute tool with error handling
                result = await self._execute_tool_with_recovery(tool_name, arguments, request.id)
                
                # Log performance metrics
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                performance_logger.request_timing(
                    endpoint=f"tools/call/{tool_name}",
                    method="MCP",
                    duration_ms=duration_ms,
                    status_code=200
                )
                
                structured_logger.info(
                    f"Tool execution completed: {tool_name} in {duration_ms:.2f}ms")
                
                return MCPResponse(id=request.id, result=result)
                
            except Exception as e:
                # Handle error with comprehensive error handler
                handler = get_error_handler()
                handled_error = await handler.handle_error(
                    e,
                    context={
                        "method": "tools_call",
                        "tool_name": params.get("name") if 'params' in locals() else None,
                        "arguments": params.get("arguments", {}) if 'params' in locals() else {}
                    },
                    request_id=str(request.id) if request.id else None
                )
                
                # Log performance metrics for failed request
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                performance_logger.request_timing(
                    endpoint=f"tools/call/{params.get('name', 'unknown') if 'params' in locals() else 'unknown'}",
                    method="MCP",
                    duration_ms=duration_ms,
                    status_code=500
                )
                
                return MCPResponse(
                    id=request.id,
                    error=MCPError(
                        code=MCPErrorCodes.TOOL_EXECUTION_ERROR,
                        message=f"Tool execution failed: {str(e)}",
                        data={
                            "error_code": handled_error.error_code,
                            "category": handled_error.category.value,
                            "severity": handled_error.severity.value
                        }
                    )
                )

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Route MCP request to appropriate handler.
        
        Args:
            request: MCP request to handle
            
        Returns:
            MCP response
        """
        try:
            method = request.method
            
            if method == MCPMethods.INITIALIZE:
                return await self.handle_initialize(request)
            elif method == MCPMethods.TOOLS_LIST:
                return await self.handle_tools_list(request)
            elif method == MCPMethods.TOOLS_CALL:
                return await self.handle_tools_call(request)
            else:
                return MCPResponse(
                    id=request.id,
                    error=MCPError(
                        code=MCPErrorCodes.METHOD_NOT_FOUND,
                        message=f"Method '{method}' not supported",
                        data={"supported_methods": [
                            MCPMethods.INITIALIZE,
                            MCPMethods.TOOLS_LIST,
                            MCPMethods.TOOLS_CALL,
                        ]}
                    )
                )
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCodes.INTERNAL_ERROR,
                    message="Internal server error",
                    data={"error": str(e)}
                )
            )

    def register_tool(self, tool: MCPTool) -> None:
        """Register a new MCP tool.
        
        Args:
            tool: MCP tool to register
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered MCP tool: {tool.name}")

    def get_available_tools(self) -> List[MCPTool]:
        """Get list of available tools.
        
        Returns:
            List of registered MCP tools
        """
        return list(self.tools.values())

    def get_fastmcp_instance(self) -> FastMCP:
        """Get the FastMCP instance for direct access.
        
        Returns:
            FastMCP instance
        """
        return self.mcp

    def set_tool_registry(self, tool_registry) -> None:
        """Set the tool registry for tool execution.
        
        Args:
            tool_registry: MCPToolRegistry instance
        """
        self.tool_registry = tool_registry
        # Update tools from registry
        self.tools = {name: tool for name, tool in zip(
            tool_registry.get_tool_names(),
            tool_registry.get_available_tools()
        )}
        logger.info(f"Updated tools from registry: {len(self.tools)} tools")

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool using the tool registry.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if hasattr(self, 'tool_registry') and self.tool_registry:
            return await self.tool_registry.execute_tool(tool_name, arguments)
        else:
            # Fallback for when no tool registry is set
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Tool '{tool_name}' executed with arguments: {arguments} (no registry)"
                    }
                ]
            }
    
    async def _execute_tool_with_recovery(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any], 
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a tool with comprehensive error handling and recovery.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            request_id: Request ID for tracking
            
        Returns:
            Tool execution result
        """
        error_handler = get_error_handler()
        
        try:
            # First attempt: normal execution
            return await self._execute_tool(tool_name, arguments)
            
        except Exception as e:
            # Handle error and attempt recovery
            error_context = await error_handler.handle_error(
                e,
                context={
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "execution_attempt": 1
                },
                request_id=request_id,
                attempt_recovery=True
            )
            
            # If recovery was successful, try again
            if error_context.recovery_successful:
                try:
                    structured_logger.info(
                        "Retrying tool execution after recovery",
                        tool_name=tool_name,
                        error_code=error_context.error_code
                    )
                    return await self._execute_tool(tool_name, arguments)
                    
                except Exception as retry_error:
                    # Second attempt failed, handle gracefully
                    await error_handler.handle_error(
                        retry_error,
                        context={
                            "tool_name": tool_name,
                            "arguments": arguments,
                            "execution_attempt": 2,
                            "original_error": error_context.error_code
                        },
                        request_id=request_id,
                        attempt_recovery=False
                    )
                    
                    # Return graceful degradation response
                    return self._get_fallback_response(tool_name, arguments, error_context)
            else:
                # Recovery failed, return graceful degradation response
                return self._get_fallback_response(tool_name, arguments, error_context)
    
    def _get_fallback_response(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any], 
        error_context
    ) -> Dict[str, Any]:
        """Get a fallback response when tool execution fails.
        
        Args:
            tool_name: Name of the failed tool
            arguments: Tool arguments
            error_context: Error context from the failure
            
        Returns:
            Fallback response
        """
        fallback_messages = {
            "code_completion": "I apologize, but I'm currently unable to provide code completion. Please try again later or check your code manually.",
            "code_explanation": "I'm unable to provide a detailed code explanation at the moment. Please refer to documentation or try again later.",
            "debug_assistance": "I cannot provide debugging assistance right now. Please check error logs and documentation for troubleshooting steps."
        }
        
        fallback_message = fallback_messages.get(
            tool_name,
            f"The {tool_name} tool is temporarily unavailable. Please try again later."
        )
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": fallback_message
                }
            ],
            "isError": True,
            "metadata": {
                "error_code": error_context.error_code,
                "fallback_used": True,
                "tool_name": tool_name
            }
        }

    def _is_protocol_version_supported(self, version: str) -> bool:
        """Check if protocol version is supported.
        
        Args:
            version: Protocol version to check
            
        Returns:
            True if version is supported
        """
        supported_versions = ["2024-11-05"]
        return version in supported_versions