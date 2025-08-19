# MCPlease MCP Server - API Documentation

**Complete API reference for MCPlease MCP Server integration**

**Version**: 1.0.0  
**Last Updated**: January 18, 2025  
**Protocol**: MCP 2024-11-05

---

## Table of Contents

1. [Overview](#overview)
2. [MCP Protocol Support](#mcp-protocol-support)
3. [Available Tools](#available-tools)
4. [Transport Protocols](#transport-protocols)
5. [Authentication & Security](#authentication--security)
6. [Error Handling](#error-handling)
7. [Integration Examples](#integration-examples)
8. [Performance & Limits](#performance--limits)

---

## Overview

MCPlease MCP Server implements the Model Context Protocol (MCP) specification, providing AI-powered coding assistance tools through multiple transport protocols. The server supports stdio, SSE, and WebSocket transports with comprehensive security and performance monitoring.

### Server Information
- **Name**: MCPlease MCP Server
- **Version**: 1.0.0
- **Protocol Version**: 2024-11-05
- **Capabilities**: tools, resources, prompts

---

## MCP Protocol Support

### Supported Methods

| Method | Status | Description |
|--------|--------|-------------|
| `initialize` | ✅ | Server initialization and capability negotiation |
| `tools/list` | ✅ | List available AI-powered tools |
| `tools/call` | ✅ | Execute AI tools with arguments |
| `tools/listChanged` | ✅ | Notify of tool changes |
| `notifications/notify` | ✅ | Send notifications to clients |

### Protocol Features

- **JSON-RPC 2.0**: Full compliance with MCP specification
- **Async Support**: All operations are asynchronous
- **Error Handling**: Comprehensive error responses with codes
- **Capability Negotiation**: Dynamic capability discovery

---

## Available Tools

### 1. Code Completion Tool

**Name**: `code_completion`  
**Description**: AI-powered code completion and generation  
**Language Support**: Python, JavaScript, TypeScript, Java, C++, Go, Rust

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "code": {
      "type": "string",
      "description": "Existing code context"
    },
    "language": {
      "type": "string",
      "description": "Programming language",
      "enum": ["python", "javascript", "typescript", "java", "cpp", "go", "rust"]
    },
    "cursor_position": {
      "type": "integer",
      "description": "Cursor position in code (optional)"
    },
    "max_tokens": {
      "type": "integer",
      "description": "Maximum tokens to generate",
      "default": 1000
    }
  },
  "required": ["code", "language"]
}
```

#### Example Usage
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "code_completion",
    "arguments": {
      "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    ",
      "language": "python",
      "max_tokens": 500
    }
  }
}
```

#### Response Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "return fibonacci(n-1) + fibonacci(n-2)"
      }
    ]
  }
}
```

### 2. Code Explanation Tool

**Name**: `code_explanation`  
**Description**: Explain code functionality and logic  
**Language Support**: All supported languages

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "code": {
      "type": "string",
      "description": "Code to explain"
    },
    "language": {
      "type": "string",
      "description": "Programming language"
    },
    "detail_level": {
      "type": "string",
      "description": "Explanation detail level",
      "enum": ["basic", "detailed", "expert"],
      "default": "detailed"
    }
  },
  "required": ["code", "language"]
}
```

#### Example Usage
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "code_explanation",
    "arguments": {
      "code": "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr)//2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)",
      "language": "python",
      "detail_level": "detailed"
    }
  }
}
```

### 3. Debug Assistance Tool

**Name**: `debug_assistance`  
**Description**: Help debug code issues and errors  
**Language Support**: All supported languages

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "code": {
      "type": "string",
      "description": "Code with issues"
    },
    "language": {
      "type": "string",
      "description": "Programming language"
    },
    "error_message": {
      "type": "string",
      "description": "Error message or description of issue"
    },
    "context": {
      "type": "string",
      "description": "Additional context about the problem"
    }
  },
  "required": ["code", "language", "error_message"]
}
```

#### Example Usage
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "debug_assistance",
    "arguments": {
      "code": "def divide(a, b):\n    return a / b\n\nresult = divide(10, 0)",
      "language": "python",
      "error_message": "ZeroDivisionError: division by zero",
      "context": "Need to handle division by zero case"
    }
  }
}
```

---

## Transport Protocols

### 1. Stdio Transport

**Use Case**: Local IDE integration (VSCode, Cursor)  
**Configuration**: Automatic for local development

```json
{
  "mcpServers": {
    "mcplease": {
      "command": "python",
      "args": ["-m", "mcplease_mcp.main", "--transport", "stdio"]
    }
  }
}
```

### 2. SSE Transport

**Use Case**: HTTP-based remote connections  
**Port**: 8000 (default)  
**Protocol**: HTTP/HTTPS with Server-Sent Events

```bash
# Start server
python -m mcplease_mcp.main --transport sse --port 8000

# Client connection
curl -N "http://localhost:8000/mcp"
```

### 3. WebSocket Transport

**Use Case**: Real-time bidirectional communication  
**Port**: 8001 (default)  
**Protocol**: WS/WSS

```bash
# Start server
python -m mcplease_mcp.main --transport websocket --port 8001

