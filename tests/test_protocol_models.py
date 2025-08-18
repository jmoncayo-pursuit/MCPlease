"""Tests for MCP protocol models."""

import json
import pytest
from datetime import datetime

from mcplease_mcp.protocol.models import (
    MCPRequest,
    MCPResponse,
    MCPError,
    MCPTool,
    MCPContext,
    MCPSession,
    MCPMethods,
    MCPErrorCodes,
)


class TestMCPRequest:
    """Test MCPRequest model."""

    def test_create_request(self):
        """Test creating an MCP request."""
        request = MCPRequest(
            id="test-123",
            method="initialize",
            params={"clientInfo": {"name": "test-client"}}
        )
        
        assert request.jsonrpc == "2.0"
        assert request.id == "test-123"
        assert request.method == "initialize"
        assert request.params == {"clientInfo": {"name": "test-client"}}

    def test_request_to_dict(self):
        """Test converting request to dictionary."""
        request = MCPRequest(
            id="test-123",
            method="tools/list",
            params={"filter": "code"}
        )
        
        result = request.to_dict()
        expected = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "method": "tools/list",
            "params": {"filter": "code"}
        }
        
        assert result == expected

    def test_request_from_dict(self):
        """Test creating request from dictionary."""
        data = {
            "jsonrpc": "2.0",
            "id": "test-456",
            "method": "tools/call",
            "params": {"name": "code_completion", "arguments": {"code": "def hello"}}
        }
        
        request = MCPRequest.from_dict(data)
        
        assert request.jsonrpc == "2.0"
        assert request.id == "test-456"
        assert request.method == "tools/call"
        assert request.params["name"] == "code_completion"

    def test_request_json_serialization(self):
        """Test JSON serialization and deserialization."""
        original = MCPRequest(
            id=123,
            method="initialize",
            params={"protocolVersion": "2024-11-05"}
        )
        
        json_str = original.to_json()
        restored = MCPRequest.from_json(json_str)
        
        assert restored.jsonrpc == original.jsonrpc
        assert restored.id == original.id
        assert restored.method == original.method
        assert restored.params == original.params

    def test_request_without_optional_fields(self):
        """Test request without optional fields."""
        request = MCPRequest(method="tools/list")
        
        result = request.to_dict()
        expected = {
            "jsonrpc": "2.0",
            "method": "tools/list"
        }
        
        assert result == expected


class TestMCPError:
    """Test MCPError model."""

    def test_create_error(self):
        """Test creating an MCP error."""
        error = MCPError(
            code=MCPErrorCodes.METHOD_NOT_FOUND,
            message="Method not found",
            data={"method": "unknown/method"}
        )
        
        assert error.code == -32601
        assert error.message == "Method not found"
        assert error.data == {"method": "unknown/method"}

    def test_error_to_dict(self):
        """Test converting error to dictionary."""
        error = MCPError(
            code=MCPErrorCodes.INVALID_PARAMS,
            message="Invalid parameters"
        )
        
        result = error.to_dict()
        expected = {
            "code": -32602,
            "message": "Invalid parameters"
        }
        
        assert result == expected

    def test_error_from_dict(self):
        """Test creating error from dictionary."""
        data = {
            "code": -32000,
            "message": "Tool execution failed",
            "data": {"tool": "code_completion", "error": "timeout"}
        }
        
        error = MCPError.from_dict(data)
        
        assert error.code == -32000
        assert error.message == "Tool execution failed"
        assert error.data["tool"] == "code_completion"


class TestMCPResponse:
    """Test MCPResponse model."""

    def test_create_success_response(self):
        """Test creating a successful MCP response."""
        response = MCPResponse(
            id="test-123",
            result={"tools": []}
        )
        
        assert response.jsonrpc == "2.0"
        assert response.id == "test-123"
        assert response.result == {"tools": []}
        assert response.error is None

    def test_create_error_response(self):
        """Test creating an error MCP response."""
        error = MCPError(
            code=MCPErrorCodes.INTERNAL_ERROR,
            message="Internal server error"
        )
        response = MCPResponse(
            id="test-456",
            error=error
        )
        
        assert response.jsonrpc == "2.0"
        assert response.id == "test-456"
        assert response.result is None
        assert response.error == error

    def test_response_to_dict(self):
        """Test converting response to dictionary."""
        response = MCPResponse(
            id="test-789",
            result={"status": "success"}
        )
        
        result = response.to_dict()
        expected = {
            "jsonrpc": "2.0",
            "id": "test-789",
            "result": {"status": "success"}
        }
        
        assert result == expected

    def test_response_from_dict(self):
        """Test creating response from dictionary."""
        data = {
            "jsonrpc": "2.0",
            "id": "test-101",
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }
        
        response = MCPResponse.from_dict(data)
        
        assert response.jsonrpc == "2.0"
        assert response.id == "test-101"
        assert response.result is None
        assert response.error.code == -32601
        assert response.error.message == "Method not found"

    def test_response_json_serialization(self):
        """Test JSON serialization and deserialization."""
        original = MCPResponse(
            id="test-202",
            result={"capabilities": {"tools": {}}}
        )
        
        json_str = original.to_json()
        restored = MCPResponse.from_json(json_str)
        
        assert restored.jsonrpc == original.jsonrpc
        assert restored.id == original.id
        assert restored.result == original.result
        assert restored.error == original.error


