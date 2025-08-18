"""Context storage implementation for MCP."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import aiofiles

from ..protocol.models import MCPContext

logger = logging.getLogger(__name__)


class ContextStorage:
    """Storage backend for MCP contexts."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize context storage.
        
        Args:
            storage_dir: Directory to store context files (optional)
        """
        self.storage_dir = storage_dir or Path.cwd() / ".mcp_contexts"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for active contexts
        self._cache: Dict[str, MCPContext] = {}
        self._cache_lock = asyncio.Lock()
        
        logger.info(f"Initialized context storage at {self.storage_dir}")
    
    async def store_context(self, context: MCPContext) -> None:
        """Store a context.
        
        Args:
            context: Context to store
        """
        async with self._cache_lock:
            # Update cache
            self._cache[context.session_id] = context
            
            # Persist to disk
            await self._persist_context(context)
            
            logger.debug(f"Stored context for session: {context.session_id}")
    
    async def get_context(self, session_id: str) -> Optional[MCPContext]:
        """Retrieve a context by session ID.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Context if found, None otherwise
        """
        async with self._cache_lock:
            # Check cache first
            if session_id in self._cache:
                context = self._cache[session_id]
                # Update last accessed time
                context.last_accessed = datetime.now()
                await self._persist_context(context)
                return context
            
            # Load from disk if not in cache
            context = await self._load_context(session_id)
            if context:
                # Update last accessed and cache
                context.last_accessed = datetime.now()
                self._cache[session_id] = context
                await self._persist_context(context)
                return context
            
            return None
    
    async def update_context(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing context.
        
        Args:
            session_id: Session ID to update
            updates: Dictionary of updates to apply
            
        Returns:
            True if context was updated, False if not found
        """
        context = await self.get_context(session_id)
        if not context:
            return False
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
        
        # Update metadata
        context.last_accessed = datetime.now()
        
        # Store updated context
        await self.store_context(context)
        
        logger.debug(f"Updated context for session: {session_id}")
        return True
    
    async def delete_context(self, session_id: str) -> bool:
        """Delete a context.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if context was deleted, False if not found
        """
        async with self._cache_lock:
            # Remove from cache
            if session_id in self._cache:
                del self._cache[session_id]
            
            # Remove from disk
            context_file = self._get_context_file_path(session_id)
            if context_file.exists():
                context_file.unlink()
                logger.debug(f"Deleted context for session: {session_id}")
                return True
            
            return False
    
    async def list_contexts(self, user_id: Optional[str] = None) -> List[MCPContext]:
        """List all contexts, optionally filtered by user.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            List of contexts
        """
        contexts = []
        
        # Load all contexts from disk
        for context_file in self.storage_dir.glob("*.json"):
            try:
                context = await self._load_context_from_file(context_file)
                if context:
                    if user_id is None or context.user_id == user_id:
                        contexts.append(context)
            except Exception as e:
                logger.warning(f"Failed to load context from {context_file}: {e}")
        
        return contexts
    
    async def cleanup_expired_contexts(self, max_age_minutes: int = 30) -> int:
        """Clean up expired contexts.
        
        Args:
            max_age_minutes: Maximum age in minutes before context expires
            
        Returns:
            Number of contexts cleaned up
        """
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        cleaned_count = 0
        
        async with self._cache_lock:
            # Clean up cache
            expired_sessions = [
                session_id for session_id, context in self._cache.items()
                if context.last_accessed and context.last_accessed < cutoff_time
            ]
            
            for session_id in expired_sessions:
                del self._cache[session_id]
                cleaned_count += 1
        
        # Clean up disk storage
        for context_file in self.storage_dir.glob("*.json"):
            try:
                context = await self._load_context_from_file(context_file)
                if context and context.last_accessed and context.last_accessed < cutoff_time:
                    context_file.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"Failed to check context file {context_file}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired contexts")
        
        return cleaned_count
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        async with self._cache_lock:
            cache_size = len(self._cache)
        
        # Count disk files
        disk_files = len(list(self.storage_dir.glob("*.json")))
        
        # Calculate storage size
        total_size = sum(
            f.stat().st_size for f in self.storage_dir.glob("*.json")
        )
        
        return {
            "storage_dir": str(self.storage_dir),
            "cached_contexts": cache_size,
            "disk_contexts": disk_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    
    def _get_context_file_path(self, session_id: str) -> Path:
        """Get file path for a context.
        
        Args:
            session_id: Session ID
            
        Returns:
            Path to context file
        """
        # Use safe filename
        safe_session_id = session_id.replace("/", "_").replace("\\", "_")
        return self.storage_dir / f"{safe_session_id}.json"
    
    async def _persist_context(self, context: MCPContext) -> None:
        """Persist context to disk.
        
        Args:
            context: Context to persist
        """
        context_file = self._get_context_file_path(context.session_id)
        
        try:
            context_data = context.to_dict()
            async with aiofiles.open(context_file, 'w') as f:
                await f.write(json.dumps(context_data, indent=2))
        except Exception as e:
            logger.error(f"Failed to persist context {context.session_id}: {e}")
    
    async def _load_context(self, session_id: str) -> Optional[MCPContext]:
        """Load context from disk.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            Context if found, None otherwise
        """
        context_file = self._get_context_file_path(session_id)
        return await self._load_context_from_file(context_file)
    
    async def _load_context_from_file(self, context_file: Path) -> Optional[MCPContext]:
        """Load context from a specific file.
        
        Args:
            context_file: Path to context file
            
        Returns:
            Context if loaded successfully, None otherwise
        """
        if not context_file.exists():
            return None
        
        try:
            async with aiofiles.open(context_file, 'r') as f:
                content = await f.read()
                context_data = json.loads(content)
                return MCPContext.from_dict(context_data)
        except Exception as e:
            logger.error(f"Failed to load context from {context_file}: {e}")
            return None