"""AI-powered MCP tools using FastMCP decorators."""

import logging
import structlog
from typing import Dict, Any, Optional

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    FastMCP = None

from ..protocol.models import MCPTool
from ..adapters.ai_adapter import MCPAIAdapter
from ..utils.error_handler import get_error_handler, error_context
from ..utils.exceptions import AIModelError, ValidationError
from ..utils.logging import get_structured_logger, get_performance_logger

logger = logging.getLogger(__name__)
structured_logger = get_structured_logger(__name__)
performance_logger = get_performance_logger()


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
    import time
    start_time = time.time()
    
    error_handler = get_error_handler()
    with error_handler.error_context(
        context={
            "tool": "code_completion",
            "language": language,
            "code_length": len(code),
            "max_completions": max_completions
        }
    ):
        try:
            # Validate inputs
            if not code.strip():
                raise ValidationError("Code input cannot be empty")
            
            if max_completions < 1 or max_completions > 10:
                raise ValidationError("max_completions must be between 1 and 10")
            
            structured_logger.info("Code completion started")
            
            if _ai_adapter:
                try:
                    # Use AI adapter for intelligent completion
                    context = {
                        "language": language,
                        "cursor_position": cursor_position,
                        "max_completions": max_completions
                    }
                    completion_text = await _ai_adapter.generate_completion(code, context)
                    
                    # Log AI inference performance
                    duration_ms = (time.time() - start_time) * 1000
                    performance_logger.ai_inference_timing(
                        model_name="code_completion",
                        input_tokens=len(code.split()),
                        output_tokens=len(completion_text.split()),
                        duration_ms=duration_ms
                    )
                    
                except Exception as e:
                    # Handle AI adapter errors with recovery
                    error_handler = get_error_handler()
                    error_context = await error_handler.handle_error(
                        AIModelError(f"Code completion failed: {str(e)}"),
                        context={
                            "tool": "code_completion",
                            "language": language,
                            "ai_adapter_available": True
                        },
                        attempt_recovery=True
                    )
                    
                    # Use fallback if recovery failed
                    if not error_context.recovery_successful:
                        completion_text = _get_code_completion_fallback(language, code)
                    else:
                        # Retry with recovery context
                        completion_text = await _ai_adapter.generate_completion(code, context)
            else:
                # Fallback when no AI adapter is available
                structured_logger.warning("AI adapter not available, using fallback")
                completion_text = _get_code_completion_fallback(language, code)
            
            structured_logger.info("Code completion completed")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": completion_text
                    }
                ]
            }
            
        except Exception as e:
            # Final error handling
            error_handler = get_error_handler()
            await error_handler.handle_error(e, context={"tool": "code_completion"})
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Code completion is temporarily unavailable: {str(e)}"
                    }
                ],
                "isError": True
            }


def _get_code_completion_fallback(language: str, code: str) -> str:
    """Get fallback code completion response.
    
    Args:
        language: Programming language
        code: Code context
        
    Returns:
        Fallback completion text
    """
    fallback_completions = {
        "python": "# Python completion suggestions:\n# - Check syntax and indentation\n# - Consider using type hints\n# - Follow PEP 8 style guidelines",
        "javascript": "// JavaScript completion suggestions:\n// - Use const/let instead of var\n// - Consider async/await for promises\n// - Add error handling with try/catch",
        "typescript": "// TypeScript completion suggestions:\n// - Add proper type annotations\n// - Use interfaces for object types\n// - Enable strict mode for better type checking",
        "java": "// Java completion suggestions:\n// - Follow camelCase naming conventions\n// - Add proper exception handling\n// - Consider using generics for type safety",
        "go": "// Go completion suggestions:\n// - Handle errors explicitly\n// - Use gofmt for formatting\n// - Follow Go naming conventions"
    }
    
    return fallback_completions.get(
        language.lower(),
        f"# {language} completion suggestions:\n# - Check syntax and formatting\n# - Follow language best practices\n# - Add appropriate error handling"
    )


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
    import time
    start_time = time.time()
    
    error_handler = get_error_handler()
    with error_handler.error_context(
        context={
            "tool": "code_explanation",
            "language": language,
            "detail_level": detail_level,
            "focus": focus,
            "code_length": len(code)
        }
    ):
        try:
            # Validate inputs
            if not code.strip():
                raise ValidationError("Code input cannot be empty")
            
            valid_detail_levels = ["brief", "detailed", "comprehensive"]
            if detail_level not in valid_detail_levels:
                raise ValidationError(f"detail_level must be one of: {valid_detail_levels}")
            
            structured_logger.info("Code explanation started")
            
            if _ai_adapter:
                try:
                    # Use AI adapter for intelligent explanation
                    question = f"Focus on {focus}" if focus else None
                    explanation_text = await _ai_adapter.explain_code(
                        code, language, detail_level, question
                    )
                    
                    # Log AI inference performance
                    duration_ms = (time.time() - start_time) * 1000
                    performance_logger.ai_inference_timing(
                        model_name="code_explanation",
                        input_tokens=len(code.split()),
                        output_tokens=len(explanation_text.split()),
                        duration_ms=duration_ms
                    )
                    
                except Exception as e:
                    # Handle AI adapter errors with recovery
                    error_handler = get_error_handler()
                    error_context = await error_handler.handle_error(
                        AIModelError(f"Code explanation failed: {str(e)}"),
                        context={
                            "tool": "code_explanation",
                            "language": language,
                            "detail_level": detail_level,
                            "ai_adapter_available": True
                        },
                        attempt_recovery=True
                    )
                    
                    # Use fallback if recovery failed
                    if not error_context.recovery_successful:
                        explanation_text = _get_code_explanation_fallback(language, code, detail_level, focus)
                    else:
                        # Retry with recovery context
                        explanation_text = await _ai_adapter.explain_code(code, language, detail_level, question)
            else:
                # Fallback when no AI adapter is available
                structured_logger.warning("AI adapter not available, using fallback")
                explanation_text = _get_code_explanation_fallback(language, code, detail_level, focus)
            
            structured_logger.info("Code explanation completed")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": explanation_text
                    }
                ]
            }
            
        except Exception as e:
            # Final error handling
            error_handler = get_error_handler()
            await error_handler.handle_error(e, context={"tool": "code_explanation"})
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Code explanation is temporarily unavailable: {str(e)}"
                    }
                ],
                "isError": True
            }


