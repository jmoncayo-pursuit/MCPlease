"""Tests for security integration with MCP server."""

import pytest
from unittest.mock import Mock, AsyncMock

from src.mcplease_mcp.server.server import MCPServer
from src.mcplease_mcp.security.manager import MCPSecurityManager
from src.mcplease_mcp.protocol.models import MCPRequest


class TestSecurityIntegration:
    """Test security integration with MCP server."""
    
    @pytest.fixture
    def mock_ai_adapter(self):
        """Create a mock AI adapter."""
        adapter = Mock()
        adapter.initialize = AsyncMock()
        adapter.is_model_ready = Mock(return_value=True)
        adapter.health_check = AsyncMock(return_value={"status": "healthy"})
        return adapter
    
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
    
    @pytest.fixture
    def server_with_security(self, mock_ai_adapter, security_manager):
        """Create MCP server with security manager."""
        return MCPServer(
            server_name="Test Server",
            transport_configs=[],  # No transports for testing
            ai_adapter=mock_ai_adapter,
            security_manager=security_manager
        )
    
    @pytest.fixture
    def server_with_auth(self, mock_ai_adapter, auth_security_manager):
        """Create MCP server with authentication required."""
        return MCPServer(
            server_name="Test Server",
            transport_configs=[],  # No transports for testing
            ai_adapter=mock_ai_adapter,
            security_manager=auth_security_manager
        )
    
    @pytest.mark.asyncio
    async def test_anonymous_message_handling(self, server_with_security):
        """Test message handling with anonymous authentication."""
        await server_with_security.start()
        
        try:
            # Create a test message
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            # Handle the message
            response = await server_with_security._handle_message(message)
            
            # Should get a successful response
            assert response is not None
            assert "error" not in response or response["error"] is None
            assert "result" in response
            assert "meta" in response["result"]
            assert "session_id" in response["result"]["meta"]
            
        finally:
            await server_with_security.stop()
    
    @pytest.mark.asyncio
    async def test_authenticated_message_handling(self, server_with_auth):
        """Test message handling with required authentication."""
        await server_with_auth.start()
        
        try:
            # Generate valid credentials
            user_info = {
                "user_id": "test_user", 
                "username": "testuser",
                "permissions": ["read", "tools/list", "tools/call"]
            }
            authenticator = server_with_auth.security_manager.authenticators[0]
            credentials = authenticator.generate_credentials(user_info)
            
            # Create a test message with credentials
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {
                    "credentials": {"token": credentials["token"]}
                }
            }
            
            # Handle the message
            response = await server_with_auth._handle_message(message)
            
            # Should get a successful response
            assert response is not None
            assert "error" not in response or response["error"] is None
            assert "result" in response
            assert "meta" in response["result"]
            assert "session_id" in response["result"]["meta"]
            
        finally:
            await server_with_auth.stop()
    
    @pytest.mark.asyncio
    async def test_unauthenticated_message_rejection(self, server_with_auth):
        """Test rejection of unauthenticated messages when auth is required."""
        await server_with_auth.start()
        
        try:
            # Create a test message without credentials
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            # Handle the message
            response = await server_with_auth._handle_message(message)
            
            # Should get an authentication error
            assert response is not None
            assert "error" in response
            assert response["error"]["code"] == -32001
            assert "Authentication required" in response["error"]["message"]
            
        finally:
            await server_with_auth.stop()
    
    @pytest.mark.asyncio
    async def test_invalid_credentials_rejection(self, server_with_auth):
        """Test rejection of invalid credentials."""
        await server_with_auth.start()
        
        try:
            # Create a test message with invalid credentials
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {
                    "credentials": {"token": "invalid_token"}
                }
            }
            
            # Handle the message
            response = await server_with_auth._handle_message(message)
            
            # Should get an authentication error
            assert response is not None
            assert "error" in response
            assert response["error"]["code"] == -32001
            assert "Authentication required" in response["error"]["message"]
            
        finally:
            await server_with_auth.stop()
    
    @pytest.mark.asyncio
    async def test_session_persistence(self, server_with_security):
        """Test session persistence across multiple requests."""
        await server_with_security.start()
        
        try:
            # First request creates session
            message1 = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            response1 = await server_with_security._handle_message(message1)
            assert response1 is not None
            session_id = response1["result"]["meta"]["session_id"]
            
            # Second request with same session ID
            message2 = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {
                    "session_id": session_id
                }
            }
            
            response2 = await server_with_security._handle_message(message2)
            assert response2 is not None
            assert response2["result"]["meta"]["session_id"] == session_id
            
        finally:
            await server_with_security.stop()
    
    @pytest.mark.asyncio
    async def test_credential_extraction(self, server_with_security):
        """Test credential extraction from different message formats."""
        # Test token in credentials
        message1 = {
            "params": {
                "credentials": {"token": "test_token"}
            }
        }
        credentials = server_with_security._extract_credentials(message1)
        assert credentials == {"token": "test_token"}
        
        # Test authorization header style
        message2 = {
            "params": {
                "authorization": "Bearer test_token"
            }
        }
        credentials = server_with_security._extract_credentials(message2)
        assert credentials == {"token": "test_token"}
        
        # Test direct token
        message3 = {
            "params": {
                "token": "test_token"
            }
        }
        credentials = server_with_security._extract_credentials(message3)
        assert credentials == {"token": "test_token"}
        
        # Test no credentials
        message4 = {
            "params": {}
        }
        credentials = server_with_security._extract_credentials(message4)
        assert credentials is None
    
    @pytest.mark.asyncio
    async def test_client_info_extraction(self, server_with_security):
        """Test client information extraction."""
        message = {
            "params": {
                "clientInfo": {
                    "name": "Test Client",
                    "version": "1.0.0"
                },
                "user_agent": "TestAgent/1.0"
            }
        }
        
        client_info = server_with_security._extract_client_info(message)
        assert client_info["name"] == "Test Client"
        assert client_info["version"] == "1.0.0"
        assert client_info["user_agent"] == "TestAgent/1.0"
    
    @pytest.mark.asyncio
    async def test_method_permission_checking(self, server_with_security):
        """Test method permission checking."""
        await server_with_security.start()
        
        try:
            # Create a session
            session = await server_with_security.security_manager.authenticate_request()
            
            # Test various method permissions
            assert await server_with_security._check_method_permission(session, "initialize") is True
            assert await server_with_security._check_method_permission(session, "tools/list") is True
            assert await server_with_security._check_method_permission(session, "tools/call") is True
            assert await server_with_security._check_method_permission(session, "resources/list") is True
            
            # Test unknown method (should default to read permission)
            assert await server_with_security._check_method_permission(session, "unknown/method") is True
            
        finally:
            await server_with_security.stop()
    
    @pytest.mark.asyncio
    async def test_health_check_with_security(self, server_with_security):
        """Test health check includes security information."""
        await server_with_security.start()
        
        try:
            health = await server_with_security.health_check()
            
            assert "components" in health
            assert "security_manager" in health["components"]
            assert health["components"]["security_manager"]["status"] == "healthy"
            assert "stats" in health["components"]["security_manager"]
            
            stats = health["components"]["security_manager"]["stats"]
            assert "total_sessions" in stats
            assert "tls_enabled" in stats
            assert "auth_required" in stats
            
        finally:
            await server_with_security.stop()


if __name__ == "__main__":
    pytest.main([__file__])