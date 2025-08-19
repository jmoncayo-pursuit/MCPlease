#!/usr/bin/env python3
"""
MCPlease HTTP Server
Separate HTTP server for Continue.dev and web client integration
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from mcplease_mcp_server import MCPleaseServer
    HTTP_AVAILABLE = True
except ImportError as e:
    print(f"❌ Required dependencies not found: {e}")
    print("💡 Please install: pip install fastapi uvicorn")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTTP transport models
class HTTPToolCall(BaseModel):
    name: str
    arguments: dict = {}

class HTTPToolResult(BaseModel):
    content: list
    isError: bool = False

class HTTPTransport:
    """HTTP transport for MCP server - enables Continue.dev and web client integration"""
    
    def __init__(self, server: MCPleaseServer):
        self.server = server
        self.app = FastAPI(title="MCPlease MCP Server", version="1.0.0")
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # For development - restrict in production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup HTTP endpoints that mirror MCP protocol"""
        
        @self.app.get("/")
        async def root():
            return {
                "name": "MCPlease MCP Server",
                "version": "1.0.0",
                "transport": "HTTP",
                "status": "running",
                "description": "Offline AI coding assistant with OSS-20B model"
            }
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            try:
                health_result = await self.server._health_check()
                return json.loads(health_result)
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        @self.app.get("/tools")
        async def list_tools():
            """List available MCP tools"""
            try:
                from mcp.types import ListToolsRequest
                tools_result = await self.server.list_tools(ListToolsRequest(method="tools/list"))
                return {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools_result.tools
                    ]
                }
            except Exception as e:
                logger.error(f"Tools endpoint error: {e}")
                return {"tools": [], "error": str(e)}
        
        @self.app.post("/tools/call")
        async def call_tool(tool_call: HTTPToolCall):
            """Call an MCP tool via HTTP"""
            try:
                from mcp.types import CallToolRequest, CallToolRequestParams
                result = await self.server.call_tool(
                    CallToolRequest(
                        method="tools/call",
                        params=CallToolRequestParams(
                            name=tool_call.name,
                            arguments=tool_call.arguments
                        )
                    )
                )
                
                # Convert MCP result to HTTP response
                content = []
                for item in result.content:
                    if hasattr(item, 'type') and item.type == 'text':
                        content.append({"type": "text", "text": item.text})
                    elif hasattr(item, 'type') and item.type == 'image':
                        content.append({"type": "image", "image": item.image})
                    else:
                        content.append({"type": "text", "text": str(item)})
                
                return HTTPToolResult(content=content)
                
            except Exception as e:
                logger.error(f"Tool call error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/mcp/initialize")
        async def initialize():
            """MCP initialize endpoint"""
            try:
                from mcp.server.models import InitializationOptions
                init_options = InitializationOptions(
                    protocol_version="2024-11-05",
                    server_name="MCPlease",
                    server_version="1.0.0",
                    capabilities={},
                    client_info={
                        "name": "HTTP Client",
                        "version": "1.0.0"
                    }
                )
                return {"status": "initialized", "options": init_options.dict()}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

def main():
    """Start the HTTP server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCPlease HTTP Server")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port")
    args = parser.parse_args()
    
    # Create MCP server instance
    server = MCPleaseServer()
    
    logger.info("🚀 Starting MCPlease HTTP Server...")
    logger.info("🏗️  Built for AI-Native Builders")
    logger.info("🌐 HTTP server starting on %s:%d", args.host, args.port)
    logger.info("🔗 Continue.dev compatible endpoint: http://%s:%d", args.host, args.port)
    
    # Create and run HTTP transport
    transport = HTTPTransport(server)
    
    # Run with uvicorn
    uvicorn.run(
        transport.app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
