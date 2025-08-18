"""Tests for network security and multi-user support."""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch

from src.mcplease_mcp.security.network import (
    NetworkSecurityManager, 
    NetworkPolicy, 
    UserSession,
    create_default_network_policy,
    create_production_network_policy
)


class TestNetworkPolicy:
    """Test NetworkPolicy configuration."""
    
    def test_default_policy_creation(self):
        """Test creating default network policy."""
        policy = create_default_network_policy()
        
        assert "127.0.0.0/8" in policy.allowed_networks
        assert "192.168.0.0/16" in policy.allowed_networks
        assert policy.rate_limit_per_ip == 100
        assert policy.max_connections_per_ip == 10
        assert policy.require_tls is False
        assert 8000 in policy.allowed_ports
        assert 8001 in policy.allowed_ports
    
    def test_production_policy_creation(self):
        """Test creating production network policy."""
        policy = create_production_network_policy()
        
        assert policy.rate_limit_per_ip == 50
        assert policy.max_connections_per_ip == 5
        assert policy.require_tls is True
        assert 8000 in policy.allowed_ports
        assert 8001 in policy.allowed_ports


class TestNetworkSecurityManager:
    """Test NetworkSecurityManager functionality."""
    
    @pytest.fixture
    def network_policy(self):
        """Create test network policy."""
        return NetworkPolicy(
            allowed_networks={"192.168.1.0/24", "10.0.0.0/8"},
            blocked_ips={"192.168.1.100"},
            rate_limit_per_ip=10,
            max_connections_per_ip=3,
            allowed_ports={8000, 8001}
        )
    
    @pytest.fixture
    def security_manager(self, network_policy):
        """Create network security manager for testing."""
        return NetworkSecurityManager(
            network_policy=network_policy,
            enable_rate_limiting=True,
            enable_connection_limiting=True,
            session_timeout_minutes=1  # Short timeout for testing
        )
    
    @pytest.mark.asyncio
    async def test_network_access_validation_allowed(self, security_manager):
        """Test network access validation for allowed IPs."""
        await security_manager.start()
        
        try:
            # Test allowed network
            allowed, reason = await security_manager.validate_network_access("192.168.1.50", 8000)
            assert allowed is True
            assert reason is None
            
            # Test another allowed network
            allowed, reason = await security_manager.validate_network_access("10.0.0.1", 8001)
            assert allowed is True
            assert reason is None
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_network_access_validation_blocked_ip(self, security_manager):
        """Test network access validation for blocked IPs."""
        await security_manager.start()
        
        try:
            # Test blocked IP
            allowed, reason = await security_manager.validate_network_access("192.168.1.100", 8000)
            assert allowed is False
            assert "blocked" in reason.lower()
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_network_access_validation_disallowed_network(self, security_manager):
        """Test network access validation for disallowed networks."""
        await security_manager.start()
        
        try:
            # Test IP not in allowed networks
            allowed, reason = await security_manager.validate_network_access("203.0.113.1", 8000)
            assert allowed is False
            assert "not in allowed" in reason.lower()
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_network_access_validation_disallowed_port(self, security_manager):
        """Test network access validation for disallowed ports."""
        await security_manager.start()
        
        try:
            # Test disallowed port
            allowed, reason = await security_manager.validate_network_access("192.168.1.50", 9000)
            assert allowed is False
            assert "not allowed" in reason.lower()
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, security_manager):
        """Test rate limiting functionality."""
        await security_manager.start()
        
        try:
            client_ip = "192.168.1.50"
            
            # Make requests up to the limit
            for i in range(10):
                allowed, reason = await security_manager.check_rate_limit(client_ip)
                assert allowed is True
                assert reason is None
            
            # Next request should be rate limited
            allowed, reason = await security_manager.check_rate_limit(client_ip)
            assert allowed is False
            assert "rate limit" in reason.lower()
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_connection_limiting(self, security_manager):
        """Test connection limiting functionality."""
        await security_manager.start()
        
        try:
            client_ip = "192.168.1.50"
            
            # Register connections up to the limit
            for i in range(3):
                allowed, reason = await security_manager.check_connection_limit(client_ip)
                assert allowed is True
                await security_manager.register_connection(client_ip)
            
            # Next connection should be limited
            allowed, reason = await security_manager.check_connection_limit(client_ip)
            assert allowed is False
            assert "connection limit" in reason.lower()
            
            # Unregister a connection
            await security_manager.unregister_connection(client_ip)
            
            # Should be allowed again
            allowed, reason = await security_manager.check_connection_limit(client_ip)
            assert allowed is True
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_user_session_management(self, security_manager):
        """Test user session creation and management."""
        await security_manager.start()
        
        try:
            # Create user session
            session = await security_manager.create_user_session(
                user_id="test_user",
                session_id="test_session",
                client_ip="192.168.1.50",
                user_agent="TestAgent/1.0",
                permissions={"read", "write"}
            )
            
            assert session.user_id == "test_user"
            assert session.session_id == "test_session"
            assert session.ip_address == "192.168.1.50"
            assert session.user_agent == "TestAgent/1.0"
            assert "read" in session.permissions
            assert "write" in session.permissions
            
            # Retrieve session
            retrieved_session = await security_manager.get_user_session("test_session")
            assert retrieved_session is not None
            assert retrieved_session.user_id == "test_user"
            
            # Update session activity
            updated = await security_manager.update_session_activity("test_session")
            assert updated is True
            
            # Revoke session
            revoked = await security_manager.revoke_user_session("test_session")
            assert revoked is True
            
            # Session should no longer exist
            retrieved_session = await security_manager.get_user_session("test_session")
            assert retrieved_session is None
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_expiration(self, security_manager):
        """Test session expiration functionality."""
        await security_manager.start()
        
        try:
            # Create session
            session = await security_manager.create_user_session(
                user_id="test_user",
                session_id="test_session",
                client_ip="192.168.1.50"
            )
            
            # Manually set old activity time
            session.last_activity = time.time() - 120  # 2 minutes ago
            
            # Session should be expired (timeout is 1 minute)
            retrieved_session = await security_manager.get_user_session("test_session")
            assert retrieved_session is None
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_revoke_user_sessions(self, security_manager):
        """Test revoking all sessions for a user."""
        await security_manager.start()
        
        try:
            # Create multiple sessions for the same user
            await security_manager.create_user_session(
                user_id="test_user",
                session_id="session1",
                client_ip="192.168.1.50"
            )
            
            await security_manager.create_user_session(
                user_id="test_user",
                session_id="session2",
                client_ip="192.168.1.51"
            )
            
            await security_manager.create_user_session(
                user_id="other_user",
                session_id="session3",
                client_ip="192.168.1.52"
            )
            
            # Revoke all sessions for test_user
            revoked_count = await security_manager.revoke_user_sessions("test_user")
            assert revoked_count == 2
            
            # test_user sessions should be gone
            assert await security_manager.get_user_session("session1") is None
            assert await security_manager.get_user_session("session2") is None
            
            # other_user session should still exist
            assert await security_manager.get_user_session("session3") is not None
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_revoke_ip_sessions(self, security_manager):
        """Test revoking all sessions from an IP address."""
        await security_manager.start()
        
        try:
            # Create sessions from different IPs
            await security_manager.create_user_session(
                user_id="user1",
                session_id="session1",
                client_ip="192.168.1.50"
            )
            
            await security_manager.create_user_session(
                user_id="user2",
                session_id="session2",
                client_ip="192.168.1.50"
            )
            
            await security_manager.create_user_session(
                user_id="user3",
                session_id="session3",
                client_ip="192.168.1.51"
            )
            
            # Revoke all sessions from IP 192.168.1.50
            revoked_count = await security_manager.revoke_ip_sessions("192.168.1.50")
            assert revoked_count == 2
            
            # Sessions from 192.168.1.50 should be gone
            assert await security_manager.get_user_session("session1") is None
            assert await security_manager.get_user_session("session2") is None
            
            # Session from 192.168.1.51 should still exist
            assert await security_manager.get_user_session("session3") is not None
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_security_stats(self, security_manager):
        """Test security statistics collection."""
        await security_manager.start()
        
        try:
            # Create some sessions and connections
            await security_manager.create_user_session(
                user_id="user1",
                session_id="session1",
                client_ip="192.168.1.50"
            )
            
            await security_manager.create_user_session(
                user_id="user2",
                session_id="session2",
                client_ip="192.168.1.51"
            )
            
            await security_manager.register_connection("192.168.1.50")
            await security_manager.register_connection("192.168.1.51")
            
            # Get stats
            stats = await security_manager.get_security_stats()
            
            assert stats["total_sessions"] == 2
            assert stats["unique_users"] == 2
            assert stats["unique_session_ips"] == 2
            assert stats["total_connections"] == 2
            assert stats["unique_connection_ips"] == 2
            assert stats["rate_limiting_enabled"] is True
            assert stats["connection_limiting_enabled"] is True
            assert stats["session_timeout_minutes"] == 1
            
            # Check network policy stats
            policy_stats = stats["network_policy"]
            assert policy_stats["rate_limit_per_ip"] == 10
            assert policy_stats["max_connections_per_ip"] == 3
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_tls_certificate_setup(self, security_manager, tmp_path):
        """Test TLS certificate setup."""
        await security_manager.start()
        
        try:
            # Setup TLS certificates
            cert_dir = tmp_path / "certs"
            success = await security_manager.setup_tls_certificates(cert_dir, "localhost")
            
            # Check if certificates were created (may fail if cryptography not available)
            if success:
                assert security_manager.tls_context is not None
                assert (cert_dir / "server.crt").exists()
                assert (cert_dir / "server.key").exists()
            else:
                # If cryptography not available, that's expected
                assert security_manager.tls_context is None
            
        finally:
            await security_manager.stop()
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, security_manager):
        """Test automatic cleanup of expired sessions."""
        # Use very short timeout for testing
        security_manager.session_timeout_seconds = 1
        await security_manager.start()
        
        try:
            # Create session
            await security_manager.create_user_session(
                user_id="test_user",
                session_id="test_session",
                client_ip="192.168.1.50"
            )
            
            # Verify session exists
            session = await security_manager.get_user_session("test_session")
            assert session is not None
            
            # Wait for session to expire
            await asyncio.sleep(2)
            
            # Trigger cleanup manually (normally done by background task)
            # Simulate the cleanup logic
            now = time.time()
            async with security_manager.session_lock:
                expired_sessions = [
                    session_id for session_id, session in security_manager.user_sessions.items()
                    if now - session.last_activity > security_manager.session_timeout_seconds
                ]
                
                for session_id in expired_sessions:
                    await security_manager._remove_session(session_id)
            
            # Session should be cleaned up
            session = await security_manager.get_user_session("test_session")
            assert session is None
            
        finally:
            await security_manager.stop()