def _get_code_explanation_fallback(language: str, code: str, detail_level: str, focus: Optional[str]) -> str:
    """Get fallback code explanation response.
    
    Args:
        language: Programming language
        code: Code to explain
        detail_level: Level of detail
        focus: Specific focus area
        
    Returns:
        Fallback explanation text
    """
    explanation = f"# Code Explanation ({detail_level})\n\n"
    explanation += f"**Language:** {language}\n"
    explanation += f"**Code Length:** {len(code)} characters\n\n"
    
    if focus:
        explanation += f"**Focus Area:** {focus}\n\n"
    
    explanation += f"**Code:**\n```{language}\n{code}\n```\n\n"
    
    # Basic analysis based on language
    if language.lower() == "python":
        explanation += "**Basic Analysis:**\n"
        explanation += "- This appears to be Python code\n"
        explanation += "- Check for proper indentation and syntax\n"
        explanation += "- Consider adding type hints for better code clarity\n"
    elif language.lower() in ["javascript", "typescript"]:
        explanation += "**Basic Analysis:**\n"
        explanation += f"- This appears to be {language} code\n"
        explanation += "- Check for proper semicolon usage\n"
        explanation += "- Consider using modern ES6+ features\n"
    else:
        explanation += "**Basic Analysis:**\n"
        explanation += f"- This appears to be {language} code\n"
        explanation += "- Follow language-specific best practices\n"
        explanation += "- Ensure proper syntax and formatting\n"
    
    explanation += "\n*Note: AI-powered analysis is temporarily unavailable. This is a basic fallback explanation.*"
    
    return explanation


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
    import time
    start_time = time.time()
    
    error_handler = get_error_handler()
    with error_handler.error_context(
        context={
            "tool": "debug_assistance",
            "language": language,
            "has_error_message": bool(error_message),
            "has_expected_behavior": bool(expected_behavior),
            "has_actual_behavior": bool(actual_behavior),
            "code_length": len(code)
        }
    ):
        try:
            # Validate inputs
            if not code.strip():
                raise ValidationError("Code input cannot be empty")
            
            structured_logger.info("Debug assistance started")
            
            if _ai_adapter:
                try:
                    # Use AI adapter for intelligent debugging
                    debug_text = await _ai_adapter.debug_code(
                        code, language, error_message, expected_behavior, actual_behavior
                    )
                    
                    # Log AI inference performance
                    duration_ms = (time.time() - start_time) * 1000
                    performance_logger.ai_inference_timing(
                        model_name="debug_assistance",
                        input_tokens=len(code.split()) + len((error_message or "").split()),
                        output_tokens=len(debug_text.split()),
                        duration_ms=duration_ms
                    )
                    
                except Exception as e:
                    # Handle AI adapter errors with recovery
                    error_handler = get_error_handler()
                    error_context = await error_handler.handle_error(
                        AIModelError(f"Debug assistance failed: {str(e)}"),
                        context={
                            "tool": "debug_assistance",
                            "language": language,
                            "has_error_message": bool(error_message),
                            "ai_adapter_available": True
                        },
                        attempt_recovery=True
                    )
                    
                    # Use fallback if recovery failed
                    if not error_context.recovery_successful:
                        debug_text = _get_debug_assistance_fallback(
                            language, code, error_message, expected_behavior, actual_behavior
                        )
                    else:
                        # Retry with recovery context
                        debug_text = await _ai_adapter.debug_code(
                            code, language, error_message, expected_behavior, actual_behavior
                        )
            else:
                # Fallback when no AI adapter is available
                structured_logger.warning("AI adapter not available, using fallback")
                debug_text = _get_debug_assistance_fallback(
                    language, code, error_message, expected_behavior, actual_behavior
                )
            
            structured_logger.info("Debug assistance completed")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": debug_text
                    }
                ]
            }
            
        except Exception as e:
            # Final error handling
            error_handler = get_error_handler()
            await error_handler.handle_error(e, context={"tool": "debug_assistance"})
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Debug assistance is temporarily unavailable: {str(e)}"
                    }
                ],
                "isError": True
            }


