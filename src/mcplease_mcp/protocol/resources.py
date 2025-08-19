"""
MCPlease MCP Server - MCP Resources and Prompts Support

This module implements MCP resources and prompts functionality,
extending the server capabilities beyond basic tools.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

from ..utils.logging import get_structured_logger
from ..utils.exceptions import ResourceError, PromptError


class ResourceType(Enum):
    """Types of MCP resources."""
    FILE = "file"
    DIRECTORY = "directory"
    DATABASE = "database"
    API = "api"
    MODEL = "model"
    CACHE = "cache"
    LOG = "log"
    CONFIG = "config"


class PromptType(Enum):
    """Types of MCP prompts."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class ResourceMetadata:
    """Metadata for MCP resources."""
    name: str
    type: ResourceType
    description: str
    uri: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    created_at: Optional[float] = None
    modified_at: Optional[float] = None
    tags: List[str] = None
    properties: Dict[str, Any] = None


@dataclass
class PromptMessage:
    """Individual prompt message."""
    role: PromptType
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    timestamp: Optional[float] = None


@dataclass
class Prompt:
    """Complete prompt with context."""
    id: str
    name: str
    description: str
    messages: List[PromptMessage]
    created_at: float
    modified_at: float
    tags: List[str] = None
    metadata: Dict[str, Any] = None


