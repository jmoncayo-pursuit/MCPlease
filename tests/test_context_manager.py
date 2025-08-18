"""Tests for MCP context manager."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from mcplease_mcp.context.manager import MCPContextManager
from mcplease_mcp.context.storage import ContextStorage
from mcplease_mcp.protocol.models import MCPContext


class TestMCPContextManager:
    """Test MCP context manager functionality."""

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
    def manager(self, storage):
        """Create context manager with test storage."""
        return MCPContextManager(
            storage=storage,
            max_context_age_minutes=30,
            max_contexts_per_user=5,
            cleanup_interval_minutes=1
        )

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager.max_context_age_minutes == 30
        assert manager.max_contexts_per_user == 5
        assert manager.cleanup_interval_minutes == 1
        assert manager.storage is not None

    @pytest.mark.asyncio
    async def test_create_context(self, manager):
        """Test creating a new context."""
        context = await manager.create_context(
            user_id="test_user",
            workspace_path="/test/workspace",
            metadata={"project": "test"}
        )
        
        assert context.session_id is not None
        assert context.user_id == "test_user"
        assert context.workspace_path == "/test/workspace"
        assert context.metadata["project"] == "test"
        assert isinstance(context.created_at, datetime)

    @pytest.mark.asyncio
    async def test_create_context_with_session_id(self, manager):
        """Test creating context with specific session ID."""
        context = await manager.create_context(
            session_id="custom_session_123",
            user_id="test_user"
        )
        
        assert context.session_id == "custom_session_123"
        assert context.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_context(self, manager):
        """Test retrieving context."""
        # Create context
        created = await manager.create_context(
            session_id="test_session",
            user_id="test_user"
        )
        
        # Retrieve context
        retrieved = await manager.get_context("test_session")
        
        assert retrieved is not None
        assert retrieved.session_id == created.session_id
        assert retrieved.user_id == created.user_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_context(self, manager):
        """Test retrieving non-existent context."""
        result = await manager.get_context("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_context(self, manager):
        """Test updating context."""
        # Create context
        await manager.create_context(
            session_id="test_session",
            user_id="test_user"
        )
        
        # Update context
        success = await manager.update_context(
            "test_session",
            {"workspace_path": "/new/path", "metadata": {"updated": True}}
        )
        
        assert success is True
        
        # Verify update
        updated = await manager.get_context("test_session")
        assert updated.workspace_path == "/new/path"
        assert updated.metadata["updated"] is True

    @pytest.mark.asyncio
    async def test_add_conversation_entry(self, manager):
        """Test adding conversation entries."""
        # Create context
        await manager.create_context(session_id="test_session")
        
        # Add conversation entries
        success1 = await manager.add_conversation_entry(
            "test_session", "user", "Hello there!"
        )
        success2 = await manager.add_conversation_entry(
            "test_session", "assistant", "Hi! How can I help?"
        )
        
        assert success1 is True
        assert success2 is True
        
        # Verify conversation history
        history = await manager.get_conversation_history("test_session")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello there!"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi! How can I help?"

    @pytest.mark.asyncio
    async def test_conversation_history_limit(self, manager):
        """Test conversation history size limiting."""
        # Create context
        await manager.create_context(session_id="test_session")
        
        # Add many conversation entries (more than limit)
        for i in range(60):  # Limit is 50
            await manager.add_conversation_entry(
                "test_session", "user", f"Message {i}"
            )
        
        # Should only keep last 50
        history = await manager.get_conversation_history("test_session")
        assert len(history) == 50
        assert history[0]["content"] == "Message 10"  # First kept message
        assert history[-1]["content"] == "Message 59"  # Last message

    @pytest.mark.asyncio
    async def test_add_active_file(self, manager):
        """Test adding active files."""
        # Create context
        await manager.create_context(session_id="test_session")
        
        # Add active files
        success1 = await manager.add_active_file("test_session", "main.py")
        success2 = await manager.add_active_file("test_session", "utils.py")
        
        assert success1 is True
        assert success2 is True
        
        # Verify active files
        context = await manager.get_context("test_session")
        assert "main.py" in context.active_files
        assert "utils.py" in context.active_files

    @pytest.mark.asyncio
    async def test_remove_active_file(self, manager):
        """Test removing active files."""
        # Create context and add files
        await manager.create_context(session_id="test_session")
        await manager.add_active_file("test_session", "main.py")
        await manager.add_active_file("test_session", "utils.py")
        
        # Remove one file
        success = await manager.remove_active_file("test_session", "main.py")
        assert success is True
        
        # Verify file was removed
        context = await manager.get_context("test_session")
        assert "main.py" not in context.active_files
        assert "utils.py" in context.active_files

    @pytest.mark.asyncio
    async def test_active_files_limit(self, manager):
        """Test active files size limiting."""
        # Create context
        await manager.create_context(session_id="test_session")
        
        # Add many files (more than limit)
        for i in range(25):  # Limit is 20
            await manager.add_active_file("test_session", f"file_{i}.py")
        
        # Should only keep last 20
        context = await manager.get_context("test_session")
        assert len(context.active_files) == 20
        assert "file_5.py" in context.active_files  # First kept file
        assert "file_24.py" in context.active_files  # Last file

    @pytest.mark.asyncio
    async def test_clear_context(self, manager):
        """Test clearing context data."""
        # Create context with data
        await manager.create_context(session_id="test_session")
        await manager.add_conversation_entry("test_session", "user", "Hello")
        await manager.add_active_file("test_session", "main.py")
        
        # Clear context
        success = await manager.clear_context("test_session")
        assert success is True
        
        # Verify data is cleared but session remains
        context = await manager.get_context("test_session")
        assert context is not None
        assert len(context.conversation_history) == 0
        assert len(context.active_files) == 0
        assert len(context.metadata) == 0

    @pytest.mark.asyncio
    async def test_delete_context(self, manager):
        """Test deleting context completely."""
        # Create context
        await manager.create_context(session_id="test_session")
        
        # Verify it exists
        context = await manager.get_context("test_session")
        assert context is not None
        
        # Delete context
        success = await manager.delete_context("test_session")
        assert success is True
        
        # Verify it's gone
        context = await manager.get_context("test_session")
        assert context is None

    @pytest.mark.asyncio
    async def test_list_user_contexts(self, manager):
        """Test listing contexts for a user."""
        # Create contexts for different users
        await manager.create_context(session_id="session1", user_id="user1")
        await manager.create_context(session_id="session2", user_id="user2")
        await manager.create_context(session_id="session3", user_id="user1")
        
        # List contexts for user1
        user1_contexts = await manager.list_user_contexts("user1")
        assert len(user1_contexts) == 2
        
        session_ids = [c.session_id for c in user1_contexts]
        assert "session1" in session_ids
        assert "session3" in session_ids

    @pytest.mark.asyncio
    async def test_cleanup_expired_contexts(self, manager):
        """Test cleaning up expired contexts."""
        # Create contexts with different ages
        old_context = MCPContext(
            session_id="old_session",
            last_accessed=datetime.now() - timedelta(minutes=45)
        )
        recent_context = MCPContext(
            session_id="recent_session",
            last_accessed=datetime.now() - timedelta(minutes=10)
        )
        
        await manager.storage.store_context(old_context)
        await manager.storage.store_context(recent_context)
        
        # Clean up expired contexts
        cleaned = await manager.cleanup_expired_contexts()
        assert cleaned >= 1
        
        # Verify old context is gone, recent remains
        assert await manager.get_context("old_session") is None
        assert await manager.get_context("recent_session") is not None

    @pytest.mark.asyncio
    async def test_enforce_user_context_limits(self, manager):
        """Test enforcing user context limits."""
        # Create more contexts than the limit (5)
        for i in range(7):
            await manager.create_context(
                session_id=f"session_{i}",
                user_id="test_user"
            )
        
        # Enforce limits
        removed = await manager.enforce_user_context_limits("test_user")
        assert removed == 2
        
        # Verify only 5 contexts remain
        remaining = await manager.list_user_contexts("test_user")
        assert len(remaining) == 5

    @pytest.mark.asyncio
    async def test_get_context_stats(self, manager):
        """Test getting context statistics."""
        # Create some contexts
        await manager.create_context(session_id="session1", user_id="user1")
        await manager.create_context(session_id="session2", user_id="user2")
        
        stats = await manager.get_context_stats()
        
        assert "total_contexts" in stats
        assert "contexts_by_age" in stats
        assert "max_context_age_minutes" in stats
        assert "max_contexts_per_user" in stats
        assert "storage_stats" in stats
        
        assert stats["total_contexts"] == 2
        assert stats["max_context_age_minutes"] == 30
        assert stats["max_contexts_per_user"] == 5

    @pytest.mark.asyncio
    async def test_context_expiration(self, manager):
        """Test that expired contexts are not returned."""
        # Create context with old timestamp
        old_context = MCPContext(
            session_id="old_session",
            last_accessed=datetime.now() - timedelta(minutes=45)
        )
        await manager.storage.store_context(old_context)
        
        # Should not be returned due to expiration
        result = await manager.get_context("old_session")
        assert result is None

    @pytest.mark.asyncio
    async def test_session_isolation(self, manager):
        """Test that sessions are properly isolated."""
        import asyncio
        
        # Create contexts
        await manager.create_context(session_id="session1")
        await manager.create_context(session_id="session2")
        
        # Define concurrent operations on different sessions
        async def update_session1():
            await manager.update_context("session1", {"metadata": {"data": "session1_data"}})
        
        async def update_session2():
            await manager.update_context("session2", {"metadata": {"data": "session2_data"}})
        
        # Run concurrent operations
        await asyncio.gather(update_session1(), update_session2())
        
        # Verify isolation
        context1 = await manager.get_context("session1")
        context2 = await manager.get_context("session2")
        
        assert context1.metadata["data"] == "session1_data"
        assert context2.metadata["data"] == "session2_data"

    @pytest.mark.asyncio
    async def test_start_stop_manager(self, manager):
        """Test starting and stopping the manager."""
        # Start manager
        await manager.start()
        assert manager._cleanup_task is not None
        
        # Stop manager
        await manager.stop()
        assert manager._cleanup_task is None or manager._cleanup_task.cancelled()

    @pytest.mark.asyncio
    async def test_conversation_history_with_metadata(self, manager):
        """Test conversation entries with metadata."""
        await manager.create_context(session_id="test_session")
        
        # Add entry with metadata
        await manager.add_conversation_entry(
            "test_session",
            "user",
            "Hello",
            metadata={"tool": "code_completion", "language": "python"}
        )
        
        history = await manager.get_conversation_history("test_session")
        assert len(history) == 1
        assert history[0]["metadata"]["tool"] == "code_completion"
        assert history[0]["metadata"]["language"] == "python"

    @pytest.mark.asyncio
    async def test_get_conversation_history_with_limit(self, manager):
        """Test getting conversation history with limit."""
        await manager.create_context(session_id="test_session")
        
        # Add multiple entries
        for i in range(10):
            await manager.add_conversation_entry("test_session", "user", f"Message {i}")
        
        # Get limited history
        history = await manager.get_conversation_history("test_session", limit=5)
        assert len(history) == 5
        assert history[0]["content"] == "Message 5"  # Last 5 messages
        assert history[-1]["content"] == "Message 9"