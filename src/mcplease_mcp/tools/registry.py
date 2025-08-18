"""MCP tool registry for managing AI-powered tools."""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    FastMCP = None

from ..protocol.models import MCPTool
from .ai_tools import (
    create_ai_tools,
    code_completion_tool,
    code_explanation_tool,
    debug_assistance_tool,
    set_ai_adapter,
)
from ..adapters.ai_adapter import MCPAIAdapter

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    """Registry for managing MCP tools and their execution."""
    
    def __init__(self, mcp_instance: Optional[FastMCP] = None, ai_adapter: Optional[MCPAIAdapter] = None):
        """Initialize the tool registry.
        
        Args:
            mcp_instance: Optional FastMCP instance for decorator-based tools
            ai_adapter: Optional AI adapter for intelligent tool execution
        """
        self.mcp_instance = mcp_instance
        self.ai_adapter = ai_adapter
        self.tools: Dict[str, MCPTool] = {}
        self.tool_executors: Dict[str, Callable] = {}
        
        # Set up AI adapter for tools
        if ai_adapter:
            set_ai_adapter(ai_adapter)
            logger.info("AI adapter configured for tools")
        
        # Register default AI tools
        self._register_default_tools()
        
        logger.info(f"Initialized MCP tool registry with {len(self.tools)} tools")
    
    def _register_default_tools(self) -> None:
        """Register default AI-powered tools."""
        # Create tool definitions
        ai_tools = create_ai_tools(self.mcp_instance)
        
        # Register tools and their executors
        for tool_name, tool in ai_tools.items():
            self.tools[tool_name] = tool
            
            # Map tool names to executor functions
            if tool_name == "code_completion":
                self.tool_executors[tool_name] = code_completion_tool
            elif tool_name == "code_explanation":
                self.tool_executors[tool_name] = code_explanation_tool
            elif tool_name == "debug_assistance":
                self.tool_executors[tool_name] = debug_assistance_tool
        
        logger.info(f"Registered {len(ai_tools)} default AI tools")
    
    def register_tool(self, tool: MCPTool, executor: Callable) -> None:
        """Register a custom tool with its executor.
        
        Args:
            tool: MCP tool definition
            executor: Function to execute the tool
        """
        self.tools[tool.name] = tool
        self.tool_executors[tool.name] = executor
        logger.info(f"Registered custom tool: {tool.name}")
    
    def get_available_tools(self) -> List[MCPTool]:
        """Get list of all available tools.
        
        Returns:
            List of registered MCP tools
        """
        return list(self.tools.values())
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get a specific tool by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            MCPTool instance or None if not found
        """
        return self.tools.get(tool_name)
    
    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is registered.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if tool is registered
        """
        return tool_name in self.tools
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with the given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result in MCP format
            
        Raises:
            ValueError: If tool is not found
            Exception: If tool execution fails
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        if tool_name not in self.tool_executors:
            raise ValueError(f"No executor found for tool '{tool_name}'")
        
        try:
            logger.debug(f"Executing tool '{tool_name}' with arguments: {arguments}")
            
            # Get the executor function
            executor = self.tool_executors[tool_name]
            
            # Execute the tool (handle both sync and async executors)
            if asyncio.iscoroutinefunction(executor):
                result = await executor(**arguments)
            else:
                result = executor(**arguments)
            
            # Ensure result is in proper MCP format
            if not isinstance(result, dict) or "content" not in result:
                # Wrap simple string results
                if isinstance(result, str):
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ]
                    }
                else:
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": str(result)
                            }
                        ]
                    }
            
            logger.debug(f"Tool '{tool_name}' executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            raise
    
    def get_tool_list(self) -> List[Dict[str, Any]]:
        """Get formatted list of available tools for MCP tools/list response.
        
        Returns:
            List of tool dictionaries in MCP format
        """
        return [tool.to_dict() for tool in self.tools.values()]
    
    def get_tool_names(self) -> List[str]:
        """Get list of all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool from the registry.
        
        Args:
            tool_name: Name of the tool to remove
            
        Returns:
            True if tool was removed, False if not found
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            if tool_name in self.tool_executors:
                del self.tool_executors[tool_name]
            logger.info(f"Removed tool: {tool_name}")
            return True
        return False
    
    def clear_tools(self) -> None:
        """Clear all registered tools."""
        self.tools.clear()
        self.tool_executors.clear()
        logger.info("Cleared all tools from registry")
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the tool registry.
        
        Returns:
            Dictionary with registry statistics
        """
        return {
            "total_tools": len(self.tools),
            "tool_names": list(self.tools.keys()),
            "has_fastmcp": FASTMCP_AVAILABLE and self.mcp_instance is not None,
            "fastmcp_available": FASTMCP_AVAILABLE,
            "has_ai_adapter": self.ai_adapter is not None,
            "ai_adapter_status": self.ai_adapter.get_model_status() if self.ai_adapter else None
        }