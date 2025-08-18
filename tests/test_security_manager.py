"""Tests for MCPSecurityManager."""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock

from src.mcplease_mcp.security.manager import MCPSecurityManager, SecuritySession
from src.mcplease_mcp.security.auth import TokenAuthenticator


class TestSecuritySession:
    """Test SecuritySession class."""
    
    def test_session_creation(self):
        """Test creating a security session."""
        session = SecuritySession(
            session_id="test_session",
            user_info={"user_id": "test_user"},
            authenticated_at=time.time(),
            last_activity=time.time()
        )
        
        assert session.session_id == "test_session"
        assert session.user_info["user_id"] == "test_user"
        assert not session.is_expired(3600)  # 1 hour timeout
    
    def test_session_expiry(self):
        """Test session expiry logic."""
        old_time = time.time() - 7200  # 2 hours ago
        session = SecuritySession(
            session_id="test_session",
            user_info={"user_id": "test_user"},
            authenticated_at=old_time,
            last_activity=old_time
        )
        
        assert session.is_expired(3600)  # 1 hour timeout
        assert not session.is_expired(10800)  # 3 hour timeout
    
    def test_activity_update(self):
        """Test updating session activity."""
        old_time = time.time() - 3700  # More than 1 hour ago
        session = SecuritySession(
            session_id="test_session",
            user_info={"user_id": "test_user"},
            authenticated_at=old_time,
            last_activity=old_time
        )
        
        # Should be expired with 1 hour timeout
        assert session.is_expired(3600)
        
        # Update activity
        session.update_activity()
        
        # Should no longer be expired
        assert not session.is_expired(3600)


class TestMCPSecurityManager:
    """Test MCPSecurityManager class."""
    
    @pytest.fixture
    def security_manager(self):
        """Create a security manager for testing."""
        return MCPSecurityManager(
            session_timeout_minutes=60,
            require_auth=False
        )
    
    @pytest.fixture
    def auth_security_manager(self):
        """Create a security manager with authentication required."""
        auth_config = {
            "token": {"use_jwt": False}
        }
        return MCPSecurityManager(
            auth_config=auth_config,
            session_timeout_minutes=60,
            require_auth=True
        )
    
    @pytest.mark.asyncio
    async def test_anonymous_authentication(self, security_manager):
        """Test anonymous authentication when auth not required."""
        await security_manager.start()
        
        try:
            session = await security_manager.authenticate_request()
            
            assert session is not None
            assert session.user_info["user_id"] == "anonymous"
            assert session.session_id.startswith("anon_")
            
            # Should be able to validate the session
            validated_session = await security_manager.validate_session(session.session_id)
            assert validated_session is not None
            assert validated_session.session_id == session.session_id
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_token_authentication(self, auth_security_manager):
        """Test token-based authentication."""
        await auth_security_manager.start()
        
        try:
            # Generate credentials for a test user
            user_info = {"user_id": "test_user", "username": "testuser"}
            authenticator = auth_security_manager.authenticators[0]
            credentials = authenticator.generate_credentials(user_info)
            
            # Authenticate with the generated token
            session = await auth_security_manager.authenticate_request(
                credentials={"token": credentials["token"]}
            )
            
            assert session is not None
            assert session.user_info["user_id"] == "test_user"
            assert session.session_id.startswith("auth_")
            
        finally:
            await auth_security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_authentication_failure(self, auth_security_manager):
        """Test authentication failure."""
        await auth_security_manager.start()
        
        try:
            # Try to authenticate without credentials
            session = await auth_security_manager.authenticate_request()
            assert session is None
            
            # Try to authenticate with invalid token
            session = await auth_security_manager.authenticate_request(
                credentials={"token": "invalid_token"}
            )
            assert session is None
            
        finally:
            await auth_security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_validation(self, security_manager):
        """Test session validation."""
        await security_manager.start()
        
        try:
            # Create a session
            session = await security_manager.authenticate_request()
            session_id = session.session_id
            
            # Validate the session
            validated_session = await security_manager.validate_session(session_id)
            assert validated_session is not None
            assert validated_session.session_id == session_id
            
            # Try to validate non-existent session
            invalid_session = await security_manager.validate_session("invalid_session")
            assert invalid_session is None
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_revocation(self, security_manager):
        """Test session revocation."""
        await security_manager.start()
        
        try:
            # Create a session
            session = await security_manager.authenticate_request()
            session_id = session.session_id
            
            # Verify session exists
            validated_session = await security_manager.validate_session(session_id)
            assert validated_session is not None
            
            # Revoke the session
            revoked = await security_manager.revoke_session(session_id)
            assert revoked is True
            
            # Verify session no longer exists
            validated_session = await security_manager.validate_session(session_id)
            assert validated_session is None
            
            # Try to revoke non-existent session
            revoked = await security_manager.revoke_session("invalid_session")
            assert revoked is False
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_permission_checking(self, security_manager):
        """Test permission checking."""
        await security_manager.start()
        
        try:
            # Create anonymous session
            session = await security_manager.authenticate_request()
            session_id = session.session_id
            
            # Check basic permissions (should be allowed for anonymous)
            assert await security_manager.check_permission(session_id, "read") is True
            assert await security_manager.check_permission(session_id, "tools/call") is True
            assert await security_manager.check_permission(session_id, "tools/list") is True
            
            # Check admin permission (should be denied for anonymous)
            assert await security_manager.check_permission(session_id, "admin") is False
            
            # Check permission for invalid session
            assert await security_manager.check_permission("invalid_session", "read") is False
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_stats(self, security_manager):
        """Test session statistics."""
        await security_manager.start()
        
        try:
            # Get initial stats
            stats = await security_manager.get_session_stats()
            assert stats["total_sessions"] == 0
            assert stats["authenticated_sessions"] == 0
            assert stats["anonymous_sessions"] == 0
            
            # Create some sessions
            session1 = await security_manager.authenticate_request()
            session2 = await security_manager.authenticate_request()
            
            # Get updated stats
            stats = await security_manager.get_session_stats()
            assert stats["total_sessions"] == 2
            assert stats["authenticated_sessions"] == 0  # Both are anonymous
            assert stats["anonymous_sessions"] == 2
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_tls_context(self):
        """Test TLS context creation."""
        # Test without TLS
        manager = MCPSecurityManager(enable_tls=False)
        assert manager.get_tls_context() is None
        
        # Test with TLS but no cert/key paths
        manager = MCPSecurityManager(enable_tls=True)
        assert manager.get_tls_context() is None
    
    @pytest.mark.asyncio
    async def test_session_cleanup(self, security_manager):
        """Test session cleanup functionality."""
        # Use very short timeout for testing
        security_manager.session_timeout_seconds = 1
        await security_manager.start()
        
        try:
            # Create a session
            session = await security_manager.authenticate_request()
            session_id = session.session_id
            
            # Verify session exists
            validated_session = await security_manager.validate_session(session_id)
            assert validated_session is not None
            
            # Wait for session to expire
            await asyncio.sleep(2)
            
            # Try to validate expired session
            validated_session = await security_manager.validate_session(session_id)
            assert validated_session is None
            
        finally:
            await security_manager.stop()


if __name__ == "__main__":
    pytest.main([__file__])