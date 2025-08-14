"""MCP tool registration and management."""

from typing import Dict, Any, List
from .protocol import MCPTool, MCPProtocolHandler
import logging

logger = logging.getLogger(__name__)


class MCPToolManager:
    """Manages MCP tool registration and discovery."""
    
    def __init__(self, protocol_handler: MCPProtocolHandler):
        self.protocol_handler = protocol_handler
        self._register_default_tools()
    
    def _register_default_tools(self) -> None:
        """Register default coding assistance tools."""
        
        # Code completion tool
        completion_tool = MCPTool(
            name="code_completion",
            description="Provides code completion suggestions",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Current code context"},
                    "language": {"type": "string", "description": "Programming language"},
                    "cursor_position": {"type": "integer", "description": "Cursor position in code"}
                },
                "required": ["code", "language"]
            }
        )
        
        # Code explanation tool
        explanation_tool = MCPTool(
            name="code_explanation",
            description="Explains code functionality and purpose",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to explain"},
                    "language": {"type": "string", "description": "Programming language"},
                    "detail_level": {"type": "string", "enum": ["brief", "detailed"], "default": "brief"}
                },
                "required": ["code", "language"]
            }
        )
        
        # Debugging assistance tool
        debug_tool = MCPTool(
            name="debug_assistance",
            description="Provides debugging help and error analysis",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code with potential issues"},
                    "error_message": {"type": "string", "description": "Error message if available"},
                    "language": {"type": "string", "description": "Programming language"}
                },
                "required": ["code", "language"]
            }
        )
        
        # Register all tools
        for tool in [completion_tool, explanation_tool, debug_tool]:
            self.protocol_handler.register_tool(tool)
    
    def register_custom_tool(self, name: str, description: str, parameters: Dict[str, Any]) -> None:
        """Register a custom tool."""
        tool = MCPTool(
            name=name,
            description=description,
            parameters=parameters
        )
        self.protocol_handler.register_tool(tool)
    
    def get_tool_list(self) -> List[Dict[str, Any]]:
        """Get formatted list of available tools."""
        tools = self.protocol_handler.get_available_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in tools
        ]