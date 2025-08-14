#!/usr/bin/env python3
"""Simple AI-powered MCP server that works out of the box.

This server provides AI-powered code completion and explanation with fallback
to mock responses when the full AI model is not available.
"""

import asyncio
import json
import logging
import sys
import time
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import error handling
try:
    from utils.error_handler import handle_error, safe_execute_async, async_error_boundary
except ImportError:
    # Fallback if error handler not available
    def handle_error(error, context=""):
        logging.error(f"Error in {context}: {error}")
        return None
    
    def safe_execute_async(func, *args, fallback_result=None, context="", **kwargs):
        async def wrapper():
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error in {context}: {e}")
                return fallback_result
        return wrapper()
    
    def async_error_boundary(fallback_result=None, context=""):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logging.error(f"Error in {context or func.__name__}: {e}")
                    return fallback_result
            return wrapper
        return decorator

# Configure logging for MCP protocol (stderr only)
logging.basicConfig(
    level=logging.INFO, 
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleAIMCPServer:
    """Simple AI-powered MCP server with fallback capabilities."""
    
    def __init__(self, enable_ai: bool = True):
        """Initialize the simple AI MCP server.
        
        Args:
            enable_ai: Whether to attempt AI model loading
        """
        self.enable_ai = enable_ai
        self.ai_manager = None
        self.is_model_ready = False
        self.initialization_error = None
        
        # Define available tools
        self.tools = {
            "code_completion": {
                "name": "code_completion",
                "description": "Generate intelligent code completions and suggestions",
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
                "description": "Get server status and capabilities",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "restart_ai": {
                "name": "restart_ai",
                "description": "Restart the AI model (if available)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "health_check": {
                "name": "health_check",
                "description": "Perform comprehensive health check",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        
        logger.info(f"SimpleAIMCPServer initialized (AI enabled: {enable_ai})")
    
    @async_error_boundary(fallback_result=False, context="AI model initialization")
    async def initialize_ai_model(self) -> bool:
        """Attempt to initialize the AI model with comprehensive error handling.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if not self.enable_ai:
            logger.info("AI model initialization skipped (disabled)")
            return False
        
        logger.info("Attempting AI model initialization...")
        
        try:
            # Try to import and initialize AI manager
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, current_dir)
            
            from models.ai_manager import AIModelManager
            
            self.ai_manager = AIModelManager(max_memory_gb=12)
            success = await self.ai_manager.load_model()
            
            if success:
                self.is_model_ready = True
                logger.info("AI model initialized successfully")
                return True
            else:
                self.initialization_error = "Model loading failed - using intelligent fallbacks"
                logger.info("AI model not available, using intelligent fallback responses")
                return False
                
        except ImportError as e:
            self.initialization_error = f"AI dependencies not available: {e}"
            logger.info("AI model dependencies not found, using intelligent fallback responses")
            handle_error(e, "AI model import")
            return False
        except Exception as e:
            self.initialization_error = f"AI initialization error: {e}"
            logger.info(f"AI model initialization failed ({e}), using intelligent fallback responses")
            handle_error(e, "AI model initialization")
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
        # Initialize AI model in background if enabled
        if self.enable_ai and not self.is_model_ready and not self.initialization_error:
            asyncio.create_task(self.initialize_ai_model())
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "simple-ai-mcp-server",
                    "version": "1.0.0",
                    "description": "Simple AI-powered coding assistant with fallback support"
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
            elif tool_name == "restart_ai":
                result = await self._restart_ai(arguments)
            elif tool_name == "health_check":
                result = await self._health_check(arguments)
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
    
    @async_error_boundary(fallback_result="# Error generating completion", context="code completion")
    async def _generate_code_completion(self, args: Dict[str, Any]) -> str:
        """Generate code completion (AI or fallback) with error handling."""
        code = args.get("code", "")
        language = args.get("language", "python")
        
        # Validate input
        if not code or not isinstance(code, str):
            return "# Please provide valid code for completion"
        
        # Try AI completion first
        if self.is_model_ready and self.ai_manager:
            try:
                completion = await self.ai_manager.generate_code_completion(code)
                return f"# AI-powered completion:\n{completion}"
            except Exception as e:
                logger.debug(f"AI completion failed, using fallback: {e}")
                handle_error(e, "AI code completion")
        
        # Fallback to rule-based completion
        try:
            return self._fallback_completion(code, language)
        except Exception as e:
            logger.error(f"Fallback completion failed: {e}")
            handle_error(e, "fallback code completion")
            return f"# Completion error - please check your code syntax\n# Original: {code[:50]}..."
    
    @async_error_boundary(fallback_result="# Error generating explanation", context="code explanation")
    async def _explain_code(self, args: Dict[str, Any]) -> str:
        """Generate code explanation (AI or fallback) with error handling."""
        code = args.get("code", "")
        question = args.get("question")
        
        # Validate input
        if not code or not isinstance(code, str):
            return "# Please provide valid code for explanation"
        
        # Try AI explanation first
        if self.is_model_ready and self.ai_manager:
            try:
                explanation = await self.ai_manager.explain_code(code, question)
                return f"# AI-powered explanation:\n{explanation}"
            except Exception as e:
                logger.debug(f"AI explanation failed, using fallback: {e}")
                handle_error(e, "AI code explanation")
        
        # Fallback to rule-based explanation
        try:
            return self._fallback_explanation(code)
        except Exception as e:
            logger.error(f"Fallback explanation failed: {e}")
            handle_error(e, "fallback code explanation")
            return f"# Explanation error - code appears to be {len(code)} characters long"
    
    @async_error_boundary(fallback_result="# Error generating debug help", context="code debugging")
    async def _debug_code(self, args: Dict[str, Any]) -> str:
        """Generate debugging assistance (AI or fallback) with error handling."""
        code = args.get("code", "")
        error_message = args.get("error_message", "")
        
        # Validate input
        if not code or not isinstance(code, str):
            return "# Please provide valid code for debugging assistance"
        
        # Try AI debugging first
        if self.is_model_ready and self.ai_manager:
            try:
                prompt = f"Debug this code:\n\nCode:\n{code}\n\nError: {error_message}\n\nAnalysis:"
                debug_help = await self.ai_manager.generate_text(prompt, max_tokens=300)
                return f"# AI-powered debugging:\n{debug_help}"
            except Exception as e:
                logger.debug(f"AI debugging failed, using fallback: {e}")
                handle_error(e, "AI code debugging")
        
        # Fallback to rule-based debugging
        try:
            return self._fallback_debug(code, error_message)
        except Exception as e:
            logger.error(f"Fallback debugging failed: {e}")
            handle_error(e, "fallback code debugging")
            return f"# Debug error - please check your code and error message\n# Code length: {len(code)} characters"
    
    async def _get_server_status(self, args: Dict[str, Any]) -> str:
        """Get server status."""
        status_lines = [
            "Simple AI MCP Server Status",
            "=" * 30,
            ""
        ]
        
        if self.is_model_ready:
            status_lines.extend([
                "🤖 AI Model: ✅ READY",
                "   Full AI-powered responses available",
                ""
            ])
        elif self.initialization_error:
            status_lines.extend([
                "🤖 AI Model: ❌ ERROR",
                f"   Error: {self.initialization_error}",
                "   Using fallback responses",
                ""
            ])
        elif self.enable_ai:
            status_lines.extend([
                "🤖 AI Model: ⏳ LOADING",
                "   Please wait for initialization...",
                ""
            ])
        else:
            status_lines.extend([
                "🤖 AI Model: ⏸️ DISABLED",
                "   Using fallback responses only",
                ""
            ])
        
        # Add system info
        import psutil
        memory = psutil.virtual_memory()
        status_lines.extend([
            "💻 System Info:",
            f"   Memory: {memory.total / (1024**3):.1f}GB total, {memory.available / (1024**3):.1f}GB available",
            f"   Python: {sys.version.split()[0]}",
            ""
        ])
        
        # Add available tools
        status_lines.extend([
            "🔧 Available Tools:",
            *[f"   - {tool}" for tool in self.tools.keys()],
            ""
        ])
        
        return "\n".join(status_lines)
    
    @async_error_boundary(fallback_result="# Error restarting AI", context="AI restart")
    async def _restart_ai(self, args: Dict[str, Any]) -> str:
        """Restart the AI model."""
        if not self.enable_ai:
            return "AI model is disabled - restart not applicable"
        
        try:
            logger.info("Restarting AI model...")
            
            # Unload current model if loaded
            if self.ai_manager:
                try:
                    await self.ai_manager.unload_model()
                except Exception as e:
                    logger.warning(f"Error unloading model: {e}")
            
            # Reset state
            self.ai_manager = None
            self.is_model_ready = False
            self.initialization_error = None
            
            # Wait a moment for cleanup
            await asyncio.sleep(2.0)
            
            # Attempt to reinitialize
            success = await self.initialize_ai_model()
            
            if success:
                return "✅ AI model restarted successfully"
            else:
                return f"⚠️ AI model restart failed: {self.initialization_error}\nUsing fallback responses"
                
        except Exception as e:
            logger.error(f"AI restart failed: {e}")
            handle_error(e, "AI model restart")
            return f"❌ AI restart error: {e}\nUsing fallback responses"
    
    @async_error_boundary(fallback_result="# Error performing health check", context="health check")
    async def _health_check(self, args: Dict[str, Any]) -> str:
        """Perform comprehensive health check."""
        health_report = []
        health_report.append("MCPlease Health Check Report")
        health_report.append("=" * 35)
        health_report.append("")
        
        overall_status = "✅ HEALTHY"
        issues = []
        
        try:
            # Check system resources
            import psutil
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Calculate memory percentage
            memory_percent = (memory.used / memory.total) * 100
            
            health_report.append("💻 System Resources:")
            health_report.append(f"   Memory: {memory_percent:.1f}% used ({memory.available / (1024**3):.1f}GB available)")
            health_report.append(f"   CPU: {cpu_percent:.1f}% usage")
            
            if memory_percent > 90:
                issues.append("High memory usage detected")
            if cpu_percent > 80:
                issues.append("High CPU usage detected")
            
            health_report.append("")
            
            # Check AI model status
            health_report.append("🤖 AI Model Status:")
            if self.is_model_ready:
                health_report.append("   Status: ✅ Ready and functional")
                
                # Test AI functionality
                try:
                    test_result = await asyncio.wait_for(
                        self._generate_code_completion({"code": "def test():", "language": "python"}),
                        timeout=10.0
                    )
                    if test_result and len(test_result) > 10:
                        health_report.append("   Functionality: ✅ Working correctly")
                    else:
                        health_report.append("   Functionality: ⚠️ Limited response")
                        issues.append("AI model producing limited responses")
                except asyncio.TimeoutError:
                    health_report.append("   Functionality: ❌ Timeout during test")
                    issues.append("AI model response timeout")
                except Exception as e:
                    health_report.append(f"   Functionality: ❌ Error during test: {e}")
                    issues.append("AI model functionality error")
                    
            elif self.initialization_error:
                health_report.append(f"   Status: ❌ Error - {self.initialization_error}")
                health_report.append("   Fallback: ✅ Intelligent responses available")
                issues.append("AI model not available")
            else:
                health_report.append("   Status: ⏳ Initializing...")
                health_report.append("   Fallback: ✅ Intelligent responses available")
            
            health_report.append("")
            
            # Check MCP protocol functionality
            health_report.append("🔌 MCP Protocol:")
            health_report.append(f"   Tools Available: {len(self.tools)}")
            health_report.append("   Communication: ✅ Active")
            health_report.append("")
            
            # Check error history if available
            try:
                from utils.error_handler import global_error_handler
                error_summary = global_error_handler.get_error_summary()
                
                health_report.append("🚨 Error History:")
                if error_summary["total_errors"] == 0:
                    health_report.append("   Errors: ✅ No errors recorded")
                else:
                    health_report.append(f"   Total Errors: {error_summary['total_errors']}")
                    for category, count in error_summary["by_category"].items():
                        health_report.append(f"   {category}: {count}")
                    
                    if error_summary["total_errors"] > 10:
                        issues.append("High error count detected")
                
                health_report.append("")
            except ImportError:
                health_report.append("🚨 Error History: Not available")
                health_report.append("")
            
            # Overall assessment
            if issues:
                overall_status = "⚠️ ISSUES DETECTED"
                health_report.append("⚠️ Issues Found:")
                for issue in issues:
                    health_report.append(f"   • {issue}")
                health_report.append("")
                health_report.append("💡 Recommendations:")
                health_report.append("   • Monitor system resources")
                health_report.append("   • Consider restarting if issues persist")
                health_report.append("   • Check logs for detailed error information")
            else:
                health_report.append("✅ All systems operating normally")
            
            health_report.insert(2, f"Overall Status: {overall_status}")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            handle_error(e, "health check")
            health_report.append(f"❌ Health check error: {e}")
        
        return "\n".join(health_report)
    
    def _fallback_completion(self, code: str, language: str) -> str:
        """Provide intelligent fallback code completion."""
        # Enhanced rule-based completion
        code_lower = code.lower().strip()
        
        if "def " in code and code.strip().endswith(":"):
            func_name = code.split("def ")[1].split("(")[0].strip()
            return f"""    \"\"\"TODO: Implement {func_name} function.\"\"\"
    pass"""
        
        elif "class " in code and code.strip().endswith(":"):
            class_name = code.split("class ")[1].split("(")[0].split(":")[0].strip()
            return f"""    \"\"\"TODO: Implement {class_name} class.\"\"\"
    
    def __init__(self):
        pass"""
        
        elif any(keyword in code for keyword in ["if ", "elif "]) and code.strip().endswith(":"):
            return "    # TODO: Add condition logic\n    pass"
        
        elif "for " in code and code.strip().endswith(":"):
            return "    # TODO: Add loop body\n    pass"
        
        elif "while " in code and code.strip().endswith(":"):
            return "    # TODO: Add loop body\n    pass"
        
        elif "try:" in code:
            return """    # TODO: Add try block code
    pass
except Exception as e:
    # TODO: Handle exception
    pass"""
        
        elif language == "javascript" and code.strip().endswith("{"):
            return "    // TODO: Implement function body\n}"
        
        elif language == "java" and "public" in code and code.strip().endswith("{"):
            return "    // TODO: Implement method body\n}"
        
        else:
            return f"""# Fallback completion for {language}
# Context: {code[:50]}{'...' if len(code) > 50 else ''}
# TODO: Add your implementation here"""
    
    def _fallback_explanation(self, code: str) -> str:
        """Provide intelligent fallback code explanation."""
        lines = code.strip().split('\n')
        explanations = []
        
        # Analyze code structure
        if "def " in code:
            func_names = [line.split("def ")[1].split("(")[0].strip() 
                         for line in lines if "def " in line]
            explanations.append(f"This code defines {len(func_names)} function(s): {', '.join(func_names)}")
        
        if "class " in code:
            class_names = [line.split("class ")[1].split("(")[0].split(":")[0].strip() 
                          for line in lines if "class " in line]
            explanations.append(f"This code defines {len(class_names)} class(es): {', '.join(class_names)}")
        
        if "import " in code:
            imports = [line.strip() for line in lines if line.strip().startswith("import ")]
            explanations.append(f"This code imports {len(imports)} module(s)")
        
        if any(keyword in code for keyword in ["if ", "elif ", "else"]):
            explanations.append("This code contains conditional logic (if/else statements)")
        
        if any(keyword in code for keyword in ["for ", "while "]):
            explanations.append("This code contains loops for iteration")
        
        if "try:" in code and "except" in code:
            explanations.append("This code includes error handling with try/except blocks")
        
        # Basic stats
        explanations.append(f"Code statistics: {len(lines)} lines, {len(code.split())} words")
        
        if not explanations:
            explanations.append("This appears to be a code snippet that may contain various programming constructs")
        
        return "Fallback code analysis:\n" + "\n".join(f"• {exp}" for exp in explanations)
    
    def _fallback_debug(self, code: str, error_message: str) -> str:
        """Provide intelligent fallback debugging help."""
        suggestions = []
        
        # Error-specific suggestions
        if error_message:
            error_lower = error_message.lower()
            if "indentationerror" in error_lower or "indentation" in error_lower:
                suggestions.append("Check your indentation - Python requires consistent spacing (4 spaces recommended)")
            elif "syntaxerror" in error_lower or "syntax" in error_lower:
                suggestions.append("Check for missing colons (:), parentheses (), brackets [], or quotes")
            elif "nameerror" in error_lower or "not defined" in error_lower:
                suggestions.append("Check if all variables and functions are defined before use")
            elif "typeerror" in error_lower:
                suggestions.append("Check if you're using the correct data types and function arguments")
            elif "indexerror" in error_lower:
                suggestions.append("Check array/list bounds - you may be accessing an index that doesn't exist")
            elif "keyerror" in error_lower:
                suggestions.append("Check dictionary keys - you may be accessing a key that doesn't exist")
            elif "attributeerror" in error_lower:
                suggestions.append("Check object attributes - you may be calling a method that doesn't exist")
            else:
                suggestions.append(f"Error type detected: {error_message}")
        
        # Code analysis suggestions
        if "print(" not in code and "return" not in code and len(code.split('\n')) > 3:
            suggestions.append("Consider adding print statements or return values for debugging")
        
        if len(code.split('\n')) > 20:
            suggestions.append("Consider breaking this into smaller, more manageable functions")
        
        # Check for common issues
        if code.count('(') != code.count(')'):
            suggestions.append("Check for unmatched parentheses")
        
        if code.count('[') != code.count(']'):
            suggestions.append("Check for unmatched square brackets")
        
        if code.count('{') != code.count('}'):
            suggestions.append("Check for unmatched curly braces")
        
        if not suggestions:
            suggestions.append("Code structure appears correct - consider checking logic and data flow")
        
        return "Fallback debugging suggestions:\n" + "\n".join(f"• {s}" for s in suggestions)
    
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
        """Handle stdio communication for MCP protocol with robust error handling."""
        logger.info("Simple AI MCP server ready for stdio communication")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                # Read request from stdin with timeout
                line = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline),
                    timeout=30.0  # 30 second timeout
                )
                
                if not line:
                    logger.info("EOF received, shutting down")
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse and handle request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON received: {e}")
                    # Send error response if we can extract an ID
                    try:
                        partial = json.loads(line.split('"id"')[1].split(',')[0].split('}')[0].strip(': '))
                        error_response = self._error_response(partial, -32700, "Parse error")
                        print(json.dumps(error_response), flush=True)
                    except:
                        pass
                    continue
                
                # Handle request with timeout
                try:
                    response = await asyncio.wait_for(
                        self.handle_request(request),
                        timeout=60.0  # 60 second timeout for request handling
                    )
                    
                    # Send response to stdout
                    print(json.dumps(response), flush=True)
                    consecutive_errors = 0  # Reset error counter on success
                    
                except asyncio.TimeoutError:
                    logger.error("Request handling timed out")
                    error_response = self._error_response(
                        request.get("id"), -32603, "Request timeout"
                    )
                    print(json.dumps(error_response), flush=True)
                
            except asyncio.TimeoutError:
                # Stdin read timeout - this is normal, continue
                continue
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in stdio handling: {e}")
                handle_error(e, "stdio communication")
                
                # If too many consecutive errors, attempt recovery
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"Too many consecutive errors ({consecutive_errors}), attempting recovery")
                    await self._attempt_recovery()
                    consecutive_errors = 0
                
                # Brief pause before continuing
                await asyncio.sleep(0.1)
    
    async def _attempt_recovery(self):
        """Attempt to recover from errors."""
        logger.info("Attempting system recovery...")
        
        try:
            # Clear any pending AI operations
            if self.ai_manager:
                # Reset AI manager state if possible
                pass
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Brief pause for recovery
            await asyncio.sleep(1.0)
            
            logger.info("Recovery attempt completed")
            
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            handle_error(e, "system recovery")
    
    async def shutdown(self):
        """Gracefully shutdown the server."""
        logger.info("Shutting down Simple AI MCP server...")
        
        if self.ai_manager:
            try:
                await self.ai_manager.unload_model()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
        
        logger.info("Simple AI MCP server shutdown complete")


async def main():
    """Main server entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple AI-powered MCP server")
    parser.add_argument("--no-ai", action="store_true", help="Disable AI model loading (fallback only)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start server
    server = SimpleAIMCPServer(enable_ai=not args.no_ai)
    
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