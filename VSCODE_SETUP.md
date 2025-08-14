# VSCode Integration Guide

This guide shows how to integrate MCPlease with VSCode using the Continue.dev extension for seamless AI coding assistance.

## Quick Setup (5 minutes)

### Step 1: Install Continue.dev Extension

1. Open VSCode
2. Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
3. Search for "Continue"
4. Install the "Continue - Codestral, Claude, and more" extension
5. Restart VSCode

### Step 2: Start MCPlease Server

Open terminal in the MCPlease directory and run:

```bash
python mcplease.py --start
```

You should see:
```
✅ AI MCP server is ready!
📋 Server Information:
   Mode: Fallback responses only
   Memory Limit: 12GB
🔌 Connect your IDE using MCP protocol
   The server is listening on stdin/stdout
```

### Step 3: Configure Continue.dev

1. In VSCode, press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "Continue: Open config.json" and select it
3. Replace the contents with this configuration:

```json
{
  "models": [
    {
      "title": "MCPlease Local",
      "provider": "openai",
      "model": "gpt-3.5-turbo",
      "apiBase": "http://localhost:8000/v1",
      "apiKey": "not-needed"
    }
  ],
  "tabAutocompleteModel": {
    "title": "MCPlease Autocomplete",
    "provider": "openai", 
    "model": "gpt-3.5-turbo",
    "apiBase": "http://localhost:8000/v1",
    "apiKey": "not-needed"
  },
  "allowAnonymousTelemetry": false
}
```

4. Save the file (Ctrl+S / Cmd+S)

### Step 4: Test the Integration

1. Create a new Python file (e.g., `test.py`)
2. Start typing a function:
   ```python
   def fibonacci(n):
   ```
3. Press `Tab` or wait for autocomplete suggestions
4. You should see AI-powered completions!

## Advanced Features

### Code Explanation

1. Select any code block
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P`)
3. Type "Continue: Explain Code" and select it
4. Get detailed explanations of your code

### Code Generation

1. Press `Ctrl+I` (or `Cmd+I`) to open the Continue chat
2. Ask questions like:
   - "Write a function to sort a list"
   - "Explain this error message"
   - "How do I fix this bug?"

### Debugging Help

1. When you encounter an error, copy the error message
2. Open Continue chat (`Ctrl+I` / `Cmd+I`)
3. Paste the error and ask for help
4. Get intelligent debugging suggestions

## Troubleshooting

### Server Not Responding

If Continue.dev can't connect to MCPlease:

1. Make sure MCPlease server is running:
   ```bash
   python mcplease.py --status
   ```

2. Check if the server is listening:
   ```bash
   python mcplease.py --start
   ```

3. Verify the configuration in Continue.dev matches the server address

### Slow Responses

If responses are slow:

1. Check available memory:
   ```bash
   python mcplease.py --status
   ```

2. Reduce memory usage:
   ```bash
   python mcplease.py --start --max-memory 8
   ```

3. Close other memory-intensive applications

### No AI Features

If you're only getting basic responses:

1. MCPlease works with intelligent fallbacks even without the full AI model
2. For full AI features, download the model:
   ```bash
   pip install huggingface-hub
   huggingface-cli download openai/gpt-oss-20b --local-dir models/gpt-oss-20b
   ```

3. Restart MCPlease:
   ```bash
   python mcplease.py --start
   ```

## Alternative: Direct MCP Integration

For advanced users who want to use MCPlease directly with MCP protocol:

1. Install an MCP-compatible client
2. Configure it to use MCPlease as an MCP server:
   ```bash
   python src/simple_ai_mcp_server.py
   ```

3. The server communicates via stdin/stdout using JSON-RPC

## Tips for Best Results

1. **Be Specific**: Ask clear, specific questions for better responses
2. **Provide Context**: Include relevant code context when asking for help
3. **Use Comments**: Add comments to help the AI understand your intent
4. **Iterate**: Refine your requests based on the responses you get

## Example Workflows

### Writing a New Function

1. Type the function signature:
   ```python
   def calculate_fibonacci(n):
   ```

2. Press Tab for autocomplete or ask Continue:
   "Complete this fibonacci function with proper error handling"

### Debugging Code

1. Copy your error message
2. Open Continue chat
3. Ask: "I'm getting this error: [paste error]. Here's my code: [paste code]. How do I fix it?"

### Code Review

1. Select a code block
2. Ask Continue: "Review this code for potential issues and improvements"
3. Get suggestions for optimization and best practices

---

**🎉 You're all set!** MCPlease is now integrated with VSCode and ready to assist with your coding tasks. The system works immediately with intelligent fallbacks and gets even better with the full AI model.