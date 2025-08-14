#!/usr/bin/env python3
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn

app = FastAPI(title="MCPleasant API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

mcp_process = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 150
    temperature: Optional[float] = 0.7

def start_mcp_server():
    global mcp_process
    if mcp_process is None or mcp_process.poll() is not None:
        mcp_process = subprocess.Popen([sys.executable, "mcp_server.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return mcp_process

def send_mcp_request(method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    process = start_mcp_server()
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    
    try:
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        response_line = process.stdout.readline()
        if response_line:
            return json.loads(response_line.strip())
    except Exception:
        pass
    return {"error": "MCP communication failed"}

@app.get("/v1/models")
async def list_models():
    return {"object": "list", "data": [{"id": "gpt-3.5-turbo", "object": "model", "created": 1677610602, "owned_by": "mcpleasant"}]}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    user_message = ""
    for msg in request.messages:
        if msg.role == "user":
            user_message = msg.content
            break
    
    if not user_message:
        user_message = "help"
    
    # Determine tool based on message
    if "complete" in user_message.lower() or "def " in user_message or user_message.endswith(":"):
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
    
    mcp_response = send_mcp_request("tools/call", {"name": tool_name, "arguments": args})
    
    response_text = "I can help you with code completion, explanation, and debugging."
    if "result" in mcp_response and "content" in mcp_response["result"]:
        content = mcp_response["result"]["content"]
        if content and len(content) > 0:
            response_text = content[0].get("text", response_text)
    
    return {
        "id": f"mcpleasant-{hash(user_message) % 10000}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": response_text},
            "finish_reason": "stop"
        }]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
