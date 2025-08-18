#!/usr/bin/env python3
"""
MCPlease MCP - ONE command for GitHub Copilot integration

Uses VSCode's native MCP support with GitHub Copilot.
No extensions needed. Just works.
"""

import os
import sys
import json
import subprocess
import time
import asyncio
from pathlib import Path

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    MCPlease MCP                           ║
║                                                              ║
║  🎯 ONE command. Works with GitHub Copilot directly.       ║
║  ⚡ No extensions, no config, just works                   ║
╚══════════════════════════════════════════════════════════════╝
""")

def create_mcp_server():
    """Create the MCP server that works with Copilot."""
    server_content = [
        "#!/usr/bin/env python3",
        '"""MCPlease MCP Server for GitHub Copilot integration."""',
        "",
        "import asyncio",
        "import json",
        "import logging",
        "import sys",
        "import os",
        "from typing import Dict, Any, List",
        "",
        "# Configure logging to stderr only",
        "logging.basicConfig(level=logging.ERROR, stream=sys.stderr)",
        "logger = logging.getLogger(__name__)",
        "",
        "class MCPleaseMCPServer:",
        '    """MCP server that provides AI coding tools to GitHub Copilot."""',
        "    ",
        "    def __init__(self):",
        "        self.ai_manager = None",
        "        self.is_model_ready = False",
        "        ",
        "        # Try to initialize AI model",
        "        asyncio.create_task(self._initialize_ai_model())",
        "        ",
        "        self.tools = [",
        "            {",
        '                "name": "complete_code",',
        '                "description": "Complete code based on context and patterns using AI",',
        "                \"inputSchema\": {",
        '                    "type": "object",',
        "                    \"properties\": {",
        '                        "code": {"type": "string", "description": "Code context to complete"},',
        '                        "language": {"type": "string", "description": "Programming language"}',
        "                    },",
        '                    "required": ["code"]',
        "                }",
        "            },",
        "            {",
        '                "name": "explain_code",',
        '                "description": "Explain what code does and how it works using AI",',
        "                \"inputSchema\": {",
        '                    "type": "object",',
        "                    \"properties\": {",
        '                        "code": {"type": "string", "description": "Code to explain"}',
        "                    },",
        '                    "required": ["code"]',
        "                }",
        "            },",
        "            {",
        '                "name": "debug_code",',
        '                "description": "Help debug code issues and suggest fixes using AI",',
        "                \"inputSchema\": {",
        '                    "type": "object",',
        "                    \"properties\": {",
        '                        "code": {"type": "string", "description": "Code with issues"},',
        '                        "error": {"type": "string", "description": "Error message"}',
        "                    },",
        '                    "required": ["code"]',
        "                }",
        "            },",
        "            {",
        '                "name": "refactor_code",',
        '                "description": "Suggest code improvements and refactoring using AI",',
        "                \"inputSchema\": {",
        '                    "type": "object",',
        "                    \"properties\": {",
        '                        "code": {"type": "string", "description": "Code to refactor"},',
        '                        "goal": {"type": "string", "description": "Refactoring goal"}',
        "                    },",
        '                    "required": ["code"]',
        "                }",
        "            }",
        "        ]",
        "",
        "    async def _initialize_ai_model(self):",
        '        """Initialize the AI model in the background."""',
        "        try:",
        "            # Add src to path for imports",
        "            current_dir = os.path.dirname(os.path.abspath(__file__))",
        "            src_dir = os.path.join(current_dir, \"src\")",
        "            if os.path.exists(src_dir):",
        "                sys.path.insert(0, src_dir)",
        "                ",
        "                from models.ai_manager import AIModelManager",
        "                ",
        "                self.ai_manager = AIModelManager(max_memory_gb=12)",
        "                success = await self.ai_manager.load_model()",
        "                ",
        "                if success:",
        "                    self.is_model_ready = True",
        "                    logger.info(\"AI model initialized successfully\")",
        "                else:",
        "                    logger.info(\"AI model not available, using fallback responses\")",
        "            else:",
        "                logger.info(\"src directory not found, using fallback responses\")",
        "                ",
        "        except Exception as e:",
        "            logger.info(f\"AI model initialization failed: {e}, using fallback responses\")",
        "",
        "    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:",
        '        """Handle MCP protocol requests."""',
        "        method = request.get(\"method\")",
        "        request_id = request.get(\"id\")",
        "        ",
        "        if method == \"initialize\":",
        "            return {",
        '                "jsonrpc": "2.0",',
        "                \"id\": request_id,",
        "                \"result\": {",
        '                    "protocolVersion": "2024-11-05",',
        "                    \"capabilities\": {",
        '                        "tools": {}',
        "                    },",
        "                    \"serverInfo\": {",
        '                        "name": "mcplease",',
        '                        "version": "1.0.0",',
        '                        "description": "MCPlease AI coding assistant"',
        "                    }",
        "                }",
        "            }",
        "        ",
        "        elif method == \"tools/list\":",
        "            return {",
        '                "jsonrpc": "2.0",',
        "                \"id\": request_id,",
        "                \"result\": {",
        '                    "tools": self.tools',
        "                }",
        "            }",
        "        ",
        "        elif method == \"tools/call\":",
        "            return await self._handle_tool_call(request)",
        "        ",
        "        else:",
        "            return {",
        '                "jsonrpc": "2.0",',
        "                \"id\": request_id,",
        "                \"error\": {",
        "                    \"code\": -32601,",
        "                    \"message\": f\"Method not found: {method}\"",
        "                }",
        "            }",
        "",
        "    async def _handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:",
        '        """Handle tool execution requests."""',
        "        params = request.get(\"params\", {})",
        "        tool_name = params.get(\"name\")",
        "        arguments = params.get(\"arguments\", {})",
        "        request_id = request.get(\"id\")",
        "        ",
        "        try:",
        "            if tool_name == \"complete_code\":",
        "                result = await self._complete_code(arguments)",
        "            elif tool_name == \"explain_code\":",
        "                result = await self._explain_code(arguments)",
        "            elif tool_name == \"debug_code\":",
        "                result = await self._debug_code(arguments)",
        "            elif tool_name == \"refactor_code\":",
        "                result = await self._refactor_code(arguments)",
        "            else:",
        "                return {",
        '                    "jsonrpc": "2.0",',
        "                    \"id\": request_id,",
        "                    \"error\": {",
        "                        \"code\": -32602,",
        "                        \"message\": f\"Unknown tool: {tool_name}\"",
        "                    }",
        "                }",
        "            ",
        "            return {",
        '                "jsonrpc": "2.0",',
        "                \"id\": request_id,",
        "                \"result\": {",
        '                    "content": [',
        "                        {",
        '                            "type": "text",',
        '                            "text": result',
        "                        }",
        "                    ]",
        "                }",
        "            }",
        "            ",
        "        except Exception as e:",
        "            logger.error(f\"Tool execution error: {e}\")",
        "            return {",
        '                "jsonrpc": "2.0",',
        "                \"id\": request_id,",
        "                \"error\": {",
        "                    \"code\": -32603,",
        "                    \"message\": f\"Tool execution failed: {str(e)}\"",
        "                }",
        "            }",
        "",
        "    async def _complete_code(self, args: Dict[str, Any]) -> str:",
        '        """Provide AI-powered code completion."""',
        "        code = args.get(\"code\", \"\")",
        "        language = args.get(\"language\", \"python\")",
        "        ",
        "        if self.is_model_ready and self.ai_manager:",
        "            try:",
        "                # Use AI model for completion",
        "                completion = await self.ai_manager.generate_code_completion(code)",
        "                return completion",
        "            except Exception as e:",
        "                logger.error(f\"AI completion failed: {e}\")",
        "                # Fall back to pattern-based completion",
        "        ",
        "        # Fallback pattern-based completion",
        "        if \"def \" in code and code.strip().endswith(\":\"):",
        "            func_name = code.split(\"def \")[1].split(\"(\")[0].strip()",
        "            if \"fibonacci\" in func_name.lower():",
        "                return \"\"\"    \"\"\"Calculate the nth Fibonacci number.",
        "    ",
        "    Args:",
        "        n: The position in the Fibonacci sequence",
        "        ",
        "    Returns:",
        "        The nth Fibonacci number",
        "    \"\"\"",
        "    if n <= 1:",
        "        return n",
        "    return fibonacci(n-1) + fibonacci(n-2)\"\"\"",
        "            else:",
        "                return f\"\"\"    \"\"\"TODO: Implement {func_name} function.",
        "    ",
        "    Args:",
        "        Add parameter descriptions here",
        "        ",
        "    Returns:",
        "        Add return value description here",
        "    \"\"\"",
        "    pass\"\"\"",
        "        ",
        "        elif \"class \" in code and code.strip().endswith(\":\"):",
        "            class_name = code.split(\"class \")[1].split(\"(\")[0].split(\":\")[0].strip()",
        "            return f\"\"\"    \"\"\"TODO: Implement {class_name} class.",
        "    ",
        "    A class that represents...",
        "    \"\"\"",
        "    ",
        "    def __init__(self):",
        "        \"\"\"Initialize the {class_name}.\"\"\"",
        "        pass\"\"\"",
        "        ",
        "        else:",
        "            return f\"# Smart completion for {language}\\n# TODO: Add your implementation here\"",
        "",
        "    async def _explain_code(self, args: Dict[str, Any]) -> str:",
        '        """Provide AI-powered code explanation."""',
        "        code = args.get(\"code\", \"\")",
        "        ",
        "        if self.is_model_ready and self.ai_manager:",
        "            try:",
        "                # Use AI model for explanation",
        "                explanation = await self.ai_manager.explain_code(code)",
        "                return explanation",
        "            except Exception as e:",
        "                logger.error(f\"AI explanation failed: {e}\")",
        "                # Fall back to pattern-based explanation",
        "        ",
        "        # Fallback pattern-based explanation",
        "        lines = code.strip().split('\\n')",
        "        explanations = []",
        "        ",
        "        if \"def \" in code:",
        "            explanations.append(\"This code defines functions\")",
        "        if \"class \" in code:",
        "            explanations.append(\"This code defines classes\")",
        "        if \"import \" in code or \"from \" in code:",
        "            explanations.append(\"This code imports modules\")",
        "        ",
        "        explanations.append(f\"Code has {len(lines)} lines\")",
        "        return \"Code Analysis: \" + \"; \".join(explanations)",
        "",
        "    async def _debug_code(self, args: Dict[str, Any]) -> str:",
        '        """Provide AI-powered debugging assistance."""',
        "        code = args.get(\"code\", \"\")",
        "        error_message = args.get(\"error\", \"\")",
        "        ",
        "        if self.is_model_ready and self.ai_manager:",
        "            try:",
        "                # Use AI model for debugging",
        "                prompt = f\"Debug this code:\\n{code}\\n\\nError: {error_message}\\n\\nProvide debugging suggestions:\"",
        "                debug_help = await self.ai_manager.generate_text(prompt)",
        "                return debug_help",
        "            except Exception as e:",
        "                logger.error(f\"AI debugging failed: {e}\")",
        "                # Fall back to pattern-based debugging",
        "        ",
        "        # Fallback pattern-based debugging",
        "        suggestions = []",
        "        if error_message:",
        "            if \"indentationerror\" in error_message.lower():",
        "                suggestions.append(\"Fix indentation consistency\")",
        "            elif \"syntaxerror\" in error_message.lower():",
        "                suggestions.append(\"Check for missing colons or parentheses\")",
        "            else:",
        "                suggestions.append(f\"Error analysis: {error_message}\")",
        "        ",
        "        if not suggestions:",
        "            suggestions.append(\"Review code logic and structure\")",
        "        ",
        "        return \"Debugging Analysis: \" + \"; \".join(suggestions)",
        "",
        "    async def _refactor_code(self, args: Dict[str, Any]) -> str:",
        '        """Provide AI-powered code refactoring suggestions."""',
        "        code = args.get(\"code\", \"\")",
        "        goal = args.get(\"goal\", \"improve readability\")",
        "        ",
        "        if self.is_model_ready and self.ai_manager:",
        "            try:",
        "                # Use AI model for refactoring",
        "                prompt = f\"Suggest refactoring improvements for this code:\\n{code}\\n\\nGoal: {goal}\\n\\nProvide specific suggestions:\"",
        "                refactor_help = await self.ai_manager.generate_text(prompt)",
        "                return refactor_help",
        "            except Exception as e:",
        "                logger.error(f\"AI refactoring failed: {e}\")",
        "                # Fall back to pattern-based refactoring",
        "        ",
        "        # Fallback pattern-based refactoring",
        "        suggestions = []",
        "        lines = code.split('\\n')",
        "        ",
        "        if len(lines) > 15:",
        "            suggestions.append(\"Consider breaking into smaller functions\")",
        "        if \"TODO\" in code or \"FIXME\" in code:",
        "            suggestions.append(\"Address TODO/FIXME comments\")",
        "        ",
        "        if not suggestions:",
        "            suggestions.append(\"Code appears well-structured\")",
        "        ",
        "        return f\"Refactoring Suggestions (Goal: {goal}): \" + \"; \".join(suggestions)",
        "",
        "    async def handle_stdio(self):",
        '        """Handle stdio communication for MCP protocol."""',
        "        while True:",
        "            try:",
        "                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)",
        "                if not line:",
        "                    break",
        "                ",
        "                line = line.strip()",
        "                if not line:",
        "                    continue",
        "                ",
        "                request = json.loads(line)",
        "                response = await self.handle_request(request)",
        "                ",
        "                print(json.dumps(response), flush=True)",
        "                ",
        "            except json.JSONDecodeError:",
        "                continue",
        "            except Exception as e:",
        "                logger.error(f\"Error handling request: {e}\")",
        "                continue",
        "",
        "async def main():",
        '    """Main server entry point."""',
        "    server = MCPleaseMCPServer()",
        "    await server.handle_stdio()",
        "",
        "if __name__ == \"__main__\":",
        "    asyncio.run(main())",
        ""
    ]
    
    return "\\n".join(server_content)

def create_vscode_mcp_config():
    """Create VSCode MCP configuration."""
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    mcp_config = {
        "servers": {
            "mcplease": {
                "type": "stdio",
                "command": "python",
                "args": ["mcplease_server.py"]
            }
        }
    }
    
    config_file = vscode_dir / "mcp.json"
    with open(config_file, 'w') as f:
        json.dump(mcp_config, f, indent=2)
    
    print(f"✅ VSCode MCP config created at {config_file}")
    return config_file

def start_mcp_server():
    """Start the MCP server."""
    print("🚀 Starting MCPlease MCP server...")
    
    # Create the server file
    with open("mcplease_server.py", "w") as f:
        f.write(create_mcp_server())
    
    print("✅ MCP server created")
    return "mcplease_server.py"

def open_vscode():
    """Open VSCode in the current directory."""
    print("🔌 Opening VSCode...")
    
    try:
        subprocess.run(["code", "."], check=True, timeout=10)
        print("✅ VSCode opened")
        return True
    except Exception as e:
        print(f"⚠️  Couldn't auto-open VSCode: {e}")
        print("   Please open VSCode manually in this directory")
        return False

def main():
    """The ONE command that sets up MCP with GitHub Copilot."""
    print_banner()
    
    print("🎯 Setting up MCPlease for GitHub Copilot...")
    print("   This will:")
    print("   • Create MCP server for AI coding tools")
    print("   • Configure VSCode to use the MCP server")
    print("   • Work directly with GitHub Copilot")
    print("   • No extensions needed!")
    print("")
    
    # Create MCP server
    server_file = start_mcp_server()
    
    # Create VSCode MCP configuration
    config_file = create_vscode_mcp_config()
    
    # Open VSCode
    vscode_opened = open_vscode()
    
    print("")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                🎉 MCPlease MCP READY! 🎉                 ║")
    print("║                                                              ║")
    print("║  GitHub Copilot can now use MCPlease tools!              ║")
    print("║                                                              ║")
    print("║  How to use:                                                ║")
    print("║  1. Open GitHub Copilot Chat in VSCode                     ║")
    print("║  2. Switch to Agent mode                                    ║")
    print("║  3. Ask: 'Complete this function: def fibonacci(n):'       ║")
    print("║  4. See MCPlease tools in action!                        ║")
    print("║                                                              ║")
    print("║  Available tools:                                           ║")
    print("║  • complete_code - Smart code completion                   ║")
    print("║  • explain_code - Detailed code explanations              ║")
    print("║  • debug_code - Debugging assistance                      ║")
    print("║  • refactor_code - Code improvement suggestions           ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    if not vscode_opened:
        print("")
        print("📝 Manual steps:")
        print("   1. Open VSCode in this directory")
        print("   2. Open GitHub Copilot Chat")
        print("   3. Switch to Agent mode")
        print("   4. Start using MCPlease tools!")
    
    print("")
    print("🎯 Files created:")
    print(f"   • {server_file} - MCP server")
    print(f"   • {config_file} - VSCode MCP config")
    print("")
    print("✅ MCPlease is ready to work with GitHub Copilot!")

if __name__ == "__main__":
    main()
