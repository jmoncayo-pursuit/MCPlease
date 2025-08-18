"""MCP protocol data models using FastMCP framework."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json


@dataclass
class MCPRequest:
    """MCP request model following JSON-RPC 2.0 specification."""
    jsonrpc: str = "2.0"
    id: Union[str, int, None] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
        }
        if self.id is not None:
            result["id"] = self.id
        if self.params is not None:
            result["params"] = self.params
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPRequest":
        """Create from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method", ""),
            params=data.get("params"),
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "MCPRequest":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class MCPError:
    """MCP error model following JSON-RPC 2.0 error specification."""
    code: int
    message: str
    data: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.data is not None:
            result["data"] = self.data
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPError":
        """Create from dictionary."""
        return cls(
            code=data["code"],
            message=data["message"],
            data=data.get("data"),
        )


@dataclass
class MCPResponse:
    """MCP response model following JSON-RPC 2.0 specification."""
    jsonrpc: str = "2.0"
    id: Union[str, int, None] = None
    result: Optional[Any] = None
    error: Optional[MCPError] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "jsonrpc": self.jsonrpc,
        }
        if self.id is not None:
            result["id"] = self.id
        if self.error is not None:
            result["error"] = self.error.to_dict()
        elif self.result is not None:
            result["result"] = self.result
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPResponse":
        """Create from dictionary."""
        error = None
        if "error" in data:
            error = MCPError.from_dict(data["error"])
        
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            result=data.get("result"),
            error=error,
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "MCPResponse":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class MCPTool:
    """MCP tool definition for FastMCP integration."""
    name: str
    description: str
    inputSchema: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP tools/list response."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPTool":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            inputSchema=data["inputSchema"],
        )


@dataclass
class MCPContext:
    """Context model for session management."""
    session_id: str
    user_id: Optional[str] = None
    workspace_path: Optional[str] = None
    active_files: List[str] = None
    conversation_history: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.active_files is None:
            self.active_files = []
        if self.conversation_history is None:
            self.conversation_history = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_accessed is None:
            self.last_accessed = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "workspace_path": self.workspace_path,
            "active_files": self.active_files,
            "conversation_history": self.conversation_history,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPContext":
        """Create from dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        last_accessed = None
        if data.get("last_accessed"):
            last_accessed = datetime.fromisoformat(data["last_accessed"])

        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            workspace_path=data.get("workspace_path"),
            active_files=data.get("active_files", []),
            conversation_history=data.get("conversation_history", []),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            last_accessed=last_accessed,
        )


@dataclass
class MCPSession:
    """Session model for client connection management."""
    session_id: str
    client_info: Dict[str, Any]
    capabilities: List[str]
    authentication_token: Optional[str] = None
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "client_info": self.client_info,
            "capabilities": self.capabilities,
            "authentication_token": self.authentication_token,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPSession":
        """Create from dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        last_activity = None
        if data.get("last_activity"):
            last_activity = datetime.fromisoformat(data["last_activity"])

        return cls(
            session_id=data["session_id"],
            client_info=data.get("client_info", {}),
            capabilities=data.get("capabilities", []),
            authentication_token=data.get("authentication_token"),
            created_at=created_at,
            last_activity=last_activity,
        )


# MCP Protocol Constants
class MCPMethods:
    """Standard MCP method names."""
    INITIALIZE = "initialize"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"


class MCPErrorCodes:
    """Standard MCP error codes following JSON-RPC 2.0."""
    # JSON-RPC 2.0 standard errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific errors
    TOOL_EXECUTION_ERROR = -32000
    AUTHENTICATION_ERROR = -32001
    AUTHORIZATION_ERROR = -32002
    RESOURCE_NOT_FOUND = -32003
    CONTEXT_ERROR = -32004