"""Tests for context storage."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from mcplease_mcp.context.storage import ContextStorage
from mcplease_mcp.protocol.models import MCPContext


class TestContextStorage:
    """Test context storage functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def storage(self, temp_dir):
        """Create context storage with temporary directory."""
        return ContextStorage(storage_dir=temp_dir)

    @pytest.fixture
    def sample_context(self):
        """Create a sample context for testing."""
        return MCPContext(
            session_id="test_session_123",
            user_id="user_456",
            workspace_path="/path/to/workspace",
            active_files=["main.py", "utils.py"],
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            metadata={"language": "python", "project": "test"}
        )

    def test_storage_initialization(self, temp_dir):
        """Test storage initialization."""
        storage = ContextStorage(storage_dir=temp_dir)
        
        assert storage.storage_dir == temp_dir
        assert temp_dir.exists()
        assert len(storage._cache) == 0

    @pytest.mark.asyncio
    async def test_store_and_get_context(self, storage, sample_context):
        """Test storing and retrieving context."""
        # Store context
        await storage.store_context(sample_context)
        
        # Retrieve context
        retrieved = await storage.get_context("test_session_123")
        
        assert retrieved is not None
        assert retrieved.session_id == sample_context.session_id
        assert retrieved.user_id == sample_context.user_id
        assert retrieved.workspace_path == sample_context.workspace_path
        assert retrieved.active_files == sample_context.active_files
        assert len(retrieved.conversation_history) == 2

    @pytest.mark.asyncio
    async def test_get_nonexistent_context(self, storage):
        """Test retrieving non-existent context."""
        result = await storage.get_context("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_context(self, storage, sample_context):
        """Test updating context."""
        # Store initial context
        await storage.store_context(sample_context)
        
        # Update context
        updates = {
            "workspace_path": "/new/path",
            "metadata": {"language": "javascript"}
        }
        
        success = await storage.update_context("test_session_123", updates)
        assert success is True
        
        # Verify updates
        updated = await storage.get_context("test_session_123")
        assert updated.workspace_path == "/new/path"
        assert updated.metadata["language"] == "javascript"

    @pytest.mark.asyncio
    async def test_update_nonexistent_context(self, storage):
        """Test updating non-existent context."""
        success = await storage.update_context("nonexistent", {"test": "value"})
        assert success is False

    @pytest.mark.asyncio
    async def test_delete_context(self, storage, sample_context):
        """Test deleting context."""
        # Store context
        await storage.store_context(sample_context)
        
        # Verify it exists
        retrieved = await storage.get_context("test_session_123")
        assert retrieved is not None
        
        # Delete context
        success = await storage.delete_context("test_session_123")
        assert success is True
        
        # Verify it's gone
        retrieved = await storage.get_context("test_session_123")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_context(self, storage):
        """Test deleting non-existent context."""
        success = await storage.delete_context("nonexistent")
        assert success is False

    @pytest.mark.asyncio
    async def test_list_contexts(self, storage):
        """Test listing contexts."""
        # Create multiple contexts
        context1 = MCPContext(session_id="session1", user_id="user1")
        context2 = MCPContext(session_id="session2", user_id="user2")
        context3 = MCPContext(session_id="session3", user_id="user1")
        
        await storage.store_context(context1)
        await storage.store_context(context2)
        await storage.store_context(context3)
        
        # List all contexts
        all_contexts = await storage.list_contexts()
        assert len(all_contexts) == 3
        
        # List contexts for specific user
        user1_contexts = await storage.list_contexts(user_id="user1")
        assert len(user1_contexts) == 2
        
        user2_contexts = await storage.list_contexts(user_id="user2")
        assert len(user2_contexts) == 1

    @pytest.mark.asyncio
    async def test_cleanup_expired_contexts(self, storage):
        """Test cleaning up expired contexts."""
        # Create contexts with different ages
        old_time = datetime.now() - timedelta(minutes=45)
        recent_time = datetime.now() - timedelta(minutes=10)
        
        old_context = MCPContext(session_id="old_session", last_accessed=old_time)
        recent_context = MCPContext(session_id="recent_session", last_accessed=recent_time)
        
        await storage.store_context(old_context)
        await storage.store_context(recent_context)
        
        # Clean up contexts older than 30 minutes
        cleaned = await storage.cleanup_expired_contexts(max_age_minutes=30)
        
        # Should clean up the old context (may count cache + disk = 2, or just disk = 1)
        assert cleaned >= 1
        
        # Verify old context is gone, recent context remains
        assert await storage.get_context("old_session") is None
        assert await storage.get_context("recent_session") is not None

    @pytest.mark.asyncio
    async def test_storage_stats(self, storage, sample_context):
        """Test getting storage statistics."""
        # Store a context
        await storage.store_context(sample_context)
        
        stats = await storage.get_storage_stats()
        
        assert "storage_dir" in stats
        assert "cached_contexts" in stats
        assert "disk_contexts" in stats
        assert "total_size_bytes" in stats
        assert "total_size_mb" in stats
        
        assert stats["cached_contexts"] == 1
        assert stats["disk_contexts"] == 1
        assert stats["total_size_bytes"] > 0

    @pytest.mark.asyncio
    async def test_context_persistence(self, storage, sample_context):
        """Test that contexts persist across storage instances."""
        # Store context
        await storage.store_context(sample_context)
        
        # Create new storage instance with same directory
        new_storage = ContextStorage(storage_dir=storage.storage_dir)
        
        # Should be able to retrieve context
        retrieved = await new_storage.get_context("test_session_123")
        assert retrieved is not None
        assert retrieved.session_id == sample_context.session_id

    @pytest.mark.asyncio
    async def test_cache_behavior(self, storage, sample_context):
        """Test caching behavior."""
        # Store context
        await storage.store_context(sample_context)
        
        # Should be in cache
        assert "test_session_123" in storage._cache
        
        # Retrieve should update last_accessed
        original_time = sample_context.last_accessed
        retrieved = await storage.get_context("test_session_123")
        
        assert retrieved.last_accessed > original_time

    @pytest.mark.asyncio
    async def test_safe_filename_handling(self, storage):
        """Test handling of session IDs with special characters."""
        context = MCPContext(session_id="session/with\\special:chars")
        
        await storage.store_context(context)
        
        retrieved = await storage.get_context("session/with\\special:chars")
        assert retrieved is not None
        assert retrieved.session_id == "session/with\\special:chars"

    @pytest.mark.asyncio
    async def test_concurrent_access(self, storage, sample_context):
        """Test concurrent access to storage."""
        import asyncio
        
        # Store initial context
        await storage.store_context(sample_context)
        
        # Define concurrent operations
        async def update_context():
            await storage.update_context("test_session_123", {"metadata": {"updated": True}})
        
        async def get_context():
            return await storage.get_context("test_session_123")
        
        # Run concurrent operations
        results = await asyncio.gather(
            update_context(),
            get_context(),
            update_context(),
            get_context(),
            return_exceptions=True
        )
        
        # Should not raise exceptions
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent access failed: {result}")
        
        # Final context should be retrievable
        final_context = await storage.get_context("test_session_123")
        assert final_context is not None