class TestMCPTool:
    """Test MCPTool model."""

    def test_create_tool(self):
        """Test creating an MCP tool."""
        tool = MCPTool(
            name="code_completion",
            description="Provides intelligent code completion",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "language": {"type": "string"}
                },
                "required": ["code"]
            }
        )
        
        assert tool.name == "code_completion"
        assert tool.description == "Provides intelligent code completion"
        assert "code" in tool.inputSchema["properties"]

    def test_tool_to_dict(self):
        """Test converting tool to dictionary."""
        tool = MCPTool(
            name="debug_assistance",
            description="Helps debug code issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "error": {"type": "string"}
                }
            }
        )
        
        result = tool.to_dict()
        expected = {
            "name": "debug_assistance",
            "description": "Helps debug code issues",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "error": {"type": "string"}
                }
            }
        }
        
        assert result == expected

    def test_tool_from_dict(self):
        """Test creating tool from dictionary."""
        data = {
            "name": "code_explanation",
            "description": "Explains code functionality",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "detail_level": {"type": "string", "enum": ["brief", "detailed"]}
                },
                "required": ["code"]
            }
        }
        
        tool = MCPTool.from_dict(data)
        
        assert tool.name == "code_explanation"
        assert tool.description == "Explains code functionality"
        assert tool.inputSchema["properties"]["detail_level"]["enum"] == ["brief", "detailed"]


class TestMCPContext:
    """Test MCPContext model."""

    def test_create_context(self):
        """Test creating an MCP context."""
        context = MCPContext(
            session_id="session-123",
            user_id="user-456",
            workspace_path="/path/to/workspace"
        )
        
        assert context.session_id == "session-123"
        assert context.user_id == "user-456"
        assert context.workspace_path == "/path/to/workspace"
        assert isinstance(context.active_files, list)
        assert isinstance(context.conversation_history, list)
        assert isinstance(context.metadata, dict)
        assert isinstance(context.created_at, datetime)

    def test_context_to_dict(self):
        """Test converting context to dictionary."""
        context = MCPContext(
            session_id="session-789",
            active_files=["main.py", "utils.py"],
            metadata={"language": "python"}
        )
        
        result = context.to_dict()
        
        assert result["session_id"] == "session-789"
        assert result["active_files"] == ["main.py", "utils.py"]
        assert result["metadata"]["language"] == "python"
        assert "created_at" in result
        assert "last_accessed" in result

    def test_context_from_dict(self):
        """Test creating context from dictionary."""
        data = {
            "session_id": "session-101",
            "user_id": "user-202",
            "workspace_path": "/workspace",
            "active_files": ["app.js"],
            "conversation_history": [{"role": "user", "content": "help"}],
            "metadata": {"framework": "react"},
            "created_at": "2024-01-01T12:00:00",
            "last_accessed": "2024-01-01T12:30:00"
        }
        
        context = MCPContext.from_dict(data)
        
        assert context.session_id == "session-101"
        assert context.user_id == "user-202"
        assert context.active_files == ["app.js"]
        assert context.metadata["framework"] == "react"
        assert isinstance(context.created_at, datetime)


class TestMCPSession:
    """Test MCPSession model."""

    def test_create_session(self):
        """Test creating an MCP session."""
        session = MCPSession(
            session_id="session-abc",
            client_info={"name": "VSCode", "version": "1.85.0"},
            capabilities=["tools", "resources"]
        )
        
        assert session.session_id == "session-abc"
        assert session.client_info["name"] == "VSCode"
        assert "tools" in session.capabilities
        assert isinstance(session.created_at, datetime)

    def test_session_to_dict(self):
        """Test converting session to dictionary."""
        session = MCPSession(
            session_id="session-def",
            client_info={"name": "Cursor"},
            capabilities=["tools"],
            authentication_token="token-123"
        )
        
        result = session.to_dict()
        
        assert result["session_id"] == "session-def"
        assert result["client_info"]["name"] == "Cursor"
        assert result["capabilities"] == ["tools"]
        assert result["authentication_token"] == "token-123"

    def test_session_from_dict(self):
        """Test creating session from dictionary."""
        data = {
            "session_id": "session-ghi",
            "client_info": {"name": "JetBrains", "version": "2023.3"},
            "capabilities": ["tools", "resources", "prompts"],
            "created_at": "2024-01-01T10:00:00",
            "last_activity": "2024-01-01T10:15:00"
        }
        
        session = MCPSession.from_dict(data)
        
        assert session.session_id == "session-ghi"
        assert session.client_info["name"] == "JetBrains"
        assert len(session.capabilities) == 3
        assert isinstance(session.created_at, datetime)


class TestMCPConstants:
    """Test MCP constants."""

    def test_mcp_methods(self):
        """Test MCP method constants."""
        assert MCPMethods.INITIALIZE == "initialize"
        assert MCPMethods.TOOLS_LIST == "tools/list"
        assert MCPMethods.TOOLS_CALL == "tools/call"
        assert MCPMethods.RESOURCES_LIST == "resources/list"

    def test_mcp_error_codes(self):
        """Test MCP error code constants."""
        assert MCPErrorCodes.PARSE_ERROR == -32700
        assert MCPErrorCodes.INVALID_REQUEST == -32600
        assert MCPErrorCodes.METHOD_NOT_FOUND == -32601
        assert MCPErrorCodes.INVALID_PARAMS == -32602
        assert MCPErrorCodes.INTERNAL_ERROR == -32603
        assert MCPErrorCodes.TOOL_EXECUTION_ERROR == -32000