class ResourceManager:
    """Manages MCP resources (files, databases, APIs, etc.)."""
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path.cwd()
        self.resources: Dict[str, ResourceMetadata] = {}
        self.resource_handlers: Dict[ResourceType, Callable] = {}
        self.logger = get_structured_logger(__name__)
        
        # Register default resource handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default resource type handlers."""
        self.register_handler(ResourceType.FILE, self._handle_file_resource)
        self.register_handler(ResourceType.DIRECTORY, self._handle_directory_resource)
        self.register_handler(ResourceType.CONFIG, self._handle_config_resource)
        self.register_handler(ResourceType.LOG, self._handle_log_resource)
    
    def register_handler(self, resource_type: ResourceType, handler: Callable):
        """Register a handler for a specific resource type."""
        self.resource_handlers[resource_type] = handler
        self.logger.info(f"Registered handler for resource type: {resource_type.value}")
    
    async def list_resources(self, type_filter: Optional[ResourceType] = None) -> List[ResourceMetadata]:
        """List available resources, optionally filtered by type."""
        if type_filter:
            return [r for r in self.resources.values() if r.type == type_filter]
        return list(self.resources.values())
    
    async def get_resource(self, uri: str) -> Optional[ResourceMetadata]:
        """Get a specific resource by URI."""
        return self.resources.get(uri)
    
    async def create_resource(self, metadata: ResourceMetadata) -> ResourceMetadata:
        """Create a new resource."""
        if metadata.uri in self.resources:
            raise ResourceError(f"Resource with URI {metadata.uri} already exists")
        
        # Set timestamps
        now = time.time()
        metadata.created_at = now
        metadata.modified_at = now
        
        # Initialize empty lists
        if metadata.tags is None:
            metadata.tags = []
        if metadata.properties is None:
            metadata.properties = {}
        
        self.resources[metadata.uri] = metadata
        self.logger.info(f"Created resource: {metadata.name} ({metadata.uri})")
        
        return metadata
    
    async def update_resource(self, uri: str, updates: Dict[str, Any]) -> ResourceMetadata:
        """Update an existing resource."""
        if uri not in self.resources:
            raise ResourceError(f"Resource with URI {uri} not found")
        
        resource = self.resources[uri]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(resource, key):
                setattr(resource, key, value)
        
        # Update modification timestamp
        resource.modified_at = time.time()
        
        self.logger.info(f"Updated resource: {resource.name} ({uri})")
        return resource
    
    async def delete_resource(self, uri: str) -> bool:
        """Delete a resource."""
        if uri not in self.resources:
            return False
        
        resource = self.resources.pop(uri)
        self.logger.info(f"Deleted resource: {resource.name} ({uri})")
        return True
    
    async def read_resource_content(self, uri: str) -> bytes:
        """Read the content of a resource."""
        resource = await self.get_resource(uri)
        if not resource:
            raise ResourceError(f"Resource with URI {uri} not found")
        
        handler = self.resource_handlers.get(resource.type)
        if not handler:
            raise ResourceError(f"No handler for resource type: {resource.type.value}")
        
        return await handler(resource, "read")
    
    async def write_resource_content(self, uri: str, content: bytes) -> bool:
        """Write content to a resource."""
        resource = await self.get_resource(uri)
        if not resource:
            raise ResourceError(f"Resource with URI {uri} not found")
        
        handler = self.resource_handlers.get(resource.type)
        if not handler:
            raise ResourceError(f"No handler for resource type: {resource.type.value}")
        
        return await handler(resource, "write", content)
    
    async def _handle_file_resource(self, resource: ResourceMetadata, operation: str, content: bytes = None) -> Any:
        """Handle file resource operations."""
        file_path = self.base_path / resource.uri.replace("file://", "")
        
        if operation == "read":
            if not file_path.exists():
                raise ResourceError(f"File not found: {file_path}")
            return file_path.read_bytes()
        
        elif operation == "write":
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)
            return True
        
        else:
            raise ResourceError(f"Unsupported operation: {operation}")
    
    async def _handle_directory_resource(self, resource: ResourceMetadata, operation: str, content: bytes = None) -> Any:
        """Handle directory resource operations."""
        dir_path = self.base_path / resource.uri.replace("directory://", "")
        
        if operation == "read":
            if not dir_path.exists():
                raise ResourceError(f"Directory not found: {dir_path}")
            
            # Return directory listing as JSON
            items = []
            for item in dir_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime
                })
            
            return json.dumps(items, indent=2).encode()
        
        elif operation == "write":
            raise ResourceError("Cannot write to directory resources")
        
        else:
            raise ResourceError(f"Unsupported operation: {operation}")
    
    async def _handle_config_resource(self, resource: ResourceMetadata, operation: str, content: bytes = None) -> Any:
        """Handle configuration resource operations."""
        config_path = self.base_path / resource.uri.replace("config://", "")
        
        if operation == "read":
            if not config_path.exists():
                raise ResourceError(f"Config file not found: {config_path}")
            return config_path.read_bytes()
        
        elif operation == "write":
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_bytes(content)
            return True
        
        else:
            raise ResourceError(f"Unsupported operation: {operation}")
    
    async def _handle_log_resource(self, resource: ResourceMetadata, operation: str, content: bytes = None) -> Any:
        """Handle log resource operations."""
        log_path = self.base_path / resource.uri.replace("log://", "")
        
        if operation == "read":
            if not log_path.exists():
                raise ResourceError(f"Log file not found: {log_path}")
            
            # Return last 100 lines
            lines = log_path.read_text().splitlines()
            return "\n".join(lines[-100:]).encode()
        
        elif operation == "write":
            # Append to log file
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("ab") as f:
                f.write(content + b"\n")
            return True
        
        else:
            raise ResourceError(f"Unsupported operation: {operation}")
    
    async def scan_directory(self, directory_path: Path) -> List[ResourceMetadata]:
        """Scan a directory and register file resources."""
        resources = []
        
        if not directory_path.exists():
            return resources
        
        for item in directory_path.rglob("*"):
            if item.is_file():
                # Create file resource
                resource = ResourceMetadata(
                    name=item.name,
                    type=ResourceType.FILE,
                    description=f"File: {item.relative_to(self.base_path)}",
                    uri=f"file://{item.relative_to(self.base_path)}",
                    mime_type=self._guess_mime_type(item),
                    size_bytes=item.stat().st_size,
                    created_at=item.stat().st_ctime,
                    modified_at=item.stat().st_mtime,
                    tags=["auto-discovered"]
                )
                
                await self.create_resource(resource)
                resources.append(resource)
        
        return resources
    
    def _guess_mime_type(self, file_path: Path) -> str:
        """Guess MIME type based on file extension."""
        extension = file_path.suffix.lower()
        
        mime_types = {
            ".txt": "text/plain",
            ".py": "text/x-python",
            ".js": "text/javascript",
            ".ts": "text/typescript",
            ".json": "application/json",
            ".xml": "application/xml",
            ".html": "text/html",
            ".css": "text/css",
            ".md": "text/markdown",
            ".yml": "text/yaml",
            ".yaml": "text/yaml",
            ".log": "text/plain",
            ".conf": "text/plain",
            ".ini": "text/plain",
            ".toml": "text/toml"
        }
        
        return mime_types.get(extension, "application/octet-stream")


