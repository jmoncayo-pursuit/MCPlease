#!/usr/bin/env python3
"""Simple MCP server for testing GitHub Copilot integration."""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, List

# Only log to stderr, keep stdout clean for MCP protocol
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

class SimpleMCPServer:
    def __init__(self):
        self.tools = {
            "code_completion": {
                "name": "code_completion",
                "description": "Generate code completions and suggestions",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code context"},
                        "language": {"type": "string", "description": "Programming language"}
                    },
                    "required": ["code"]
                }
            },
            "explain_code": {
                "name": "explain_code", 
                "description": "Explain code functionality",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to explain"}
                    },
                    "required": ["code"]
                }
            }
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP protocol requests."""
        method = request.get("method")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "simple-coding-assistant",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tools": list(self.tools.values())
                }
            }
        
        elif method == "tools/call":
            return await self.handle_tool_call(request)
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    async def handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution requests."""
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "code_completion":
            result = self.generate_code_completion(arguments)
        elif tool_name == "explain_code":
            result = self.explain_code(arguments)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32602,
                    "message": f"Unknown tool: {tool_name}"
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": result
                    }
                ]
            }
        }

    def generate_code_completion(self, args: Dict[str, Any]) -> str:
        """Generate code completion (mock implementation)."""
        code = args.get("code", "")
        language = args.get("language", "python")
        
        # Simple mock completions based on context
        if "def " in code and code.strip().endswith(":"):
            return "    pass  # TODO: Implement function"
        elif "class " in code and code.strip().endswith(":"):
            return "    def __init__(self):\n        pass"
        elif "if " in code and code.strip().endswith(":"):
            return "    # TODO: Add condition logic"
        else:
            return f"# Code completion for {language}\n# Context: {code[:50]}..."

    def explain_code(self, args: Dict[str, Any]) -> str:
        """Explain code functionality (mock implementation)."""
        code = args.get("code", "")
        
        if "def " in code:
            return "This appears to be a function definition. Functions are reusable blocks of code that perform specific tasks."
        elif "class " in code:
            return "This is a class definition. Classes are blueprints for creating objects with shared attributes and methods."
        elif "import " in code:
            return "This is an import statement that brings external modules or libraries into your code."
        else:
            return f"This code snippet contains {len(code.split())} words and appears to be {code.split()[0] if code.split() else 'empty'} code."

async def main():
    """Main server loop."""
    server = SimpleMCPServer()
    logger.info("Simple MCP server starting...")
    
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            try:
                request = json.loads(line.strip())
                response = await server.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {line}")
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                
    except KeyboardInterrupt:
        logger.info("Server shutting down...")

if __name__ == "__main__":
    asyncio.run(main())