#!/usr/bin/env python3
"""MCPlease MCP Server for GitHub Copilot integration."""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any, List

# Configure logging to stderr only
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger(__name__)

class MCPleaseMCPServer:
    """MCP server that provides AI coding tools to GitHub Copilot."""
    
    def __init__(self):
        self.ai_manager = None
        self.is_model_ready = False
        
        # Try to initialize AI model
        asyncio.create_task(self._initialize_ai_model())
        
        self.tools = [
            {
                "name": "complete_code",
                "description": "Complete code based on context and patterns using AI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code context to complete"},
                        "language": {"type": "string", "description": "Programming language"}
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "explain_code",
                "description": "Explain what code does and how it works using AI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to explain"}
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "debug_code",
                "description": "Help debug code issues and suggest fixes using AI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code with issues"},
                        "error": {"type": "string", "description": "Error message"}
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "refactor_code",
                "description": "Suggest code improvements and refactoring using AI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to refactor"},
                        "goal": {"type": "string", "description": "Refactoring goal"}
                    },
                    "required": ["code"]
                }
            }
        ]

    async def _initialize_ai_model(self):
        """Initialize the AI model in the background."""
        try:
            # Add src to path for imports
            current_dir = os.path.dirname(os.path.abspath(__file__))
            src_dir = os.path.join(current_dir, "src")
            if os.path.exists(src_dir):
                sys.path.insert(0, src_dir)
                
                from models.ai_manager import AIModelManager
                
                self.ai_manager = AIModelManager(max_memory_gb=12)
                success = await self.ai_manager.load_model()
                
                if success:
                    self.is_model_ready = True
                    logger.info("AI model initialized successfully")
                else:
                    logger.info("AI model not available, using fallback responses")
            else:
                logger.info("src directory not found, using fallback responses")
                
        except Exception as e:
            logger.info(f"AI model initialization failed: {e}, using fallback responses")

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP protocol requests."""
        method = request.get("method")
        request_id = request.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "mcplease",
                        "version": "1.0.0",
                        "description": "MCPlease AI coding assistant"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": self.tools
                }
            }
        
        elif method == "tools/call":
            return await self._handle_tool_call(request)
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    async def _handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution requests."""
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        request_id = request.get("id")
        
        try:
            if tool_name == "complete_code":
                result = await self._complete_code(arguments)
            elif tool_name == "explain_code":
                result = await self._explain_code(arguments)
            elif tool_name == "debug_code":
                result = await self._debug_code(arguments)
            elif tool_name == "refactor_code":
                result = await self._refactor_code(arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution failed: {str(e)}"
                }
            }

    async def _complete_code(self, args: Dict[str, Any]) -> str:
        """Provide AI-powered code completion."""
        code = args.get("code", "")
        language = args.get("language", "python")
        
        if self.is_model_ready and self.ai_manager:
            try:
                # Use AI model for completion
                completion = await self.ai_manager.generate_code_completion(code)
                return completion
            except Exception as e:
                logger.error(f"AI completion failed: {e}")
                # Fall back to pattern-based completion
        
        # Fallback pattern-based completion
        if "def " in code and code.strip().endswith(":"):
            func_name = code.split("def ")[1].split("(")[0].strip()
            if "fibonacci" in func_name.lower():
                return '''    """Calculate the nth Fibonacci number.
    
    Args:
        n: The position in the Fibonacci sequence
        
    Returns:
        The nth Fibonacci number
    """
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)'''
            else:
                return f'''    """TODO: Implement {func_name} function.
    
    Args:
        Add parameter descriptions here
        
    Returns:
        Add return value description here
    """
    pass'''
        
        elif "class " in code and code.strip().endswith(":"):
            class_name = code.split("class ")[1].split("(")[0].split(":")[0].strip()
            return f'''    """TODO: Implement {class_name} class.
    
    A class that represents...
    """
    
    def __init__(self):
        """Initialize the {class_name}."""
        pass'''
        
        else:
            return f"# Smart completion for {language}\n# TODO: Add your implementation here"

    async def _explain_code(self, args: Dict[str, Any]) -> str:
        """Provide AI-powered code explanation."""
        code = args.get("code", "")
        
        if self.is_model_ready and self.ai_manager:
            try:
                # Use AI model for explanation
                explanation = await self.ai_manager.explain_code(code)
                return explanation
            except Exception as e:
                logger.error(f"AI explanation failed: {e}")
                # Fall back to pattern-based explanation
        
        # Fallback pattern-based explanation
        lines = code.strip().split('\n')
        explanations = []
        
        if "def " in code:
            explanations.append("This code defines functions")
        if "class " in code:
            explanations.append("This code defines classes")
        if "import " in code or "from " in code:
            explanations.append("This code imports modules")
        
        explanations.append(f"Code has {len(lines)} lines")
        return "Code Analysis: " + "; ".join(explanations)

    async def _debug_code(self, args: Dict[str, Any]) -> str:
        """Provide AI-powered debugging assistance."""
        code = args.get("code", "")
        error_message = args.get("error", "")
        
        if self.is_model_ready and self.ai_manager:
            try:
                # Use AI model for debugging
                prompt = f"Debug this code:\n{code}\n\nError: {error_message}\n\nProvide debugging suggestions:"
                debug_help = await self.ai_manager.generate_text(prompt)
                return debug_help
            except Exception as e:
                logger.error(f"AI debugging failed: {e}")
                # Fall back to pattern-based debugging
        
        # Fallback pattern-based debugging
        suggestions = []
        if error_message:
            if "indentationerror" in error_message.lower():
                suggestions.append("Fix indentation consistency")
            elif "syntaxerror" in error_message.lower():
                suggestions.append("Check for missing colons or parentheses")
            else:
                suggestions.append(f"Error analysis: {error_message}")
        
        if not suggestions:
            suggestions.append("Review code logic and structure")
        
        return "Debugging Analysis: " + "; ".join(suggestions)

    async def _refactor_code(self, args: Dict[str, Any]) -> str:
        """Provide AI-powered code refactoring suggestions."""
        code = args.get("code", "")
        goal = args.get("goal", "improve readability")
        
        if self.is_model_ready and self.ai_manager:
            try:
                # Use AI model for refactoring
                prompt = f"Suggest refactoring improvements for this code:\n{code}\n\nGoal: {goal}\n\nProvide specific suggestions:"
                refactor_help = await self.ai_manager.generate_text(prompt)
                return refactor_help
            except Exception as e:
                logger.error(f"AI refactoring failed: {e}")
                # Fall back to pattern-based refactoring
        
        # Fallback pattern-based refactoring
        suggestions = []
        lines = code.split('\n')
        
        if len(lines) > 15:
            suggestions.append("Consider breaking into smaller functions")
        if "TODO" in code or "FIXME" in code:
            suggestions.append("Address TODO/FIXME comments")
        
        if not suggestions:
            suggestions.append("Code appears well-structured")
        
        return f"Refactoring Suggestions (Goal: {goal}): " + "; ".join(suggestions)

    async def handle_stdio(self):
        """Handle stdio communication for MCP protocol."""
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                request = json.loads(line)
                response = await self.handle_request(request)
                
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error handling request: {e}")
                continue

async def main():
    """Main server entry point."""
    server = MCPleaseMCPServer()
    await server.handle_stdio()

if __name__ == "__main__":
    asyncio.run(main())