class PromptManager:
    """Manages MCP prompts for AI interactions."""
    
    def __init__(self):
        self.prompts: Dict[str, Prompt] = {}
        self.logger = get_structured_logger(__name__)
    
    async def create_prompt(self, name: str, description: str, messages: List[Dict[str, Any]]) -> Prompt:
        """Create a new prompt."""
        prompt_id = f"prompt_{int(time.time() * 1000)}"
        
        # Convert message dictionaries to PromptMessage objects
        prompt_messages = []
        for msg in messages:
            prompt_message = PromptMessage(
                role=PromptType(msg["role"]),
                content=msg["content"],
                name=msg.get("name"),
                function_call=msg.get("function_call"),
                tool_calls=msg.get("tool_calls"),
                timestamp=time.time()
            )
            prompt_messages.append(prompt_message)
        
        prompt = Prompt(
            id=prompt_id,
            name=name,
            description=description,
            messages=prompt_messages,
            created_at=time.time(),
            modified_at=time.time(),
            tags=[],
            metadata={}
        )
        
        self.prompts[prompt_id] = prompt
        self.logger.info(f"Created prompt: {name} ({prompt_id})")
        
        return prompt
    
    async def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Get a prompt by ID."""
        return self.prompts.get(prompt_id)
    
    async def list_prompts(self, tag_filter: Optional[str] = None) -> List[Prompt]:
        """List available prompts, optionally filtered by tag."""
        if tag_filter:
            return [p for p in self.prompts.values() if tag_filter in p.tags]
        return list(self.prompts.values())
    
    async def update_prompt(self, prompt_id: str, updates: Dict[str, Any]) -> Prompt:
        """Update an existing prompt."""
        if prompt_id not in self.prompts:
            raise PromptError(f"Prompt with ID {prompt_id} not found")
        
        prompt = self.prompts[prompt_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(prompt, key):
                setattr(prompt, key, value)
        
        # Update modification timestamp
        prompt.modified_at = time.time()
        
        self.logger.info(f"Updated prompt: {prompt.name} ({prompt_id})")
        return prompt
    
    async def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt."""
        if prompt_id not in self.prompts:
            return False
        
        prompt = self.prompts.pop(prompt_id)
        self.logger.info(f"Deleted prompt: {prompt.name} ({prompt_id})")
        return True
    
    async def add_message_to_prompt(self, prompt_id: str, message: Dict[str, Any]) -> Prompt:
        """Add a message to an existing prompt."""
        prompt = await self.get_prompt(prompt_id)
        if not prompt:
            raise PromptError(f"Prompt with ID {prompt_id} not found")
        
        prompt_message = PromptMessage(
            role=PromptType(message["role"]),
            content=message["content"],
            name=message.get("name"),
            function_call=message.get("function_call"),
            tool_calls=message.get("tool_calls"),
            timestamp=time.time()
        )
        
        prompt.messages.append(prompt_message)
        prompt.modified_at = time.time()
        
        self.logger.info(f"Added message to prompt: {prompt.name} ({prompt_id})")
        return prompt
    
    async def get_prompt_for_tool(self, tool_name: str, context: Dict[str, Any] = None) -> Optional[Prompt]:
        """Get a prompt suitable for a specific tool."""
        # Find prompts tagged with the tool name
        tool_prompts = [p for p in self.prompts.values() if tool_name in p.tags]
        
        if not tool_prompts:
            return None
        
        # Return the most recently modified prompt
        return max(tool_prompts, key=lambda p: p.modified_at)
    
    async def create_system_prompt(self, name: str, content: str, tags: List[str] = None) -> Prompt:
        """Create a system prompt for AI interactions."""
        messages = [{
            "role": "system",
            "content": content
        }]
        
        return await self.create_prompt(name, f"System prompt: {name}", messages)
    
    async def create_tool_prompt(self, tool_name: str, description: str, examples: List[str] = None) -> Prompt:
        """Create a prompt specifically for a tool."""
        content = f"You are an AI assistant specialized in using the {tool_name} tool. {description}"
        
        if examples:
            content += "\n\nExamples:\n" + "\n".join(f"- {example}" for example in examples)
        
        messages = [{
            "role": "system",
            "content": content
        }]
        
        tags = [tool_name, "tool-specific"]
        return await self.create_prompt(f"{tool_name}_prompt", description, messages)


