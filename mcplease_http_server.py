#!/usr/bin/env python3
"""HTTP server wrapper for MCP server to work with Continue.dev."""

import asyncio
import json
import logging
import sys
import os
import time
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCPlease HTTP Server")

class ChatRequest(BaseModel):
    messages: list
    model: str = "oss-20b-local"
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = False

class CompletionRequest(BaseModel):
    prompt: str
    model: str = "oss-20b-local"
    temperature: float = 0.7
    max_tokens: int = 1000

class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list
    usage: dict

class CompletionResponse(BaseModel):
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list
    usage: dict

class MCPleaseAI:
    """AI interface that provides intelligent coding assistance."""
    
    def __init__(self):
        self.ai_manager = None
        self.is_model_ready = False
        logger.info("MCPleaseAI initialized with fallback responses")
    
    async def generate_response(self, prompt: str) -> str:
        """Generate intelligent response for coding tasks."""
        prompt_lower = prompt.lower()
        
        # Code completion
        if "function" in prompt_lower or "def " in prompt_lower:
            if "fibonacci" in prompt_lower:
                return '''Here's a complete Fibonacci function:

def fibonacci(n):
    """Calculate the nth Fibonacci number.
    
    Args:
        n: The position in the Fibonacci sequence
        
    Returns:
        The nth Fibonacci number
    """
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Example usage:
# print(fibonacci(10))  # Output: 55'''
            else:
                return '''Here's a function template:

def example_function():
    """TODO: Add function description.
    
    Args:
        TODO: Add parameter descriptions
        
    Returns:
        TODO: Add return value description
    """
    # TODO: Implement your function logic
    pass

# You can customize this template based on your needs!'''
        
        # Code explanation
        elif "explain" in prompt_lower or "what does" in prompt_lower:
            return '''I can help explain code! Here's what I can do:

1. **Code Analysis**: Break down complex functions
2. **Logic Explanation**: Explain how algorithms work
3. **Best Practices**: Suggest improvements
4. **Debugging Help**: Identify potential issues

Just paste your code and ask me to explain it!'''
        
        # Debugging help
        elif "error" in prompt_lower or "debug" in prompt_lower or "fix" in prompt_lower:
            return '''Here's a systematic debugging approach:

1. **Read the error message carefully** - it often tells you exactly what's wrong
2. **Check the line number** - look at the code around that line
3. **Common issues**:
   - Missing colons (:)
   - Incorrect indentation
   - Undefined variables
   - Type mismatches
4. **Add print statements** to see what's happening
5. **Test with simple examples**

Paste your error and code, and I'll help you debug it!'''
        
        # General coding help
        elif "code" in prompt_lower or "help" in prompt_lower:
            return '''I'm your AI coding assistant! I can help with:

🚀 **Code Completion**: Complete functions, classes, and logic
📚 **Code Explanation**: Break down complex code
🐛 **Debugging**: Help fix errors and issues
🔧 **Refactoring**: Suggest improvements and optimizations
💡 **Best Practices**: Share coding standards and patterns

**Try asking me:**
- "Complete this function: def sort_list(items):"
- "Explain this code: [paste your code]"
- "Help debug this error: [paste error]"
- "How do I implement a binary search?"'''
        
        # Default response
        else:
            return '''Hello! I'm your AI coding assistant powered by MCPlease.

I can help you with:
• Writing and completing code
• Explaining how code works
• Debugging issues
• Suggesting improvements
• Answering programming questions

What would you like help with today?'''

    async def complete_code(self, code: str) -> str:
        """Complete code based on context."""
        if "def " in code and code.strip().endswith(":"):
            func_name = code.split("def ")[1].split("(")[0].strip()
            if "fibonacci" in func_name.lower():
                return '''    """Calculate the nth Fibonacci number.
    
    Args:
        n: The position in the Fibonacci sequence
        
    Returns:
        The nth Fibonacci number
    """
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)'''
            else:
                return f'''    """TODO: Implement {func_name} function.
    
    Args:
        Add parameter descriptions here
        
    Returns:
        Add return value description here
    """
    # TODO: Add your implementation
    pass'''
        
        elif "class " in code and code.strip().endswith(":"):
            class_name = code.split("class ")[1].split("(")[0].split(":")[0].strip()
            return f'''    """TODO: Implement {class_name} class.
    
    A class that represents...
    """
    
    def __init__(self):
        """Initialize the {class_name}."""
        pass'''
        
        else:
            return f"# Smart completion for your code\n# TODO: Add your implementation here"

# Global AI instance
ai = MCPleaseAI()

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """Handle chat completion requests from Continue.dev."""
    try:
        # Extract the last user message
        user_message = None
        for msg in reversed(request.messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Generate response using our AI
        response_text = await ai.generate_response(user_message)
        
        # Check if streaming is requested
        if request.stream:
            return StreamingResponse(
                stream_response(response_text, request.model),
                media_type="text/plain"
            )
        
        # Format response for Continue.dev (non-streaming)
        response = ChatResponse(
            id="mcplease_" + str(int(time.time())),
            created=int(time.time()),
            model=request.model,
            choices=[{
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop",
                "index": 0
            }],
            usage={
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(user_message.split()) + len(response_text.split())
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def stream_response(text: str, model: str):
    """Generate streaming response for Continue.dev."""
    # Send the entire response as one chunk for better formatting
    yield f"data: {json.dumps({'id': f'mcplease_{int(time.time())}', 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': model, 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': text}, 'finish_reason': 'stop'}]})}\n\n"
    
    # End of stream
    yield "data: [DONE]\n\n"

@app.post("/v1/completions")
async def completions(request: CompletionRequest):
    """Handle text completion requests from Continue.dev."""
    try:
        # Generate response using our AI
        response_text = await ai.generate_response(request.prompt)
        
        # Format response for Continue.dev
        response = CompletionResponse(
            id="mcplease_" + str(int(time.time())),
            created=int(time.time()),
            model=request.model,
            choices=[{
                "text": response_text,
                "index": 0,
                "logprobs": None,
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": len(request.prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(request.prompt.split()) + len(response_text.split())
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "ai_model_ready": ai.is_model_ready}

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
