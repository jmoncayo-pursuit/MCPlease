#!/usr/bin/env python3
"""MCPleasant MCP Server for GitHub Copilot integration."""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, List

# Configure logging to stderr only
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger(__name__)

class MCPleasantMCPServer:
    """MCP server that provides AI coding tools to GitHub Copilot."""
    
    def __init__(self):
        self.tools = [
            {
                "name": "complete_code",
                "description": "Complete code based on context and patterns",
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
                "description": "Explain what code does and how it works",
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
                "description": "Help debug code issues and suggest fixes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code with issues"},
                        "error": {"type": "string", "description": "Error message"}
                    },
                    "required": ["code"]
                }
            }
        ]

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
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "mcpleasant",
                        "version": "1.0.0",
                        "description": "MCPleasant AI coding assistant"
                    }
                }
            }
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": self.tools}
            }
        elif method == "tools/call":
            return await self._handle_tool_call(request)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

    async def _handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution requests."""
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        request_id = request.get("id")
        
        try:
            if tool_name == "complete_code":
                result = self._complete_code(arguments)
            elif tool_name == "explain_code":
                result = self._explain_code(arguments)
            elif tool_name == "debug_code":
                result = self._debug_code(arguments)
            else:
                return {
                    "jsonrpc": "2.0", "id": request_id,
                    "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}
                }
            
            return {
                "jsonrpc": "2.0", "id": request_id,
                "result": {"content": [{"type": "text", "text": result}]}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0", "id": request_id,
                "error": {"code": -32603, "message": f"Tool execution failed: {str(e)}"}
            }

    def _complete_code(self, args: Dict[str, Any]) -> str:
        """Provide intelligent code completion."""
        code = args.get("code", "")
        language = args.get("language", "python")
        
        if "def " in code and code.strip().endswith(":"):
            func_name = code.split("def ")[1].split("(")[0].strip()
            if "fibonacci" in func_name.lower():
                return """    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)"""
            else:
                return f"""    # TODO: Implement {func_name}
    pass"""
        elif "class " in code and code.strip().endswith(":"):
            return """    def __init__(self):
        pass"""
        elif "if " in code and code.strip().endswith(":"):
            return "    # TODO: Add condition logic"
        else:
            return f"# Code completion for {language}"

    def _explain_code(self, args: Dict[str, Any]) -> str:
        """Provide detailed code explanation."""
        code = args.get("code", "")
        lines = len(code.split('\n'))
        
        explanations = []
        if "def " in code:
            explanations.append("This code defines a function")
        if "class " in code:
            explanations.append("This code defines a class")
        if "if " in code:
            explanations.append("This code contains conditional logic")
        
        explanations.append(f"Code has {lines} lines")
        return "Code Analysis: " + "; ".join(explanations)

    def _debug_code(self, args: Dict[str, Any]) -> str:
        """Provide debugging assistance."""
        code = args.get("code", "")
        error = args.get("error", "")
        
        suggestions = []
        if "IndentationError" in error:
            suggestions.append("Check indentation consistency")
        elif "SyntaxError" in error:
            suggestions.append("Check for missing colons or parentheses")
        elif "NameError" in error:
            suggestions.append("Check variable names and definitions")
        else:
            suggestions.append("Review code logic and structure")
        
        return "Debug suggestions: " + "; ".join(suggestions)

    async def handle_stdio(self):
        """Handle stdio communication for MCP protocol."""
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                request = json.loads(line.strip())
                response = await self.handle_request(request)
                print(json.dumps(response), flush=True)
                
            except (json.JSONDecodeError, Exception):
                continue

async def main():
    server = MCPleasantMCPServer()
    await server.handle_stdio()

if __name__ == "__main__":
    asyncio.run(main())
