"""AI-powered MCP tools using FastMCP decorators."""

import logging
from typing import Dict, Any, Optional

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    FastMCP = None

from ..protocol.models import MCPTool
from ..adapters.ai_adapter import MCPAIAdapter

logger = logging.getLogger(__name__)


def create_ai_tools(mcp_instance: Optional[FastMCP] = None) -> Dict[str, MCPTool]:
    """Create AI-powered MCP tools.
    
    Args:
        mcp_instance: FastMCP instance to register tools with
        
    Returns:
        Dictionary of tool name to MCPTool instances
    """
    tools = {}
    
    # Create tool definitions
    code_completion = MCPTool(
        name="code_completion",
        description="Provides intelligent code completion suggestions based on context",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Current code context around cursor position"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (e.g., python, javascript, java)"
                },
                "cursor_position": {
                    "type": "integer",
                    "description": "Cursor position in the code (optional)",
                    "minimum": 0
                },
                "max_completions": {
                    "type": "integer",
                    "description": "Maximum number of completion suggestions",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 3
                }
            },
            "required": ["code", "language"]
        }
    )
    
    code_explanation = MCPTool(
        name="code_explanation",
        description="Explains code functionality, purpose, and provides technical analysis",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Code to explain and analyze"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language of the code"
                },
                "detail_level": {
                    "type": "string",
                    "enum": ["brief", "detailed", "comprehensive"],
                    "description": "Level of detail for the explanation",
                    "default": "detailed"
                },
                "focus": {
                    "type": "string",
                    "enum": ["functionality", "performance", "security", "best_practices"],
                    "description": "Specific aspect to focus on (optional)"
                }
            },
            "required": ["code", "language"]
        }
    )
    
    debug_assistance = MCPTool(
        name="debug_assistance",
        description="Provides debugging help, error analysis, and troubleshooting suggestions",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Code that has issues or needs debugging"
                },
                "error_message": {
                    "type": "string",
                    "description": "Error message or stack trace (if available)"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language of the code"
                },
                "expected_behavior": {
                    "type": "string",
                    "description": "What the code should do (optional)"
                },
                "actual_behavior": {
                    "type": "string",
                    "description": "What the code actually does (optional)"
                }
            },
            "required": ["code", "language"]
        }
    )
    
    tools["code_completion"] = code_completion
    tools["code_explanation"] = code_explanation
    tools["debug_assistance"] = debug_assistance
    
    # Register with FastMCP if available and instance provided
    if FASTMCP_AVAILABLE and mcp_instance:
        _register_fastmcp_tools(mcp_instance)
    
    return tools


def _register_fastmcp_tools(mcp: FastMCP) -> None:
    """Register tools with FastMCP using decorators.
    
    Args:
        mcp: FastMCP instance to register tools with
    """
    
    @mcp.tool()
    def code_completion(
        code: str,
        language: str,
        cursor_position: Optional[int] = None,
        max_completions: int = 3
    ) -> str:
        """Provides intelligent code completion suggestions based on context.
        
        Args:
            code: Current code context around cursor position
            language: Programming language (e.g., python, javascript, java)
            cursor_position: Cursor position in the code (optional)
            max_completions: Maximum number of completion suggestions
            
        Returns:
            Code completion suggestions
        """
        # This will be implemented when we integrate with AI model
        logger.info(f"Code completion requested for {language} code")
        return f"# Code completion for {language}\n# Context: {code[:50]}...\n# TODO: Implement AI completion"
    
    @mcp.tool()
    def code_explanation(
        code: str,
        language: str,
        detail_level: str = "detailed",
        focus: Optional[str] = None
    ) -> str:
        """Explains code functionality, purpose, and provides technical analysis.
        
        Args:
            code: Code to explain and analyze
            language: Programming language of the code
            detail_level: Level of detail for the explanation
            focus: Specific aspect to focus on (optional)
            
        Returns:
            Code explanation and analysis
        """
        # This will be implemented when we integrate with AI model
        logger.info(f"Code explanation requested for {language} code with {detail_level} detail")
        return f"# Code Explanation ({detail_level})\n\nThis {language} code:\n```{language}\n{code}\n```\n\n# TODO: Implement AI explanation"
    
    @mcp.tool()
    def debug_assistance(
        code: str,
        language: str,
        error_message: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        actual_behavior: Optional[str] = None
    ) -> str:
        """Provides debugging help, error analysis, and troubleshooting suggestions.
        
        Args:
            code: Code that has issues or needs debugging
            language: Programming language of the code
            error_message: Error message or stack trace (if available)
            expected_behavior: What the code should do (optional)
            actual_behavior: What the code actually does (optional)
            
        Returns:
            Debugging analysis and suggestions
        """
        # This will be implemented when we integrate with AI model
        logger.info(f"Debug assistance requested for {language} code")
        debug_info = f"# Debug Analysis for {language}\n\n"
        debug_info += f"**Code:**\n```{language}\n{code}\n```\n\n"
        
        if error_message:
            debug_info += f"**Error:** {error_message}\n\n"
        if expected_behavior:
            debug_info += f"**Expected:** {expected_behavior}\n\n"
        if actual_behavior:
            debug_info += f"**Actual:** {actual_behavior}\n\n"
            
        debug_info += "# TODO: Implement AI debugging analysis"
        return debug_info