# Client connection
wscat -c ws://localhost:8001/mcp
```

---

## Authentication & Security

### Authentication Methods

1. **Token-based Authentication**
   ```json
   {
     "headers": {
       "Authorization": "Bearer your-token-here"
     }
   }
   ```

2. **Session-based Authentication**
   - Automatic session creation on first request
   - Configurable session timeout
   - Session isolation between users

### Security Features

- **TLS/SSL Support**: Encrypted communication
- **Rate Limiting**: Configurable per-IP limits
- **Connection Limiting**: Maximum concurrent connections per IP
- **Network Policies**: IP whitelist/blacklist support

### Security Configuration

```python
# Example security configuration
security_config = {
    "require_auth": True,
    "tls_enabled": True,
    "rate_limit_per_ip": 100,
    "max_connections_per_ip": 10,
    "allowed_networks": ["192.168.0.0/16", "10.0.0.0/8"]
}
```

---

## Error Handling

### Error Response Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "details": "Additional error information",
      "request_id": "uuid-here"
    }
  }
}
```

### Common Error Codes

| Code | Message | Description |
|------|---------|-------------|
| -32600 | Invalid Request | JSON-RPC request format error |
| -32601 | Method not found | Unsupported MCP method |
| -32602 | Invalid params | Tool argument validation failed |
| -32603 | Internal error | Server-side processing error |
| -32001 | Tool execution failed | AI tool execution error |
| -32002 | Authentication required | Missing or invalid authentication |
| -32003 | Rate limited | Request rate limit exceeded |

### Error Recovery

- **Automatic Retry**: Built-in retry logic for transient failures
- **Graceful Degradation**: Fallback responses when AI tools fail
- **Detailed Logging**: Comprehensive error logging for debugging

---

## Integration Examples

### VSCode Integration

1. **Install Continue.dev Extension**
2. **Configure MCP Server**
   ```json
   // .vscode/settings.json
   {
     "continue.serverUrl": "http://localhost:8000",
     "continue.apiKey": "your-api-key"
   }
   ```

3. **Use AI Tools**
   - Press `Ctrl+I` to open Continue chat
   - Ask for code completion, explanation, or debugging help

### Cursor IDE Integration

1. **Enable MCP Support**
2. **Configure Server Connection**
3. **Use AI-powered coding features**

### Programmatic Integration

```python
import asyncio
import aiohttp
import json

async def call_mcp_tool():
    async with aiohttp.ClientSession() as session:
        # Initialize connection
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"}
        }
        
        async with session.post(
            "http://localhost:8000/mcp",
            json=init_request,
            headers={"Content-Type": "application/json"}
        ) as response:
            init_result = await response.json()
        
        # Call tool
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "code_completion",
                "arguments": {
                    "code": "def hello():",
                    "language": "python"
                }
            }
        }
        
        async with session.post(
            "http://localhost:8000/mcp",
            json=tool_request,
            headers={"Content-Type": "application/json"}
        ) as response:
            tool_result = await response.json()
            
        return tool_result

# Run the example
result = asyncio.run(call_mcp_tool())
print(json.dumps(result, indent=2))
```

---

## Performance & Limits

### Performance Characteristics

- **Response Time**: 1-5 seconds for AI tool execution
- **Concurrent Requests**: Up to 50 simultaneous users
- **Memory Usage**: 8-12GB with AI model loaded
- **CPU Usage**: Optimized for multi-core systems

### Rate Limits

- **Default**: 100 requests per minute per IP
- **Configurable**: Adjustable per deployment
- **Burst Handling**: Graceful handling of request spikes

### Resource Limits

- **Memory**: Automatic memory pressure detection
- **CPU**: Configurable CPU usage thresholds
- **Disk**: Model storage and temporary file management
- **Network**: Connection pooling and timeout management

### Monitoring

- **Health Checks**: `/health` endpoint for system status
- **Metrics**: Performance metrics collection
- **Logging**: Structured logging with security events
- **Alerts**: Configurable alerting for resource issues

---

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if server is running
   - Verify port configuration
   - Check firewall settings

2. **Authentication Errors**
   - Verify API key/token
   - Check session expiration
   - Validate network policies

3. **Tool Execution Failures**
   - Check AI model status
   - Verify input validation
   - Review error logs

4. **Performance Issues**
   - Monitor resource usage
   - Check rate limiting
   - Review concurrent request count

### Debug Commands

```bash
# Check server health
curl http://localhost:8000/health

# View server logs
tail -f logs/mcplease-mcp.log

# Test MCP protocol
python -m mcplease_mcp.main --transport stdio --debug

# Check resource usage
python -c "import psutil; print(psutil.virtual_memory())"
```

---

## Support & Resources

### Documentation
- **Quick Start Guide**: `QUICK_START_GUIDE.md`
- **Installation Guide**: `INSTALLATION_SYSTEM.md`
- **Development Guide**: `DEVELOPMENT_JOURNEY.md`

### Community
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and questions
- **Examples**: Code examples and use cases

### Development
- **Source Code**: Full source code available
- **Contributing**: Contribution guidelines
- **Testing**: Comprehensive test suite

---

*This documentation is maintained as part of the MCPlease MCP Server project. For updates and contributions, please visit our GitHub repository.*