class MCPResourcesAndPrompts:
    """Main class for managing MCP resources and prompts."""
    
    def __init__(self, base_path: Path = None):
        self.resource_manager = ResourceManager(base_path)
        self.prompt_manager = PromptManager()
        self.logger = get_structured_logger(__name__)
    
    async def initialize(self):
        """Initialize the resources and prompts system."""
        # Scan for existing resources
        await self.resource_manager.scan_directory(self.resource_manager.base_path)
        
        # Create default prompts
        await self._create_default_prompts()
        
        self.logger.info("MCP Resources and Prompts system initialized")
    
    async def _create_default_prompts(self):
        """Create default system prompts."""
        # Code completion prompt
        await self.prompt_manager.create_system_prompt(
            "code_completion",
            "You are an expert code completion AI. Provide accurate, context-aware code completions that follow best practices and maintain code style consistency.",
            ["code-completion", "ai-tool"]
        )
        
        # Code explanation prompt
        await self.prompt_manager.create_system_prompt(
            "code_explanation",
            "You are an expert code explanation AI. Explain code clearly, concisely, and in a way that helps developers understand the logic, purpose, and implementation details.",
            ["code-explanation", "ai-tool"]
        )
        
        # Debug assistance prompt
        await self.prompt_manager.create_system_prompt(
            "debug_assistance",
            "You are an expert debugging AI. Help developers identify, understand, and fix code issues by analyzing error messages, code logic, and providing actionable solutions.",
            ["debug-assistance", "ai-tool"]
        )
    
    async def get_resources_list(self, type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get a list of resources for MCP protocol."""
        if type_filter:
            try:
                resource_type = ResourceType(type_filter)
                resources = await self.resource_manager.list_resources(resource_type)
            except ValueError:
                resources = await self.resource_manager.list_resources()
        else:
            resources = await self.resource_manager.list_resources()
        
        return [asdict(resource) for resource in resources]
    
    async def get_prompts_list(self, tag_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get a list of prompts for MCP protocol."""
        prompts = await self.prompt_manager.list_prompts(tag_filter)
        return [asdict(prompt) for prompt in prompts]
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource and return its content."""
        try:
            content = await self.resource_manager.read_resource_content(uri)
            resource = await self.resource_manager.get_resource(uri)
            
            return {
                "success": True,
                "resource": asdict(resource),
                "content": content.decode('utf-8', errors='ignore'),
                "content_bytes": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "uri": uri
            }
    
    async def write_resource(self, uri: str, content: str) -> Dict[str, Any]:
        """Write content to a resource."""
        try:
            success = await self.resource_manager.write_resource_content(uri, content.encode())
            resource = await self.resource_manager.get_resource(uri)
            
            return {
                "success": success,
                "resource": asdict(resource) if resource else None,
                "content_written": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "uri": uri
            }
    
    async def get_prompt_for_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a prompt suitable for a specific tool."""
        prompt = await self.prompt_manager.get_prompt_for_tool(tool_name)
        if prompt:
            return asdict(prompt)
        return None
    
    async def create_custom_prompt(self, name: str, description: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a custom prompt."""
        try:
            prompt = await self.prompt_manager.create_prompt(name, description, messages)
            return {
                "success": True,
                "prompt": asdict(prompt)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status for resources and prompts."""
        resources = await self.resource_manager.list_resources()
        prompts = await self.prompt_manager.list_prompts()
        
        return {
            "resources": {
                "total": len(resources),
                "by_type": {
                    resource_type.value: len([r for r in resources if r.type == resource_type])
                    for resource_type in ResourceType
                }
            },
            "prompts": {
                "total": len(prompts),
                "by_tag": self._count_prompts_by_tag(prompts)
            },
            "status": "healthy"
        }
    
    def _count_prompts_by_tag(self, prompts: List[Prompt]) -> Dict[str, int]:
        """Count prompts by tag."""
        tag_counts = {}
        for prompt in prompts:
            for tag in prompt.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return tag_counts


# Global instance
_global_resources_prompts: Optional[MCPResourcesAndPrompts] = None


def get_resources_prompts() -> MCPResourcesAndPrompts:
    """Get the global resources and prompts instance."""
    global _global_resources_prompts
    if _global_resources_prompts is None:
        _global_resources_prompts = MCPResourcesAndPrompts()
    return _global_resources_prompts


async def setup_resources_prompts(base_path: Path = None) -> MCPResourcesAndPrompts:
    """Setup and initialize the resources and prompts system."""
    global _global_resources_prompts
    _global_resources_prompts = MCPResourcesAndPrompts(base_path)
    await _global_resources_prompts.initialize()
    return _global_resources_prompts
