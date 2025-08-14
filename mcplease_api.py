#!/usr/bin/env python3
"""
MCPlease HTTP API Server
Wraps the MCP server with an OpenAI-compatible HTTP API
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn

app = FastAPI(title="MCPlease API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP server process
mcp_process = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 150
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]

def start_mcp_server():
    """Start the MCP server process."""
    global mcp_process
    
    if mcp_process is None or mcp_process.poll() is not None:
        server_path = Path(__file__).parent / "src" / "simple_ai_mcp_server.py"
        mcp_process = subprocess.Popen(
            [sys.executable, str(server_path), "--no-ai"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    
    return mcp_process

def send_mcp_request(method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Send request to MCP server."""
    process = start_mcp_server()
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    
    try:
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            return json.loads(response_line.strip())
    except Exception as e:
        print(f"MCP request error: {e}")
    
    return {"error": "MCP communication failed"}

@app.get("/")
async def root():
    return {"message": "MCPlease API Server", "status": "running"}

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": 1677610602,
                "owned_by": "mcplease"
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint."""
    
    # Extract the user message
    user_message = ""
    for msg in request.messages:
        if msg.role == "user":
            user_message = msg.content
            break
    
    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found")
    
    # Determine the tool to use based on the message
    if "complete" in user_message.lower() or "def " in user_message:
        tool_name = "code_completion"
        args = {"code": user_message, "language": "python"}
    elif "explain" in user_message.lower():
        tool_name = "explain_code"
        args = {"code": user_message}
    elif "debug" in user_message.lower() or "error" in user_message.lower():
        tool_name = "debug_code"
        args = {"code": user_message}
    else:
        tool_name = "code_completion"
        args = {"code": user_message, "language": "python"}
    
    # Send request to MCP server
    mcp_response = send_mcp_request("tools/call", {
        "name": tool_name,
        "arguments": args
    })
    
    # Extract response text
    response_text = "I'm sorry, I couldn't process that request."
    if "result" in mcp_response and "content" in mcp_response["result"]:
        content = mcp_response["result"]["content"]
        if content and len(content) > 0:
            response_text = content[0].get("text", response_text)
    
    # Format as OpenAI response
    return ChatCompletionResponse(
        id="mcplease-" + str(hash(user_message))[:8],
        created=1677610602,
        model=request.model,
        choices=[
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }
        ]
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    mcp_response = send_mcp_request("tools/call", {
        "name": "server_status",
        "arguments": {}
    })
    
    return {
        "status": "healthy",
        "mcp_server": "running" if "result" in mcp_response else "error"
    }

if __name__ == "__main__":
    print("🚀 Starting MCPlease API Server...")
    print("📡 Server will be available at http://localhost:8000")
    print("🔌 VSCode can now connect to MCPlease!")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
