#!/usr/bin/env python3
"""MCP server with actual gpt-oss-20b model."""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, List
from vllm import LLM, SamplingParams

# Disable logging to stdout for MCP protocol
logging.basicConfig(level=logging.ERROR, filename='/tmp/mcp_server.log')
logger = logging.getLogger(__name__)


class MCPServer:
    def __init__(self):
        self.llm = None
        self.tools = {
            "code_completion": {
                "name": "code_completion",
                "description": "Complete code based on context",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code context"},
                        "language": {"type": "string", "description": "Programming language"}
                    },
                    "required": ["code"]
                }
            }
        }
    
    async def initialize_model(self):
        """Load the gpt-oss-20b model."""
        logger.info("Loading gpt-oss-20b model...")
        try:
            self.llm = LLM(
                model="./models/gpt-oss-20b",
                quantization="mxfp4",
                gpu_memory_utilization=0.85,
                max_model_len=8192,
                enforce_eager=True
            )
            logger.info("Model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            # Fallback to mock responses
            self.llm = None
    
    def generate_completion(self, code: str, language: str = "python") -> str:
        """Generate code completion using the model."""
        if not self.llm:
            return f"# Mock completion for {language}\n{code}\nprint('Model not loaded')"
        
        prompt = f"Complete this {language} code:\n\n{code}"
        
        sampling_params = SamplingParams(
            temperature=0.3,
            top_p=0.9,
            max_tokens=150,
            stop=["\n\n", "```"]
        )
        
        try:
            outputs = self.llm.generate([prompt], sampling_params)
            return outputs[0].outputs[0].text.strip()
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"# Error generating completion\n{code}"
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "initialize":
            # Initialize model when MCP client connects
            await self.initialize_model()
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "offline-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": list(self.tools.values())
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "code_completion":
                code = arguments.get("code", "")
                language = arguments.get("language", "python")
                
                completion = self.generate_completion(code, language)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": completion
                            }
                        ]
                    }
                }
        
        # Default error response
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }
    
    async def handle_stdio(self):
        """Handle stdio communication for MCP."""
        logger.info("MCP server ready for stdio communication")
        
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
            except Exception as e:
                logger.error(f"Error handling request: {e}")
                continue

async def main():
    server = MCPServer()
    logger.info("Starting MCP server with gpt-oss-20b...")
    
    try:
        await server.handle_stdio()
    except KeyboardInterrupt:
        logger.info("Shutting down MCP server...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
         