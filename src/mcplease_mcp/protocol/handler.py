"""MCP protocol handler using FastMCP framework."""

import asyncio
import logging
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

logger = logging.getLogger(__name__)


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
        try:
            params = request.params or {}
            client_info = params.get("clientInfo", {})
            protocol_version = params.get("protocolVersion", "2024-11-05")
            
            logger.info(f"Initialize request from client: {client_info}")
            
            # Validate protocol version
            if not self._is_protocol_version_supported(protocol_version):
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
            
            return MCPResponse(id=request.id, result=result)
            
        except Exception as e:
            logger.error(f"Error handling initialize request: {e}")
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCodes.INTERNAL_ERROR,
                    message="Failed to initialize server",
                    data={"error": str(e)}
                )
            )

    async def handle_tools_list(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP tools/list request.
        
        Args:
            request: MCP tools/list request
            
        Returns:
            MCP response with available tools
        """
        try:
            tools_list = [tool.to_dict() for tool in self.tools.values()]
            
            result = {
                "tools": tools_list
            }
            
            logger.debug(f"Returning {len(tools_list)} tools")
            return MCPResponse(id=request.id, result=result)
            
        except Exception as e:
            logger.error(f"Error handling tools/list request: {e}")
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCodes.INTERNAL_ERROR,
                    message="Failed to list tools",
                    data={"error": str(e)}
                )
            )

    async def handle_tools_call(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP tools/call request.
        
        Args:
            request: MCP tools/call request
            
        Returns:
            MCP response with tool execution result
        """
        try:
            params = request.params or {}
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                return MCPResponse(
                    id=request.id,
                    error=MCPError(
                        code=MCPErrorCodes.INVALID_PARAMS,
                        message="Tool name is required",
                    )
                )
            
            if tool_name not in self.tools:
                return MCPResponse(
                    id=request.id,
                    error=MCPError(
                        code=MCPErrorCodes.METHOD_NOT_FOUND,
                        message=f"Tool '{tool_name}' not found",
                        data={"available_tools": list(self.tools.keys())}
                    )
                )
            
            # Execute tool (will be implemented in tool registry)
            result = await self._execute_tool(tool_name, arguments)
            
            return MCPResponse(id=request.id, result=result)
            
        except Exception as e:
            logger.error(f"Error handling tools/call request: {e}")
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCodes.TOOL_EXECUTION_ERROR,
                    message=f"Tool execution failed: {str(e)}",
                    data={"error": str(e)}
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

    def _is_protocol_version_supported(self, version: str) -> bool:
        """Check if protocol version is supported.
        
        Args:
            version: Protocol version to check
            
        Returns:
            True if version is supported
        """
        supported_versions = ["2024-11-05"]
        return version in supported_versions