#!/usr/bin/env python3
import asyncio
import json
import logging
import sys
from typing import Dict, Any

logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

class SimpleMCPServer:
    def __init__(self):
        self.tools = {
            "code_completion": {"name": "code_completion", "description": "Generate code completions"},
            "explain_code": {"name": "explain_code", "description": "Explain code"},
            "debug_code": {"name": "debug_code", "description": "Debug code"}
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        request_id = request.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0", "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "mcpleasant", "version": "1.0.0"}
                }
            }
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0", "id": request_id,
                "result": {"tools": list(self.tools.values())}
            }
        elif method == "tools/call":
            return await self._handle_tool_call(request)
        else:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

    async def _handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        request_id = request.get("id")
        
        if tool_name == "code_completion":
            result = self._complete_code(arguments)
        elif tool_name == "explain_code":
            result = self._explain_code(arguments)
        elif tool_name == "debug_code":
            result = self._debug_code(arguments)
        else:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}}
        
        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result}]}}

    def _complete_code(self, args: Dict[str, Any]) -> str:
        code = args.get("code", "")
        if "def " in code and code.strip().endswith(":"):
            func_name = code.split("def ")[1].split("(")[0].strip()
            return f'    """TODO: Implement {func_name} function."""\n    pass'
        elif "class " in code and code.strip().endswith(":"):
            class_name = code.split("class ")[1].split("(")[0].split(":")[0].strip()
            return f'    """TODO: Implement {class_name} class."""\n    \n    def __init__(self):\n        pass'
        elif "if " in code and code.strip().endswith(":"):
            return "    # TODO: Add condition logic\n    pass"
        elif "for " in code and code.strip().endswith(":"):
            return "    # TODO: Add loop body\n    pass"
        else:
            return f"# Code completion for: {code[:50]}..."

    def _explain_code(self, args: Dict[str, Any]) -> str:
        code = args.get("code", "")
        lines = len(code.split('\n'))
        words = len(code.split())
        
        if "def " in code:
            return f"This code defines a function. It has {lines} lines and {words} words."
        elif "class " in code:
            return f"This code defines a class. It has {lines} lines and {words} words."
        elif "if " in code:
            return f"This code contains conditional logic. It has {lines} lines and {words} words."
        else:
            return f"This code snippet has {lines} lines and {words} words."

    def _debug_code(self, args: Dict[str, Any]) -> str:
        code = args.get("code", "")
        error_message = args.get("error_message", "")
        
        suggestions = []
        if "IndentationError" in error_message:
            suggestions.append("Check your indentation - Python requires consistent spacing")
        elif "SyntaxError" in error_message:
            suggestions.append("Check for missing colons, parentheses, or quotes")
        elif "NameError" in error_message:
            suggestions.append("Check if all variables are defined before use")
        else:
            suggestions.append("Review your code for common issues")
        
        return "Debugging suggestions:\n" + "\n".join(f"• {s}" for s in suggestions)

    async def handle_stdio(self):
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                request = json.loads(line.strip())
                response = await self.handle_request(request)
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError:
                continue
            except Exception:
                continue

async def main():
    server = SimpleMCPServer()
    await server.handle_stdio()

if __name__ == "__main__":
    asyncio.run(main())