def _get_debug_assistance_fallback(
    language: str, 
    code: str, 
    error_message: Optional[str], 
    expected_behavior: Optional[str], 
    actual_behavior: Optional[str]
) -> str:
    """Get fallback debug assistance response.
    
    Args:
        language: Programming language
        code: Code to debug
        error_message: Error message if available
        expected_behavior: Expected behavior
        actual_behavior: Actual behavior
        
    Returns:
        Fallback debug analysis text
    """
    debug_text = f"# Debug Analysis for {language}\n\n"
    debug_text += f"**Code:**\n```{language}\n{code}\n```\n\n"
    
    if error_message:
        debug_text += f"**Error Message:**\n```\n{error_message}\n```\n\n"
        
        # Basic error analysis
        debug_text += "**Basic Error Analysis:**\n"
        if "syntax" in error_message.lower():
            debug_text += "- This appears to be a syntax error\n"
            debug_text += "- Check for missing brackets, parentheses, or semicolons\n"
            debug_text += "- Verify proper indentation (especially for Python)\n"
        elif "name" in error_message.lower() and "not defined" in error_message.lower():
            debug_text += "- This appears to be a name/variable error\n"
            debug_text += "- Check if all variables are properly declared\n"
            debug_text += "- Verify import statements are correct\n"
        elif "type" in error_message.lower():
            debug_text += "- This appears to be a type-related error\n"
            debug_text += "- Check data types and conversions\n"
            debug_text += "- Verify function arguments match expected types\n"
        else:
            debug_text += "- Review the error message carefully\n"
            debug_text += "- Check the line number mentioned in the error\n"
            debug_text += "- Look for common issues in the problematic area\n"
        debug_text += "\n"
    
    if expected_behavior:
        debug_text += f"**Expected Behavior:**\n{expected_behavior}\n\n"
    
    if actual_behavior:
        debug_text += f"**Actual Behavior:**\n{actual_behavior}\n\n"
    
    # Language-specific debugging tips
    debug_text += "**General Debugging Tips:**\n"
    if language.lower() == "python":
        debug_text += "- Use print() statements to trace execution\n"
        debug_text += "- Check indentation carefully\n"
        debug_text += "- Use Python debugger (pdb) for step-by-step debugging\n"
        debug_text += "- Verify all imports are available\n"
    elif language.lower() in ["javascript", "typescript"]:
        debug_text += "- Use console.log() to trace execution\n"
        debug_text += "- Check browser developer tools for errors\n"
        debug_text += "- Verify all variables are properly declared\n"
        debug_text += "- Check for asynchronous operation issues\n"
    elif language.lower() == "java":
        debug_text += "- Use System.out.println() for debugging output\n"
        debug_text += "- Check for null pointer exceptions\n"
        debug_text += "- Verify class and method visibility\n"
        debug_text += "- Use IDE debugger for step-by-step analysis\n"
    else:
        debug_text += "- Add logging/print statements to trace execution\n"
        debug_text += "- Use language-specific debugging tools\n"
        debug_text += "- Check documentation for common issues\n"
        debug_text += "- Verify syntax and language-specific rules\n"
    
    debug_text += "\n*Note: AI-powered debugging analysis is temporarily unavailable. This is a basic fallback analysis.*"
    
    return debug_text


class AITools:
    """Simple AITools class for compatibility with advanced tools."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def _call_ai_model(self, prompt: str) -> str:
        """Call AI model with a prompt.
        
        Args:
            prompt: The prompt to send to the AI model
            
        Returns:
            AI model response
        """
        # This is a placeholder implementation
        # In a real implementation, this would call the actual AI model
        return f"AI response to: {prompt[:100]}..."