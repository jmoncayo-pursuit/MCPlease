#!/usr/bin/env python3
"""
MCPlease - MCP Server for AI-Native Builders
Full MCP protocol implementation with file operations, terminal access, and OSS-20B AI
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP Protocol imports
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolRequest, CallToolResult, ListToolsRequest, ListToolsResult,
        Tool, TextContent, ImageContent, EmbeddedResource
    )
except ImportError:
    print("❌ MCP library not found. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "mcp"], check=True)
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolRequest, CallToolResult, ListToolsRequest, ListToolsResult,
        Tool, TextContent, ImageContent, EmbeddedResource
    )

# AI Model imports
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    AI_AVAILABLE = True
except ImportError:
    print("⚠️  Transformers not installed - using fallback responses")
    AI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPleaseServer(Server):
    """MCP Server with file operations, terminal access, and AI capabilities"""
    
    def __init__(self):
        super().__init__("mcplease")
        self.workspace_root = Path.cwd()
        self.ai_model = None
        self.tokenizer = None
        self._setup_ai_model()
        
    def _setup_ai_model(self):
        """Initialize the OSS-20B model if available"""
        if not AI_AVAILABLE:
            logger.warning("Using fallback AI responses")
            return
            
        try:
            model_path = Path("models/gpt-oss-20b")
            if model_path.exists():
                logger.info("Loading OSS-20B model...")
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path, 
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
                logger.info("✅ OSS-20B model loaded successfully")
            else:
                logger.warning("OSS-20B model not found at models/gpt-oss-20b")
        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")
    
    async def ai_generate(self, prompt: str, context: str = "") -> str:
        """Generate AI response using OSS-20B or fallback"""
        if self.model and self.tokenizer:
            try:
                full_prompt = f"{context}\n\n{prompt}" if context else prompt
                inputs = self.tokenizer(full_prompt, return_tensors="pt")
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=512,
                    temperature=0.7,
                    do_sample=True
                )
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                return response[len(full_prompt):].strip()
            except Exception as e:
                logger.error(f"AI generation failed: {e}")
        
        # Fallback responses for AI-native builders
        fallbacks = [
            "I can help you build that! Let me analyze the codebase first.",
            "Great idea! I'll need to examine the relevant files to implement this properly.",
            "I'm ready to help you build! What would you like me to work on?",
            "Let me search through your code to understand the current architecture."
        ]
        import random
        return random.choice(fallbacks)

    async def list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """List all available MCP tools for AI-native building"""
        tools = [
            Tool(
                name="file/read",
                description="Read contents of a file for analysis and modification",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path relative to workspace"}
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="file/write", 
                description="Write or modify file content for building and refactoring",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path relative to workspace"},
                        "content": {"type": "string", "description": "File content to write"}
                    },
                    "required": ["path", "content"]
                }
            ),
            Tool(
                name="file/list",
                description="List files in directory for codebase exploration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path (optional, defaults to workspace root)"}
                    }
                }
            ),
            Tool(
                name="terminal/run",
                description="Execute terminal commands for building, testing, and deployment",
                inputSchema={
                    "type": "object", 
                    "properties": {
                        "command": {"type": "string", "description": "Command to execute"},
                        "cwd": {"type": "string", "description": "Working directory (optional)"}
                    },
                    "required": ["command"]
                }
            ),
            Tool(
                name="codebase/search",
                description="Search codebase for patterns, functions, or text for understanding architecture",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "file_pattern": {"type": "string", "description": "File pattern to search (optional)"}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="ai/analyze",
                description="Analyze code or architecture using OSS-20B AI for intelligent building decisions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "AI prompt for analysis"},
                        "context": {"type": "string", "description": "Code or context to analyze (optional)"}
                    },
                    "required": ["prompt"]
                }
            ),
            Tool(
                name="ai/build",
                description="Generate code or architecture using OSS-20B AI based on requirements",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "requirements": {"type": "string", "description": "What to build"},
                        "context": {"type": "string", "description": "Existing code context (optional)"}
                    },
                    "required": ["requirements"]
                }
            )
        ]
        return ListToolsResult(tools=tools)

    async def call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Execute MCP tools for AI-native building"""
        tool_name = request.name
        arguments = request.arguments
        
        try:
            if tool_name == "file/read":
                result = await self._read_file(arguments.get("path", ""))
            elif tool_name == "file/write":
                result = await self._write_file(arguments.get("path", ""), arguments.get("content", ""))
            elif tool_name == "file/list":
                result = await self._list_files(arguments.get("path", "."))
            elif tool_name == "terminal/run":
                result = await self._run_terminal(arguments.get("command", ""), arguments.get("cwd"))
            elif tool_name == "codebase/search":
                result = await self._search_codebase(arguments.get("query", ""), arguments.get("file_pattern"))
            elif tool_name == "ai/analyze":
                result = await self._ai_analyze(arguments.get("prompt", ""), arguments.get("context", ""))
            elif tool_name == "ai/build":
                result = await self._ai_build(arguments.get("requirements", ""), arguments.get("context", ""))
            else:
                result = f"Unknown tool: {tool_name}"
                
            return CallToolResult(
                content=[TextContent(type="text", text=str(result))]
            )
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )

    async def _read_file(self, path: str) -> str:
        """Read file contents for analysis"""
        file_path = self.workspace_root / path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        return file_path.read_text(encoding='utf-8')

    async def _write_file(self, path: str, content: str) -> str:
        """Write content to file for building/modifying"""
        file_path = self.workspace_root / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return f"Successfully wrote {len(content)} characters to {path}"

    async def _list_files(self, path: str) -> str:
        """List files in directory for exploration"""
        dir_path = self.workspace_root / path
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        files = []
        for item in dir_path.iterdir():
            if item.is_file():
                files.append(f"📄 {item.name}")
            elif item.is_dir():
                files.append(f"📁 {item.name}/")
        
        return f"Files in {path}:\n" + "\n".join(sorted(files))

    async def _run_terminal(self, command: str, cwd: Optional[str] = None) -> str:
        """Execute terminal command for building/testing"""
        working_dir = self.workspace_root / cwd if cwd else self.workspace_root
        
        process = await asyncio.create_subprocess_exec(
            *command.split(),
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        result = f"Command: {command}\n"
        result += f"Working directory: {working_dir}\n"
        result += f"Exit code: {process.returncode}\n"
        if stdout:
            result += f"STDOUT:\n{stdout.decode()}\n"
        if stderr:
            result += f"STDERR:\n{stderr.decode()}\n"
            
        return result

    async def _search_codebase(self, query: str, file_pattern: str = "*.py") -> str:
        """Search codebase for understanding architecture"""
        results = []
        
        for file_path in self.workspace_root.rglob(file_pattern):
            try:
                content = file_path.read_text(encoding='utf-8')
                if query.lower() in content.lower():
                    results.append(f"Found in: {file_path.relative_to(self.workspace_root)}")
            except Exception:
                continue
                
        if not results:
            return f"No matches found for '{query}' in {file_pattern} files"
        
        return f"Search results for '{query}':\n" + "\n".join(results[:10])

    async def _ai_analyze(self, prompt: str, context: str = "") -> str:
        """Analyze code using OSS-20B AI"""
        return await self.ai_generate(prompt, context)

    async def _ai_build(self, requirements: str, context: str = "") -> str:
        """Generate code using OSS-20B AI"""
        prompt = f"Build this: {requirements}"
        if context:
            prompt += f"\n\nContext:\n{context}"
        
        return await self.ai_generate(prompt, context)

async def main():
    """Start the MCPlease MCP server"""
    server = MCPleaseServer()
    
    logger.info("🚀 Starting MCPlease MCP Server...")
    logger.info("🏗️  Built for AI-Native Builders")
    logger.info(" Workspace root: %s", server.workspace_root)
    logger.info("🤖 AI Model: %s", "OSS-20B" if AI_AVAILABLE else "Fallback")
    
    # Create initialization options
    init_options = InitializationOptions(
        protocol_version="2024-11-05",
        server_name="MCPlease",
        server_version="1.0.0",
        capabilities={},
        client_info={
            "name": "MCPlease",
            "version": "1.0.0"
        }
    )
    
    # Run the server with stdio
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)

if __name__ == "__main__":
    asyncio.run(main())
