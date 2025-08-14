#!/usr/bin/env python3
"""AI-powered MCP server using the integrated AI model manager.

This server replaces mock implementations with real AI-powered code completion
and explanation using the gpt-oss-20b model with memory optimization.
"""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import with absolute paths
import os
import sys

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from models.ai_manager import AIModelManager, ModelConfig
from utils.logging import get_logger

# Configure logging for MCP protocol (stderr only)
logging.basicConfig(
    level=logging.INFO, 
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)


class AIMCPServer:
    """AI-powered MCP server with real model integration."""
    
    def __init__(self, model_path: Optional[str] = None, max_memory_gb: int = 12):
        """Initialize the AI MCP server.
        
        Args:
            model_path: Optional path to pre-downloaded model
            max_memory_gb: Maximum memory to use for model loading
        """
        self.ai_manager = AIModelManager(model_path=model_path, max_memory_gb=max_memory_gb)
        self.is_model_ready = False
        self.initialization_error = None
        
        # Define available tools
        self.tools = {
            "code_completion": {
                "name": "code_completion",
                "description": "Generate intelligent code completions and suggestions using AI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string", 
                            "description": "Code context for completion"
                        },
                        "language": {
                            "type": "string", 
                            "description": "Programming language (python, javascript, java, etc.)",
                            "default": "python"
                        },
                        "cursor_position": {
                            "type": "integer",
                            "description": "Cursor position in the code (optional)"
                        }
                    },
                    "required": ["code"]
                }
            },
            "explain_code": {
                "name": "explain_code",
                "description": "Explain code functionality with AI-powered analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to explain"
                        },
                        "question": {
                            "type": "string",
                            "description": "Specific question about the code (optional)"
                        }
                    },
                    "required": ["code"]
                }
            },
            "debug_code": {
                "name": "debug_code",
                "description": "Help debug code issues and suggest fixes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code with potential issues"
                        },
                        "error_message": {
                            "type": "string",
                            "description": "Error message or description of the problem (optional)"
                        }
                    },
                    "required": ["code"]
                }
            },
            "server_status": {
                "name": "server_status",
                "description": "Get AI model server status and performance metrics",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        
        logger.info("AIMCPServer initialized")
    
    async def initialize_model(self) -> bool:
        """Initialize the AI model asynchronously.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        logger.info("Starting AI model initialization...")
        
        try:
            # Load the model with memory optimization
            success = await self.ai_manager.load_model()
            
            if success:
                self.is_model_ready = True
                logger.info("AI model initialized successfully")
                
                # Log model status
                status = self.ai_manager.get_model_status()
                logger.info(f"Model ready with {status['config']['quantization']} quantization")
                logger.info(f"Memory usage: {status['memory']['used_percent']:.1%}")
                
                return True
            else:
                self.initialization_error = "Model loading failed"
                logger.error("AI model initialization failed")
                return False
                
        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"AI model initialization error: {e}")
            return False
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP protocol requests."""
        method = request.get("method")
        request_id = request.get("id")
        
        logger.debug(f"Handling request: {method}")
        
        if method == "initialize":
            return await self._handle_initialize(request_id)
        elif method == "tools/list":
            return self._handle_tools_list(request_id)
        elif method == "tools/call":
            return await self._handle_tool_call(request)
        else:
            return self._error_response(request_id, -32601, f"Method not found: {method}")
    
    async def _handle_initialize(self, request_id: str) -> Dict[str, Any]:
        """Handle MCP initialization request."""
        # Initialize model in background if not already done
        if not self.is_model_ready and not self.initialization_error:
            asyncio.create_task(self.initialize_model())
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "ai-mcp-server",
                    "version": "1.0.0",
                    "description": "AI-powered coding assistant with gpt-oss-20b"
                }
            }
        }
    
    def _handle_tools_list(self, request_id: str) -> Dict[str, Any]:
        """Handle tools list request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": list(self.tools.values())
            }
        }
    
    async def _handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution requests."""
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        request_id = request.get("id")
        
        logger.debug(f"Tool call: {tool_name}")
        
        try:
            if tool_name == "code_completion":
                result = await self._generate_code_completion(arguments)
            elif tool_name == "explain_code":
                result = await self._explain_code(arguments)
            elif tool_name == "debug_code":
                result = await self._debug_code(arguments)
            elif tool_name == "server_status":
                result = await self._get_server_status(arguments)
            else:
                return self._error_response(request_id, -32602, f"Unknown tool: {tool_name}")
            
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
            return self._error_response(request_id, -32603, f"Tool execution failed: {str(e)}")
    
    async def _generate_code_completion(self, args: Dict[str, Any]) -> str:
        """Generate AI-powered code completion."""
        code = args.get("code", "")
        language = args.get("language", "python")
        cursor_position = args.get("cursor_position")
        
        if not self.is_model_ready:
            if self.initialization_error:
                return f"# AI model unavailable: {self.initialization_error}\n# Fallback completion for {language}\n{self._fallback_completion(code, language)}"
            else:
                return f"# AI model loading... Please wait\n# Fallback completion for {language}\n{self._fallback_completion(code, language)}"
        
        try:
            # Use AI model for code completion
            if cursor_position is not None:
                completion = await self.ai_manager.generate_code_completion(code, cursor_position)
            else:
                completion = await self.ai_manager.generate_code_completion(code)
            
            return completion
            
        except Exception as e:
            logger.error(f"AI code completion error: {e}")
            return f"# AI completion error: {str(e)}\n# Fallback completion:\n{self._fallback_completion(code, language)}"
    
    async def _explain_code(self, args: Dict[str, Any]) -> str:
        """Generate AI-powered code explanation."""
        code = args.get("code", "")
        question = args.get("question")
        
        if not self.is_model_ready:
            if self.initialization_error:
                return f"AI model unavailable: {self.initialization_error}\n\nFallback explanation:\n{self._fallback_explanation(code)}"
            else:
                return f"AI model loading... Please wait\n\nFallback explanation:\n{self._fallback_explanation(code)}"
        
        try:
            # Use AI model for code explanation
            explanation = await self.ai_manager.explain_code(code, question)
            return explanation
            
        except Exception as e:
            logger.error(f"AI code explanation error: {e}")
            return f"AI explanation error: {str(e)}\n\nFallback explanation:\n{self._fallback_explanation(code)}"
    
    async def _debug_code(self, args: Dict[str, Any]) -> str:
        """Generate AI-powered debugging assistance."""
        code = args.get("code", "")
        error_message = args.get("error_message", "")
        
        if not self.is_model_ready:
            if self.initialization_error:
                return f"AI model unavailable: {self.initialization_error}\n\nFallback debugging help:\n{self._fallback_debug(code, error_message)}"
            else:
                return f"AI model loading... Please wait\n\nFallback debugging help:\n{self._fallback_debug(code, error_message)}"
        
        try:
            # Create debugging prompt
            if error_message:
                prompt = f"Debug this code that has an error:\n\nCode:\n{code}\n\nError: {error_message}\n\nPlease explain the issue and suggest a fix:"
            else:
                prompt = f"Review this code for potential issues and suggest improvements:\n\n{code}\n\nAnalysis:"
            
            debug_help = await self.ai_manager.generate_text(prompt, max_tokens=300, temperature=0.3)
            return debug_help
            
        except Exception as e:
            logger.error(f"AI debugging error: {e}")
            return f"AI debugging error: {str(e)}\n\nFallback debugging help:\n{self._fallback_debug(code, error_message)}"
    
    async def _get_server_status(self, args: Dict[str, Any]) -> str:
        """Get comprehensive server status."""
        try:
            if self.is_model_ready:
                status = self.ai_manager.get_model_status()
                memory_report = self.ai_manager.get_memory_report()
                
                status_text = f"""AI MCP Server Status Report
{'='*40}

Model Status: ✅ READY
Model: {status['config']['model_name']}
Quantization: {status['config']['quantization']}
Context Length: {status['config']['max_model_len']} tokens

Memory Status:
- Total: {memory_report['current_stats']['total_memory_gb']:.1f} GB
- Available: {memory_report['current_stats']['available_memory_gb']:.1f} GB  
- Used: {memory_report['current_stats']['used_percent']:.1%}
- Pressure: {memory_report['current_stats']['pressure_level'].upper()}

Performance:
- Total Requests: {status['performance']['total_requests']}
- Avg Response Time: {status['performance']['avg_inference_time']:.2f}s

Compatible Quantizations: {len(memory_report['compatible_quantizations'])}
"""
                
                if memory_report['recommendations']:
                    status_text += f"\nRecommendations:\n"
                    for rec in memory_report['recommendations']:
                        status_text += f"- {rec}\n"
                
                return status_text
                
            elif self.initialization_error:
                return f"""AI MCP Server Status Report
{'='*40}

Model Status: ❌ ERROR
Error: {self.initialization_error}

The AI model failed to load. The server will provide fallback responses.
"""
            else:
                return f"""AI MCP Server Status Report
{'='*40}

Model Status: ⏳ LOADING
The AI model is currently being loaded. Please wait...
"""
                
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return f"Status check error: {str(e)}"
    
    def _fallback_completion(self, code: str, language: str) -> str:
        """Provide fallback code completion when AI is unavailable."""
        if "def " in code and code.strip().endswith(":"):
            return "    pass  # TODO: Implement function"
        elif "class " in code and code.strip().endswith(":"):
            return "    def __init__(self):\n        pass"
        elif "if " in code and code.strip().endswith(":"):
            return "    # TODO: Add condition logic"
        elif "for " in code and code.strip().endswith(":"):
            return "    # TODO: Add loop body"
        elif "while " in code and code.strip().endswith(":"):
            return "    # TODO: Add loop body"
        else:
            return f"# {language} code completion\n# Context: {code[:50]}..."
    
    def _fallback_explanation(self, code: str) -> str:
        """Provide fallback code explanation when AI is unavailable."""
        lines = code.strip().split('\n')
        
        if "def " in code:
            return "This appears to be a function definition. Functions are reusable blocks of code that perform specific tasks."
        elif "class " in code:
            return "This is a class definition. Classes are blueprints for creating objects with shared attributes and methods."
        elif "import " in code:
            return "This contains import statements that bring external modules or libraries into your code."
        elif any(keyword in code for keyword in ["if ", "elif ", "else"]):
            return "This code contains conditional statements that execute different code paths based on conditions."
        elif any(keyword in code for keyword in ["for ", "while "]):
            return "This code contains loops that repeat execution of code blocks."
        else:
            return f"This code snippet contains {len(lines)} line(s) and {len(code.split())} words. It appears to be a {code.split()[0] if code.split() else 'empty'} code block."
    
    def _fallback_debug(self, code: str, error_message: str) -> str:
        """Provide fallback debugging help when AI is unavailable."""
        suggestions = []
        
        if error_message:
            if "IndentationError" in error_message:
                suggestions.append("Check your indentation - Python requires consistent spacing")
            elif "SyntaxError" in error_message:
                suggestions.append("Check for missing colons, parentheses, or quotes")
            elif "NameError" in error_message:
                suggestions.append("Check if all variables are defined before use")
            elif "TypeError" in error_message:
                suggestions.append("Check if you're using the correct data types")
            else:
                suggestions.append(f"Error type: {error_message}")
        
        # General code analysis
        if "print(" not in code and "return" not in code:
            suggestions.append("Consider adding print statements or return values for debugging")
        
        if len(code.split('\n')) > 20:
            suggestions.append("Consider breaking this into smaller functions")
        
        if not suggestions:
            suggestions.append("Code appears to be structured correctly")
        
        return "Debugging suggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
    
    def _error_response(self, request_id: str, code: int, message: str) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    async def handle_stdio(self):
        """Handle stdio communication for MCP protocol."""
        logger.info("AI MCP server ready for stdio communication")
        
        while True:
            try:
                # Read request from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                # Parse and handle request
                request = json.loads(line.strip())
                response = await self.handle_request(request)
                
                # Send response to stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                continue
            except Exception as e:
                logger.error(f"Error handling request: {e}")
                continue
    
    async def shutdown(self):
        """Gracefully shutdown the server."""
        logger.info("Shutting down AI MCP server...")
        
        if self.ai_manager:
            try:
                await self.ai_manager.unload_model()
                self.ai_manager.stop_memory_monitoring()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
        
        logger.info("AI MCP server shutdown complete")


async def main():
    """Main server entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-powered MCP server")
    parser.add_argument("--model-path", help="Path to pre-downloaded model")
    parser.add_argument("--max-memory", type=int, default=12, help="Maximum memory to use (GB)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start server
    server = AIMCPServer(model_path=args.model_path, max_memory_gb=args.max_memory)
    
    try:
        await server.handle_stdio()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())