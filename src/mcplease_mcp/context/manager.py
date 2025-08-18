"""MCP context manager for session-based context handling."""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .storage import ContextStorage
from ..protocol.models import MCPContext

logger = logging.getLogger(__name__)


class MCPContextManager:
    """Manages conversation context and state across MCP sessions."""
    
    def __init__(
        self, 
        storage: Optional[ContextStorage] = None,
        max_context_age_minutes: int = 30,
        max_contexts_per_user: int = 10,
        cleanup_interval_minutes: int = 5
    ):
        """Initialize the context manager.
        
        Args:
            storage: Context storage backend (optional)
            max_context_age_minutes: Maximum age before context expires
            max_contexts_per_user: Maximum contexts per user
            cleanup_interval_minutes: How often to run cleanup
        """
        self.storage = storage or ContextStorage()
        self.max_context_age_minutes = max_context_age_minutes
        self.max_contexts_per_user = max_contexts_per_user
        self.cleanup_interval_minutes = cleanup_interval_minutes
        
        # Session isolation
        self._session_locks: Dict[str, asyncio.Lock] = {}
        self._locks_lock = asyncio.Lock()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        logger.info(f"Initialized MCP context manager")
    
    async def start(self) -> None:
        """Start the context manager and background tasks."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Started context manager background tasks")
    
    async def stop(self) -> None:
        """Stop the context manager and background tasks."""
        self._shutdown_event.set()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        logger.info("Stopped context manager")
    
    async def create_context(
        self, 
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        workspace_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MCPContext:
        """Create a new context.
        
        Args:
            session_id: Session ID (generated if not provided)
            user_id: User ID (optional)
            workspace_path: Workspace path (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Created context
        """
        if not session_id:
            session_id = f"mcp_session_{uuid.uuid4().hex[:8]}"
        
        context = MCPContext(
            session_id=session_id,
            user_id=user_id,
            workspace_path=workspace_path,
            metadata=metadata or {}
        )
        
        await self.storage.store_context(context)
        
        logger.info(f"Created context for session: {session_id}")
        return context
    
    async def get_context(self, session_id: str) -> Optional[MCPContext]:
        """Get context for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Context if found, None otherwise
        """
        async with await self._get_session_lock(session_id):
            # Get context without updating last_accessed first
            context = None
            
            # Check cache first
            if session_id in self.storage._cache:
                context = self.storage._cache[session_id]
            else:
                # Load from disk without updating last_accessed
                context_file = self.storage._get_context_file_path(session_id)
                context = await self.storage._load_context_from_file(context_file)
            
            if context:
                # Check if context is expired before updating last_accessed
                if self._is_context_expired(context):
                    await self.storage.delete_context(session_id)
                    logger.debug(f"Context expired for session: {session_id}")
                    return None
                
                # Context is valid, now update last_accessed and store
                context.last_accessed = datetime.now()
                await self.storage.store_context(context)
                
                logger.debug(f"Retrieved context for session: {session_id}")
                return context
            
            return None
    
    async def update_context(
        self, 
        session_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update context with new data.
        
        Args:
            session_id: Session ID
            updates: Updates to apply
            
        Returns:
            True if context was updated, False if not found
        """
        async with await self._get_session_lock(session_id):
            success = await self.storage.update_context(session_id, updates)
            
            if success:
                logger.debug(f"Updated context for session: {session_id}")
            
            return success
    
    async def add_conversation_entry(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add an entry to the conversation history.
        
        Args:
            session_id: Session ID
            role: Role (user, assistant, system)
            content: Message content
            metadata: Optional metadata for the entry
            
        Returns:
            True if entry was added, False if context not found
        """
        context = await self.get_context(session_id)
        if not context:
            return False
        
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        context.conversation_history.append(entry)
        
        # Limit conversation history size
        max_history = 50  # Keep last 50 entries
        if len(context.conversation_history) > max_history:
            context.conversation_history = context.conversation_history[-max_history:]
        
        await self.storage.store_context(context)
        
        logger.debug(f"Added conversation entry for session: {session_id}")
        return True
    
    async def add_active_file(self, session_id: str, file_path: str) -> bool:
        """Add a file to the active files list.
        
        Args:
            session_id: Session ID
            file_path: Path to the file
            
        Returns:
            True if file was added, False if context not found
        """
        context = await self.get_context(session_id)
        if not context:
            return False
        
        if file_path not in context.active_files:
            context.active_files.append(file_path)
            
            # Limit active files
            max_files = 20
            if len(context.active_files) > max_files:
                context.active_files = context.active_files[-max_files:]
            
            await self.storage.store_context(context)
            logger.debug(f"Added active file {file_path} for session: {session_id}")
        
        return True
    
    async def remove_active_file(self, session_id: str, file_path: str) -> bool:
        """Remove a file from the active files list.
        
        Args:
            session_id: Session ID
            file_path: Path to the file
            
        Returns:
            True if file was removed, False if context not found or file not active
        """
        context = await self.get_context(session_id)
        if not context:
            return False
        
        if file_path in context.active_files:
            context.active_files.remove(file_path)
            await self.storage.store_context(context)
            logger.debug(f"Removed active file {file_path} for session: {session_id}")
            return True
        
        return False
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session.
        
        Args:
            session_id: Session ID
            limit: Maximum number of entries to return
            
        Returns:
            List of conversation entries
        """
        context = await self.get_context(session_id)
        if not context:
            return []
        
        history = context.conversation_history
        if limit:
            history = history[-limit:]
        
        return history
    
    async def clear_context(self, session_id: str) -> bool:
        """Clear all data for a context but keep the session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if context was cleared, False if not found
        """
        context = await self.get_context(session_id)
        if not context:
            return False
        
        # Clear data but keep session info
        context.active_files = []
        context.conversation_history = []
        context.metadata = {}
        
        await self.storage.store_context(context)
        
        logger.info(f"Cleared context data for session: {session_id}")
        return True
    
    async def delete_context(self, session_id: str) -> bool:
        """Delete a context completely.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if context was deleted, False if not found
        """
        async with await self._get_session_lock(session_id):
            success = await self.storage.delete_context(session_id)
            
            if success:
                logger.info(f"Deleted context for session: {session_id}")
            
            return success
    
    async def list_user_contexts(self, user_id: str) -> List[MCPContext]:
        """List all contexts for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of contexts for the user
        """
        contexts = await self.storage.list_contexts(user_id=user_id)
        
        # Filter out expired contexts
        valid_contexts = [
            context for context in contexts
            if not self._is_context_expired(context)
        ]
        
        return valid_contexts
    
    async def cleanup_expired_contexts(self) -> int:
        """Clean up expired contexts.
        
        Returns:
            Number of contexts cleaned up
        """
        return await self.storage.cleanup_expired_contexts(self.max_context_age_minutes)
    
    async def enforce_user_context_limits(self, user_id: str) -> int:
        """Enforce context limits for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of contexts removed
        """
        contexts = await self.list_user_contexts(user_id)
        
        if len(contexts) <= self.max_contexts_per_user:
            return 0
        
        # Sort by last accessed time, keep most recent
        contexts.sort(key=lambda c: c.last_accessed or datetime.min)
        
        # Remove oldest contexts
        contexts_to_remove = contexts[:-self.max_contexts_per_user]
        removed_count = 0
        
        for context in contexts_to_remove:
            if await self.delete_context(context.session_id):
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} contexts for user {user_id} to enforce limits")
        
        return removed_count
    
    async def get_context_stats(self) -> Dict[str, Any]:
        """Get context management statistics.
        
        Returns:
            Dictionary with statistics
        """
        storage_stats = await self.storage.get_storage_stats()
        
        # Count contexts by age
        all_contexts = await self.storage.list_contexts()
        now = datetime.now()
        
        age_stats = {
            "under_5_min": 0,
            "5_to_15_min": 0,
            "15_to_30_min": 0,
            "over_30_min": 0
        }
        
        for context in all_contexts:
            if context.last_accessed:
                age = now - context.last_accessed
                if age < timedelta(minutes=5):
                    age_stats["under_5_min"] += 1
                elif age < timedelta(minutes=15):
                    age_stats["5_to_15_min"] += 1
                elif age < timedelta(minutes=30):
                    age_stats["15_to_30_min"] += 1
                else:
                    age_stats["over_30_min"] += 1
        
        return {
            "total_contexts": len(all_contexts),
            "contexts_by_age": age_stats,
            "max_context_age_minutes": self.max_context_age_minutes,
            "max_contexts_per_user": self.max_contexts_per_user,
            "storage_stats": storage_stats
        }
    
    def _is_context_expired(self, context: MCPContext) -> bool:
        """Check if a context is expired.
        
        Args:
            context: Context to check
            
        Returns:
            True if context is expired
        """
        if not context.last_accessed:
            return False
        
        age = datetime.now() - context.last_accessed
        return age > timedelta(minutes=self.max_context_age_minutes)
    
    async def _get_session_lock(self, session_id: str) -> asyncio.Lock:
        """Get or create a lock for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Lock for the session
        """
        async with self._locks_lock:
            if session_id not in self._session_locks:
                self._session_locks[session_id] = asyncio.Lock()
            return self._session_locks[session_id]
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while not self._shutdown_event.is_set():
            try:
                # Wait for cleanup interval or shutdown
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.cleanup_interval_minutes * 60
                )
                break  # Shutdown requested
            except asyncio.TimeoutError:
                # Time to run cleanup
                try:
                    cleaned = await self.cleanup_expired_contexts()
                    if cleaned > 0:
                        logger.debug(f"Background cleanup removed {cleaned} expired contexts")
                except Exception as e:
                    logger.error(f"Error in background cleanup: {e}")
        
        logger.debug("Context manager cleanup loop stopped")