#!/usr/bin/env python3
"""
Local AI Client with MCP Integration

A simple AI client that uses MCPleasant MCP tools to provide coding assistance.
This simulates how a real AI assistant would use your MCP server.
"""

import asyncio
import json
import subprocess
import sys
import re
from typing import Dict, Any, List, Optional

class LocalAIClient:
    """Local AI that uses MCP tools for enhanced responses."""
    
    def __init__(self):
        self.server_process = None
        self.tools = []
        self.request_id = 0
        self.conversation_history = []
    
    async def start_mcp_server(self):
        """Start the MCPleasant MCP server."""
        # Look for MCP server files
        server_candidates = [
            "mcpleasant_mcp.py",
            "mcpleasant_mcp_fixed.py", 
            "src/mcp_server.py"
        ]
        
        server_file = None
        for candidate in server_candidates:
            from pathlib import Path
            if Path(candidate).exists():
                server_file = candidate
                break
        
        if not server_file:
            print("❌ No MCP server file found!")
            return False
        
        print(f"🚀 Starting MCP server: {server_file}")
        
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, server_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            await asyncio.sleep(1)
            
            # Initialize
            init_response = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "LocalAI", "version": "1.0.0"}
            })
            
            if "result" in init_response:
                # Get tools
                tools_response = await self._send_request("tools/list", {})
                if "result" in tools_response and "tools" in tools_response["result"]:
                    self.tools = tools_response["result"]["tools"]
                    print(f"✅ Connected to MCP server with {len(self.tools)} tools")
                    return True
            
            print("❌ Failed to initialize MCP server")
            return False
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to MCP server."""
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        try:
            request_json = json.dumps(request) + "\n"
            self.server_process.stdin.write(request_json)
            self.server_process.stdin.flush()
            
            response_line = await asyncio.wait_for(
                asyncio.to_thread(self.server_process.stdout.readline),
                timeout=10.0
            )
            
            if response_line.strip():
                return json.loads(response_line.strip())
            else:
                return {"error": "Empty response"}
                
        except Exception as e:
            return {"error": f"Request failed: {e}"}
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool and return the response."""
        print(f"🔧 Using MCP tool: {tool_name}")
        
        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        if "result" in response and "content" in response["result"]:
            content = response["result"]["content"]
            if content and len(content) > 0:
                return content[0].get("text", "No response from tool")
        
        return f"Error: {response.get('error', 'Unknown error')}"
    
    def analyze_user_intent(self, user_input: str) -> Dict[str, Any]:
        """Analyze what the user wants and determine which MCP tool to use."""
        user_input_lower = user_input.lower()
        
        # Code completion patterns
        completion_patterns = [
            r"complete.*(?:function|def|class)",
            r"finish.*code",
            r"implement.*function",
            r"write.*function",
            r"def\s+\w+\s*\(",
            r"function\s+\w+\s*\(",
            r"class\s+\w+"
        ]
        
        # Code explanation patterns  
        explanation_patterns = [
            r"explain.*code",
            r"what.*does.*code",
            r"how.*work",
            r"analyze.*code",
            r"describe.*function"
        ]
        
        # Debugging patterns
        debug_patterns = [
            r"debug.*code",
            r"fix.*error",
            r"error.*code",
            r"bug.*code",
            r"exception",
            r"traceback"
        ]
        
        # Check for code blocks
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', user_input, re.DOTALL)
        inline_code = re.findall(r'`([^`]+)`', user_input)
        
        # Extract code from input
        extracted_code = ""
        if code_blocks:
            extracted_code = code_blocks[0]
        elif inline_code:
            extracted_code = inline_code[0]
        else:
            # Look for code-like patterns
            lines = user_input.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ['def ', 'function ', 'class ', 'import ', 'from ']):
                    extracted_code = line
                    break
        
        # Determine intent
        if any(re.search(pattern, user_input_lower) for pattern in completion_patterns):
            return {
                "intent": "complete_code",
                "tool": "complete_code",
                "code": extracted_code or self._extract_incomplete_code(user_input),
                "language": self._detect_language(user_input)
            }
        
        elif any(re.search(pattern, user_input_lower) for pattern in explanation_patterns):
            return {
                "intent": "explain_code", 
                "tool": "explain_code",
                "code": extracted_code or user_input
            }
        
        elif any(re.search(pattern, user_input_lower) for pattern in debug_patterns):
            error_msg = self._extract_error_message(user_input)
            return {
                "intent": "debug_code",
                "tool": "debug_code", 
                "code": extracted_code or user_input,
                "error": error_msg
            }
        
        else:
            return {
                "intent": "general",
                "tool": None
            }
    
    def _extract_incomplete_code(self, text: str) -> str:
        """Extract incomplete code that needs completion."""
        lines = text.split('\n')
        for line in lines:
            if any(pattern in line for pattern in ['def ', 'function ', 'class ', ':']):
                return line.strip()
        return text
    
    def _detect_language(self, text: str) -> str:
        """Detect programming language."""
        if any(keyword in text for keyword in ['def ', 'import ', 'from ', 'print(']):
            return 'python'
        elif any(keyword in text for keyword in ['function', 'const ', 'let ', 'var ']):
            return 'javascript'
        elif any(keyword in text for keyword in ['public class', 'public static', 'System.out']):
            return 'java'
        else:
            return 'python'  # Default
    
    def _extract_error_message(self, text: str) -> str:
        """Extract error message from text."""
        error_patterns = [
            r'Error: (.+)',
            r'Exception: (.+)', 
            r'Traceback.*?(\w+Error: .+)',
            r'(\w+Error: .+)'
        ]
        
        for pattern in error_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    async def process_user_request(self, user_input: str) -> str:
        """Process user request and provide AI-powered response."""
        # Analyze what the user wants
        intent = self.analyze_user_intent(user_input)
        
        if intent["tool"]:
            # Use MCP tool
            if intent["tool"] == "complete_code":
                response = await self.call_mcp_tool("complete_code", {
                    "code": intent["code"],
                    "language": intent["language"]
                })
                return f"**Code Completion:**\n\n```{intent['language']}\n{intent['code']}\n{response}\n```\n\n*✨ Generated using MCPleasant MCP tool*"
            
            elif intent["tool"] == "explain_code":
                response = await self.call_mcp_tool("explain_code", {
                    "code": intent["code"]
                })
                return f"**Code Explanation:**\n\n{response}\n\n*✨ Generated using MCPleasant MCP tool*"
            
            elif intent["tool"] == "debug_code":
                response = await self.call_mcp_tool("debug_code", {
                    "code": intent["code"],
                    "error": intent["error"]
                })
                return f"**Debugging Help:**\n\n{response}\n\n*✨ Generated using MCPleasant MCP tool*"
        
        else:
            # Handle general queries
            return self._handle_general_query(user_input)
    
    def _handle_general_query(self, user_input: str) -> str:
        """Handle general queries without MCP tools."""
        user_lower = user_input.lower()
        
        if any(greeting in user_lower for greeting in ['hello', 'hi', 'hey']):
            return """👋 Hello! I'm your Local AI Assistant with MCPleasant MCP integration!

I can help you with:
• **Code Completion** - "Complete this function: def fibonacci(n):"
• **Code Explanation** - "Explain this code: [your code]"  
• **Code Debugging** - "Debug this error: [code with error]"

Try asking me to complete, explain, or debug some code! 🚀"""
        
        elif 'help' in user_lower:
            return """**Local AI Help - MCP Integration**

**Available Commands:**
• Complete code: "Complete this function: def my_function():"
• Explain code: "Explain this code: [paste your code]"
• Debug code: "Debug this error: [code] Error: [error message]"
• Show tools: "What MCP tools do you have?"

**Example Requests:**
• "Complete this Python function: def factorial(n):"
• "Explain this code: def quicksort(arr): return sorted(arr)"
• "Debug this error: def divide(a,b): return a/b Error: ZeroDivisionError"

**MCP Integration Status:** ✅ Connected with MCPleasant tools"""
        
        elif 'tools' in user_lower or 'mcp' in user_lower:
            tools_list = "\n".join([f"• **{tool['name']}**: {tool.get('description', 'No description')}" for tool in self.tools])
            return f"""**Available MCP Tools:**

{tools_list}

*These tools are provided by your MCPleasant MCP server and enhance my coding assistance capabilities.*"""
        
        else:
            return f"""I understand you said: "{user_input}"

I'm a Local AI focused on coding assistance using MCP tools. I work best when you ask me to:
• Complete code snippets
• Explain code functionality  
• Debug code errors

Try something like: "Complete this function: def fibonacci(n):" 🤖"""
    
    def stop_server(self):
        """Stop the MCP server."""
        if self.server_process:
            print("🛑 Stopping MCP server...")
            self.server_process.terminate()
            self.server_process.wait()


async def interactive_session():
    """Run interactive AI session."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              Local AI with MCPleasant MCP Tools             ║
║                                                              ║
║  🤖 Your personal coding assistant using MCP integration   ║
║  💬 Chat naturally - I'll use MCP tools when needed        ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    ai = LocalAIClient()
    
    if not await ai.start_mcp_server():
        print("❌ Failed to start MCP server. Cannot continue.")
        return
    
    print("\n✅ Local AI is ready! Type 'quit' to exit, 'help' for commands.")
    print("\n🧪 **Try these MCP-powered requests:**")
    print("   • 'Complete this function: def fibonacci(n):'")
    print("   • 'Explain this code: def quicksort(arr): return sorted(arr)'")
    print("   • 'Debug this error: def divide(a,b): return a/b Error: ZeroDivisionError'")
    print("-" * 70)
    
    try:
        while True:
            user_input = input("\n🧑‍💻 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                break
            
            if not user_input:
                continue
            
            print("\n🤖 Local AI:")
            try:
                response = await ai.process_user_request(user_input)
                print(response)
            except Exception as e:
                print(f"❌ Error processing request: {e}")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    finally:
        ai.stop_server()


if __name__ == "__main__":
    asyncio.run(interactive_session())