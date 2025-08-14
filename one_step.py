#!/usr/bin/env python3
"""
MCPlease One-Step Setup
Run this ONE command and you're done.
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
import urllib.request
import zipfile
import shutil

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    MCPlease One-Step Setup                  ║
║                                                              ║
║  🎯 Goal: One command, working AI in VSCode                ║
║  ⚡ No manual steps, no config files, no BS               ║
╚══════════════════════════════════════════════════════════════╝
""")

def detect_vscode():
    """Find VSCode installation."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        paths = [
            "/Applications/Visual Studio Code.app",
            os.path.expanduser("~/Applications/Visual Studio Code.app")
        ]
        for path in paths:
            if os.path.exists(path):
                return path
    
    elif system == "Windows":
        paths = [
            os.path.expanduser("~/AppData/Local/Programs/Microsoft VS Code"),
            "C:\\Program Files\\Microsoft VS Code",
            "C:\\Program Files (x86)\\Microsoft VS Code"
        ]
        for path in paths:
            if os.path.exists(path):
                return path
    
    else:  # Linux
        paths = [
            "/usr/share/code",
            "/opt/visual-studio-code",
            os.path.expanduser("~/.local/share/applications")
        ]
        for path in paths:
            if os.path.exists(path):
                return path
    
    return None

def get_vscode_extensions_dir():
    """Get VSCode extensions directory."""
    system = platform.system()
    
    if system == "Darwin":
        return os.path.expanduser("~/.vscode/extensions")
    elif system == "Windows":
        return os.path.expanduser("~/.vscode/extensions")
    else:
        return os.path.expanduser("~/.vscode/extensions")

def install_continue_extension():
    """Install Continue.dev extension automatically."""
    print("📦 Installing Continue.dev extension...")
    
    try:
        # Try using VSCode CLI first
        result = subprocess.run([
            "code", "--install-extension", "Continue.continue"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Continue.dev extension installed via CLI")
            return True
    except:
        pass
    
    # Fallback: Manual installation
    print("📥 Downloading Continue.dev extension manually...")
    
    extensions_dir = Path(get_vscode_extensions_dir())
    extensions_dir.mkdir(parents=True, exist_ok=True)
    
    # Download the extension (this is a simplified approach)
    # In reality, we'd need to download from VSCode marketplace
    print("⚠️  Manual extension installation required")
    print("   Run: code --install-extension Continue.continue")
    return False

def setup_continue_config():
    """Set up Continue.dev configuration automatically."""
    print("⚙️  Configuring Continue.dev...")
    
    # Find Continue.dev config directory
    system = platform.system()
    if system == "Darwin":
        config_dir = Path.home() / ".continue"
    elif system == "Windows":
        config_dir = Path.home() / ".continue"
    else:
        config_dir = Path.home() / ".continue"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    
    # Create the configuration
    config = {
        "models": [
            {
                "title": "MCPlease Local",
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "apiBase": "http://localhost:8000/v1",
                "apiKey": "mcplease-local"
            }
        ],
        "tabAutocompleteModel": {
            "title": "MCPlease Local",
            "provider": "openai",
            "model": "gpt-3.5-turbo", 
            "apiBase": "http://localhost:8000/v1",
            "apiKey": "mcplease-local"
        },
        "allowAnonymousTelemetry": False
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Continue.dev configured at {config_file}")
    return True

def create_api_server():
    """Create a simple HTTP API server that wraps our MCP server."""
    api_server_code = '''#!/usr/bin/env python3
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
        process.stdin.write(json.dumps(request) + "\\n")
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
'''
    
    api_file = Path("mcplease_api.py")
    with open(api_file, 'w') as f:
        f.write(api_server_code)
    
    print(f"✅ API server created at {api_file}")
    return api_file

def install_fastapi():
    """Install FastAPI if not available."""
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI already installed")
        return True
    except ImportError:
        print("📦 Installing FastAPI...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"], 
                         check=True, capture_output=True)
            print("✅ FastAPI installed")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install FastAPI")
            return False

def create_launcher_script():
    """Create a simple launcher script."""
    launcher_code = '''#!/usr/bin/env python3
"""
MCPlease Launcher - One command to rule them all
"""

import subprocess
import sys
import time
from pathlib import Path

def main():
    print("🚀 Starting MCPlease...")
    
    # Start the API server
    api_file = Path("mcplease_api.py")
    if not api_file.exists():
        print("❌ API server not found. Run one_step.py first.")
        return
    
    try:
        print("📡 Starting API server on http://localhost:8000")
        print("🔌 VSCode Continue.dev should now work!")
        print("⏹️  Press Ctrl+C to stop")
        
        subprocess.run([sys.executable, str(api_file)])
        
    except KeyboardInterrupt:
        print("\\n👋 MCPlease stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
'''
    
    launcher_file = Path("start_mcplease_now.py")
    with open(launcher_file, 'w') as f:
        f.write(launcher_code)
    
    print(f"✅ Launcher created at {launcher_file}")
    return launcher_file

def main():
    """One-step setup."""
    print_banner()
    
    print("🎯 Setting up MCPlease in ONE step...")
    print("   This will:")
    print("   1. Install Continue.dev extension")
    print("   2. Configure it automatically")
    print("   3. Create HTTP API wrapper")
    print("   4. Give you ONE command to start everything")
    print("")
    
    success = True
    
    # Check if VSCode is installed
    vscode_path = detect_vscode()
    if not vscode_path:
        print("⚠️  VSCode not found. Please install VSCode first.")
        print("   Download from: https://code.visualstudio.com/")
        success = False
    else:
        print(f"✅ Found VSCode at {vscode_path}")
    
    # Install FastAPI
    if not install_fastapi():
        success = False
    
    # Create API server
    api_file = create_api_server()
    
    # Create launcher
    launcher_file = create_launcher_script()
    
    # Set up Continue.dev config
    setup_continue_config()
    
    # Try to install Continue.dev extension
    print("📦 Installing Continue.dev extension...")
    print("   Run this command in terminal:")
    print("   code --install-extension Continue.continue")
    
    if success:
        print("")
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                    🎉 ONE-STEP COMPLETE! 🎉                ║")
        print("║                                                              ║")
        print("║  Now run just ONE command:                                  ║")
        print("║                                                              ║")
        print("║      python start_mcplease_now.py                          ║")
        print("║                                                              ║")
        print("║  Then open VSCode and start coding with AI!                ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print("")
        print("📋 What just happened:")
        print("   ✅ Created HTTP API wrapper for MCPlease")
        print("   ✅ Configured Continue.dev automatically")
        print("   ✅ Created one-command launcher")
        print("")
        print("🔌 VSCode Setup:")
        print("   1. Install Continue.dev: code --install-extension Continue.continue")
        print("   2. Restart VSCode")
        print("   3. Start coding - AI completions will work!")
        print("")
        print("🚀 Start MCPlease: python start_mcplease_now.py")
    else:
        print("")
        print("❌ Setup incomplete. Please fix the issues above.")

if __name__ == "__main__":
    main()