class TestNetworkSecurityIntegration:
    """Test network security integration with MCP server."""
    
    @pytest.mark.asyncio
    async def test_network_validation_in_message_handling(self):
        """Test network validation during message handling."""
        from src.mcplease_mcp.server.server import MCPServer
        from src.mcplease_mcp.security.network import NetworkPolicy
        
        # Create restrictive network policy
        network_policy = NetworkPolicy(
            allowed_ips={"192.168.1.50"},  # Only allow specific IP
            allowed_ports={8000}
        )
        
        network_security_manager = NetworkSecurityManager(network_policy=network_policy)
        
        server = MCPServer(
            transport_configs=[],  # No transports for testing
            network_security_manager=network_security_manager
        )
        
        await server.start()
        
        try:
            # Test allowed IP
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            response = await server._handle_message(message, "192.168.1.50")
            assert "error" not in response or response["error"] is None
            
            # Test blocked IP
            response = await server._handle_message(message, "203.0.113.1")
            assert "error" in response
            assert response["error"]["code"] == -32003
            assert "Network access denied" in response["error"]["message"]
            
        finally:
            await server.stop()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_in_message_handling(self):
        """Test rate limiting during message handling."""
        from src.mcplease_mcp.server.server import MCPServer
        from src.mcplease_mcp.security.network import NetworkPolicy
        
        # Create policy with very low rate limit
        network_policy = NetworkPolicy(
            allowed_networks={"192.168.1.0/24"},
            rate_limit_per_ip=2,  # Very low limit for testing
            allowed_ports={8000}
        )
        
        network_security_manager = NetworkSecurityManager(network_policy=network_policy)
        
        server = MCPServer(
            transport_configs=[],  # No transports for testing
            network_security_manager=network_security_manager
        )
        
        await server.start()
        
        try:
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            client_ip = "192.168.1.50"
            
            # First two requests should succeed
            for i in range(2):
                response = await server._handle_message(message, client_ip)
                assert "error" not in response or response["error"] is None
            
            # Third request should be rate limited
            response = await server._handle_message(message, client_ip)
            assert "error" in response
            assert response["error"]["code"] == -32004
            assert "Rate limit exceeded" in response["error"]["message"]
            
        finally:
            await server.stop()


if __name__ == "__main__":
    pytest.main([__file__])