# Global AI adapter instance (will be set by the tool registry)
_ai_adapter: Optional[MCPAIAdapter] = None

def set_ai_adapter(adapter: MCPAIAdapter) -> None:
    """Set the global AI adapter for tools.
    
    Args:
        adapter: MCPAIAdapter instance
    """
    global _ai_adapter
    _ai_adapter = adapter
    logger.info("AI adapter set for MCP tools")

def get_ai_adapter() -> Optional[MCPAIAdapter]:
    """Get the current AI adapter.
    
    Returns:
        Current MCPAIAdapter instance or None
    """
    return _ai_adapter

# Tool function implementations for non-FastMCP usage
async def code_completion_tool(
    code: str,
    language: str,
    cursor_position: Optional[int] = None,
    max_completions: int = 3
) -> Dict[str, Any]:
    """Code completion tool implementation.
    
    Args:
        code: Current code context around cursor position
        language: Programming language
        cursor_position: Cursor position in the code (optional)
        max_completions: Maximum number of completion suggestions
        
    Returns:
        MCP tool response with completion suggestions
    """
    logger.info(f"Code completion requested for {language}")
    
    if _ai_adapter:
        try:
            # Use AI adapter for intelligent completion
            context = {
                "language": language,
                "cursor_position": cursor_position,
                "max_completions": max_completions
            }
            completion_text = await _ai_adapter.generate_completion(code, context)
        except Exception as e:
            logger.error(f"AI completion failed: {e}")
            completion_text = f"# Error generating AI completion: {e}\n# Fallback for {language} code"
    else:
        # Fallback when no AI adapter is available
        completion_text = f"# Code completion for {language}\n# Context: {code[:50]}...\n# AI adapter not available"
    
    return {
        "content": [
            {
                "type": "text",
                "text": completion_text
            }
        ]
    }


async def code_explanation_tool(
    code: str,
    language: str,
    detail_level: str = "detailed",
    focus: Optional[str] = None
) -> Dict[str, Any]:
    """Code explanation tool implementation.
    
    Args:
        code: Code to explain and analyze
        language: Programming language of the code
        detail_level: Level of detail for the explanation
        focus: Specific aspect to focus on (optional)
        
    Returns:
        MCP tool response with code explanation
    """
    logger.info(f"Code explanation requested for {language} with {detail_level} detail")
    
    if _ai_adapter:
        try:
            # Use AI adapter for intelligent explanation
            question = f"Focus on {focus}" if focus else None
            explanation_text = await _ai_adapter.explain_code(
                code, language, detail_level, question
            )
        except Exception as e:
            logger.error(f"AI explanation failed: {e}")
            explanation_text = f"# Error generating AI explanation: {e}\n# Fallback explanation for {language} code"
    else:
        # Fallback when no AI adapter is available
        explanation_text = f"# Code Explanation ({detail_level})\n\n"
        explanation_text += f"This {language} code:\n```{language}\n{code}\n```\n\n"
        explanation_text += "AI adapter not available for detailed explanation."
    
    return {
        "content": [
            {
                "type": "text",
                "text": explanation_text
            }
        ]
    }


async def debug_assistance_tool(
    code: str,
    language: str,
    error_message: Optional[str] = None,
    expected_behavior: Optional[str] = None,
    actual_behavior: Optional[str] = None
) -> Dict[str, Any]:
    """Debug assistance tool implementation.
    
    Args:
        code: Code that has issues or needs debugging
        language: Programming language of the code
        error_message: Error message or stack trace (if available)
        expected_behavior: What the code should do (optional)
        actual_behavior: What the code actually does (optional)
        
    Returns:
        MCP tool response with debugging analysis
    """
    logger.info(f"Debug assistance requested for {language}")
    
    if _ai_adapter:
        try:
            # Use AI adapter for intelligent debugging
            debug_text = await _ai_adapter.debug_code(
                code, language, error_message, expected_behavior, actual_behavior
            )
        except Exception as e:
            logger.error(f"AI debug assistance failed: {e}")
            debug_text = f"# Error generating AI debug assistance: {e}\n# Fallback debug analysis for {language}"
    else:
        # Fallback when no AI adapter is available
        debug_text = f"# Debug Analysis for {language}\n\n"
        debug_text += f"**Code:**\n```{language}\n{code}\n```\n\n"
        
        if error_message:
            debug_text += f"**Error:** {error_message}\n\n"
        if expected_behavior:
            debug_text += f"**Expected:** {expected_behavior}\n\n"
        if actual_behavior:
            debug_text += f"**Actual:** {actual_behavior}\n\n"
            
        debug_text += "AI adapter not available for detailed debugging analysis."
    
    return {
        "content": [
            {
                "type": "text",
                "text": debug_text
            }
        ]
    }